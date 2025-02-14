from pathlib import Path
import uuid
import time
import logging

# Чистое имя пользователя
def sanitize_username(username):
    return username.split('@')[0].replace(".", "_")
def sanitize_filename(name):
    return "".join(c if c.isalnum() or c in ("_", "-", " ") else "_" for c in name).strip()

def create_user_upload_folder(base_path, username, custom_zip_name=""):
    """
    Создаёт уникальный каталог внутри каталога пользователя.
    Если пользователь указал имя архива, оно используется. Иначе генерируется автоматически.
    """
    sanitized_username = sanitize_username(username)
    timestamp = time.strftime("%d%m%y_%H") #"%Y%m%d_%H%M%S"
    unique_code = str(uuid.uuid4())[:4]

    # Определяем имя архива
    if custom_zip_name:
        zip_name = sanitize_filename(custom_zip_name) + ".zip"
    else:
        zip_name = f"{sanitized_username}_{timestamp}_{unique_code}.zip"

    folder_name = zip_name.replace(".zip", "")  # переводим имя каталог в имя архива без .zip
    user_folder = Path(base_path) / sanitized_username  # Каталог пользователя
    upload_folder = user_folder / folder_name         # Уникальный каталог для загрузки

    # Создаем каталоги
    upload_folder.mkdir(parents=True, exist_ok=True)
    logging.info(f"Создана папка загрузки: {upload_folder}")

    zip_path = user_folder / zip_name  # Итоговый путь к ZIP-архивау

    return str(upload_folder), str(zip_path)
