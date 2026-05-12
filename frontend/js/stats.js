/**
 * DogDexStats
 * Módulo autónomo de estadísticas locales. Mantiene su propio registro
 * acumulativo en localStorage, independiente del historial (que solo guarda
 * las últimas 5 entradas). Así el total y el promedio reflejan todos los
 * análisis realizados, no solo los más recientes.
 *
 * API pública:
 *   DogDexStats.record(data)  — registra un nuevo análisis
 *   DogDexStats.render()      — actualiza el DOM con los valores actuales
 *   DogDexStats.clear()       — resetea todas las estadísticas
 */
const DogDexStats = (() => {
  const STORAGE_KEY = 'dogdex_stats';

  // ─── localStorage ────────────────────────────────────

  function load() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY)) || empty();
    } catch {
      return empty();
    }
  }

  function empty() {
    return { totalCount: 0, breedCounts: {}, confidenceSum: 0 };
  }

  function persist(stats) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(stats));
  }

  // ─── Cálculos ─────────────────────────────────────────

  function topBreed(breedCounts) {
    const entries = Object.entries(breedCounts);
    if (entries.length === 0) return null;
    return entries.reduce((best, curr) => curr[1] > best[1] ? curr : best)[0];
  }

  function avgConfidence(stats) {
    if (stats.totalCount === 0) return null;
    return Math.round(stats.confidenceSum / stats.totalCount);
  }

  // ─── API pública ──────────────────────────────────────

  function record(data) {
    const stats = load();
    const pct   = parseInt(data.confidence, 10);

    stats.totalCount++;
    stats.breedCounts[data.breed] = (stats.breedCounts[data.breed] || 0) + 1;
    stats.confidenceSum += pct;

    persist(stats);
  }

  function clear() {
    localStorage.removeItem(STORAGE_KEY);
  }

  function render() {
    const section = document.getElementById('statsSection');
    const stats   = load();

    if (stats.totalCount === 0) {
      section.classList.add('hidden');
      return;
    }

    section.classList.remove('hidden');

    document.getElementById('statTotal').textContent   = stats.totalCount;
    document.getElementById('statTopBreed').textContent = topBreed(stats.breedCounts) ?? '—';
    document.getElementById('statAvgConf').textContent  = `${avgConfidence(stats)}%`;
  }

  return { record, clear, render };
})();
