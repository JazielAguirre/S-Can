const axios    = require('axios');
const FormData = require('form-data');
const fs       = require('fs');
const breeds   = require('../data/breeds');

const PYTHON_API = 'http://localhost:5000';

/**
 * Analiza una imagen y devuelve la raza detectada con su porcentaje de confianza.
 *
 * Responsabilidades de este servicio (Node.js):
 *   - Enviar la imagen al servidor de inferencia Python
 *   - Convertir el nombre técnico de carpeta → nombre legible
 *   - Convertir confidence float (0.91) → string porcentaje ("91%")
 *   - Agregar información de cuidados desde data/breeds.js
 *   - Mantener el contrato JSON hacia el controller y el frontend
 *
 * Contrato de retorno (invariante):
 * {
 *   breed:      string,
 *   confidence: string,   // ej. "91%"
 *   care: {
 *     exercise:    string,
 *     grooming:    string,
 *     temperament: string
 *   }
 * }
 *
 * @param {Express.Multer.File} file  Archivo procesado por multer
 * @returns {Promise<object>}
 */
async function analyzeImage(file) {
  const raw = await callPythonApi(file);

  // Node.js transforma la respuesta mínima de Python al contrato completo
  const displayName = toDisplayName(raw.breed);
  const confidence  = `${Math.round(raw.confidence * 100)}%`;
  const care        = findCare(displayName);

  return { breed: displayName, confidence, care };
}

// ── Comunicación con FastAPI ──────────────────────────────────

async function callPythonApi(file) {
  const form = new FormData();
  form.append('image', fs.createReadStream(file.path), {
    filename:    file.originalname,
    contentType: file.mimetype,
  });

  try {
    const { data } = await axios.post(`${PYTHON_API}/predict`, form, {
      headers: form.getHeaders(),
      timeout: 15000,
    });
    return data;
  } catch (err) {
    if (err.code === 'ECONNREFUSED') {
      throw new Error(
        'El servicio de IA no está disponible. ' +
        '¿Está corriendo predict.py en el puerto 5000?'
      );
    }
    throw err;
  }
}

// ── Helpers de transformación ─────────────────────────────────

/**
 * Convierte el nombre técnico de carpeta al nombre legible.
 * "golden_retriever" → "Golden Retriever"
 * "border_collie"   → "Border Collie"
 */
function toDisplayName(snakeName) {
  return snakeName
    .replace(/_/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase());
}

/**
 * Busca los datos de cuidados en breeds.js por nombre (insensible a mayúsculas).
 * Si la raza detectada no está en el catálogo devuelve valores genéricos
 * en lugar de fallar: el modelo podría detectar razas no registradas aún.
 */
function findCare(displayName) {
  const entry = breeds.find(
    b => b.breed.toLowerCase() === displayName.toLowerCase()
  );
  return entry?.care ?? {
    exercise:    'Información no disponible',
    grooming:    'Información no disponible',
    temperament: 'Información no disponible',
  };
}

module.exports = { analyzeImage };
