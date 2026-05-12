# S-Can — Reconocimiento de Razas Caninas con IA

S-Can es una aplicación web que identifica la raza de un perro a partir de una fotografía, usando un modelo de Deep Learning basado en Transfer Learning con MobileNetV2 entrenado sobre 5 razas. El sistema devuelve la raza detectada, el nivel de confianza y una guía de cuidados personalizada.

**Precisión del modelo en test set:** 94.0% sobre 134 imágenes (5 clases)

---

## Tabla de Contenidos

- [Stack tecnológico](#stack-tecnológico)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Inicio rápido](#inicio-rápido)
- [Razas soportadas](#razas-soportadas)
- [Documentación adicional](#documentación-adicional)
- [Decisiones de arquitectura](#decisiones-de-arquitectura)
- [Limitaciones actuales](#limitaciones-actuales)
- [Mejoras futuras](#mejoras-futuras)

---

## Stack tecnológico

| Capa | Tecnología | Versión |
|---|---|---|
| Frontend | HTML5, CSS3, JavaScript Vanilla | — |
| Backend API | Node.js + Express | Express ^4.18 |
| Subida de archivos | Multer | ^2.1 |
| Cliente HTTP (Node→Python) | Axios + form-data | ^1.16 / ^4.0 |
| Servidor de inferencia | FastAPI + Uvicorn | FastAPI ^0.103 |
| Modelo ML | TensorFlow/Keras + MobileNetV2 | TF ^2.13 |
| Preprocesamiento | Pillow | ^10.0 |
| Métricas | scikit-learn | ^1.3 |

---

## Estructura del proyecto

```
S-Can/
├── frontend/                  # Interfaz web estática
│   ├── index.html             # Única página HTML (SPA sin framework)
│   ├── css/
│   │   └── styles.css         # Design system completo (~1200 líneas)
│   └── js/
│       ├── main.js            # Lógica principal: form, fetch, render
│       ├── history.js         # Módulo de historial (localStorage)
│       └── stats.js           # Módulo de estadísticas (localStorage)
│
├── backend/                   # API Node.js
│   ├── server.js              # Arranque Express, CORS, error handler global
│   ├── routes/
│   │   └── detect.js          # POST /api/detect → middleware + controller
│   ├── controllers/
│   │   └── detectController.js # Recibe req.file, delega a aiService
│   ├── services/
│   │   └── aiService.js       # Llama a FastAPI, transforma respuesta
│   ├── middlewares/
│   │   └── upload.js          # Multer: tipo, tamaño, nombre único
│   ├── data/
│   │   └── breeds.js          # Catálogo de razas y datos de cuidados
│   └── uploads/               # Archivos temporales subidos por Multer
│
└── ai/                        # Pipeline Python completo
    ├── predict.py             # Servidor FastAPI de inferencia
    ├── train.py               # Entrenamiento (2 fases: extraction + fine-tuning)
    ├── prepare_dataset.py     # Preparación y split 70/15/15 del dataset
    ├── requirements.txt       # Dependencias Python
    ├── utils/
    │   ├── image_utils.py     # Validación, resize, recolección de imágenes
    │   └── training_utils.py  # Generadores, plot, evaluación
    ├── models/
    │   ├── dogdex_model.keras # Modelo entrenado (formato nativo Keras)
    │   ├── dogdex_model.h5    # Modelo entrenado (formato legacy TF 2.x)
    │   ├── class_indices.json # Mapeo índice → nombre de raza
    │   └── evaluation_report.txt # Métricas sobre test set
    └── dataset/
        ├── raw/               # Imágenes originales sin procesar (por raza)
        └── processed/
            ├── train/         # 70% — 600 imágenes
            ├── validation/    # 15% — 126 imágenes
            └── test/          # 15% — 134 imágenes
```

---

## Inicio rápido

### Prerrequisitos

```bash
# Verificar versiones
node --version        # >= 18
npm --version         # >= 9
python3 --version     # >= 3.10
```

### 1. Clonar e instalar dependencias del backend

```bash
cd S-Can/backend
npm install
```

### 2. Configurar entorno Python

```bash
cd S-Can/ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Verificar que el modelo existe

```bash
ls ai/models/
# Deben existir: dogdex_model.keras  class_indices.json
# Si no existen, ver docs/TRAINING_GUIDE.md
```

### 4. Iniciar el servidor Python (puerto 5000)

```bash
cd S-Can/ai
source venv/bin/activate
uvicorn predict:app --host 0.0.0.0 --port 5000
```

### 5. Iniciar el servidor Node.js (puerto 3000)

```bash
cd S-Can/backend
npm start
# o en desarrollo con hot reload:
npm run dev
```

### 6. Abrir el frontend

```bash
# Opción A — abrir directamente en el navegador
xdg-open /home/jaziel/Proyectos/S-Can/frontend/index.html

# Opción B — servir estáticamente (evita problemas CORS en algunos navegadores)
cd S-Can/frontend
python3 -m http.server 8080
# Abrir http://localhost:8080
```

### Verificación del sistema

```bash
# Verificar backend Node.js
curl http://localhost:3000/api/health
# {"status":"ok","message":"DogDex API funcionando"}

# Verificar servidor Python
curl http://localhost:5000/health
# {"status":"ok","model_loaded":true}
```

---

## Razas soportadas

El modelo detecta 5 razas. El catálogo de cuidados (`data/breeds.js`) contiene 8 razas — las 3 adicionales están preparadas para cuando el modelo sea reentrenado.

| # | Nombre técnico (modelo) | Nombre visible (UI) | Imágenes totales |
|---|---|---|---|
| 0 | `beagle` | Beagle | 195 |
| 1 | `chihuahua` | Chihuahua | 152 |
| 2 | `golden_retriever` | Golden Retriever | 150 |
| 3 | `husky_siberiano` | Husky Siberiano | 192 |
| 4 | `labrador_retriever` | Labrador Retriever | 171 |

**Total dataset:** 860 imágenes · **Train:** 600 · **Validation:** 126 · **Test:** 134

---

## Documentación adicional

| Documento | Contenido |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Arquitectura modular, flujo de datos, contratos JSON |
| [API.md](API.md) | Endpoints, parámetros, respuestas, errores |
| [AI_PIPELINE.md](AI_PIPELINE.md) | MobileNetV2, Transfer Learning, pipeline completo |
| [TRAINING_GUIDE.md](TRAINING_GUIDE.md) | Reentrenar el modelo, agregar razas, dataset |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Despliegue completo en Ubuntu desde cero |

---

## Decisiones de arquitectura

### Por qué FastAPI y no TensorFlow.js

TensorFlow.js ejecuta el modelo directamente en el navegador o en Node.js. Fue considerado y descartado por:

1. **Peso del modelo:** MobileNetV2 con cabeza personalizada supera los 10 MB; descargarlo en cada sesión de usuario impacta la carga inicial.
2. **Compatibilidad de versiones:** la conversión entre formatos (SavedModel → TFLite → TFJS) introduce inconsistencias de preprocesamiento difíciles de depurar.
3. **Aislamiento de responsabilidades:** tener el modelo en un servidor Python independiente permite actualizar el modelo sin tocar el frontend ni el backend Node.js.
4. **Ecosistema de entrenamiento:** todo el toolchain de entrenamiento (Keras callbacks, sklearn metrics, matplotlib) vive naturalmente en Python.

FastAPI fue elegido sobre Flask porque ofrece validación automática de tipos, documentación interactiva integrada en `/docs`, y soporte asíncrono nativo con Uvicorn.

### Por qué separar Node.js de Python

Node.js actúa como orquestador: maneja la subida de archivos (Multer), la autenticación futura, el caché de resultados y la transformación del contrato JSON. Python actúa como motor de inferencia puro: solo preprocesa y predice. Esta separación permite reemplazar el motor IA (por ejemplo, pasar de TensorFlow a PyTorch) sin modificar ninguna línea del backend Node.js.

### Por qué JavaScript Vanilla sin framework

El MVP requería velocidad de desarrollo y cero dependencias de build en el frontend. Con un solo archivo HTML, un CSS y tres módulos JS se cubren todos los casos de uso actuales. La estructura IIFE de `history.js` y `stats.js` simula módulos con API pública explícita, lo que hace el código mantenible sin un bundler.

---

## Limitaciones actuales

- Los archivos subidos en `backend/uploads/` no se eliminan automáticamente tras la inferencia; se acumulan en disco.
- El frontend llama directamente a `http://localhost:3000` sin variable de configuración, por lo que no funciona en producción sin modificar `main.js:1`.
- El historial almacena imágenes como base64 en localStorage, lo que puede saturar el almacenamiento (~1-2 MB por análisis dependiendo de la imagen).
- El modelo solo reconoce 5 razas; cualquier otra raza producirá un resultado incorrecto con alta confianza (no hay clase "desconocido").
- No existe autenticación ni rate limiting en los endpoints.

---

## Mejoras futuras

- Añadir limpieza automática de `uploads/` tras cada petición (unlink del archivo temporal).
- Implementar una clase "no es un perro" / "raza desconocida" para evitar falsos positivos.
- Expandir el dataset a 20+ razas con el pipeline existente de `prepare_dataset.py` y `train.py`.
- Agregar variable `API_URL` configurable por entorno en el frontend.
- Introducir un endpoint `GET /api/breeds` que exponga el catálogo de razas dinámicamente.
- Considerar compresión de imágenes en el cliente antes del upload para reducir latencia.
- Agregar tests de integración Node.js → Python con Jest + supertest.
