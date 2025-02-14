import os
import logging
from waitress import serve
from app.main import app  # Импортируем приложение Flask

# Очистка существующих обработчиков для Python 3.7 (force=True не доступен)
root_logger = logging.getLogger()
if root_logger.hasHandlers():
    root_logger.handlers.clear()

# Настройка логирования только один раз в точке входа
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(levelname)s - %(message)s'
)

HOST = os.getenv('HOST', '0.0.0.0')  # В режиме разработки можно использовать 0.0.0.0
PORT = int(os.getenv('PORT', 8000))

# Количество потоков, используемых Waitress
THREADS = int(os.getenv("WAITRESS_THREADS", 4))

logging.info("Запуск сервера в Docker-среде с Waitress")

def run_server():
    try:
        serve(
            app,
            host=HOST,
            port=PORT,
            max_request_body_size=10 * 1024 * 1024 * 1024,  # Ограничение на размер файла: 10 ГБ
            threads=THREADS,
            expose_tracebacks=False  # В продакшене лучше не показывать трассировки ошибок
        )
    except Exception as e:
        logging.error(f"Ошибка при запуске сервера: {e}")
        raise

if __name__ == '__main__':
    run_server()
