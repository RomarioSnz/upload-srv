#!/bin/bash

# ===== ПЕРЕМЕННЫЕ =====
APP_DIR="/srv/file"  # Путь к папке проекта
ENV_FILE="$APP_DIR/.env"  # Файл переменных окружения
LOG_DIR="$APP_DIR/logs"  # Каталог для логов
LOG_FILE="$LOG_DIR/install.log"  # Файл логов
CELERY_SERVICE="/etc/systemd/system/celery.service"
PYTHON_VERSION="python3.10"  # Версия Python для Ubuntu 22.04
VENV_DIR="$APP_DIR/venv"  # Виртуальное окружение

# ===== ФУНКЦИИ =====

log() {
    mkdir -p $LOG_DIR  # Создаём папку логов, если её нет
    touch $LOG_FILE  # Создаём файл логов
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a $LOG_FILE
}

# === 1. Удаление всех компонентов ===
cleanup_system() {
    log "Удаление всех компонентов и зависимостей..."

    # Остановка и удаление сервисов Celery и Redis
    sudo systemctl stop celery
    sudo systemctl disable celery
    sudo rm -f $CELERY_SERVICE
    sudo systemctl daemon-reload

    sudo systemctl stop redis
    sudo systemctl disable redis
    sudo apt purge --auto-remove redis-server -y

    # Удаление Python и зависимостей
    sudo apt purge --auto-remove $PYTHON_VERSION python3-pip python3-venv -y
    sudo apt autoremove -y
    sudo apt autoclean

    # Удаление виртуального окружения и данных
    rm -rf $VENV_DIR
    rm -rf $APP_DIR/uploads
    rm -rf $LOG_DIR
    rm -rf $APP_DIR/__pycache__

    log "Система очищена."
}

# === 2. Установка зависимостей ===
install_dependencies() {
    log "Обновление системы..."
    sudo apt update && sudo apt upgrade -y

    log "Установка Python, Redis и других зависимостей..."
    sudo apt install -y $PYTHON_VERSION $PYTHON_VERSION-venv python3-pip redis-server git curl wget gcc build-essential libssl-dev libffi-dev python3-dev

    log "Создание виртуального окружения..."
    $PYTHON_VERSION -m venv $VENV_DIR
    source $VENV_DIR/bin/activate

    log "Установка Python-зависимостей..."
    pip install --upgrade pip
    pip install flask redis celery waitress  # Включает waitress
    pip install -r $APP_DIR/docker/requirements.txt  # Установка из requirements.txt
}

# === 3. Настройка Redis ===
setup_redis() {
    log "Настройка Redis..."
    sudo systemctl enable redis
    sudo systemctl start redis
    sudo systemctl status redis --no-pager
}

# === 4. Настройка Celery ===
setup_celery_service() {
    log "Создание systemd-сервиса для Celery..."

    sudo tee $CELERY_SERVICE > /dev/null <<EOF
[Unit]
Description=Celery Worker Service
After=network.target
Requires=redis.service

[Service]
User=root
Group=root
WorkingDirectory=$APP_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$VENV_DIR/bin/python3 -m celery -A app.main.celery worker --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    log "Перезагрузка systemd..."
    sudo systemctl daemon-reload
    sudo systemctl enable celery
    sudo systemctl start celery
    sudo systemctl status celery --no-pager
}

# === 5. Создание переменных окружения ===
setup_env_file() {
    if [ ! -f "$ENV_FILE" ]; then
        log "Создание .env файла..."
        cat <<EOF > $ENV_FILE
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
NETWORK_FOLDER=$APP_DIR/uploads
EOF
    fi
}

# === 6. Проверка статусов сервисов ===
check_status() {
    log "Проверка статуса Redis..."
    sudo systemctl status redis --no-pager

    log "Проверка статуса Celery..."
    sudo systemctl status celery --no-pager
}

# === 7. Перезапуск сервисов ===
restart_services() {
    log "Перезапуск Redis..."
    sudo systemctl restart redis

    log "Перезапуск Celery..."
    sudo systemctl restart celery
}

# === 8. Просмотр логов сервисов ===
logs_services() {
    log "Логи Celery:"
    journalctl -u celery.service -n 50

    log "Логи Redis:"
    journalctl -u redis.service -n 50
}

# === 9. Запуск приложения ===
start_app() {
    log "Запуск приложения..."
    cd $APP_DIR
    source $VENV_DIR/bin/activate  # Автоматическая активация окружения
    python3 server.py
}

# === МЕНЮ ===
log "===== Начало установки и настройки сервера ====="
echo "Выберите действие:"
echo "1. Полная установка и настройка сервера"
echo "2. Очистка системы и удаление всех зависимостей"
echo "3. Проверка статуса сервисов"
echo "4. Перезапуск сервисов"
echo "5. Просмотр логов"
echo "6. Запуск приложения"
echo "7. Выход"

read -p "Введите номер действия: " ACTION

case $ACTION in
    1)
        log "Начинается полная установка и настройка..."
        install_dependencies
        setup_redis
        setup_env_file
        setup_celery_service
        log "Установка завершена!"
        ;;
    2)
        log "Очистка системы..."
        cleanup_system
        ;;
    3)
        check_status
        ;;
    4)
        restart_services
        ;;
    5)
        logs_services
        ;;
    6)
        start_app
        ;;
    7)
        log "Выход..."
        exit 0
        ;;
    *)
        log "Неверный выбор! Попробуйте снова."
        ;;
esac
