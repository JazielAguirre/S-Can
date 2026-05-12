"""
train.py — DogDex
─────────────────
Entrena un clasificador de razas caninas usando Transfer Learning
con MobileNetV2 preentrenado en ImageNet.

Fases:
  1. Feature extraction  — base congelada, solo entrena la cabeza
  2. Fine-tuning         — se descongela el final de la base con LR muy bajo

Uso:
    python train.py                   # ambas fases
    python train.py --skip-finetune   # solo fase 1

Requisitos:
    - dataset/processed/ con subdirectorios train/, validation/, test/
    - Ejecutar primero: python prepare_dataset.py
"""

import json
import argparse
from pathlib import Path

import tensorflow as tf
from tensorflow.keras import Model
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam

from utils.training_utils import build_generators, plot_history, evaluate_on_test

# ── Configuración ────────────────────────────────────────────

PROCESSED_DIR = Path('dataset/processed')
MODELS_DIR    = Path('models')
IMG_SIZE      = (224, 224)
BATCH_SIZE    = 32

# Fase 1: feature extraction
EPOCHS_P1    = 20
LR_P1        = 1e-3

# Fase 2: fine-tuning
EPOCHS_P2          = 10
LR_P2              = 1e-5        # LR muy bajo para no destruir pesos preentrenados
FINETUNE_FROM      = 100         # descongelar capas a partir de este índice
MIN_VAL_ACC_FINETUNE = 0.60      # no hacer fine-tuning si fase 1 no llega aquí


# ── Arquitectura del modelo ───────────────────────────────────

def build_model(num_classes: int) -> Model:
    """
    Construye el modelo con MobileNetV2 como base y una cabeza clasificadora.
    La base se carga con pesos ImageNet y se congela completamente para fase 1.
    """
    base = MobileNetV2(
        input_shape=(*IMG_SIZE, 3),
        include_top=False,          # excluye la capa densa original de ImageNet
        weights='imagenet',
    )
    base.trainable = False          # congela toda la base para fase 1

    # Cabeza clasificadora según arquitectura aprobada
    x = GlobalAveragePooling2D()(base.output)
    x = Dense(128, activation='relu')(x)
    x = Dropout(0.3)(x)
    output = Dense(num_classes, activation='softmax')(x)

    model = Model(inputs=base.input, outputs=output)
    return model


# ── Callbacks ─────────────────────────────────────────────────

def get_callbacks(phase: str, models_dir: Path) -> list:
    """
    Devuelve la lista de callbacks para una fase dada.
    ModelCheckpoint guarda solo el mejor modelo por val_accuracy.
    EarlyStopping restaura los mejores pesos si no hay mejora.
    """
    return [
        EarlyStopping(
            monitor='val_accuracy',
            patience=5 if phase == 'phase1' else 4,
            restore_best_weights=True,
            verbose=1,
        ),
        ModelCheckpoint(
            filepath=str(models_dir / 'dogdex_model.keras'),
            monitor='val_accuracy',
            save_best_only=True,
            verbose=1,
        ),
        ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.3,
            patience=3 if phase == 'phase1' else 2,
            min_lr=1e-7,
            verbose=1,
        ),
    ]


# ── Fase 1: feature extraction ────────────────────────────────

def run_phase1(model: Model, train_gen, val_gen):
    """
    Entrena solo la cabeza clasificadora con la base completamente congelada.
    El modelo aprende a distinguir razas usando las representaciones de ImageNet.
    """
    print('\n' + '═' * 55)
    print('  FASE 1 — Feature Extraction')
    print(f'  Base congelada · LR: {LR_P1} · Épocas máx: {EPOCHS_P1}')
    print('═' * 55)

    model.compile(
        optimizer=Adam(learning_rate=LR_P1),
        loss='categorical_crossentropy',
        metrics=['accuracy'],
    )

    history = model.fit(
        train_gen,
        epochs=EPOCHS_P1,
        validation_data=val_gen,
        callbacks=get_callbacks('phase1', MODELS_DIR),
        verbose=1,
    )

    best_val_acc = max(history.history['val_accuracy'])
    print(f'\n  Mejor val_accuracy fase 1: {best_val_acc:.4f} ({best_val_acc * 100:.1f}%)')
    return history


# ── Fase 2: fine-tuning ───────────────────────────────────────

