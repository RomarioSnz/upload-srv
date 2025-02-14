# app/celery_app.py
import os
import logging
import time
import shutil
import zipfile
import pyzipper

from celery import Celery
from app import create_app  # Импортируем функцию создания Flask-приложения из app/__init__.py

# Создаем экземпляр Flask-приложения, чтобы использовать его конфигурацию и контекст
flask_app = create_app()

# Инициализируем Celery, используя параметры из конфигурации Flask-приложения
celery = Celery(
    flask_app.import_name,
    broker=flask_app.config.get('CELERY_BROKER_URL'),
    backend=flask_app.config.get('CELERY_RESULT_BACKEND')
)
celery.conf.update(flask_app.config)

def _update_progress(task, idx, total_files):
    """
    Обновляет состояние задачи с расчётом прогресса.
    Вызывается каждые max(1, total_files // 20) файлов.
    """
    if (idx + 1) % max(1, total_files // 20) == 0:
        progress = int((idx + 1) / total_files * 100)
        task.update_state(state='PROGRESS', meta={'progress': progress})
        logging.info(f"⏳ Прогресс упаковки: {progress}%")

@celery.task(bind=True)
def create_zip_task(self, folder_path, zip_path, password=None):
    """
    Фоновая задача для создания ZIP-архива с возможным шифрованием.

    Аргументы:
      - folder_path: путь к каталогу с файлами для упаковки;
      - zip_path: итоговый путь к архиву;
      - password: (опционально) пароль для шифрования архива.
    """
    # Используем контекст Flask для доступа к ресурсам (например, к БД и конфигурации)
    with flask_app.app_context():
        try:
            logging.info(f"🟢 Запуск создания архива: {zip_path}")

            # Сбор списка файлов для упаковки
            file_list = [
                os.path.join(root, file)
                for root, _, files in os.walk(folder_path)
                for file in files
            ]
            if not file_list:
                logging.error(f"❌ Ошибка: Каталог {folder_path} пуст.")
                self.update_state(state='FAILURE', meta={'progress': 0})
                return {'progress': 0}

            total_files = len(file_list)
            logging.info(f"📂 Файлов для упаковки: {total_files}")

            if password:
                logging.info("🔒 Используется AES-шифрование.")
                compress_kwargs = {
                    'compression': pyzipper.ZIP_DEFLATED,
                    'compresslevel': 0,
                    'encryption': pyzipper.WZ_AES
                }
                with pyzipper.AESZipFile(zip_path, 'w', **compress_kwargs) as zipf:
                    zipf.setpassword(password.encode())
                    for idx, file in enumerate(file_list):
                        arcname = os.path.relpath(file, folder_path)
                        zipf.write(file, arcname)
                        _update_progress(self, idx, total_files)
            else:
                logging.info("📦 Создание обычного ZIP-архива.")
                compress_kwargs = {
                    'compression': zipfile.ZIP_DEFLATED,
                    'compresslevel': 0
                }
                with zipfile.ZipFile(zip_path, 'w', **compress_kwargs) as zipf:
                    for idx, file in enumerate(file_list):
                        arcname = os.path.relpath(file, folder_path)
                        zipf.write(file, arcname)
                        _update_progress(self, idx, total_files)

            logging.info(f"✅ Архив создан: {zip_path}")
            self.update_state(state='SUCCESS', meta={'progress': 100, 'link': os.path.basename(zip_path)})

            # Небольшая задержка для гарантии сохранения статуса в брокере задач
            time.sleep(2)

            # Удаляем временный каталог после завершения упаковки
            shutil.rmtree(folder_path)
            logging.info("🗑 Удалена временная папка")

            return {'progress': 100, 'link': os.path.basename(zip_path)}

        except Exception as e:
            logging.error(f"❌ Ошибка при упаковке: {str(e)}")
            self.update_state(state='FAILURE', meta={'progress': 0})
            raise
