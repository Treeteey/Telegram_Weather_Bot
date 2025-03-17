import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, CallbackContext

# Bot configuration
BOT_TOKEN = ""
WEATHER_API_KEY = ""
ALLOWED_CHAT_ID = 0  # Your supergroup chat ID
ALLOWED_TOPIC_ID = 0  # Your Weather Bot topic ID

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
        [InlineKeyboardButton("☀ 1 неделя", callback_data="one_week")]
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


# Function to fetch weather data
async def send_weather(update: Update, context: CallbackContext, city: str, days: int) -> None:
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
            
            message_text = (
                f"📍 Город: {city}\n"
                f"🌡 Температура: {temp}°C (Ощущается как {feels_like}°C)\n"
                f"💨 Ветер: {wind_speed} м/с\n"
                f"💧 Влажность: {humidity}%\n"
                f"☁️ Состояние: {weather_desc}"
            )
        else:
            message_text = "⚠️ Город не найден."
    
    else:  # Multi-day forecast
        url = f"{FORECAST_WEATHER_URL}?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            forecasts = data["list"]
            message_text = f"📆 Прогноз погоды для {city}:\n"

            for i in range(0, days * 8, 8):  # 8 timestamps per day
                entry = forecasts[i]
                date = entry["dt_txt"].split(" ")[0]
                temp = entry["main"]["temp"]
                condition = entry["weather"][0]["description"].capitalize()

                message_text += f"\n📅 {date}: {temp}°C, {condition}"
        else:
            message_text = "⚠️ Ошибка получения прогноза."

    # Delete old weather message
    if "weather_message_id" in context.bot_data:
        try:
            await context.bot.delete_message(chat_id=ALLOWED_CHAT_ID, message_id=context.bot_data["weather_message_id"])
        except:
            pass  # Ignore if already deleted

    # Send new weather message
    message = await update.message.reply_text(message_text)
    context.bot_data["weather_message_id"] = message.message_id

    # Ensure buttons are last
    await send_static_buttons(context)


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
    await send_weather(update, context, city, days=1)


# Function to handle button clicks
async def button_click(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    if query.message.chat.id != ALLOWED_CHAT_ID or query.message.message_thread_id != ALLOWED_TOPIC_ID:
        return  # Ignore messages outside the allowed topic

    if "city" not in context.user_data:
        await query.message.reply_text("❗ Сначала введите название города.")
        return

    city = context.user_data["city"]

    if query.data == "one_day":
        await send_weather(update, context, city, days=1)
    elif query.data == "three_days":
        await send_weather(update, context, city, days=3)
    elif query.data == "one_week":
        await send_weather(update, context, city, days=7)


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
