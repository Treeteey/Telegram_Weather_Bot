from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext


BOT_TOKEN = ""

async def get_topic_id(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat.id
    topic_id = update.message.message_thread_id  # This is the topic ID
    await update.message.reply_text(f"Chat ID: {chat_id}\nTopic ID: {topic_id}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_topic_id))
    app.run_polling()

if __name__ == "__main__":
    main()