import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")

# Создаём Flask-приложение
app = Flask(__name__)

# Создаём Telegram Application
application = ApplicationBuilder().token(TOKEN).build()

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Бот работает!")

application.add_handler(CommandHandler("start", start))

# Важно: асинхронно инициализируем Telegram-приложение
@app.before_first_request
def init_bot():
    asyncio.get_event_loop().run_until_complete(application.initialize())
    print("✅ Telegram Application initialized")

# Webhook endpoint
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    asyncio.get_event_loop().run_until_complete(application.process_update(update))
    return "ok"

# Gunicorn будет искать переменную с названием `app`
if __name__ == "__main__":
    app.run(debug=True)

