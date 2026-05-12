# Guía de Entrenamiento del Modelo — S-Can

Este documento cubre: cómo preparar el dataset, cómo entrenar el modelo desde cero, cómo reentrenarlo con nuevas razas, y cómo reemplazar el modelo sin romper la arquitectura.

---

## Prerrequisitos

```bash
# Desde el directorio ai/
cd S-Can/ai

# Activar entorno virtual (crearlo si no existe)
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Verificar GPU disponible (opcional pero recomendado)
python3 -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
```

**Dependencias de `requirements.txt`:**

```
Pillow>=10.0,<11.0        # procesamiento de imágenes
numpy>=1.24,<2.0          # operaciones matriciales
scikit-learn>=1.3,<2.0    # métricas de evaluación
tqdm>=4.66                # barras de progreso

tensorflow>=2.13,<2.17    # framework ML
matplotlib>=3.7           # gráficas de entrenamiento

fastapi>=0.103            # servidor de inferencia
uvicorn>=0.23             # servidor ASGI
python-multipart>=0.0.6   # parseo de multipart en FastAPI
requests>=2.31            # cliente HTTP (para pruebas)
```

---

## Paso 1 — Organizar el dataset

Crear la estructura de carpetas con una carpeta por raza. El nombre de la carpeta se convierte automáticamente en el nombre técnico de la raza.

```
ai/dataset/raw/
├── beagle/
│   ├── imagen1.jpg
│   ├── imagen2.png
│   └── ...
├── chihuahua/
│   └── ...
├── golden_retriever/
│   └── ...
├── husky_siberiano/      ← los guiones bajos son el formato esperado
│   └── ...
└── labrador_retriever/
    └── ...
```

**Recomendaciones de cantidad de imágenes:**

| Imágenes por raza | Resultado esperado |
|---|---|
| < 50 | El modelo probablemente no aprenderá bien esa raza |
| 50 – 149 | Posible overfitting; usar augmentation (ya configurado) |
| ≥ 150 | Recomendado para resultados estables |
| ≥ 300 | Excelente. Permite fine-tuning más agresivo |

**Formatos aceptados:** `.jpg`, `.jpeg`, `.png`, `.webp`

**Tamaño mínimo:** 80×80 píxeles (imágenes más pequeñas son automáticamente descartadas por `image_utils.py`).

Las imágenes pueden ser de cualquier tamaño y aspecto; `prepare_dataset.py` las redimensiona automáticamente a 224×224.

---

## Paso 2 — Preparar el dataset

```bash
cd S-Can/ai
source venv/bin/activate
python3 prepare_dataset.py
```

Este script:

1. Lee todas las imágenes válidas de `dataset/raw/<raza>/`
2. Las valida (extensión, apertura real con Pillow, tamaño mínimo)
3. Hace un shuffle con `seed=42` (reproducible)
4. Las divide en 70% train / 15% validation / 15% test
5. Redimensiona cada imagen a 224×224 con filtro LANCZOS
6. Las guarda como JPEG (quality=92) en `dataset/processed/`

**Salida esperada:**

```
Razas encontradas (5): beagle, chihuahua, golden_retriever, husky_siberiano, labrador_retriever

──────────────────────────────────────────────────────────
  Raza                       Train     Val    Test
──────────────────────────────────────────────────────────
  beagle                       136      29      30
  chihuahua                    106      22      24
  golden_retriever             105      22      23
  husky_siberiano              134      28      30
  labrador_retriever           119      25      27
──────────────────────────────────────────────────────────
  TOTAL                        600     126     134

  Total imágenes procesadas: 860
```

> **Importante:** el script borra y recrea `dataset/processed/` cada ejecución para evitar mezclar imágenes de ejecuciones anteriores.

---

## Paso 3 — Entrenar el modelo

```bash
cd S-Can/ai
source venv/bin/activate

# Entrenamiento completo (fase 1 + fase 2)
python3 train.py

# Solo fase 1 (más rápido, menor precisión)
python3 train.py --skip-finetune
```

### Qué hace el entrenamiento

