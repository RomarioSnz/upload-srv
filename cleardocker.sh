#!/bin/bash

echo "Остановка всех контейнеров..."
docker stop $(docker ps -aq)

echo "Удаление всех контейнеров..."
docker rm $(docker ps -aq)

echo "Удаление всех образов..."
docker rmi -f $(docker images -aq)

echo "Удаление всех томов..."
docker volume rm $(docker volume ls -q)

echo "Удаление всех сетей, кроме default..."
docker network rm $(docker network ls | grep "bridge\|host\|none" -v | awk '{print $1}')

echo "Очистка системы Docker..."
docker system prune -af
docker builder prune -af

echo "Docker очищен!"
