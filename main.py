import os
import logging
from flask import Flask, request
from telegram import Bot, Update
from telegram.ext import Dispatcher, MessageHandler, Filters
from telegram.ext import CallbackContext
import openai
import asyncio

# Логирование для отладки
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация Flask
app = Flask(__name__)

# Инициализация Telegram бота
TOKEN = os.environ.get("TELEGRAM_TOKEN")
bot = Bot(token=TOKEN)

# Инициализация OpenAI (OpenRouter)
client = openai.OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# Функция обработки сообщений Telegram
def handle_message(update: Update, context: CallbackContext):
    user_message = update.message.text
    chat_id = update.message.chat.id
    logger.info(f"Получено сообщение от {chat_id}: {user_message}")

    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o",
            messages=[{"role": "user", "content": user_message}]
        )
        reply_text = response.choices[0].message.content
    except Exception as e:
        logger.error(f"Ошибка OpenAI: {e}")
        reply_text = "Извините, произошла ошибка при обработке вашего запроса."

    # Отправляем ответ пользователю
    bot.send_message(chat_id=chat_id, text=reply_text)

# Инициализация диспетчера для webhook
dispatcher = Dispatcher(bot, None, workers=0)
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

# Flask route для приема webhook от Telegram
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok"

# Просто корень сайта
@app.route("/")
def index():
    return "Бот работает!"

if __name__ == "__main__":
    app.run(debug=True)

