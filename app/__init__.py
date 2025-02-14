# app/__init__.py
from flask import Flask
from pathlib import Path
import os
import redis
import logging
from flask_sqlalchemy import SQLAlchemy

# Не вызываем logging.basicConfig здесь, чтобы избежать дублирования (настройка производится в серверном модуле)
logger = logging.getLogger(__name__)

# Инициализация SQLAlchemy
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # Настройка подключения к базе данных PostgreSQL через переменную окружения DATABASE_URL
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL', 'postgresql://postgres:postgres@postgres:5432/mydb'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Инициализируем SQLAlchemy
    db.init_app(app)

    # Настройка пути для загрузок через pathlib
    network_folder = Path(os.getenv('NETWORK_FOLDER', './uploads')).resolve()
    network_folder.mkdir(parents=True, exist_ok=True)
    app.config['NETWORK_FOLDER'] = str(network_folder)
    logger.info(f"Папка для загрузок: {network_folder}")

    # Настройки Celery (используются в celery_app.py)
    app.config['CELERY_BROKER_URL'] = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
    app.config['CELERY_RESULT_BACKEND'] = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')

    logger.info(f"Используем BROKER_URL: {app.config['CELERY_BROKER_URL']}")
    logger.info(f"Используем RESULT_BACKEND: {app.config['CELERY_RESULT_BACKEND']}")

    # Проверка подключения к Redis
    try:
        r = redis.Redis.from_url(app.config['CELERY_BROKER_URL'])
        r.ping()
        logger.info("✅ Соединение с Redis установлено.")
    except redis.ConnectionError:
        logger.error("❌ Не удается подключиться к Redis. Проверьте настройки и подключение.")
        raise RuntimeError("Ошибка подключения к Redis.")

    app.config.update(
        CELERY_TASK_TRACK_STARTED=True,
        CELERY_TASK_TIME_LIMIT=7200,      # 2 часа
        CELERY_TASK_SOFT_TIME_LIMIT=3600,   # 1 час
        CELERY_RESULT_EXPIRES=86400
    )

    return app
