import time
from flask import Flask, request, jsonify, redirect, url_for, render_template, send_file
from . import create_app
from .tasks import create_zip_task
from .utils import create_unique_folder
from celery.result import AsyncResult
import os
import logging

# Логирование
logging.basicConfig(level=logging.DEBUG)

# Создание приложения и Celery
app = create_app()
celery = app.celery

@app.route('/', methods=['GET', 'POST'])
def index():
    # Получаем имя пользователя из заголовка REMOTE_USER
    username = request.headers.get('REMOTE_USER')

    if request.method == 'GET':
        # Отображаем страницу загрузки файлов
        return render_template('index.html', username=username)  # передаем имя пользователя в шаблон

    # Получаем загруженные файлы
    files = request.files.getlist('files[]')
    if not files:
        return jsonify({'error': 'No files selected'}), 400

    # Создаем уникальную папку
    unique_id, folder_path = create_unique_folder(app.config['NETWORK_FOLDER'])
    logging.info(f"Создана папка: {folder_path}")

    # Сохраняем файлы с поддержкой вложенной структуры
    for file in files:
        # Сохраняем относительный путь файла для поддержки структуры папок
        relative_path = file.filename  # Файл может содержать относительный путь
        save_path = os.path.join(folder_path, relative_path)

        # Создаём папки, если их нет
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # Сохраняем файл
        file.save(save_path)
        logging.info(f"Сохранён файл: {save_path}")

    # Путь к ZIP-архиву
    zip_path = os.path.join(app.config['NETWORK_FOLDER'], f"{unique_id}.zip")
    logging.info(f"Создание архива: {zip_path}")

    # Запускаем задачу создания ZIP-архива
    task = create_zip_task.apply_async(args=[folder_path, zip_path])

    # Возвращаем ID задачи и ссылку для скачивания
    return jsonify({
        'task_id': task.id,
        'link': url_for('download_files', unique_id=unique_id, _external=True)
    })

@app.route('/success')
def success():
    # Отображение страницы успешной загрузки
    link = request.args.get('link')  # Получаем ссылку для скачивания
    if not link:
        return redirect(url_for('index'))
    return render_template('success.html', link=link)

@app.route('/download/<unique_id>', methods=['GET'])
def download_files(unique_id):
    # Загрузка ZIP-архива по его ID
    if not unique_id.endswith(".zip"):
        unique_id += ".zip"

    zip_path = os.path.join(app.config['NETWORK_FOLDER'], unique_id)

    logging.info(f"Проверка архива: {zip_path}")

    if not os.path.exists(zip_path):
        logging.error(f"Файл не найден: {zip_path}")
        return jsonify({'error': 'File not found'}), 404

    logging.info(f"Отправка архива: {zip_path}")
    try:
        return send_file(zip_path, as_attachment=True)
    except Exception as e:
        logging.error(f"Ошибка при отправке файла: {e}")
        return jsonify({'error': 'Failed to download file'}), 500

@app.route('/status/<task_id>', methods=['GET'])
def task_status(task_id):
    # Проверка статуса задачи
    task = AsyncResult(task_id, app=celery)

    if task.state == 'PENDING':
        response = {'state': task.state, 'progress': 0}
    elif task.state == 'PROGRESS':
        response = {'state': task.state, 'progress': task.info.get('progress', 0)}
    elif task.state == 'SUCCESS':
        response = {'state': task.state, 'progress': 100}
    else:
        response = {'state': task.state, 'error': str(task.info)}

    return jsonify(response)

if __name__ == "__main__":
    app.run()
