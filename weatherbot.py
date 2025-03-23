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

# Погодные эмодзи
WEATHER_EMOJI = {
    "01d": "☀️",  # ясно
    "01n": "🌙",  # ясно ночью
    "02d": "⛅",  # малооблачно
    "02n": "☁️",  # малооблачно ночью
    "03d": "☁️",  # облачно
    "03n": "☁️",  # облачно ночью
    "04d": "☁️",  # пасмурно
    "04n": "☁️",  # пасмурно ночью
    "09d": "🌧",  # дождь
    "09n": "🌧",  # дождь ночью
    "10d": "🌦",  # дождь с прояснениями
    "10n": "🌧",  # дождь ночью
    "11d": "⛈",  # гроза
    "11n": "⛈",  # гроза ночью
    "13d": "🌨",  # снег
    "13n": "🌨",  # снег ночью
    "50d": "🌫",  # туман
    "50n": "🌫",  # туман ночью
}

# Logging setup
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

async def send_static_buttons(context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("🌤 1 день", callback_data="one_day"),
         InlineKeyboardButton("⛅ 3 дня", callback_data="three_days")],
        [InlineKeyboardButton("☀ 5 дней", callback_data="five_days")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if "buttons_message_id" in context.bot_data:
        try:
            await context.bot.delete_message(chat_id=ALLOWED_CHAT_ID, message_id=context.bot_data["buttons_message_id"])
        except: pass

    message = await context.bot.send_message(
        chat_id=ALLOWED_CHAT_ID,
        message_thread_id=ALLOWED_TOPIC_ID,
        text="🔘 Выберите прогноз:",
        reply_markup=reply_markup
    )
    context.bot_data["buttons_message_id"] = message.message_id

# Function to format temperature table for single day
def format_hourly_table(forecasts, date):
    # Преобразуем дату в формат дд-мм-гггг
    date_parts = date.split("-")
    formatted_date = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"
    
    rows = []
    rows.append(f"📅 {formatted_date}\n")
    
    for entry in forecasts:
        if entry["dt_txt"].split(" ")[0] == date:
            hour = entry["dt_txt"].split(" ")[1][:5]
            temp = entry["main"]["temp"]
            wind = entry["wind"]["speed"]
            icon = entry["weather"][0]["icon"]
            emoji = WEATHER_EMOJI.get(icon, "❓")
            desc = entry["weather"][0]["description"].capitalize()
            
            row = f"{hour} - {temp:>2.0f}°C, {wind:.1f} м/с, {emoji} {desc}\n"
            rows.append(row)
    
    return "".join(rows)

# Function to format multi-day temperature table
def format_multiday_table(forecasts, days):
    dates = []
    hours_data = {}
    
    for entry in forecasts:
        date = entry["dt_txt"].split(" ")[0]
        hour = int(entry["dt_txt"].split(" ")[1][:2])
        
        if date not in dates and len(dates) < days:
            dates.append(date)
        
        if len(dates) <= days:
            if hour not in hours_data:
                hours_data[hour] = {}
            hours_data[hour][date] = entry

    if not dates:
        return "Нет данных для отображения"

    rows = []
    
    for date in dates:
        # Преобразуем дату в формат дд-мм-гггг
        date_parts = date.split("-")
        formatted_date = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"
        
        rows.append(f"\n📅 {formatted_date}\n")
        for hour in sorted(hours_data.keys()):
            if date in hours_data[hour]:
                entry = hours_data[hour][date]
                temp = entry["main"]["temp"]
                wind = entry["wind"]["speed"]
                icon = entry["weather"][0]["icon"]
                emoji = WEATHER_EMOJI.get(icon, "❓")
                desc = entry["weather"][0]["description"].capitalize()
                row = f"{hour:02d}:00 - {temp:>2.0f}°C, {wind:.1f} м/с, {emoji} {desc}\n"
                rows.append(row)
    
    return "".join(rows)

async def send_weather_message(context: CallbackContext, message_text: str) -> None:
    if "weather_message_id" in context.bot_data:
        try:
            await context.bot.delete_message(chat_id=ALLOWED_CHAT_ID, message_id=context.bot_data["weather_message_id"])
        except: pass

    message = await context.bot.send_message(
        chat_id=ALLOWED_CHAT_ID,
        message_thread_id=ALLOWED_TOPIC_ID,
        text=message_text
    )
    context.bot_data["weather_message_id"] = message.message_id
    await send_static_buttons(context)

async def get_weather_data(context: CallbackContext, city: str, days: int) -> str:
    if days == 1:
        current_url = f"{CURRENT_WEATHER_URL}?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
        forecast_url = f"{FORECAST_WEATHER_URL}?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
        
        current_response = requests.get(current_url)
        forecast_response = requests.get(forecast_url)
        
        if current_response.status_code == 200 and forecast_response.status_code == 200:
            current_data = current_response.json()
            forecast_data = forecast_response.json()
            
            weather_desc = current_data["weather"][0]["description"].capitalize()
            temp = current_data["main"]["temp"]
            feels_like = current_data["main"]["feels_like"]
            humidity = current_data["main"]["humidity"]
            wind_speed = current_data["wind"]["speed"]
            
            header = (
                f"📍 Город: {city}\n"
                f"🌡 Сейчас: {temp}°C (Ощущается как {feels_like}°C)\n"
                f"💨 Ветер: {wind_speed} м/с\n"
                f"💧 Влажность: {humidity}%\n"
                f"☁️ Состояние: {weather_desc}\n\n"
                "Прогноз на сегодня:\n"
            )
            
            today = forecast_data["list"][0]["dt_txt"].split(" ")[0]
            return header + format_hourly_table(forecast_data["list"], today)
        else:
            return "⚠️ Город не найден."
    
    else:  # Multi-day forecast
        url = f"{FORECAST_WEATHER_URL}?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            header = f"📆 Прогноз погоды для {city}:\n\n"
            return header + format_multiday_table(data["list"], days)
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
