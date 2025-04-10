#!/bin/bash

echo "🚀 Начинаем установку Telegram Weather Bot..."

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

# Клонируем репозиторий
echo "Клонирование репозитория..."
git clone https://github.com/Treeteey/Telegram_Weather_Bot.git temp_bot
# cp -r temp_bot/* .
# rm -rf temp_bot
cd temp_bot

# Создаем .env файл из примера
if [ ! -f .env ]; then
    echo "Создание файла .env..."
    cp .env.example .env
    echo "Пожалуйста, отредактируйте файл .env и добавьте в него ваши данные"
fi

# Делаем скрипт запуска исполняемым
chmod +x docker/run.sh

echo "✅ Установка завершена!"
echo "📝 Следующие шаги:"
echo "1. Отредактируйте файл .env и добавьте в него ваши данные"
echo "2. Перезагрузите систему для применения изменений группы docker"
echo "3. После перезагрузки запустите бота командой: ./docker/run.sh" 