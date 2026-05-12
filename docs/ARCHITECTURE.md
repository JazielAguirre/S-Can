# Arquitectura del Sistema — S-Can

Este documento describe la arquitectura modular del sistema, el flujo de datos desde el navegador hasta el modelo IA, y las responsabilidades exactas de cada capa.

---

## Visión general

S-Can está construido como tres procesos independientes que se comunican por HTTP:

```
┌─────────────────────────────────────────────────────────────────┐
│  NAVEGADOR                                                      │
│  frontend/index.html                                            │
│  ├── css/styles.css        (design system, sin JS)              │
│  ├── js/history.js         (IIFE: localStorage historial)       │
│  ├── js/stats.js           (IIFE: localStorage estadísticas)    │
│  └── js/main.js            (orquestador: form, fetch, render)   │
└────────────────────┬────────────────────────────────────────────┘
                     │  POST /api/detect  (multipart/form-data)
                     │  http://localhost:3000
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  BACKEND  Node.js + Express   :3000                             │
│                                                                 │
│  server.js                                                      │
│  └── routes/detect.js                                           │
│      └── middlewares/upload.js  (Multer: valida y persiste)     │
│          └── controllers/detectController.js                    │
│              └── services/aiService.js                          │
│                  ├── Llama a FastAPI /predict                   │
│                  ├── Transforma respuesta                       │
│                  └── Enriquece con data/breeds.js               │
└────────────────────┬────────────────────────────────────────────┘
                     │  POST /predict  (multipart/form-data)
                     │  http://localhost:5000
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  SERVIDOR IA  FastAPI + Uvicorn   :5000                         │
│                                                                 │
│  predict.py                                                     │
│  ├── lifespan: carga modelo y class_indices al arrancar         │
│  ├── /health  → {"status":"ok","model_loaded":true}             │
│  └── /predict → recibe imagen, preprocesa, infiere, devuelve   │
│                  {"breed":"golden_retriever","confidence":0.91}  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Flujo completo de una petición

Desde que el usuario hace clic en "Analizar imagen" hasta que ve el resultado:

```
Usuario hace clic "Analizar imagen"
        │
        ▼
[main.js] Valida tipo y tamaño del archivo en el navegador
        │  ALLOWED_TYPES: jpeg, png, webp, gif — MAX: 5 MB
        ▼
[main.js] FormData.append('image', file)
          fetch('http://localhost:3000/api/detect', { method:'POST', body:formData })
        │
        ▼
[upload.js] Multer intercepta la petición
          - Verifica MIME (image/jpeg | png | webp | gif)
          - Verifica tamaño ≤ 5 MB
          - Escribe el archivo en backend/uploads/<timestamp>-<nombre>.ext
          - Adjunta req.file con { path, originalname, mimetype, size }
        │  Si falla → Error 400 (capturado en el error handler de server.js)
        ▼
[detectController.js] Verifica que req.file exista
          Si no hay archivo → 400 { error: "No se recibió ninguna imagen." }
        │
        ▼
[aiService.js] analyzeImage(req.file)
          └── callPythonApi(file)
                FormData con el archivo
                axios.POST('http://localhost:5000/predict', form, timeout:15s)
                  │  Si ECONNREFUSED → Error legible "¿Está corriendo predict.py?"
                  ▼
              [predict.py] preprocess(bytes)
                  - Pillow: abrir → convert('RGB') → resize(224,224, LANCZOS)
                  - NumPy: array float32 / 255.0 → expand_dims → shape (1,224,224,3)
                  ▼
              [predict.py] model.predict(batch)
                  - shape salida: (1, 5)   — 5 clases
                  - argmax → índice clase con mayor probabilidad
                  - class_indices[str(idx)] → nombre técnico ("golden_retriever")
                  ▼
              Respuesta Python:
                  { "breed": "golden_retriever", "confidence": 0.9134 }
        │
        ▼
[aiService.js] Transforma la respuesta mínima de Python
          - toDisplayName("golden_retriever") → "Golden Retriever"
          - confidence: Math.round(0.9134 * 100) → "91%"
          - findCare("Golden Retriever") → busca en breeds.js (insensible a mayúsculas)
            Si no está en el catálogo → { exercise/grooming/temperament: "Información no disponible" }
        │
        ▼
Respuesta Node.js → Frontend:
        {
          "breed":      "Golden Retriever",
          "confidence": "91%",
          "care": {
            "exercise":    "Alta actividad física diaria",
            "grooming":    "Cepillado frecuente, especialmente en muda",
            "temperament": "Amigable, confiable y muy sociable"
          }
        }
        │
        ▼
[main.js] renderResult(data)
        - Muestra nombre de raza, confianza, barra animada, cuidados
        - DogDexHistory.save(data, previewImg.src)   → localStorage
        - DogDexStats.record(data)                   → localStorage
