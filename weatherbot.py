import logging
import requests
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
ALLOWED_CHAT_ID = int(os.getenv("ALLOWED_CHAT_ID", "0"))
ALLOWED_TOPIC_ID = int(os.getenv("ALLOWED_TOPIC_ID", "0"))

if not all([BOT_TOKEN, WEATHER_API_KEY, ALLOWED_CHAT_ID, ALLOWED_TOPIC_ID]):
    raise ValueError("Не все необходимые переменные окружения установлены")

# OpenWeatherMap URLs
CURRENT_WEATHER_URL = "http://api.openweathermap.org/data/2.5/weather"
FORECAST_WEATHER_URL = "https://api.openweathermap.org/data/2.5/forecast"

# Logging setup
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)


# Function to create static buttons
async def send_static_buttons(context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("🌤 1 день", callback_data="one_day"),
         InlineKeyboardButton("⛅ 3 дня", callback_data="three_days")],
        [InlineKeyboardButton("☀ 5 дней", callback_data="five_days")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Remove previous button message
    if "buttons_message_id" in context.bot_data:
        try:
            await context.bot.delete_message(chat_id=ALLOWED_CHAT_ID, message_id=context.bot_data["buttons_message_id"])
        except:
            pass  # Ignore if message was already deleted

    # Send new button message
    message = await context.bot.send_message(
        chat_id=ALLOWED_CHAT_ID,
        message_thread_id=ALLOWED_TOPIC_ID,
        text="🔘 **Выберите прогноз:**",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

    # Store the new buttons message ID
    context.bot_data["buttons_message_id"] = message.message_id


# Function to send weather message
async def send_weather_message(context: CallbackContext, message_text: str) -> None:
    # Delete old weather message
    if "weather_message_id" in context.bot_data:
        try:
            await context.bot.delete_message(chat_id=ALLOWED_CHAT_ID, message_id=context.bot_data["weather_message_id"])
        except:
            pass  # Ignore if already deleted

    # Send new weather message
    message = await context.bot.send_message(
        chat_id=ALLOWED_CHAT_ID,
        message_thread_id=ALLOWED_TOPIC_ID,
        text=message_text
    )
    context.bot_data["weather_message_id"] = message.message_id

    # Ensure buttons are last
    await send_static_buttons(context)


# Function to fetch weather data
async def get_weather_data(context: CallbackContext, city: str, days: int) -> str:
    if days == 1:
        url = f"{CURRENT_WEATHER_URL}?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            weather_desc = data["weather"][0]["description"].capitalize()
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            wind_speed = data["wind"]["speed"]
            
            return (
                f"📍 Город: {city}\n"
                f"🌡 Температура: {temp}°C (Ощущается как {feels_like}°C)\n"
                f"💨 Ветер: {wind_speed} м/с\n"
                f"💧 Влажность: {humidity}%\n"
                f"☁️ Состояние: {weather_desc}"
            )
        else:
            return "⚠️ Город не найден."
    
    else:  # Multi-day forecast
        url = f"{FORECAST_WEATHER_URL}?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            forecasts = data["list"]
            message_text = f"📆 Прогноз погоды для {city}:\n"

            # Получаем уникальные даты (максимум 5 дней)
            dates_seen = set()
            for entry in forecasts:
                date = entry["dt_txt"].split(" ")[0]
                if date not in dates_seen and len(dates_seen) < days:
                    dates_seen.add(date)
                    temp = entry["main"]["temp"]
                    feels_like = entry["main"]["feels_like"]
                    humidity = entry["main"]["humidity"]
                    wind_speed = entry["wind"]["speed"]
                    condition = entry["weather"][0]["description"].capitalize()

                    message_text += (
                        f"\n📅 {date}:\n"
                        f"🌡 Температура: {temp}°C (Ощущается как {feels_like}°C)\n"
                        f"💨 Ветер: {wind_speed} м/с\n"
                        f"💧 Влажность: {humidity}%\n"
                        f"☁️ Состояние: {condition}\n"
                    )

            return message_text
        else:
            return "⚠️ Ошибка получения прогноза."


# Function to handle city input and clean up old messages
async def get_city(update: Update, context: CallbackContext) -> None:
    if update.message.chat.id != ALLOWED_CHAT_ID or update.message.message_thread_id != ALLOWED_TOPIC_ID:
        return  # Ignore messages outside the allowed topic

    # Delete previous user message
    if "last_user_message_id" in context.bot_data:
        try:
            await context.bot.delete_message(chat_id=ALLOWED_CHAT_ID, message_id=context.bot_data["last_user_message_id"])
        except:
            pass  # Ignore if already deleted

    # Save new user message ID
    context.bot_data["last_user_message_id"] = update.message.message_id

    city = update.message.text.strip()
    context.user_data["city"] = city

    # Fetch default 1-day weather
    weather_text = await get_weather_data(context, city, days=1)
    await send_weather_message(context, weather_text)


# Function to handle button clicks
async def button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.message.chat.id != ALLOWED_CHAT_ID or query.message.message_thread_id != ALLOWED_TOPIC_ID:
        return  # Ignore messages outside the allowed topic

    if "city" not in context.user_data:
        await context.bot.send_message(
            chat_id=ALLOWED_CHAT_ID,
            message_thread_id=ALLOWED_TOPIC_ID,
            text="❗ Сначала введите название города."
        )
        return

    city = context.user_data["city"]
    days = {
        "one_day": 1,
        "three_days": 3,
        "five_days": 5
    }.get(query.data, 1)

    weather_text = await get_weather_data(context, city, days)
    await send_weather_message(context, weather_text)


# Main function
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", send_static_buttons))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_city))

    logging.info("Бот запущен...")
    app.run_polling()


if __name__ == "__main__":
    main()
