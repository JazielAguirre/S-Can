/**
 * DogDexHistory
 * Módulo autónomo de historial local. Gestiona localStorage y renderiza
 * las tarjetas sin conocer el formulario ni el flujo de análisis.
 *
 * API pública:
 *   DogDexHistory.save(data, imageBase64)  — guarda un análisis
 *   DogDexHistory.render()                 — reconstruye la sección de historial
 *   DogDexHistory.clear()                  — borra todo el historial
 */
const DogDexHistory = (() => {
  const STORAGE_KEY = 'dogdex_history';
  const MAX_ENTRIES = 5;

  // ─── localStorage ────────────────────────────────────

  function load() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
    } catch {
      return [];
    }
  }

  function persist(entries) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
  }

  // ─── API pública ─────────────────────────────────────

  function save(data, imageBase64) {
    const entry = {
      breed:      data.breed,
      confidence: data.confidence,
      care:       data.care,
      date:       new Date().toISOString(),
      imageBase64
    };

    // Más reciente primero; máximo MAX_ENTRIES entradas
    const updated = [entry, ...load()].slice(0, MAX_ENTRIES);
    persist(updated);
  }

  function clear() {
    localStorage.removeItem(STORAGE_KEY);
  }

  function render() {
    const list    = document.getElementById('historyList');
    const clearBtn = document.getElementById('clearHistoryBtn');
    const entries = load();

    list.innerHTML = '';

    if (entries.length === 0) {
      clearBtn.classList.add('hidden');
      list.appendChild(buildEmptyState());
      return;
    }

    clearBtn.classList.remove('hidden');
    entries.forEach((entry, index) => {
      const card = buildCard(entry, index);
      list.appendChild(card);
    });
  }

  // ─── Construcción de DOM ──────────────────────────────

  function buildEmptyState() {
    const p = document.createElement('p');
    p.className = 'history-empty';
    p.textContent = 'Aún no has analizado ninguna imagen.';
    return p;
  }

  function buildCard(entry, index) {
    const card = document.createElement('div');
    card.className = 'history-card';
    // Escalonamiento de la animación de entrada
    card.style.animationDelay = `${index * 0.06}s`;

    const img = document.createElement('img');
    img.className = 'history-thumb';
    img.src = entry.imageBase64;
    img.alt = entry.breed;

    const info = document.createElement('div');
    info.className = 'history-info';

    const breedRow = document.createElement('div');
    breedRow.className = 'history-breed-row';

    const breedName = document.createElement('span');
    breedName.className = 'history-breed';
    breedName.textContent = entry.breed;

    const badge = document.createElement('span');
    badge.className = 'history-badge';
    badge.textContent = entry.confidence;

    const date = document.createElement('span');
    date.className = 'history-date';
    date.textContent = formatDate(entry.date);

    breedRow.appendChild(breedName);
    breedRow.appendChild(badge);
    info.appendChild(breedRow);
    info.appendChild(date);
    card.appendChild(img);
    card.appendChild(info);

    return card;
  }

  // ─── Utilidades ───────────────────────────────────────

  function formatDate(iso) {
    const then = new Date(iso);
    const now  = new Date();
    const diffMs  = now - then;
    const diffMin = Math.floor(diffMs / 60000);

    if (diffMin < 1)  return 'Hace un momento';
    if (diffMin < 60) return `Hace ${diffMin} min`;

    const diffH = Math.floor(diffMin / 60);
    if (diffH < 24)   return `Hace ${diffH} h`;

    // Distinto día: mostrar fecha completa
    return then.toLocaleDateString('es-MX', {
      day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'
    });
  }

  return { save, clear, render };
})();
