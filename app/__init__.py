from flask import Flask
from celery import Celery
import os
import redis
import logging

# Логирование
logging.basicConfig(level=logging.DEBUG)

def create_app():
    app = Flask(__name__)

    # Путь к папке uploads
    NETWORK_FOLDER = os.getenv('NETWORK_FOLDER', os.path.abspath('./uploads'))
    os.makedirs(NETWORK_FOLDER, exist_ok=True)
    app.config['NETWORK_FOLDER'] = NETWORK_FOLDER
    logging.info(f"Папка для загрузок: {NETWORK_FOLDER}")

    # Настройки Celery
    app.config['CELERY_BROKER_URL'] = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
    app.config['CELERY_RESULT_BACKEND'] = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
    
    logging.info(f"Используем BROKER_URL: {app.config['CELERY_BROKER_URL']}")
    logging.info(f"Используем RESULT_BACKEND: {app.config['CELERY_RESULT_BACKEND']}")

    # Проверка подключения к Redis
    try:
        r = redis.Redis.from_url(app.config['CELERY_BROKER_URL'])
        r.ping()
        logging.info("Соединение с Redis установлено.")
    except redis.ConnectionError:
        logging.error("Не удается подключиться к Redis. Проверь настройки и подключение.")
        raise RuntimeError("Ошибка подключения к Redis.")

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
