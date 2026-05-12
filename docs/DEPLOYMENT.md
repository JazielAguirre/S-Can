# Guía de Despliegue — S-Can

Instrucciones completas para ejecutar S-Can desde cero en Ubuntu Linux. Cubre instalación de dependencias, configuración, arranque de los tres servicios (frontend, backend Node.js, servidor Python), y troubleshooting de errores comunes.

---

## Requisitos del sistema

| Componente | Mínimo | Recomendado |
|---|---|---|
| Ubuntu | 20.04 LTS | 22.04 LTS |
| RAM | 2 GB | 4 GB |
| Disco | 3 GB (incluye venv y dataset) | 5 GB |
| Python | 3.10 | 3.12 |
| Node.js | 18 | 20 LTS |
| GPU | No requerida | NVIDIA con CUDA (solo para reentrenar) |

---

## Instalación desde cero

### 1. Instalar Node.js

```bash
# Agregar repositorio de NodeSource
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -

# Instalar
sudo apt-get install -y nodejs

# Verificar
node --version    # debe mostrar v20.x.x
npm --version     # debe mostrar 10.x.x
```

### 2. Instalar Python y herramientas

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv python3-dev

# Verificar
python3 --version   # debe mostrar 3.10+ o 3.12+
```

### 3. Instalar dependencias del sistema para Pillow

```bash
sudo apt-get install -y libjpeg-dev libpng-dev libwebp-dev
```

### 4. Clonar o ubicarse en el proyecto

```bash
cd ~/Proyectos/S-Can
# Verificar estructura
ls
# Debe mostrar: ai/  backend/  frontend/  docs/  claude.md
```

---

## Configurar el Backend Node.js

```bash
cd S-Can/backend

# Instalar dependencias (lee package.json)
npm install

# Verificar que se instalaron
ls node_modules/ | grep -E "^(express|multer|axios|cors|form-data)"
# Debe listar los 5 paquetes
```

**Dependencias instaladas:**

```
express    ^4.18.2    framework web HTTP
cors       ^2.8.5     habilita CORS para peticiones desde el frontend
multer     ^2.1.1     manejo de subida de archivos multipart
axios      ^1.16.0    cliente HTTP para llamar a FastAPI
form-data  ^4.0.5     construir peticiones multipart desde Node.js
nodemon    ^3.0.1     (dev) hot reload al guardar archivos
```

Crear la carpeta de uploads si no existe:

```bash
mkdir -p S-Can/backend/uploads
```

---

## Configurar el Entorno Python

```bash
cd S-Can/ai

# Crear entorno virtual (aislado del Python del sistema)
python3 -m venv venv

# Activar entorno
source venv/bin/activate
# El prompt debe cambiar a: (venv) ...

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# Verificar TensorFlow
python3 -c "import tensorflow as tf; print(f'TF {tf.__version__}')"
# Debe mostrar: TF 2.13.x o superior
```

---

## Verificar que el modelo existe

```bash
ls S-Can/ai/models/
# Debe mostrar:
# class_indices.json  dogdex_model.keras  dogdex_model.h5  evaluation_report.txt
```

Si los archivos no existen, entrenar el modelo primero:

```bash
cd S-Can/ai
source venv/bin/activate
python3 prepare_dataset.py   # requiere imágenes en dataset/raw/
python3 train.py
```

Ver `TRAINING_GUIDE.md` para instrucciones completas de entrenamiento.

---

## Arrancar el sistema

### Terminal 1 — Servidor de Inferencia Python

```bash
cd S-Can/ai
source venv/bin/activate

uvicorn predict:app --host 0.0.0.0 --port 5000
```

Salida esperada:

```
Modelo cargado: models/dogdex_model.keras
Razas disponibles (5): ['beagle', 'chihuahua', 'golden_retriever', 'husky_siberiano', 'labrador_retriever']
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
```

Verificar:

```bash
curl http://localhost:5000/health
# {"status":"ok","model_loaded":true}
```

### Terminal 2 — Backend Node.js

```bash
cd S-Can/backend

# Producción
npm start

# Desarrollo (con hot reload)
npm run dev
```

Salida esperada:

```
Servidor DogDex corriendo en http://localhost:3000
```

Verificar:

```bash
curl http://localhost:3000/api/health
# {"status":"ok","message":"DogDex API funcionando"}
```

### Terminal 3 (o navegador) — Frontend

```bash
# Opción A: abrir directamente
xdg-open S-Can/frontend/index.html

# Opción B: servidor HTTP local (evita restricciones de seguridad en algunos navegadores)
cd S-Can/frontend
python3 -m http.server 8080
# Abrir http://localhost:8080
```

---

## Verificación completa del sistema

```bash
# 1. Verificar Python
curl http://localhost:5000/health

# 2. Verificar Node.js
curl http://localhost:3000/api/health

# 3. Probar el pipeline completo (necesita una imagen de perro)
curl -X POST http://localhost:3000/api/detect \
  -F "image=@/ruta/a/perro.jpg" | python3 -m json.tool
