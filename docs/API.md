# Referencia de API — S-Can

Este documento describe todos los endpoints HTTP del sistema: el backend Node.js (puerto 3000) y el servidor de inferencia Python (puerto 5000).

---

## Backend Node.js — puerto 3000

Base URL en desarrollo: `http://localhost:3000`

### `GET /api/health`

Verifica que el servidor Node.js está funcionando.

**Respuesta exitosa** `200 OK`

```json
{
  "status": "ok",
  "message": "DogDex API funcionando"
}
```

---

### `POST /api/detect`

Endpoint principal. Recibe una imagen, la envía al servidor de inferencia Python, y devuelve la raza detectada con datos de cuidados.

**Content-Type:** `multipart/form-data`

**Campo requerido:**

| Campo | Tipo | Descripción |
|---|---|---|
| `image` | File | Imagen del perro. Formatos: JPG, PNG, WEBP, GIF. Tamaño máximo: 5 MB. |

**Ejemplo con curl:**

```bash
curl -X POST http://localhost:3000/api/detect \
  -F "image=@/ruta/a/mi_perro.jpg"
```

**Respuesta exitosa** `200 OK`

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

**Campos de la respuesta:**

| Campo | Tipo | Descripción |
|---|---|---|
| `breed` | `string` | Nombre legible de la raza en Title Case. Ej: `"Husky Siberiano"` |
| `confidence` | `string` | Porcentaje de confianza del modelo. Siempre formato `"NN%"`. Ej: `"94%"` |
| `care.exercise` | `string` | Descripción del nivel de ejercicio requerido |
| `care.grooming` | `string` | Descripción del cuidado del pelaje |
| `care.temperament` | `string` | Descripción del temperamento de la raza |

> Si la raza detectada no está en el catálogo de cuidados (`data/breeds.js`), los tres campos de `care` devuelven `"Información no disponible"` en lugar de un error.

---

**Respuestas de error:**

`400 Bad Request` — archivo no adjuntado:

```json
{ "error": "No se recibió ninguna imagen." }
```

`400 Bad Request` — tipo de archivo no válido:

```json
{ "error": "Formato no válido. Solo se aceptan JPG, PNG, WEBP o GIF." }
```

`400 Bad Request` — archivo supera 5 MB:

```json
{ "error": "El archivo supera el límite de 5 MB." }
```

`500 Internal Server Error` — error en el pipeline de inferencia:

```json
{ "error": "Error al procesar la imagen." }
```

Este último error ocurre cuando:
- FastAPI no está disponible (`ECONNREFUSED`)
- La imagen es ilegible por Pillow
- Error inesperado en el modelo

---

## Servidor de Inferencia Python — puerto 5000

Base URL en desarrollo: `http://localhost:5000`

Este servidor **no debe ser llamado directamente desde el frontend**. Es un servicio interno consumido únicamente por `aiService.js`.

### `GET /health`

Verifica que el servidor Python está activo y el modelo está cargado en memoria.

**Respuesta exitosa** `200 OK`

```json
{
  "status": "ok",
  "model_loaded": true
}
```

`model_loaded: false` no ocurre en práctica porque el servidor falla al arrancar si el modelo no existe. Está incluido como señal de diagnóstico en caso de carga demorada.

---

### `POST /predict`

Recibe una imagen y devuelve la predicción del modelo.

**Content-Type:** `multipart/form-data`

**Campo requerido:**

| Campo | Tipo | Descripción |
|---|---|---|
| `image` | UploadFile | Imagen con content-type que empiece por `image/` |

**Respuesta exitosa** `200 OK`

```json
{
  "breed":      "golden_retriever",
  "confidence": 0.9134
}
```

**Campos de la respuesta:**

| Campo | Tipo | Descripción |
|---|---|---|
| `breed` | `string` | Nombre técnico de la raza (igual al nombre de la carpeta en el dataset). Siempre snake_case. |
| `confidence` | `float` | Probabilidad del modelo entre 0.0 y 1.0, redondeada a 4 decimales. |

> Python devuelve intencionalmente la representación mínima. `aiService.js` es responsable de toda transformación posterior (snake_case → Title Case, float → porcentaje, enriquecimiento con cuidados).

**Errores:**

`400 Bad Request` — archivo no es imagen:

```json
{ "detail": "El archivo debe ser una imagen." }
```

`400 Bad Request` — imagen ilegible o corrupta:

```json
{ "detail": "No se pudo procesar la imagen: <mensaje de Pillow>" }
```

`500 Internal Server Error` — error inesperado del modelo (muy inusual).

---

## Documentación interactiva de FastAPI

FastAPI genera automáticamente documentación Swagger UI. Disponible en:

```
http://localhost:5000/docs       ← Swagger UI (interactivo)
http://localhost:5000/redoc      ← ReDoc (solo lectura)
```

Permite probar el endpoint `/predict` directamente desde el navegador subiendo una imagen.

---

## Contratos internos

### Node.js → Python (`callPythonApi`)

**Petición:**
```
POST http://localhost:5000/predict
Content-Type: multipart/form-data
Campo: image (stream del archivo en disco)
Timeout: 15,000 ms
```

**Respuesta esperada:**
```json
{ "breed": "golden_retriever", "confidence": 0.9134 }
```

### Frontend → Backend (`fetch` en `main.js`)

**Petición:**
```
POST http://localhost:3000/api/detect
Content-Type: multipart/form-data (automático con FormData)
Campo: image (File del input)
```

**Respuesta esperada:**
```json
{
  "breed": "Golden Retriever",
  "confidence": "91%",
  "care": { "exercise": "...", "grooming": "...", "temperament": "..." }
}
```

---

## Tabla de razas válidas

Valores posibles del campo `breed` en la respuesta del backend Node.js:

| Respuesta Node.js (`breed`) | Respuesta Python interna (`breed`) |
|---|---|
| `"Beagle"` | `"beagle"` |
| `"Chihuahua"` | `"chihuahua"` |
| `"Golden Retriever"` | `"golden_retriever"` |
| `"Husky Siberiano"` | `"husky_siberiano"` |
| `"Labrador Retriever"` | `"labrador_retriever"` |

> El modelo solo reconoce estas 5 razas. Cualquier imagen que no sea de estas razas producirá igualmente un resultado (la clase con mayor probabilidad), sin una señal de "desconocido". El nivel de `confidence` puede ser bajo en estos casos.
