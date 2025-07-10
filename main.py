import os
from flask import Flask, request
from telegram.ext import ApplicationBuilder, CommandHandler

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

# Создаём Telegram-бота
telegram_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# Обработчик команды /start
async def start(update, context):
    await update.message.reply_text("Бот работает!")

telegram_app.add_handler(CommandHandler("start", start))

# Flask-приложение для Render
flask_app = Flask(__name__)

@flask_app.route('/')
def index():
    return "Bot is running!"

@flask_app.before_first_request
def run_bot():
    telegram_app.run_polling()

# Это точка входа для Gunicorn
app = flask_app

