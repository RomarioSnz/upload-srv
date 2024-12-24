from flask import request, jsonify, redirect, url_for, render_template, send_from_directory
from . import create_app
from .tasks import create_zip_task
from .utils import create_unique_folder, generate_unique_filename
import os

app = create_app()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')

    # POST-запрос
    files = request.files.getlist('files[]')
    if not files:
        return jsonify({'error': 'No files selected'}), 400

    # Создание папки
    unique_id, folder_path = create_unique_folder(app.config['NETWORK_FOLDER'])

    # Сохранение файлов
    for file in files:
        unique_filename = generate_unique_filename(file.filename)
        file.save(os.path.join(folder_path, unique_filename))

    # Создание ZIP архива в фоне
    zip_path = os.path.join(app.config['NETWORK_FOLDER'], f"{unique_id}.zip")
    create_zip_task.delay(folder_path, zip_path)

    # Ссылка для скачивания
    download_link = url_for('download_files', unique_id=unique_id, _external=True)
    return redirect(url_for('success', link=download_link))


@app.route('/success')
def success():
    link = request.args.get('link')
    if not link:
        return redirect(url_for('index'))
    return render_template('success.html', link=link)

@app.route('/download/<unique_id>', methods=['GET'])
def download_files(unique_id):
    zip_path = os.path.join(app.config['NETWORK_FOLDER'], f"{unique_id}.zip")
    if not os.path.exists(zip_path):
        return jsonify({'error': 'File not found'}), 404
    return send_from_directory(app.config['NETWORK_FOLDER'], f"{unique_id}.zip", as_attachment=True)
