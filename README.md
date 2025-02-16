
# Upload-SRV

Upload-SRV — это веб-сервис для загрузки файлов и папок, их асинхронного архивирования с возможностью шифрования и управления готовыми архивами. Приложение реализовано с использованием Flask, Celery, PostgreSQL, Redis и контейнеризации через Docker Compose.

## Особенности

- **Загрузка файлов и папок:** Пользователь может выбрать файлы и/или папки для загрузки.
- **Асинхронное архивирование:** Файлы упаковываются в ZIP-архив с опциональным шифрованием с использованием Celery.
- **Прогресс выполнения:** Отображается прогресс загрузки файлов и создания архива.
- **Управление архивами:** Возможность просмотра содержимого архива, скачивания и удаления.
- **Контейнеризация:** Сборка и запуск всех сервисов (Flask-приложение, Celery-воркер, Redis, PostgreSQL и Apache) через Docker Compose.

## Структура проекта

```markdown
/upload-srv/
├── apache
│   ├── apache2.conf         # Конфигурация Apache-сервера
│   ├── apache_sso.keytab    # Ключ для SSO (при необходимости)
│   └── krb5.conf            # Конфигурация Kerberos
├── app
│   ├── celery_app.py        # Определение фоновых задач через Celery
│   ├── __init__.py          # Инициализация Flask-приложения и настроек
│   ├── main.py              # Основные маршруты и логика приложения
│   ├── models.py            # Определение моделей SQLAlchemy (например, Upload)
│   ├── static               # Статические файлы
│   │   ├── css
│   │   │   └── styles.css   # Общие стили для приложения
│   │   ├── js
│   │   │   ├── main.js      # Скрипты для работы интерфейса загрузки
│   │   │   └── success.js   # Скрипты для страницы успешной загрузки
│   │   └── webfonts         # Шрифты для оформления
│   ├── templates            # HTML-шаблоны
│   │   ├── archive_view.html  # Просмотр содержимого архива
│   │   ├── index.html         # Главная страница загрузки
│   │   ├── success.html       # Страница успешной загрузки
│   │   └── uploads.html       # Список загруженных архивов
│   ├── utils.py             # Утилиты для обработки имён и создания каталогов
│   └── whi
│       └── pyzipper-0.3.6-py2.py3-none-any.whl   # Локальная библиотека для работы с ZIP
├── data
│   └── redis                # Данные Redis
├── docker-compose.yml       # Конфигурация Docker Compose (web, worker, redis, postgres, apache)
├── dockerfiles
│   ├── Dockerfile.apache    # Dockerfile для сборки образа Apache
│   ├── Dockerfile.web       # Dockerfile для сборки образа веб-приложения
│   └── Dockerfile.worker    # Dockerfile для сборки образа Celery-воркера
├── init_db.sql              # Скрипт инициализации базы данных (для PostgreSQL)
├── postgres
│   ├── Dockerfile.postgres  # Dockerfile для сборки образа PostgreSQL (опционально)
│   └── init_db.sql          # Скрипт инициализации БД для контейнера postgres
├── README.md                # Этот файл
├── server.py                # Точка входа для запуска сервера с использованием Waitress
└── start.sh                 # Скрипт запуска приложения
```

## Технологии

- **Flask:** Основной веб-фреймворк для создания REST API и серверного рендеринга HTML.
- **Celery:** Асинхронное выполнение задач (архивирование файлов) в фоне.
- **Waitress:** WSGI-сервер для продакшн-развертывания Flask-приложения.
- **PostgreSQL:** Хранение метаданных загруженных архивов.
- **Redis:** Брокер сообщений для очередей задач Celery.
- **Docker & Docker Compose:** Контейнеризация приложения для простоты развертывания.

## Установка и запуск

### Предварительные требования

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Инструкции

1. **Клонирование репозитория:**

   ```bash
   git clone https://github.com/yourusername/upload-srv.git
   cd upload-srv
   ```

2. **Настройка переменных окружения:**

   Создайте файл `.env` (если требуется) и настройте следующие переменные:
   - `DATABASE_URL` (например, `postgresql://postgres:postgres@postgres:5432/mydb`)
   - `CELERY_BROKER_URL` (например, `redis://redis:6379/0`)
   - `CELERY_RESULT_BACKEND` (например, `redis://redis:6379/0`)
   - Другие переменные: `NETWORK_FOLDER`, `DOCKER_ENV`, `LOG_LEVEL` и т.д.

3. **Сборка и запуск контейнеров:**

   ```bash
   docker-compose up --build
   ```

   Эта команда соберёт и запустит все необходимые сервисы:
   - **web:** Веб-сервер с Flask-приложением.
   - **worker:** Celery-воркер для обработки задач.
   - **redis:** Брокер сообщений.
   - **postgres:** База данных.
   - **apache:** Обратный прокси/статический сервер (при необходимости).

4. **Доступ к приложению:**

   Перейдите в браузере по адресу: [http://localhost:8000/](http://localhost:8000/)  
   Здесь можно загрузить файлы, задать имя архива и пароль (опционально).

## Использование

- **Главная страница:**  
  Загрузка файлов и папок происходит через страницу [index.html](app/templates/index.html).

- **Просмотр архивов:**  
  По адресу [uploads.html](app/templates/uploads.html) можно увидеть список загруженных архивов, а также перейти к просмотру содержимого или скачиванию.

- **Просмотр содержимого архива:**  
  Шаблон [archive_view.html](app/templates/archive_view.html) позволяет отобразить список файлов внутри архива.

- **Страница успеха:**  
  После успешной загрузки отображается страница [success.html](app/templates/success.html) с ссылкой на скачивание архива.
