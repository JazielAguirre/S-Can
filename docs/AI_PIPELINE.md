# Pipeline de Inteligencia Artificial — S-Can

Este documento explica el pipeline completo de IA: qué es MobileNetV2, cómo funciona Transfer Learning, cómo fluye una imagen desde el disco hasta la predicción, y cómo se integra Python con Node.js.

---

## Qué es una CNN (Red Neuronal Convolucional)

Una CNN es un tipo de red neuronal diseñada para procesar imágenes. En lugar de ver una imagen como una lista de píxeles, aplica filtros que detectan patrones visuales de forma jerárquica:

```
Píxeles crudos
    │
    ▼ Capas iniciales
Bordes y contornos (líneas horizontales, verticales, diagonales)
    │
    ▼ Capas intermedias
Formas y texturas (pelaje, orejas, manchas)
    │
    ▼ Capas finales
Conceptos complejos (cara de perro, tipo de hocico, forma de orejas)
    │
    ▼ Clasificador final
Probabilidad de cada raza → softmax → [0.02, 0.01, 0.91, 0.04, 0.02]
                                         Bea   Chi   GR    Hus   Lab
```

---

## Qué es MobileNetV2

MobileNetV2 es una arquitectura CNN diseñada por Google para ser eficiente en dispositivos con recursos limitados (móviles, servidores pequeños). Sus características clave:

- Entrenada en **ImageNet**: un dataset de 1.2 millones de imágenes en 1000 categorías (perros, gatos, coches, herramientas...).
- Entrada esperada: imágenes de **224×224 píxeles** en RGB, valores normalizados a [0, 1].
- Parámetros totales: ~3.4 millones (muy liviana comparada con VGG16 ~138M o ResNet50 ~25M).
- Usa **inverted residuals** y **linear bottlenecks** para maximizar precisión por operación de cómputo.

En S-Can se usa **sin la capa de clasificación original** (`include_top=False`). Solo se extraen las representaciones aprendidas de ImageNet, no las 1000 clases de salida.

---

## Qué es Transfer Learning

Transfer Learning significa aprovechar un modelo que ya aprendió a reconocer patrones visuales generales y adaptarlo a una tarea nueva específica.

**Analogía:** un experto en fotografía de naturaleza que nunca ha visto perros aprende a distinguir razas mucho más rápido que alguien que nunca ha observado animales, porque ya conoce formas, texturas, proporciones.

```
MobileNetV2 preentrenado en ImageNet
(sabe reconocer: bordes, texturas, formas, colores, patrones)
        │
        │  CONGELAR la base durante Fase 1
        │  (no modificar lo que ya sabe)
        ▼
Añadir cabeza clasificadora nueva:
  GlobalAveragePooling2D  ← colapsa el mapa de activación en un vector
  Dense(128, relu)         ← capa densa de aprendizaje intermedio
  Dropout(0.3)             ← regularización: apaga 30% de neuronas al azar
  Dense(5, softmax)        ← 5 salidas = 5 razas, probabilidades suman 1.0
        │
        ▼
Entrenar SOLO la cabeza (Fase 1): el modelo aprende a usar los patrones
de ImageNet para distinguir entre las 5 razas caninas.
        │
        ▼
Descongelar capas finales de MobileNetV2 (Fase 2): ajuste fino con LR muy bajo
para especializar las representaciones en características caninas específicas.
```

---

## Arquitectura del modelo en S-Can

```
Capa                       Salida              Parámetros
─────────────────────────────────────────────────────────
MobileNetV2 (base)         (None, 7, 7, 1280)  ~2.2M  (congelada en fase 1)
GlobalAveragePooling2D     (None, 1280)         0
Dense(128, relu)           (None, 128)          163,968
Dropout(0.3)               (None, 128)          0
Dense(5, softmax)          (None, 5)            645
─────────────────────────────────────────────────────────
Total parámetros:          ~2.4M
Parámetros entrenables F1: ~164,613  (solo la cabeza)
Parámetros entrenables F2: varía según FINETUNE_FROM=100
```

La capa `GlobalAveragePooling2D` toma el mapa de características de 7×7×1280 que produce la base de MobileNetV2 y calcula el promedio de cada uno de los 1280 filtros, produciendo un vector de 1280 números que representa la imagen completa.

