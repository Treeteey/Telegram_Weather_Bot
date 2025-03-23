#!/bin/bash

# Загружаем переменные из .env файла
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Ошибка: Файл .env не найден!"
    echo "Создайте файл .env на основе .env.example"
    exit 1
fi

# Проверяем наличие переменных окружения
if [ -z "$BOT_TOKEN" ] || [ -z "$WEATHER_API_KEY" ] || [ -z "$ALLOWED_CHAT_ID" ] || [ -z "$ALLOWED_TOPIC_ID" ]; then
    echo "Ошибка: Не все необходимые переменные установлены в файле .env"
    echo "Проверьте, что все переменные из .env.example заполнены"
    exit 1
fi

# Собираем Docker образ
docker build -t weather-bot -f docker/Dockerfile .

# Запускаем контейнер
docker run -d \
    --name weather-bot \
    --restart unless-stopped \
    -e BOT_TOKEN="$BOT_TOKEN" \
    -e WEATHER_API_KEY="$WEATHER_API_KEY" \
    -e ALLOWED_CHAT_ID="$ALLOWED_CHAT_ID" \
    -e ALLOWED_TOPIC_ID="$ALLOWED_TOPIC_ID" \
    weather-bot

echo "Бот успешно запущен в Docker-контейнере!" 