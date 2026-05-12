"""
predict.py — DogDex Inference API
──────────────────────────────────
Servidor FastAPI minimalista. Responsabilidades estrictamente acotadas:

  ✓  Cargar el modelo una sola vez al arrancar
  ✓  Preprocesar la imagen recibida
  ✓  Ejecutar la inferencia
  ✓  Devolver breed (nombre técnico) y confidence (float 0–1)

  ✗  No convierte confidence a porcentaje (eso es responsabilidad de Node.js)
  ✗  No agrega información de cuidados (eso vive en data/breeds.js)
  ✗  No conoce el contrato JSON final del frontend

Uso:
    cd /home/jaziel/Proyectos/S-Can/ai
    source venv/bin/activate
    uvicorn predict:app --host 0.0.0.0 --port 5000 --reload

Requiere:
    models/dogdex_model.keras
    models/class_indices.json
    (generados por train.py)
"""

import io
import json
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image
import tensorflow as tf

# ── Configuración ─────────────────────────────────────────────

MODEL_PATH   = Path('models/dogdex_model.keras')
INDICES_PATH = Path('models/class_indices.json')
IMG_SIZE     = (224, 224)

# Estado compartido del proceso: se inicializa en el arranque,
# no se modifica en cada petición para evitar latencia de carga.
_state: dict = {'model': None, 'class_indices': None}


# ── Ciclo de vida ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Carga el modelo al arrancar; libera recursos al detener el servidor."""
    if not MODEL_PATH.exists():
        raise RuntimeError(
            f'Modelo no encontrado en {MODEL_PATH}.\n'
            'Ejecuta primero: python train.py'
        )
    if not INDICES_PATH.exists():
        raise RuntimeError(
            f'class_indices.json no encontrado en {INDICES_PATH}.\n'
            'Ejecuta primero: python train.py'
        )

    _state['model'] = tf.keras.models.load_model(str(MODEL_PATH))

    with open(INDICES_PATH, encoding='utf-8') as f:
        _state['class_indices'] = json.load(f)

    razas = list(_state['class_indices'].values())
    print(f'Modelo cargado: {MODEL_PATH}')
    print(f'Razas disponibles ({len(razas)}): {razas}')
    yield
    # Teardown: TF libera memoria al terminar el proceso


app = FastAPI(title='DogDex Inference API', version='1.0.0', lifespan=lifespan)


# ── Preprocesamiento ──────────────────────────────────────────

def preprocess(image_bytes: bytes) -> np.ndarray:
    """
    Convierte los bytes de la imagen al tensor que espera el modelo.
    Debe ser idéntico al pipeline usado en training_utils.py:
      RGB · 224×224 · valores en [0, 1] · dimensión de batch añadida.
    """
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    img = img.resize(IMG_SIZE, Image.LANCZOS)
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)   # shape: (1, 224, 224, 3)


# ── Endpoints ─────────────────────────────────────────────────

@app.get('/health')
def health():
    """Permite a Node.js verificar que el servicio Python está activo."""
    return {
        'status': 'ok',
        'model_loaded': _state['model'] is not None,
    }


@app.post('/predict')
async def predict(image: UploadFile = File(...)):
    """
    Recibe una imagen y devuelve la raza inferida y la confianza.

    Respuesta:
        {
            "breed":      "golden_retriever",   <- nombre técnico (nombre de carpeta)
            "confidence": 0.9134               <- float entre 0 y 1
        }

    Node.js / aiService.js es responsable de:
        - convertir "golden_retriever" → "Golden Retriever"
        - convertir 0.9134 → "91%"
        - agregar datos de cuidados desde breeds.js
    """
    if not image.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail='El archivo debe ser una imagen.')

    contents = await image.read()

    try:
        batch = preprocess(contents)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'No se pudo procesar la imagen: {e}')

    predictions = _state['model'].predict(batch, verbose=0)
    idx         = int(np.argmax(predictions[0]))
    confidence  = float(predictions[0][idx])

    return {
        'breed':      _state['class_indices'][str(idx)],
        'confidence': round(confidence, 4),
    }