```

---

## Responsabilidades por capa

### Frontend (`frontend/`)

| Archivo | Responsabilidad |
|---|---|
| `index.html` | Estructura HTML semántica. Carga CSS y los tres módulos JS en orden correcto (history.js → stats.js → main.js). |
| `css/styles.css` | Design system completo: variables CSS, layout, componentes, animaciones, responsive. No contiene lógica. |
| `js/main.js` | Orquestador principal. Maneja eventos del formulario, validación del lado cliente, llamada `fetch` al backend, renderizado del resultado. Depende de `DogDexHistory` y `DogDexStats` (definidos en los otros módulos). |
| `js/history.js` | IIFE que expone `{ save, clear, render }`. Escribe y lee `localStorage['dogdex_history']`. Guarda máximo 5 entradas; la imagen se almacena como base64. No sabe nada del formulario. |
| `js/stats.js` | IIFE que expone `{ record, clear, render }`. Escribe y lee `localStorage['dogdex_stats']`. Mantiene conteo total, frecuencia por raza y suma de confianza para el promedio. Es independiente del historial: refleja **todos** los análisis aunque el historial solo guarde los últimos 5. |

**localStorage — claves y estructuras:**

```
dogdex_history  →  Array<{
  breed:        string,          // "Golden Retriever"
  confidence:   string,          // "91%"
  care:         { exercise, grooming, temperament },
  date:         string,          // ISO 8601
  imageBase64:  string           // data:image/...;base64,...
}>  (máximo 5 elementos)

dogdex_stats  →  {
  totalCount:     number,        // total acumulado de análisis
  breedCounts:    { [breed]: number },  // frecuencia por raza
  confidenceSum:  number         // suma de porcentajes para calcular promedio
}
```

---

### Backend Node.js (`backend/`)

#### `server.js`

Punto de entrada. Inicializa Express, habilita CORS global, parsea JSON, monta el router de detección en `/api/detect`, y registra un error handler de último recurso que convierte errores de Multer (incluyendo `LIMIT_FILE_SIZE`) en respuestas JSON con código 400.

```
app.use(cors())
app.use(express.json())
app.get('/api/health', ...)
app.use('/api/detect', detectRouter)
app.use((err, req, res, next) => { /* error handler global */ })
app.listen(3000)
```

#### `routes/detect.js`

Registra la única ruta: `POST /` → `upload.single('image')` → `detectImage`. El campo multipart que se espera se llama `image`.

#### `middlewares/upload.js`

Encapsula toda la lógica de Multer:

- **Storage:** disco local en `backend/uploads/`. Nombre de archivo: `${Date.now()}-${originalname}` para evitar colisiones.
- **fileFilter:** acepta solo `image/jpeg`, `image/png`, `image/webp`, `image/gif`. Rechaza cualquier otro tipo con un error que llega al error handler global.
- **limits:** `fileSize: 5 * 1024 * 1024` (5 MB). Los archivos más grandes generan el error `LIMIT_FILE_SIZE`.

#### `controllers/detectController.js`

Controlador delgado. Solo hace dos cosas:

1. Verifica que `req.file` exista (Multer no siempre lo garantiza si el campo tiene un nombre incorrecto).
2. Llama a `aiService.analyzeImage(req.file)` y devuelve el resultado o un error 500 genérico.

No contiene lógica de negocio. Toda la transformación ocurre en el servicio.

#### `services/aiService.js`

Capa de negocio. Es el único archivo que conoce la URL de FastAPI (`http://localhost:5000`). Sus responsabilidades son:

| Función | Qué hace |
|---|---|
| `analyzeImage(file)` | Orquesta: llama a Python, transforma, busca en catálogo, retorna contrato final. |
| `callPythonApi(file)` | Construye FormData con `fs.createReadStream`, hace `axios.post` a `/predict` con timeout 15 s. Traduce `ECONNREFUSED` en mensaje útil. |
| `toDisplayName(snakeName)` | `"golden_retriever"` → `"Golden Retriever"` (replace `_` → ` `, capitalizar cada palabra). |
| `findCare(displayName)` | Busca en `breeds.js` con comparación case-insensitive. Si no encuentra la raza, devuelve fallback en lugar de lanzar error. |

#### `data/breeds.js`

Catálogo estático con 8 razas. Cada entrada tiene:

```javascript
{
  breed: string,      // nombre legible, debe coincidir con toDisplayName()
  care: {
    exercise:    string,
    grooming:    string,
    temperament: string
  }
}
```

Razas en el catálogo: Golden Retriever, Labrador Retriever, Border Collie, Bulldog Francés, Husky Siberiano, Beagle, Pastor Alemán, Poodle Estándar.

Razas que el modelo detecta: Beagle, Chihuahua, Golden Retriever, Husky Siberiano, Labrador Retriever. Las 3 razas adicionales del catálogo están preparadas para cuando el modelo sea reentrenado.

---

### Servidor de Inferencia Python (`ai/predict.py`)

