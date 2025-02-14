from flask import Flask, request, jsonify, redirect, url_for, render_template, send_file, flash
from . import create_app, db
from app.celery_app import create_zip_task, celery
from .utils import create_user_upload_folder, sanitize_username
from .models import Upload
from celery.result import AsyncResult
from sqlalchemy.exc import OperationalError
import os
import logging
import zipfile

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)

# Создание приложения и Celery
app = create_app()
@app.route('/', methods=['GET', 'POST'])
def index():
    username = request.environ.get('HTTP_X_FORWARDED_USER', 'anonymous')

    if request.method == 'GET':
        return render_template('index.html', username=username)

    # Получаем файлы из формы
    files = request.files.getlist('files[]')
    if not files:
        return jsonify({'error': 'No files selected'}), 400

    # Получаем имя архива и пароль (если заданы)
    zip_name = request.form.get('zip_name', '').strip()
    password = request.form.get('password', '').strip()

    logging.info(
        f"Пользователь: {username}, Запрошенное имя архива: {zip_name}, Пароль: {'есть' if password else 'нет'}")

    # Создаем уникальный каталог для загрузки и определяем путь к итоговому ZIP-архиву
    upload_folder, zip_path = create_user_upload_folder(app.config['NETWORK_FOLDER'], username, zip_name)

    total_size = 0
    file_count = 0
    # Сохраняем файлы и подсчитываем их размер и количество
    for file in files:
        save_path = os.path.join(upload_folder, file.filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        file.save(save_path)
        size = os.path.getsize(save_path)
        total_size += size
        file_count += 1
        logging.info(f"Сохранён файл: {save_path} ({size} байт)")

    logging.info(f"Сохранено файлов: {file_count}. Общий размер: {total_size} байт. ZIP: {zip_path}")

    # Проверяем, существует ли архив с таким именем и, если да, добавляем суффикс _1, _2, _3 и т.д.
    original_archive_name, ext = os.path.splitext(os.path.basename(zip_path))
    new_archive_name = os.path.basename(zip_path)
    i = 1
    while Upload.query.filter_by(username=username, archive_name=new_archive_name).first():
        new_archive_name = f"{original_archive_name}_{i}{ext}"
        i += 1
    if new_archive_name != os.path.basename(zip_path):
        zip_path = os.path.join(os.path.dirname(zip_path), new_archive_name)
        logging.info(f"Архив с именем {original_archive_name + ext} уже существует. Используем новое имя: {new_archive_name}")

    # Сохранение метаданных загрузки в PostgreSQL (таблица uploads)
    new_upload = Upload(
        username=username,
        archive_name=os.path.basename(zip_path),
        file_count=file_count,
        filesize=total_size
    )
    db.session.add(new_upload)
    db.session.commit()
    logging.info(f"Запись о загрузке сохранена: {new_upload}")

    # Запускаем фоновую задачу создания ZIP-архива с паролем (если указан)
    task = create_zip_task.apply_async((upload_folder, zip_path, password))

    return jsonify({
        'task_id': task.id,
        'link': url_for('download_files', unique_id=os.path.basename(zip_path), _external=True)
    })

@app.route('/download/<unique_id>', methods=['GET'])
def download_files(unique_id):
    """Скачивание ZIP-архива"""
    network_folder = app.config.get('NETWORK_FOLDER')
    if not network_folder:
        logging.error("Переменная NETWORK_FOLDER не задана!")
        return jsonify({'error': 'Storage not found'}), 500

    zip_path = None
    for root, _, files in os.walk(network_folder):
        if unique_id in files or f"{unique_id}.zip" in files:
            zip_path = os.path.join(root, unique_id if unique_id in files else f"{unique_id}.zip")
            break

    if not zip_path:
        logging.error(f"Файл {unique_id} не найден в {network_folder}")
        return jsonify({'error': 'Not found'}), 404

    logging.info(f"Отправка архива: {zip_path}")
    try:
        return send_file(zip_path, as_attachment=True)
    except Exception as e:
        logging.error(f"Ошибка отправки файла: {e}")
        return jsonify({'error': 'Failed to download file'}), 500


@app.route('/status/<task_id>', methods=['GET'])
def task_status(task_id):
    """Проверка статуса задачи упаковки"""
    task = AsyncResult(task_id, app=celery)
    if task.state == 'PENDING':
        response = {'state': task.state, 'progress': 0}
    elif task.state == 'PROGRESS':
        response = {'state': task.state, 'progress': task.info.get('progress', 0)}
    elif task.state == 'SUCCESS':
        response = {
            'state': task.state,
            'progress': 100,
            'link': url_for('download_files', unique_id=os.path.basename(task.info['link']), _external=True)
        }
    else:
        response = {'state': task.state, 'error': str(task.info)}
    return jsonify(response)


@app.route("/success")
def success():
    link = request.args.get("link", "")
    return render_template("success.html", link=link)


@app.route('/uploads', methods=['GET'])
def list_uploads():
    """Отображение списка загруженных архивов"""
    username = request.environ.get('HTTP_X_FORWARDED_USER', 'anonymous')

    try:
        uploads = Upload.query.filter_by(username=username).order_by(Upload.upload_time.desc()).all()
    except OperationalError:
        db.session.rollback()
        return "Ошибка подключения к базе данных. Попробуйте позже.", 500

    return render_template("uploads.html", uploads=uploads, username=username)


@app.route('/uploads/<archive>', methods=['GET'])
def view_archive(archive):
    """Просмотр содержимого архива"""
    username = request.environ.get('HTTP_X_FORWARDED_USER', 'anonymous')
    network_folder = app.config.get('NETWORK_FOLDER')
    sanitized_username = sanitize_username(username)
    user_folder = os.path.join(network_folder, sanitized_username)
    archive_path = os.path.join(user_folder, archive)

    if not os.path.exists(archive_path):
        logging.error(f"Архив {archive} не найден для пользователя {username}")
        return render_template("error.html", message="Архив не найден."), 404

    try:
        with zipfile.ZipFile(archive_path, 'r') as zf:
            file_list = zf.namelist()
    except zipfile.BadZipFile:
        file_list = []
        logging.error("Не удалось прочитать архив, возможно, он повреждён.")

    return render_template("archive_view.html", archive=archive, file_list=file_list, username=username)


@app.route('/uploads/<archive>/delete', methods=['POST'])
def delete_archive(archive):
    """Удаление архива и записи в БД"""
    username = request.environ.get('HTTP_X_FORWARDED_USER', 'anonymous')
    network_folder = app.config.get('NETWORK_FOLDER')
    sanitized_username = sanitize_username(username)
    user_folder = os.path.join(network_folder, sanitized_username)
    archive_path = os.path.join(user_folder, archive)

    upload_record = Upload.query.filter_by(username=username, archive_name=archive).first()

    if not upload_record:
        logging.error(f"Попытка удалить несуществующий архив {archive} у пользователя {username}")
        return jsonify({'error': 'Архив не найден в базе данных'}), 404

    if os.path.exists(archive_path):
        try:
            os.remove(archive_path)
            logging.info(f"Архив {archive} удалён с диска.")
        except Exception as e:
            logging.error(f"Ошибка при удалении архива {archive}: {e}")
            return jsonify({'error': 'Не удалось удалить архив'}), 500
    else:
        logging.warning(f"Архив {archive} отсутствует на диске, но есть в базе.")

    db.session.delete(upload_record)
    db.session.commit()
    logging.info(f"Запись о загрузке {archive} удалена из базы данных.")

    return redirect(url_for('list_uploads'))


if __name__ == "__main__":
    app.run()