---

## Pipeline de entrenamiento (train.py)

### Fase 1 — Feature Extraction

- Base MobileNetV2 completamente congelada (`base.trainable = False`)
- Solo entrena la cabeza: 164,613 parámetros
- Optimizador: Adam con `lr=1e-3`
- Hasta 20 épocas con EarlyStopping (patience=5)
- ReduceLROnPlateau: si `val_loss` no mejora 3 épocas, LR × 0.3
- ModelCheckpoint: guarda `dogdex_model.keras` cuando `val_accuracy` mejora

Objetivo: que la cabeza aprenda a usar las representaciones de ImageNet para distinguir razas.

### Fase 2 — Fine-Tuning

- Solo se ejecuta si Fase 1 alcanzó `val_accuracy >= 0.60`
- Descongela capas de MobileNetV2 a partir del índice 100
  - Las capas 0-99 siguen congeladas (patrones genéricos: bordes, texturas)
  - Las capas 100+ se descongelan (patrones de alto nivel: formas complejas)
- Optimizador: Adam con `lr=1e-5` (100× menor que Fase 1)
  - LR muy bajo para no sobreescribir los pesos preentrenados con un cambio brusco
- Hasta 10 épocas con EarlyStopping (patience=4)

Objetivo: especializar las capas finales del modelo en características específicas de razas caninas.

### Data Augmentation (solo en train)

El generador de entrenamiento aplica transformaciones aleatorias a cada imagen en cada época para aumentar la variabilidad del dataset sin añadir imágenes nuevas:

```python
rotation_range=20          # rota la imagen ±20° al azar
width_shift_range=0.10     # desplaza horizontalmente ±10% del ancho
height_shift_range=0.10    # desplaza verticalmente ±10% del alto
horizontal_flip=True       # voltea horizontalmente (natural en fotos de perros)
zoom_range=0.10            # aplica zoom ±10%
fill_mode='nearest'        # rellena píxeles vacíos con el vecino más cercano
```

Las imágenes de validación y test **no reciben augmentation** para que la evaluación sea reproducible y comparable.

---

## Pipeline de preprocesamiento (prepare_dataset.py)

```
dataset/raw/<raza>/         ← imágenes originales (cualquier tamaño)
        │
        ▼ collect_images()
Filtrar imágenes válidas:
  - extensión: .jpg .jpeg .png .webp
  - abrir con Pillow → img.verify() (detecta corrupción)
  - dimensión mínima: 80px
        │
        ▼ split_images(seed=42)
Shuffle determinista + split 70/15/15
        │
        ├── train/     70%   → 600 imágenes totales
        ├── validation/ 15%  → 126 imágenes totales
        └── test/       15%  → 134 imágenes totales
        │
        ▼ resize_and_save()
Para cada imagen:
  - Pillow: convert('RGB')          ← normaliza RGBA, escala de grises, etc.
  - resize(224, 224, LANCZOS)       ← LANCZOS minimiza aliasing
  - save(dest, 'JPEG', quality=92)  ← guarda con nombre raza_NNNN.jpg
```

El uso de `seed=42` garantiza que el split sea reproducible: ejecutar `prepare_dataset.py` dos veces produce exactamente el mismo reparto de imágenes en train/val/test.

---

## Pipeline de inferencia (predict.py)

```
Imagen recibida (bytes)
        │
        ▼ preprocess()
PIL.Image.open(BytesIO(bytes))
        │
        ▼ .convert('RGB')
Garantiza 3 canales RGB — descarta alpha, convierte grises a RGB
        │
        ▼ .resize((224, 224), LANCZOS)
Igual que en entrenamiento — debe ser IDÉNTICO para evitar distribución shift
        │
        ▼ np.array(img, dtype=float32) / 255.0
Normaliza píxeles de [0, 255] a [0.0, 1.0]
El modelo fue entrenado con esta normalización — cambiarla destruye las predicciones
        │
        ▼ np.expand_dims(arr, axis=0)
Añade dimensión de batch → shape: (1, 224, 224, 3)
El modelo espera siempre un batch, aunque sea de 1 imagen
        │
        ▼ model.predict(batch, verbose=0)
Salida: array de shape (1, 5) — probabilidad de cada raza
Ej: [[0.02, 0.01, 0.91, 0.04, 0.02]]
        │
        ▼ argmax → índice 2
        │
        ▼ class_indices["2"] → "golden_retriever"
        │
        ▼ Respuesta: { "breed": "golden_retriever", "confidence": 0.9100 }
```