def run_phase2(model: Model, train_gen, val_gen, history_p1):
    """
    Descongela el bloque final de MobileNetV2 y reentrena con LR muy bajo.
    Solo se ejecuta si fase 1 alcanzó la accuracy mínima configurada.

    FINETUNE_FROM controla cuántas capas quedan congeladas: las capas anteriores
    mantienen los patrones genéricos (bordes, texturas) mientras las últimas
    se especializan en razas caninas.
    """
    best_val_acc = max(history_p1.history['val_accuracy'])

    if best_val_acc < MIN_VAL_ACC_FINETUNE:
        print(f'\n  Fine-tuning omitido: val_accuracy ({best_val_acc:.2f}) '
              f'< umbral mínimo ({MIN_VAL_ACC_FINETUNE}).')
        print('  Considera más datos o más épocas en fase 1.')
        return None

    print('\n' + '═' * 55)
    print('  FASE 2 — Fine-Tuning')
    print(f'  Descongelando capas desde índice {FINETUNE_FROM}')
    print(f'  LR: {LR_P2} · Épocas máx: {EPOCHS_P2}')
    print('═' * 55)

    # Descongelar capas a partir del índice dado
    base = model.layers[0]             # MobileNetV2 es la primera capa del modelo
    base.trainable = True
    for layer in base.layers[:FINETUNE_FROM]:
        layer.trainable = False

    trainable = sum(1 for l in model.layers if l.trainable)
    print(f'  Capas entrenables: {trainable}')

    # LR muy bajo para no sobreescribir los pesos preentrenados abruptamente
    model.compile(
        optimizer=Adam(learning_rate=LR_P2),
        loss='categorical_crossentropy',
        metrics=['accuracy'],
    )

    history = model.fit(
        train_gen,
        epochs=EPOCHS_P2,
        validation_data=val_gen,
        callbacks=get_callbacks('phase2', MODELS_DIR),
        verbose=1,
    )

    best_val_acc_p2 = max(history.history['val_accuracy'])
    print(f'\n  Mejor val_accuracy fase 2: {best_val_acc_p2:.4f} ({best_val_acc_p2 * 100:.1f}%)')
    return history


# ── Exportación de artefactos ─────────────────────────────────

def save_artifacts(model: Model, train_gen) -> None:
    """
    Guarda el modelo en dos formatos y el mapeo índice→raza.
    Se guardan ambos formatos para máxima compatibilidad:
    - .keras : formato nativo Keras (recomendado, cargado en predict.py)
    - .h5    : formato legacy, compatible con TF 2.x anteriores
    """
    MODELS_DIR.mkdir(exist_ok=True)

    # .keras ya fue guardado por ModelCheckpoint durante el entrenamiento;
    # se vuelve a guardar explícitamente para garantizar el estado final
    model.save(MODELS_DIR / 'dogdex_model.keras')
    model.save(MODELS_DIR / 'dogdex_model.h5')
    print(f'\n  Modelo guardado: {MODELS_DIR / "dogdex_model.keras"}')
    print(f'  Modelo guardado: {MODELS_DIR / "dogdex_model.h5"}')

    # Invertir class_indices: Keras devuelve {nombre: índice},
    # pero en inferencia necesitamos {índice: nombre}
    inverted = {str(v): k for k, v in train_gen.class_indices.items()}
    indices_path = MODELS_DIR / 'class_indices.json'
    with open(indices_path, 'w', encoding='utf-8') as f:
        json.dump(inverted, f, ensure_ascii=False, indent=2)
    print(f'  Clases guardadas: {indices_path}')
    print(f'  Razas: {list(train_gen.class_indices.keys())}')


# ── Punto de entrada ──────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description='Entrenamiento DogDex con MobileNetV2')
    parser.add_argument(
        '--skip-finetune',
        action='store_true',
        help='Ejecutar solo fase 1 (feature extraction)',
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    MODELS_DIR.mkdir(exist_ok=True)

    print(f'\nTensorFlow: {tf.__version__}')
    gpus = tf.config.list_physical_devices('GPU')
    print(f'GPU disponible: {"Sí — " + gpus[0].name if gpus else "No (entrenando en CPU)"}')

    # Verificar que el dataset procesado existe
    if not (PROCESSED_DIR / 'train').exists():
        print(f'\nError: no se encontró {PROCESSED_DIR / "train"}')
        print('Ejecuta primero: python prepare_dataset.py')
        raise SystemExit(1)

    # Cargar generadores
    print('\nCargando dataset...')
    train_gen, val_gen, test_gen = build_generators(PROCESSED_DIR, BATCH_SIZE)
    num_classes = len(train_gen.class_indices)

    print(f'  Clases: {num_classes} razas → {list(train_gen.class_indices.keys())}')
    print(f'  Train:      {train_gen.samples} imágenes')
    print(f'  Validation: {val_gen.samples} imágenes')
    print(f'  Test:       {test_gen.samples} imágenes')

    # Construir modelo
    model = build_model(num_classes)
    total_params = model.count_params()
    print(f'\nParámetros totales:     {total_params:,}')
    print(f'Parámetros entrenables: {sum(tf.keras.backend.count_params(w) for w in model.trainable_weights):,}')

    # ── Fase 1 ───────────────────────────────────────────
    history_p1 = run_phase1(model, train_gen, val_gen)
    plot_history(history_p1, 'Fase 1 - Feature Extraction', MODELS_DIR)

    # ── Fase 2 (opcional) ─────────────────────────────────
    history_p2 = None
    if not args.skip_finetune:
        history_p2 = run_phase2(model, train_gen, val_gen, history_p1)
        if history_p2:
            plot_history(history_p2, 'Fase 2 - Fine Tuning', MODELS_DIR)

    # ── Guardar artefactos ────────────────────────────────
    print('\n' + '─' * 55)
    print('  Guardando artefactos...')
    save_artifacts(model, train_gen)

    # ── Evaluación final sobre test ───────────────────────
    evaluate_on_test(model, test_gen, MODELS_DIR)

    print('\n' + '═' * 55)
    print('  Entrenamiento completado.')
    print(f'  Artefactos en: {MODELS_DIR.resolve()}')
    print('═' * 55)


if __name__ == '__main__':
    main()
