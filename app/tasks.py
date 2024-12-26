from celery import Celery, shared_task
import os
import zipfile
import shutil

# Инициализация Celery
celery = Celery(
    'tasks',
    broker='redis://redis:6379/0',
    backend='redis://redis:6379/0'
)

celery.conf.update(
    task_track_started=True,
    result_extended=True,
)

@shared_task(bind=True)
def create_zip_task(self, folder_path, zip_path):
    try:
        # Логи начала задачи
        print(f"Начало упаковки: {folder_path} -> {zip_path}")

        # Проверка существования файлов в папке
        file_list = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_list.append(os.path.join(root, file))

        if not file_list:
            print("Ошибка: Папка пуста.")
            self.update_state(state='FAILURE', meta={'progress': 0})
            return {'progress': 0}

        # Лог количества файлов
        print(f"Файлов для упаковки: {len(file_list)}")

        # Создание ZIP архива
        total_files = len(file_list)
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for idx, file in enumerate(file_list):
                # Лог текущего файла
                print(f"Добавление файла в архив: {file}")
                zipf.write(file, os.path.relpath(file, folder_path))
                # Обновление прогресса
                progress = int((idx + 1) / total_files * 100)
                self.update_state(state='PROGRESS', meta={'progress': progress})

        # Лог успешного создания ZIP
        print(f"ZIP-архив успешно создан: {zip_path}")

        # Удаление временной папки
        shutil.rmtree(folder_path)
        print(f"Удалена временная папка: {folder_path}")

        # Возврат состояния SUCCESS с ссылкой на архив
        return {'progress': 100, 'link': os.path.basename(zip_path)}

    except Exception as e:
        # Лог ошибки
        print(f"Ошибка при упаковке: {str(e)}")
        self.update_state(state='FAILURE', meta={'progress': 0})
        raise e