```

Respuesta esperada del pipeline completo:

```json
{
  "breed": "Golden Retriever",
  "confidence": "94%",
  "care": {
    "exercise": "Alta actividad física diaria",
    "grooming": "Cepillado frecuente, especialmente en muda",
    "temperament": "Amigable, confiable y muy sociable"
  }
}
```

---

## Orden correcto de arranque

El orden importa. Si Node.js arranca antes que Python, el primer análisis fallará con error 500. Los análisis siguientes funcionarán (Node.js reintenta en cada petición).

```
1. Iniciar Python (uvicorn)   → esperar mensaje "Application startup complete"
2. Iniciar Node.js (npm start) → esperar "Servidor DogDex corriendo en..."
3. Abrir el frontend
```

---

## Detener los servidores

```bash
# En cada terminal con el servidor corriendo
Ctrl + C

# O desde otra terminal (fuerza detención)
pkill -f "uvicorn predict:app"
pkill -f "node server.js"
pkill -f "nodemon"
```

---

## Troubleshooting de errores comunes

### "No se pudo conectar con el servidor"

El frontend muestra este mensaje cuando no puede alcanzar el backend Node.js.

```bash
# Verificar que Node.js está corriendo
curl http://localhost:3000/api/health

# Si no responde, verificar el puerto
ss -tlnp | grep :3000

# Iniciar si no está corriendo
cd S-Can/backend && npm start
```

### "Error al procesar la imagen" (500 del backend)

Node.js recibió la imagen pero falló al comunicarse con Python.

```bash
# Verificar que FastAPI está corriendo
curl http://localhost:5000/health

# Si no responde
cd S-Can/ai && source venv/bin/activate
uvicorn predict:app --host 0.0.0.0 --port 5000
```

Si Python arranca pero falla inmediatamente:

```bash
# Verificar que el modelo existe
ls S-Can/ai/models/dogdex_model.keras

# Si no existe, entrenar primero
python3 train.py
```

### "Formato no válido" aunque la imagen parece válida

Multer verifica el MIME type real del archivo, no la extensión. Algunos archivos `.jpg` descargados de internet pueden tener un MIME incorrecto.

```bash
# Verificar MIME real
file /ruta/a/imagen.jpg
# Debe mostrar: JPEG image data

# Convertir si es necesario
convert imagen.jpg -format jpg imagen_corregida.jpg
```

### `ModuleNotFoundError` al iniciar predict.py

El entorno virtual no está activado o no tiene las dependencias instaladas.

```bash
cd S-Can/ai
source venv/bin/activate
pip install -r requirements.txt
```

### Puerto 5000 o 3000 ya en uso

```bash
# Identificar qué proceso usa el puerto
ss -tlnp | grep :5000
ss -tlnp | grep :3000

# Matar el proceso (reemplazar PID con el número encontrado)
kill -9 <PID>
```

### El modelo carga pero la precisión es muy baja

El modelo en `ai/models/` puede estar desactualizado o ser de una versión anterior.

```bash
# Ver el reporte de evaluación
cat S-Can/ai/models/evaluation_report.txt

# Si la accuracy es < 80%, reentrenar
cd S-Can/ai && source venv/bin/activate
python3 train.py
```

### CORS error en el navegador

Si el frontend se abre como archivo local (`file://`) y hay un error CORS al llamar al backend, usar el servidor HTTP de Python:

```bash
cd S-Can/frontend
python3 -m http.server 8080
# Abrir http://localhost:8080 (no file:///...)
```

### `npm install` falla con errores de permisos

```bash
# Nunca usar sudo con npm install en proyectos locales
# Si hay problemas de permisos con ~/.npm:
npm install --prefix ~/.npm-global
# o reconfigurar npm:
npm config set prefix '~/.npm-global'
```

### La barra de confianza no se anima

Esto ocurre solo en Firefox con versiones muy antiguas que no soportan `requestAnimationFrame` doble (el hack en `main.js:113`). Actualizar el navegador a una versión modern a (Chrome 90+, Firefox 90+, Edge 90+).

---

## Estructura de puertos

| Servicio | Puerto | Proceso |
|---|---|---|
| Frontend (servidor HTTP opcional) | 8080 | `python3 -m http.server` |
| Backend Node.js | 3000 | `node server.js` |
| Servidor de inferencia Python | 5000 | `uvicorn` |

El frontend (`main.js`) tiene la URL del backend hardcodeada:

```javascript
const API_URL = 'http://localhost:3000/api/detect';
```

Para cambiarla en un entorno diferente, editar `frontend/js/main.js:1`.

---

## Flujo de archivos temporales

Multer guarda las imágenes subidas en `backend/uploads/`:

```bash
ls S-Can/backend/uploads/
# 1715432156789-mi_perro.jpg
# 1715432201234-labrador.png
# ...
```

Estos archivos **no se eliminan automáticamente**. En producción, agregar limpieza tras la inferencia en `detectController.js`:

```javascript
const fs = require('fs');

const detectImage = async (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'No se recibió ninguna imagen.' });
  try {
    const result = await analyzeImage(req.file);
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: 'Error al procesar la imagen.' });
  } finally {
    // Eliminar archivo temporal después de la inferencia
    if (req.file?.path) fs.unlink(req.file.path, () => {});
  }
};
```

Para limpiar manualmente archivos acumulados:

```bash
rm S-Can/backend/uploads/*
```
