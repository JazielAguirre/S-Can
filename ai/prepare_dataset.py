"""
prepare_dataset.py
──────────────────
Lee imágenes crudas de dataset/raw/<raza>/, las valida, redimensiona a
224×224 y las distribuye en train / validation / test con proporción 70/15/15.

Uso:
    python prepare_dataset.py

Estructura esperada de entrada:
    dataset/raw/
        golden_retriever/   ← al menos 150 imágenes recomendadas
        labrador_retriever/
        border_collie/
        ...

Resultado:
    dataset/processed/
        train/
        validation/
        test/
"""

import os
import random
import shutil
from pathlib import Path
from tqdm import tqdm

from utils.image_utils import collect_images, resize_and_save

# ── Configuración ────────────────────────────────────────────

RAW_DIR       = Path('dataset/raw')
PROCESSED_DIR = Path('dataset/processed')

SPLIT_RATIOS = {'train': 0.70, 'validation': 0.15, 'test': 0.15}
RANDOM_SEED  = 42
MIN_IMAGES_WARNING = 150

# ── Funciones ────────────────────────────────────────────────

def split_images(images: list[str], ratios: dict, seed: int) -> dict[str, list[str]]:
    """
    Divide la lista de imágenes en tres subconjuntos manteniendo las proporciones.
    Usa una semilla fija para que el split sea reproducible entre ejecuciones.
    """
    rng = random.Random(seed)
    shuffled = images.copy()
    rng.shuffle(shuffled)

    total     = len(shuffled)
    train_end = int(total * ratios['train'])
    val_end   = train_end + int(total * ratios['validation'])

    return {
        'train':      shuffled[:train_end],
        'validation': shuffled[train_end:val_end],
        'test':       shuffled[val_end:],
    }


def process_breed(breed: str, images: list[str]) -> dict[str, int]:
    """
    Procesa todas las imágenes de una raza: valida el split,
    redimensiona cada imagen y la guarda en el directorio correspondiente.
    Devuelve el conteo de imágenes por split.
    """
    splits = split_images(images, SPLIT_RATIOS, RANDOM_SEED)
    counts = {}

    for split_name, split_files in splits.items():
        dest_dir = PROCESSED_DIR / split_name / breed
        dest_dir.mkdir(parents=True, exist_ok=True)

        for idx, src_path in enumerate(tqdm(split_files, desc=f'  {split_name:<12}', leave=False)):
            dest_path = dest_dir / f'{breed}_{idx:04d}.jpg'
            try:
                resize_and_save(src_path, str(dest_path))
            except Exception as e:
                print(f'\n  Error procesando {src_path}: {e}')

        counts[split_name] = len(split_files)

    return counts


def validate_raw_dir() -> list[str]:
    """
    Verifica que el directorio raw exista y tenga subdirectorios de razas.
    Retorna la lista de razas encontradas o termina con mensaje de ayuda.
    """
    if not RAW_DIR.exists():
        print(f'\nError: no existe el directorio "{RAW_DIR}".')
        print('Crea la carpeta y organiza las imágenes así:')
        print('  dataset/raw/<nombre_raza>/<imagen>.jpg')
        raise SystemExit(1)

    breeds = sorted(
        d for d in os.listdir(RAW_DIR)
        if (RAW_DIR / d).is_dir() and not d.startswith('.')
    )

    if not breeds:
        print(f'\nNo se encontraron subdirectorios de razas en "{RAW_DIR}".')
        raise SystemExit(1)

    return breeds


def print_report(report: dict[str, dict[str, int]]) -> None:
    """Imprime tabla resumen con conteo de imágenes por raza y por split."""
    line = '─' * 58
    print(f'\n{line}')
    print(f'  {"Raza":<26} {"Train":>7} {"Val":>7} {"Test":>7}')
    print(line)

    totals = {s: 0 for s in SPLIT_RATIOS}
    for breed, counts in sorted(report.items()):
        print(f'  {breed:<26} {counts["train"]:>7} {counts["validation"]:>7} {counts["test"]:>7}')
        for split in totals:
            totals[split] += counts[split]

    print(line)
    print(f'  {"TOTAL":<26} {totals["train"]:>7} {totals["validation"]:>7} {totals["test"]:>7}')
    total_all = sum(totals.values())
    print(f'\n  Total imágenes procesadas: {total_all}')
    print(f'  Guardadas en: {PROCESSED_DIR.resolve()}')
    print(line)


# ── Punto de entrada ─────────────────────────────────────────

def main() -> None:
    breeds = validate_raw_dir()

    print(f'\nRazas encontradas ({len(breeds)}): {", ".join(breeds)}')
    print(f'Destino: {PROCESSED_DIR.resolve()}\n')

    # Limpiar procesados previos para evitar mezcla con ejecuciones anteriores
    if PROCESSED_DIR.exists():
        shutil.rmtree(PROCESSED_DIR)
    PROCESSED_DIR.mkdir()

    report = {}

    for breed in breeds:
        breed_dir = RAW_DIR / breed
        images    = collect_images(str(breed_dir))
        total     = len(images)

        print(f'[{breed}] {total} imágenes encontradas')

        if total < MIN_IMAGES_WARNING:
            print(f'  ⚠ Se recomiendan al menos {MIN_IMAGES_WARNING} imágenes para entrenar bien.')

        if total < 3:
            print(f'  ✗ Raza omitida: necesita al menos 3 imágenes para hacer el split.')
            continue

        report[breed] = process_breed(breed, images)

    if report:
        print_report(report)
    else:
        print('\nNo se procesó ninguna raza. Revisa el contenido de dataset/raw/.')


if __name__ == '__main__':
    main()