**Fase 1 — Feature Extraction** (~5-15 minutos en CPU, ~2-5 en GPU):

```
FASE 1 — Feature Extraction
  Base congelada · LR: 0.001 · Épocas máx: 20
═══════════════════════════════════════════════════════

Epoch 1/20
 19/19 ━━━━━━━━━━━━━━━━ 28s - accuracy: 0.5983 - val_accuracy: 0.8254
...
Epoch 10/20
 19/19 ━━━━━━━━━━━━━━━━ 18s - accuracy: 0.9350 - val_accuracy: 0.9365

EarlyStopping: restaurando mejor modelo de época 10.

  Mejor val_accuracy fase 1: 0.9365 (93.7%)
```

**Fase 2 — Fine-Tuning** (~10-20 minutos en CPU, ~3-8 en GPU):

```
FASE 2 — Fine-Tuning
  Descongelando capas desde índice 100
  LR: 1e-05 · Épocas máx: 10
═══════════════════════════════════════════════════════

Epoch 1/10
 19/19 ━━━━━━━━━━━━━━━━ 45s - accuracy: 0.9417 - val_accuracy: 0.9444
```

### Artefactos generados

Después del entrenamiento exitoso, `ai/models/` contiene:

```
models/
├── dogdex_model.keras           ← modelo principal (cargado en predict.py)
├── dogdex_model.h5              ← copia en formato legacy
├── class_indices.json           ← mapeo índice → nombre de raza
├── evaluation_report.txt        ← métricas en test set
├── training_fase_1_-_feature_extraction.png   ← gráfica accuracy/loss
└── training_fase_2_-_fine_tuning.png          ← gráfica accuracy/loss
```

### Parámetros de entrenamiento configurables

En la sección de configuración de `train.py`:

```python
EPOCHS_P1          = 20      # épocas máximas fase 1
LR_P1              = 1e-3    # learning rate fase 1
EPOCHS_P2          = 10      # épocas máximas fase 2
LR_P2              = 1e-5    # learning rate fase 2 (muy bajo)
FINETUNE_FROM      = 100     # índice a partir del cual descongelar capas de la base
MIN_VAL_ACC_FINETUNE = 0.60  # mínimo val_accuracy para ejecutar fase 2
BATCH_SIZE         = 32      # imágenes por batch
```

---

## Paso 4 — Verificar el modelo

```bash
# Evaluar métricas en test set (sin reentrenar)
python3 -c "
import tensorflow as tf
import json
from utils.training_utils import build_generators
from pathlib import Path

model = tf.keras.models.load_model('models/dogdex_model.keras')
_, _, test_gen = build_generators(Path('dataset/processed'), 32)
loss, acc = model.evaluate(test_gen, verbose=1)
print(f'Test accuracy: {acc*100:.1f}%')
"
```

---

## Cómo agregar una nueva raza

### 1. Agregar imágenes al dataset

```bash
# Crear carpeta con el nombre técnico de la raza (snake_case)
mkdir -p S-Can/ai/dataset/raw/border_collie

# Copiar imágenes (mínimo 150 recomendado)
cp /ruta/a/fotos/*.jpg S-Can/ai/dataset/raw/border_collie/
```

### 2. Reprocesar el dataset

```bash
cd S-Can/ai
source venv/bin/activate
python3 prepare_dataset.py
```

### 3. Reentrenar el modelo

```bash
python3 train.py
```

El script detecta automáticamente todas las razas en `dataset/raw/` y ajusta el número de clases del modelo. El nuevo `class_indices.json` tendrá 6 entradas en lugar de 5.

### 4. Agregar datos de cuidados al catálogo

En `backend/data/breeds.js`, agregar una nueva entrada:

```javascript
{
  breed: 'Border Collie',      // debe coincidir exactamente con toDisplayName('border_collie')
  care: {
    exercise: 'Muy alta actividad, necesita estimulación mental',
    grooming: 'Cepillado regular dos veces por semana',
    temperament: 'Inteligente, enérgico e instinto de pastoreo'
  }
}
```