FastAPI con ciclo de vida (`lifespan`):

- **Al arrancar:** carga `models/dogdex_model.keras` en `_state['model']` y `models/class_indices.json` en `_state['class_indices']`. Falla rápido si alguno de los dos archivos no existe.
- **Durante peticiones:** no recarga el modelo. El modelo vive en memoria del proceso para evitar latencia de disco en cada petición.
- **Al detenerse:** TensorFlow libera memoria automáticamente.

```
_state = { 'model': None, 'class_indices': None }
```

El endpoint `POST /predict`:

1. Verifica que `content_type` comience con `image/`.
2. Lee los bytes del archivo con `await image.read()`.
3. Llama a `preprocess()`: Pillow abre, convierte a RGB, redimensiona a 224×224 con LANCZOS, convierte a float32, normaliza a [0,1], añade dimensión de batch.
4. `model.predict(batch, verbose=0)` → array de forma `(1, 5)`.
5. `argmax` → índice con mayor probabilidad.
6. Devuelve `{ "breed": str, "confidence": float }`.

**Lo que Python NO hace** (intencional, responsabilidad de Node.js):
- Convertir `"golden_retriever"` → `"Golden Retriever"`
- Convertir `0.9134` → `"91%"`
- Buscar datos de cuidados

---

## Contrato JSON invariante

El contrato que el backend Node.js siempre garantiza al frontend, independientemente de la respuesta de Python:

```json
{
  "breed":      "Golden Retriever",
  "confidence": "91%",
  "care": {
    "exercise":    "Alta actividad física diaria",
    "grooming":    "Cepillado frecuente, especialmente en muda",
    "temperament": "Amigable, confiable y muy sociable"
  }
}
```

Tipos garantizados:
- `breed`: `string` — nombre legible en Title Case
- `confidence`: `string` — número entero con símbolo `%` (ej. `"91%"`, `"100%"`)
- `care.exercise`, `care.grooming`, `care.temperament`: `string` — puede ser `"Información no disponible"` si la raza no está en el catálogo

---

## Cómo volver al mock si el modelo falla

Si FastAPI no está disponible (`ECONNREFUSED`), `aiService.js` lanza un error descriptivo que llega al controller y devuelve HTTP 500 al frontend.

Para volver temporalmente a respuestas simuladas mientras el modelo no está disponible, reemplazar `callPythonApi` en `aiService.js` con una función que devuelva datos fijos:

```javascript
// Modo mock temporal — descomentar si FastAPI no está disponible
async function callPythonApi(_file) {
  const mockBreeds = ['golden_retriever', 'beagle', 'husky_siberiano', 'labrador_retriever', 'chihuahua'];
  const breed = mockBreeds[Math.floor(Math.random() * mockBreeds.length)];
  return { breed, confidence: 0.80 + Math.random() * 0.19 };
}
```

El resto del pipeline (transformación, catálogo de cuidados, contrato JSON) sigue funcionando sin ningún cambio adicional.

---

## Manejo de errores

| Origen del error | Qué pasa | Respuesta al usuario |
|---|---|---|
| Archivo no es imagen | Multer `fileFilter` rechaza | `400 { error: "Formato no válido. Solo se aceptan JPG, PNG, WEBP o GIF." }` |
| Archivo > 5 MB | Multer `LIMIT_FILE_SIZE` | `400 { error: "El archivo supera el límite de 5 MB." }` |
| No se adjuntó imagen | `detectController` verifica `req.file` | `400 { error: "No se recibió ninguna imagen." }` |
| FastAPI no disponible | `axios ECONNREFUSED` | `500 { error: "Error al procesar la imagen." }` (+ log en consola Node) |
| Imagen corrupta en Python | `HTTPException 400` en `predict.py` | `500 { error: "Error al procesar la imagen." }` |
| Sin conexión al backend | `fetch` lanza `TypeError` | UI muestra "No se pudo conectar con el servidor." |

---

## Escalabilidad futura

La arquitectura actual soporta estas extensiones sin reestructurar:

1. **Más razas:** reentrenar el modelo con nuevas carpetas en `dataset/raw/` y agregar entradas a `breeds.js`. No se toca ninguna ruta ni controller.
2. **Reemplazar el modelo:** subir un nuevo `dogdex_model.keras` y reiniciar Uvicorn. Node.js no necesita cambios.
3. **Cachear resultados:** agregar un Map en memoria (o Redis) en `aiService.js` usando un hash de la imagen como clave. El controller y el frontend no cambian.
4. **Rate limiting:** agregar `express-rate-limit` en `server.js` antes del router, sin modificar la lógica de negocio.
5. **Base de datos:** reemplazar `data/breeds.js` con una consulta a PostgreSQL/SQLite en `findCare()`. El contrato de retorno no cambia.
6. **Autenticación:** agregar middleware JWT entre `cors()` y `express.json()` en `server.js`.
