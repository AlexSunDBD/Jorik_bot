from flask import Flask, request
import os
import telegram
import asyncio
from openai import OpenAI

# Настройки
TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
BOT = telegram.Bot(token=TOKEN)

# Клиент OpenRouter с новой версией API
client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

app = Flask(__name__)

async def send_async_message(chat_id, text):
    try:
        await BOT.send_message(chat_id=chat_id, text=text)
    except Exception as e:
        print(f"Telegram send error: {e}")

@app.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
    try:
        update = telegram.Update.de_json(request.get_json(force=True), BOT)
        message = update.message.text

        # Проверка API ключа
        if not OPENROUTER_API_KEY:
            asyncio.run(send_async_message(update.message.chat.id, "Ошибка: Не настроен API-ключ OpenRouter"))
            return "ok"

        # Запрос к OpenRouter с новым синтаксисом
        response = client.chat.completions.create(
            model="openai/gpt-4",  # Можно изменить на другую модель
            messages=[{"role": "user", "content": message}]
        )
        
        reply = response.choices[0].message.content
        asyncio.run(send_async_message(update.message.chat.id, reply))
            
    except Exception as e:
        error_msg = f"System error: {str(e)}"
        print(error_msg)
        asyncio.run(send_async_message(update.message.chat.id, "Техническая ошибка. Разработчик уже уведомлен"))
    
    return "ok"

@app.route("/")
def index():
    return "Bot is running"

if __name__ == "__main__":
    app.run(debug=True)