from app.main import app  # Импортируем приложение из main.py
from waitress import serve
import os
import logging

logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    # Проверяем режим запуска: Docker или локально
    if os.getenv('DOCKER_ENV'):  # Переменная окружения для Docker
        # Запускаем сервер Waitress для Docker
        serve(app, host='0.0.0.0', port=8000)
    else:
        # Запускаем локальный отладочный сервер Flask
        app.run(debug=True, host='0.0.0.0', port=8000)