> El nombre en `breed` es case-insensitive en la búsqueda (`findCare` usa `.toLowerCase()`), pero por convención debe ser Title Case.

### 5. Reiniciar el servidor de inferencia

```bash
# Detener Uvicorn (Ctrl+C) y volver a iniciar
uvicorn predict:app --host 0.0.0.0 --port 5000
```

El servidor carga el nuevo modelo al arrancar y reporta las razas disponibles en consola.

No es necesario reiniciar Node.js.

---

## Cómo reemplazar el modelo sin romper la arquitectura

El modelo está completamente desacoplado del resto del sistema. Solo `predict.py` lo carga. El contrato de la API Python es estable: siempre devuelve `{ "breed": str, "confidence": float }`.

Para reemplazar el modelo (por ejemplo, actualizar a una versión más precisa):

1. Entrenar el nuevo modelo con `train.py` (sobreescribe `dogdex_model.keras`)
2. Verificar que `class_indices.json` fue actualizado correctamente
3. Reiniciar el servidor Uvicorn

```bash
# Verificar class_indices.json antes de reiniciar
cat ai/models/class_indices.json

# Reiniciar Uvicorn
pkill -f uvicorn
cd S-Can/ai && source venv/bin/activate
uvicorn predict:app --host 0.0.0.0 --port 5000
```

**Node.js y el frontend no requieren ningún cambio**, a menos que se agreguen razas que aún no estén en `breeds.js`.

Para reemplazar por un modelo completamente diferente (por ejemplo, ResNet50 en lugar de MobileNetV2):

1. Modificar `build_model()` en `train.py` para usar la nueva arquitectura
2. Reentrenar: `python3 train.py`
3. El contrato de `predict.py` (`{ breed, confidence }`) no cambia
4. Node.js sigue funcionando sin modificaciones

---

## Troubleshooting de entrenamiento

### `ModuleNotFoundError: No module named 'tensorflow'`

```bash
source S-Can/ai/venv/bin/activate
pip install tensorflow>=2.13
```

### `Error: no se encontró dataset/processed/train`

```bash
# Ejecutar primero la preparación del dataset
python3 prepare_dataset.py
```

### El entrenamiento es muy lento (solo CPU)

Normal en CPU para 860 imágenes. Tiempos aproximados:
- CPU sin GPU: 20-40 minutos total
- GPU (NVIDIA con CUDA): 5-10 minutos total

Para habilitar GPU, verificar que CUDA y cuDNN están instalados:
```bash
python3 -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
```

### `val_accuracy` se estanca en ~0.20 desde el inicio

Las razas tienen distribuciones muy similares en el dataset, o las imágenes son de baja calidad. Verificar:

```bash
# Contar imágenes por raza
for d in dataset/processed/train/*/; do
  echo "$d: $(ls $d | wc -l) imágenes"
done
```

Un desbalance severo (ej: 200 imágenes de una raza y 20 de otra) puede causar este problema. Aumentar las imágenes de las razas minoritarias.

### Fine-tuning omitido: val_accuracy < 0.60

El modelo no aprendió suficiente en Fase 1. Causas y soluciones:

1. **Pocas imágenes:** agregar más imágenes por raza (mínimo 100-150)
2. **Imágenes de baja calidad:** revisar manualmente `dataset/raw/` y eliminar fotos borrosas, sin el perro en primer plano, o de ángulos muy inusuales
3. **LR muy alto:** reducir `LR_P1` a `5e-4`
4. **Pocas épocas:** aumentar `EPOCHS_P1` a 30 y reducir `patience` a 7

### `RuntimeError: Modelo no encontrado en models/dogdex_model.keras`

El modelo aún no ha sido entrenado. Ejecutar el proceso completo:

```bash
python3 prepare_dataset.py
python3 train.py
```

### `LIMIT_FILE_SIZE` al enviar imágenes al backend

Este error viene de Multer en Node.js (no del entrenamiento). El límite es 5 MB. Comprimir la imagen antes de subirla o aumentar el límite en `upload.js`:

```javascript
limits: { fileSize: 10 * 1024 * 1024 }  // 10 MB
```
