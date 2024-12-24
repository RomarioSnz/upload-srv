from flask import Flask
from celery import Celery
import os

def create_app():
    app = Flask(__name__)

    # Путь к сетевой папке
    NETWORK_FOLDER = os.getenv('NETWORK_FOLDER', './uploads')
    os.makedirs(NETWORK_FOLDER, exist_ok=True)
    app.config['NETWORK_FOLDER'] = NETWORK_FOLDER

    # Настройки для Celery
    app.config['CELERY_BROKER_URL'] = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    app.config['CELERY_RESULT_BACKEND'] = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

    # Создаём Celery
    celery = make_celery(app)
    app.celery = celery

    return app

def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL'],
        backend=app.config['CELERY_RESULT_BACKEND']
    )
    celery.conf.update(app.config)
    return celery
