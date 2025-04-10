#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Telegram Weather Bot - Установка ===${NC}"

# Проверяем наличие git
if ! command -v git &> /dev/null; then
    echo "📦 Установка Git..."
    if [ -f /etc/debian_version ]; then
        sudo apt-get update
        sudo apt-get install -y git
    elif [ -f /etc/redhat-release ]; then
        sudo yum install -y git
    else
        echo "❌ Не удалось определить тип системы для установки Git"
        exit 1
    fi
fi

# Проверяем наличие Docker
if ! command -v docker &> /dev/null; then
    echo "📦 Установка Docker..."
    if [ -f /etc/debian_version ]; then
        # Установка Docker для Debian/Ubuntu
        sudo apt-get update
        sudo apt-get install -y ca-certificates curl gnupg
        sudo install -m 0755 -d /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
        sudo chmod a+r /etc/apt/keyrings/docker.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    elif [ -f /etc/redhat-release ]; then
        # Установка Docker для RHEL/CentOS
        sudo yum install -y yum-utils
        sudo yum-config-manager --add-repo https://download.docker.com/linux/rhel/docker-ce.repo
        sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    else
        echo "Не удалось определить тип системы для установки Docker"
        exit 1
    fi
    
    # Добавляем текущего пользователя в группу docker
    sudo usermod -aG docker $USER
    echo "⚠️ Для применения изменений группы docker, пожалуйста, перезагрузите систему"
fi

# Проверяем, находимся ли мы уже в директории проекта
if [ ! -f "weatherbot.py" ]; then
    # Если мы не в директории проекта, клонируем репозиторий
    echo "Клонирование репозитория..."
    git clone https://github.com/Treeteey/Telegram_Weather_Bot.git temp_bot
    
    # Копируем файлы из temp_bot в текущую директорию
    echo "Копирование файлов..."
    cp -r temp_bot/* .
    
    # Делаем скрипт setup.sh исполняемым
    chmod +x setup.sh
    
    # Удаляем временную директорию
    rm -rf temp_bot
else
    echo "Вы уже находитесь в директории проекта."
fi

# Создаем .env файл из примера
if [ ! -f .env ]; then
    echo -e "${RED}Ошибка: Файл .env не найден!${NC}"
    echo -e "${YELLOW}Создайте файл .env со следующими переменными:${NC}"
    echo -e "BOT_TOKEN=your_telegram_bot_token"
    echo -e "WEATHER_API_KEY=your_openweathermap_api_key"
    echo -e "ALLOWED_CHAT_ID=your_telegram_chat_id"
    echo -e "ALLOWED_TOPIC_ID=your_telegram_topic_id"
    echo
    exit 1
fi

# Проверка наличия необходимых переменных в .env
echo -e "${GREEN}Проверка переменных окружения...${NC}"

# Функция для проверки наличия переменной в .env
check_env_var() {
    if ! grep -q "^$1=" .env; then
        echo -e "${RED}Ошибка: Переменная $1 не найдена в файле .env${NC}"
        return 1
    fi
    return 0
}

# Проверяем наличие всех необходимых переменных
missing_vars=0
check_env_var "BOT_TOKEN" || missing_vars=1
check_env_var "WEATHER_API_KEY" || missing_vars=1
check_env_var "ALLOWED_CHAT_ID" || missing_vars=1
check_env_var "ALLOWED_TOPIC_ID" || missing_vars=1

if [ $missing_vars -eq 1 ]; then
    echo -e "${RED}Пожалуйста, добавьте все необходимые переменные в файл .env и запустите скрипт снова.${NC}"
    exit 1
fi

# Проверка наличия docker/run.sh
if [ ! -f docker/run.sh ]; then
    echo -e "${RED}Ошибка: Файл docker/run.sh не найден!${NC}"
    echo -e "${YELLOW}Убедитесь, что вы находитесь в корневой директории проекта.${NC}"
    exit 1
fi

# Делаем скрипт запуска исполняемым
chmod +x docker/run.sh

# Запускаем бота
echo -e "${GREEN}Запуск бота...${NC}"
./docker/run.sh

echo -e "${GREEN}Установка завершена!${NC}"
echo -e "${YELLOW}Бот запущен в фоновом режиме.${NC}"
echo -e "${YELLOW}Для остановки бота используйте: docker stop weather-bot${NC}"
echo -e "${YELLOW}Для просмотра логов используйте: docker logs weather-bot${NC}" 