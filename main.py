import os
import asyncio
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

# Получаем токен из переменной окружения
TOKEN = os.environ.get("TELEGRAM_TOKEN")
bot = Bot(token=TOKEN)

# Инициализация Flask и Telegram Application
app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

# Пример команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я бот, всё работает!")

# Регистрируем обработчики
application.add_handler(CommandHandler("start", start))

# Webhook endpoint
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, bot)

    async def process():
        await application.initialize()
        await application.process_update(update)

    asyncio.run(process())
    return "ok"

# Тестовая заглушка
@app.route("/", methods=["GET"])
def home():
    return "Бот работает!"

if __name__ == "__main__":
    app.run(debug=True)

