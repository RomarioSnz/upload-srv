from app.main import app  # Импортируем приложение из main.py
from waitress import serve
import os
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,  # Уровень логирования
    format='%(asctime)s - %(levelname)s - %(message)s'  # Формат вывода
)

# Определяем параметры запуска
HOST = os.getenv('HOST', '0.0.0.0')  # По умолчанию слушает на всех интерфейсах
PORT = int(os.getenv('PORT', 8000))  # По умолчанию порт 8000

if __name__ == '__main__':
    if os.getenv('DOCKER_ENV'):  # Если запускается в Docker
        logging.info("Запуск в Docker-среде с Waitress")
        serve(app, host=HOST, port=PORT)
    else:  # Локальный режим (для разработки)
        logging.info("Запуск в локальной среде в отладочном режиме")
        app.run(debug=True, host=HOST, port=PORT)
