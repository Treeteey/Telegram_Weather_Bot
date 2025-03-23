# Telegram_Weather_Bot
Bot that fetches data from openweather.com using its API for personal/specific channel.

1. Go to **@BotFather** in telegram
2. Input `/newbot`. Create bots name.
3. Save the bot's token
4. Sign in to `https://openweathermap.org/api` and create API key. Save it.
5. Create group in Telegram. Go to group settings -> Manage group -> Enable "Topics"
   
   ![](images/image_0.png)

   ![](images/image_1.png)

6. Create new topic and invite **YOUR** bot.

    ![](images/image_2.png)

    ![](images/image_3.png)

7. Make bot as administrator of that group

    ![](images/image_4.png)

8. Get group and topic ID. (as a homework find it yourself)
9. To make bot **"private"** you need to insert those IDs in `weatherbot.py` script at `ALLOWED_CHAT_ID` and `ALLOWED_TOPIC_ID`. That way **only your** topic can work with that bot. Insert `BOT_TOKEN` and `WEATHER_API_KEY`  also.
10. Install modules `pip install -r requirements.txt`
11. Launch bot `py weatherbot.py`. In your topic input city name.

    ![](images/image_5.png)

## Запуск в Docker

1. Убедитесь, что у вас установлен Docker и Docker Compose
2. Скопируйте файл с примером переменных окружения:
   ```bash
   cp .env.example .env
   ```
3. Отредактируйте файл `.env`, вставив в него ваши данные:
   - `BOT_TOKEN` - токен вашего бота
   - `WEATHER_API_KEY` - ключ API OpenWeatherMap
   - `ALLOWED_CHAT_ID` - ID вашей группы
   - `ALLOWED_TOPIC_ID` - ID темы в группе
4. Сделайте скрипт запуска исполняемым:
   ```bash
   chmod +x docker/run.sh
   ```
5. Запустите бота:
   ```bash
   ./docker/run.sh
   ```

Бот будет запущен в Docker-контейнере и автоматически перезапустится при перезагрузке сервера.

Для остановки бота используйте:
```bash
docker stop weather-bot
```

Для просмотра логов:
```bash
docker logs weather-bot
```

## Быстрая установка

Для автоматической установки бота и всех зависимостей выполните следующие команды:

```bash
# Скачиваем скрипт установки
curl -O https://raw.githubusercontent.com/Treeteey/Telegram_Weather_Bot/main/setup.sh

# Делаем скрипт исполняемым
chmod +x setup.sh

# Запускаем установку
./setup.sh
```

Скрипт автоматически:
1. Установит Git (если не установлен)
2. Установит Docker (если не установлен)
3. Скачает все файлы бота
4. Создаст файл .env из примера
5. Настроит необходимые права доступа

После установки следуйте инструкциям, которые появятся на экране.
