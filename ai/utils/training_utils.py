"""
Utilidades de entrenamiento para DogDex.
Funciones auxiliares reutilizables: generadores de datos, visualización
y evaluación. Ninguna de estas funciones construye ni entrena modelos.
"""

import json
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report

from tensorflow.keras.preprocessing.image import ImageDataGenerator


IMG_SIZE   = (224, 224)
BATCH_SIZE = 32


# ── Generadores de datos ─────────────────────────────────────

def build_generators(processed_dir: Path, batch_size: int = BATCH_SIZE):
    """
    Crea los tres generadores de imágenes para train / validation / test.

    El data augmentation solo se aplica en train para enriquecer el conjunto
    sin modificar las imágenes de validación ni de test.
    El rescale 1/255 normaliza los píxeles al rango [0, 1] que espera MobileNetV2.
    """
    train_datagen = ImageDataGenerator(
        rescale=1.0 / 255,
        rotation_range=20,         # rotación moderada (±20°)
        width_shift_range=0.10,    # desplazamiento horizontal ±10%
        height_shift_range=0.10,
        horizontal_flip=True,      # flip horizontal (natural en fotos de perros)
        zoom_range=0.10,           # zoom sutil ±10%
        fill_mode='nearest',       # rellena píxeles vacíos con el vecino más cercano
    )

    base_datagen = ImageDataGenerator(rescale=1.0 / 255)

    common = dict(
        target_size=IMG_SIZE,
        batch_size=batch_size,
        class_mode='categorical',
    )

    train_gen = train_datagen.flow_from_directory(
        processed_dir / 'train',
        shuffle=True,
        **common,
    )
    val_gen = base_datagen.flow_from_directory(
        processed_dir / 'validation',
        shuffle=False,
        **common,
    )
    # shuffle=False en test es obligatorio para que las predicciones
    # se alineen con test_gen.classes al evaluar con classification_report
    test_gen = base_datagen.flow_from_directory(
        processed_dir / 'test',
        shuffle=False,
        **common,
    )

    return train_gen, val_gen, test_gen


# ── Visualización ────────────────────────────────────────────

def plot_history(history, phase_name: str, output_dir: Path) -> None:
    """
    Genera y guarda una figura con dos subgráficas: accuracy y loss.
    Muestra train vs validation para detectar overfitting visualmente.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    fig.suptitle(f'Entrenamiento — {phase_name}', fontsize=14)

    epochs = range(1, len(history.history['accuracy']) + 1)

    # Accuracy
    ax1.plot(epochs, history.history['accuracy'],     label='Train')
    ax1.plot(epochs, history.history['val_accuracy'], label='Validation')
    ax1.set_title('Accuracy')
    ax1.set_xlabel('Épocas')
    ax1.set_ylabel('Accuracy')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Loss
    ax2.plot(epochs, history.history['loss'],     label='Train')
    ax2.plot(epochs, history.history['val_loss'], label='Validation')
    ax2.set_title('Loss')
    ax2.set_xlabel('Épocas')
    ax2.set_ylabel('Loss')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    output_path = output_dir / f'training_{phase_name.lower().replace(" ", "_")}.png'
    plt.savefig(output_path, dpi=150)
    plt.close()
    print(f'  Gráfica guardada: {output_path}')


# ── Evaluación final ─────────────────────────────────────────

def evaluate_on_test(model, test_gen, output_dir: Path) -> None:
    """
    Evalúa el modelo sobre el conjunto de test y guarda:
    - métricas globales (loss y accuracy)
    - reporte por clase (precision, recall, F1)
    """
    print('\nEvaluando sobre conjunto de test...')
    test_gen.reset()

    loss, accuracy = model.evaluate(test_gen, verbose=0)
    print(f'  Test loss:     {loss:.4f}')
    print(f'  Test accuracy: {accuracy:.4f} ({accuracy * 100:.1f}%)')

    # Obtener predicciones y etiquetas reales para el reporte por clase
    test_gen.reset()
    predictions     = model.predict(test_gen, verbose=0)
    predicted_labels = np.argmax(predictions, axis=1)
    true_labels      = test_gen.classes
    class_names      = list(test_gen.class_indices.keys())

    report = classification_report(
        true_labels,
        predicted_labels,
        target_names=class_names,
        zero_division=0,
    )

    report_path = output_dir / 'evaluation_report.txt'
    with open(report_path, 'w') as f:
        f.write(f'DogDex — Reporte de evaluación sobre test set\n')
        f.write('=' * 50 + '\n\n')
        f.write(f'Loss:     {loss:.4f}\n')
        f.write(f'Accuracy: {accuracy:.4f} ({accuracy * 100:.1f}%)\n\n')
        f.write('Reporte por clase:\n')
        f.write(report)

    print(f'\n{report}')
    print(f'  Reporte guardado: {report_path}')
