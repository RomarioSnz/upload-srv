#!/bin/bash

# ===== ПЕРЕМЕННЫЕ =====
APP_DIR="/srv/new"  # Путь к вашему приложению
ENV_FILE="$APP_DIR/.env"  # Файл переменных окружения
CELERY_SERVICE="/etc/systemd/system/celery.service"

# ===== ФУНКЦИИ =====
function install_dependencies() {
    echo "Обновление пакетов..."
    sudo apt update && sudo apt upgrade -y

    echo "Установка Python и Redis..."
    sudo apt install -y python3 python3-pip python3-venv redis-server

    echo "Установка Python-зависимостей..."
    pip install --upgrade pip
    pip install celery[redis] flask redis
}

function setup_redis() {
    echo "Настройка Redis..."
    sudo systemctl enable redis
    sudo systemctl start redis
    sudo systemctl status redis --no-pager
}

function setup_celery_service() {
    echo "Создание systemd-сервиса для Celery..."

    # Создание файла celery.service
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
ExecStart=/usr/bin/python3 -m celery -A app.main.celery worker --loglevel=info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    echo "Перезагрузка демонов systemd..."
    sudo systemctl daemon-reload

    echo "Включение автозапуска Celery..."
    sudo systemctl enable celery
    sudo systemctl start celery
    sudo systemctl status celery --no-pager
}

function check_status() {
    echo "Проверка статусов сервисов..."

    echo "Redis:"
    sudo systemctl status redis --no-pager

    echo "Celery:"
    sudo systemctl status celery --no-pager
}

function restart_services() {
    echo "Перезапуск Redis..."
    sudo systemctl restart redis
    sudo systemctl status redis --no-pager

    echo "Перезапуск Celery..."
    sudo systemctl restart celery
    sudo systemctl status celery --no-pager
}

function logs_services() {
    echo "Логи Celery:"
    journalctl -u celery.service -n 50

    echo "Логи Redis:"
    journalctl -u redis.service -n 50
}

# ===== ОСНОВНОЕ МЕНЮ =====
echo "Выберите действие:"
echo "1. Установка и настройка Celery и Redis"
echo "2. Проверка статуса сервисов"
echo "3. Перезапуск сервисов"
echo "4. Просмотр логов"
echo "5. Выход"

read -p "Введите номер действия: " ACTION

case $ACTION in
    1)
        echo "Начало установки и настройки..."
        install_dependencies
        setup_redis
        setup_celery_service
        echo "Настройка завершена!"
        ;;
    2)
        check_status
        ;;
    3)
        restart_services
        ;;
    4)
        logs_services
        ;;
    5)
        echo "Выход..."
        exit 0
        ;;
    *)
        echo "Неверный выбор! Попробуйте снова."
        ;;
esac
