const API_URL = 'http://localhost:3000/api/detect';

// ─── Referencias DOM ──────────────────────────────────
const imageInput     = document.getElementById('imageInput');
const selectBtn      = document.getElementById('selectBtn');
const uploadBtn      = document.getElementById('uploadBtn');
const previewEl      = document.getElementById('preview');
const previewImg     = document.getElementById('previewImg');
const fileNameEl     = document.getElementById('fileName');
const messageEl      = document.getElementById('message');
const resultCard     = document.getElementById('resultCard');
const resultBreed    = document.getElementById('resultBreed');
const resultConf     = document.getElementById('resultConfidence');
const confidenceBar  = document.getElementById('confidenceBar');
const careExercise   = document.getElementById('careExercise');
const careGrooming   = document.getElementById('careGrooming');
const careTemperament = document.getElementById('careTemperament');
const resetBtn       = document.getElementById('resetBtn');

const clearHistoryBtn = document.getElementById('clearHistoryBtn');

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
const MAX_SIZE_MB   = 5;

clearHistoryBtn.addEventListener('click', () => {
  DogDexHistory.clear();
  DogDexStats.clear();
  DogDexHistory.render();
  DogDexStats.render();
});

// Carga historial y estadísticas al abrir la página
DogDexHistory.render();
DogDexStats.render();

// ─── Eventos ──────────────────────────────────────────

selectBtn.addEventListener('click', () => imageInput.click());

imageInput.addEventListener('change', () => {
  const file = imageInput.files[0];
  hideMessage();
  hideResult();

  if (!file) return;

  const error = validateFile(file);
  if (error) {
    showMessage(error, 'error');
    resetPreview();
    return;
  }

  showPreview(file);
  uploadBtn.classList.remove('hidden');
});

uploadBtn.addEventListener('click', async () => {
  const file = imageInput.files[0];
  if (!file) return;

  setLoading(true);
  hideMessage();
  hideResult();

  try {
    const formData = new FormData();
    formData.append('image', file);

    const response = await fetch(API_URL, { method: 'POST', body: formData });
    const data = await response.json();

    if (!response.ok) {
      showMessage(data.error || 'Error al procesar la imagen.', 'error');
    } else {
      DogDexHistory.save(data, previewImg.src);
      DogDexStats.record(data);
      DogDexHistory.render();
      DogDexStats.render();
      renderResult(data);
    }
  } catch {
    showMessage('No se pudo conectar con el servidor. ¿Está corriendo el backend?', 'error');
  } finally {
    setLoading(false);
  }
});

// Resetea el formulario para analizar otra imagen
resetBtn.addEventListener('click', () => {
  resetPreview();
  hideResult();
  hideMessage();
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

// ─── Renderizado de resultado ─────────────────────────

function renderResult(data) {
  const pct = parseInt(data.confidence, 10);

  resultBreed.textContent       = data.breed;
  resultConf.textContent        = data.confidence;
  careExercise.textContent      = data.care.exercise;
  careGrooming.textContent      = data.care.grooming;
  careTemperament.textContent   = data.care.temperament;

  // Resetea la barra antes de animar para que la transición siempre se dispare
  confidenceBar.style.width = '0%';
  resultCard.classList.remove('hidden');

  // Pequeño delay para que el navegador pinte el 0% antes de expandir
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      confidenceBar.style.width = `${pct}%`;
    });
  });

  resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ─── Helpers ──────────────────────────────────────────

function validateFile(file) {
  if (!ALLOWED_TYPES.includes(file.type)) {
    return 'Formato no válido. Solo se aceptan JPG, PNG, WEBP o GIF.';
  }
  if (file.size > MAX_SIZE_MB * 1024 * 1024) {
    return `El archivo supera el límite de ${MAX_SIZE_MB} MB.`;
  }
  return null;
}

function showPreview(file) {
  const reader = new FileReader();
  reader.onload = (e) => {
    previewImg.src = e.target.result;
    fileNameEl.textContent = file.name;
    previewEl.classList.remove('hidden');
  };
  reader.readAsDataURL(file);
}

function resetPreview() {
  previewEl.classList.add('hidden');
  uploadBtn.classList.add('hidden');
  imageInput.value = '';
}

function hideResult() {
  resultCard.classList.add('hidden');
}

function showMessage(text, type) {
  messageEl.textContent = text;
  messageEl.className = `message ${type}`;
}

function hideMessage() {
  messageEl.className = 'message hidden';
}

function setLoading(isLoading) {
  uploadBtn.disabled = isLoading;
  uploadBtn.textContent = isLoading ? 'Analizando...' : 'Analizar imagen';
}
