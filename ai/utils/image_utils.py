"""
Utilidades de preprocesamiento de imágenes para DogDex.
Todas las funciones son independientes del framework ML para
poder usarse tanto en prepare_dataset.py como en predict.py.
"""

import os
from PIL import Image, UnidentifiedImageError

# MobileNetV2 espera entradas de 224×224
TARGET_SIZE = (224, 224)

# Tamaño mínimo aceptable para una imagen de entrenamiento
MIN_DIMENSION = 80

VALID_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}


def is_valid_image(path: str) -> bool:
    """
    Verifica que el archivo sea una imagen soportada con dimensiones mínimas.
    Abre el archivo real para detectar imágenes corruptas que pasan la extensión.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext not in VALID_EXTENSIONS:
        return False
    try:
        with Image.open(path) as img:
            img.verify()   # detecta corrupción sin cargar píxeles
        # verify() cierra el archivo internamente; hay que reabrir para leer size
        with Image.open(path) as img:
            return min(img.size) >= MIN_DIMENSION
    except (UnidentifiedImageError, Exception):
        return False


def resize_and_save(src_path: str, dest_path: str, size: tuple = TARGET_SIZE) -> None:
    """
    Redimensiona la imagen al tamaño objetivo y la guarda como JPEG.
    Convierte a RGB antes de guardar para normalizar RGBA, escala de grises, etc.
    LANCZOS minimiza el aliasing al reducir imágenes grandes.
    """
    with Image.open(src_path) as img:
        img = img.convert('RGB')
        img = img.resize(size, Image.LANCZOS)
        img.save(dest_path, 'JPEG', quality=92)


def collect_images(directory: str) -> list[str]:
    """
    Devuelve rutas absolutas de todas las imágenes válidas en un directorio.
    No es recursivo: asume que las imágenes están directamente en el directorio dado.
    """
    if not os.path.isdir(directory):
        return []
    return sorted(
        os.path.join(directory, fname)
        for fname in os.listdir(directory)
        if is_valid_image(os.path.join(directory, fname))
    )