**Por qué el preprocesamiento de inferencia debe ser idéntico al de entrenamiento:**

Si el modelo aprendió con imágenes normalizadas a [0, 1] pero en inferencia se le pasan valores en [0, 255], ve distribuciones completamente diferentes a las del entrenamiento. La red produce predicciones sin sentido. Este es uno de los errores más comunes al desplegar modelos ML.

---

## Artefactos del modelo

| Archivo | Descripción | Uso |
|---|---|---|
| `models/dogdex_model.keras` | Modelo completo en formato Keras nativo | Cargado por `predict.py` en producción |
| `models/dogdex_model.h5` | Modelo en formato HDF5 legacy | Compatibilidad con TF < 2.12 |
| `models/class_indices.json` | Mapeo `{"0": "beagle", "1": "chihuahua", ...}` | Convierte índice de argmax a nombre de raza |
| `models/evaluation_report.txt` | Métricas sobre test set | Documentación del rendimiento |

**Contenido actual de `class_indices.json`:**

```json
{
  "0": "beagle",
  "1": "chihuahua",
  "2": "golden_retriever",
  "3": "husky_siberiano",
  "4": "labrador_retriever"
}
```

---

## Métricas del modelo actual

Evaluación sobre test set (134 imágenes):

```
Loss:     0.1621
Accuracy: 0.9403 (94.0%)

                    precision    recall  f1-score   support
        beagle       0.94      0.97      0.95        30
     chihuahua       0.95      0.88      0.91        24
golden_retriever     0.96      0.96      0.96        23
 husky_siberiano     0.94      0.97      0.95        30
labrador_retriever   0.93      0.93      0.93        27

      accuracy                           0.94       134
```

- **Precision:** de todas las veces que el modelo predijo "raza X", ¿cuántas eran correctas?
- **Recall:** de todas las imágenes reales de "raza X", ¿cuántas detectó correctamente?
- **F1-score:** media armónica de precision y recall.

La clase con menor recall es **chihuahua** (0.88), lo que indica que el 12% de los chihuahuas se confunden con otra raza. Ampliar el dataset de chihuahua mejoraría esta métrica.

---

## Por qué FastAPI sobre TensorFlow.js

| Criterio | FastAPI + Python | TensorFlow.js (Node.js) |
|---|---|---|
| Ecosistema de entrenamiento | Keras, sklearn, matplotlib nativo | Requiere conversión tfjs-converter |
| Peso en el cliente | ~0 (modelo en servidor) | ~10-40 MB descargados por usuario |
| Conversión de formato | Ninguna — .keras → predict.py directo | SavedModel → TFLite → TFJS (3 pasos con riesgo de inconsistencia) |
| Preprocesamiento | Pillow (idéntico a entrenamiento) | Browser canvas API (diferencias sutiles de normalización) |
| Escalabilidad | GPU cloud, workers async | Limitado a CPU del cliente |
| Actualización del modelo | Reiniciar Uvicorn | Redeploy frontend completo |
| Documentación autogenerada | `/docs` Swagger UI integrado | Manual |

La razón principal de elegir FastAPI es el **aislamiento total entre el motor IA y el resto del sistema**. Actualizar o reemplazar el modelo no requiere tocar Node.js ni el frontend.

---

## Integración Node.js ↔ Python

El único punto de contacto entre los dos procesos es una petición HTTP:

```
aiService.js                           predict.py
    │                                       │
    │  FormData { image: ReadStream }       │
    │ ─────────────────────────────────►   │
    │                                       │ preprocess
    │                                       │ model.predict
    │  { breed: str, confidence: float }    │
    │ ◄─────────────────────────────────   │
    │                                       │
```

`aiService.js` usa `fs.createReadStream(file.path)` para enviar el archivo que Multer ya guardó en disco, sin leerlo completo en memoria. Esto es eficiente para imágenes grandes.

El timeout de 15 segundos en `axios` protege al backend Node.js de quedar bloqueado si Python tarda demasiado (por ejemplo, si el modelo está cargando por primera vez en una máquina lenta).
