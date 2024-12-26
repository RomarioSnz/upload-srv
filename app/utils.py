import os
import uuid
import hashlib
import time
import logging

def create_unique_folder(base_path):
    """
    Создаёт уникальную папку в указанной директории.
    Возвращает уникальный ID и путь к созданной папке.
    """
    # Проверяем базовую директорию
    if not os.path.exists(base_path):
        logging.error(f"Базовая папка не найдена: {base_path}")
        raise FileNotFoundError(f"Базовая папка не найдена: {base_path}")

    try:
        unique_id = str(uuid.uuid4())  # Генерация UUID
        folder_path = os.path.join(base_path, unique_id)
        os.makedirs(folder_path, exist_ok=True)  # Создаём папку
        logging.info(f"Создана уникальная папка: {folder_path}")
        return unique_id, folder_path
    except Exception as e:
        logging.error(f"Ошибка создания папки {folder_path}: {e}")
        raise

def generate_unique_filename(filename):
    """
    Генерирует уникальное имя файла с сохранением исходного расширения.
    Добавляет к имени временную метку для уникальности.
    """
    base, ext = os.path.splitext(filename)
    timestamp = int(time.time())  # Добавляем метку времени
    return f"{base}_{timestamp}{ext}"  # Пример: file_1703513262.pdf
