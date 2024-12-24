from . import create_app
import zipfile
import shutil
import os

app = create_app()

@app.celery.task
def create_zip_task(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, folder_path))
    shutil.rmtree(folder_path)  # Удаляем исходные файлы
