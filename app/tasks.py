from app import create_app
import zipfile
import os
import shutil
import logging
import time

# Логирование для отладки
logging.basicConfig(level=logging.DEBUG)

# Создание приложения и объекта Celery
app = create_app()
celery = app.celery


@celery.task(bind=True)
def create_zip_task(self, folder_path, zip_path):
    """
    Фоновая задача для создания ZIP-архива из папки с файлами.
    """
    logging.info(f"Начало создания ZIP-архива: {zip_path}")

    try:
        # Проверка наличия файлов в папке
        file_count = sum(len(files) for _, _, files in os.walk(folder_path))
        if file_count == 0:
            logging.error("Ошибка: в папке нет файлов для архивации!")
            raise Exception("В папке нет файлов для архивации!")

        # Прогресс создания архива
        total_files = file_count
        processed_files = 0

        # Создаём ZIP-архив
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)

                    # Добавляем файл в архив
                    arcname = os.path.relpath(file_path, folder_path)
                    zipf.write(file_path, arcname=arcname)

                    # Обновляем прогресс
                    processed_files += 1
                    self.update_state(state='PROGRESS', meta={'progress': int(processed_files / total_files * 100)})
                    time.sleep(0.1)  # Имитируем задержку для тестирования

        logging.info(f"ZIP-архив успешно создан: {zip_path}")

    except Exception as e:
        logging.error(f"Ошибка при создании ZIP-архива: {e}", exc_info=True)
        raise e  # Пробрасываем исключение

    finally:
        # Удаляем временную папку после создания архива
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)

    # Возвращаем успешный статус
    return {'progress': 100}
