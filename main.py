from flask import Flask, request
import os
import telegram
import asyncio
from openai import OpenAI
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройки
TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
BOT = telegram.Bot(token=TOKEN)

# Клиент OpenRouter
client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

app = Flask(__name__)

async def send_async_message(chat_id, text):
    try:
        await BOT.send_message(chat_id=chat_id, text=text)
    except Exception as e:
        logger.error(f"Telegram send error: {e}")

@app.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
    try:
        update = telegram.Update.de_json(request.get_json(force=True), BOT)
        message = update.message.text
        chat_id = update.message.chat.id

        # Проверка API ключа
        if not OPENROUTER_API_KEY:
            asyncio.run(send_async_message(chat_id, "❌ Ошибка: Не настроен API-ключ OpenRouter"))
            return "ok"

        # Запрос к OpenRouter
        try:
            response = client.chat.completions.create(
                model="deepseek/deepseek-v3",  # Правильное имя модели
                messages=[{"role": "user", "content": message}],
                max_tokens=2000  # Ограничение длины ответа
            )
            reply = response.choices[0].message.content
            asyncio.run(send_async_message(chat_id, reply))
            
        except Exception as api_error:
            error_msg = f"API error: {str(api_error)}"
            logger.error(error_msg)
            
            if "402" in str(api_error):
                msg = "❌ Закончились кредиты на OpenRouter. Пополните баланс: https://openrouter.ai/settings/credits"
            elif "404" in str(api_error):
                msg = "❌ Модель не найдена. Проверьте название модели."
            else:
                msg = f"❌ Ошибка API: {str(api_error)}"
            
            asyncio.run(send_async_message(chat_id, msg))
            
    except Exception as e:
        error_msg = f"System error: {str(e)}"
        logger.error(error_msg)
        asyncio.run(send_async_message(chat_id, "❌ Техническая ошибка. Разработчик уже уведомлен"))
    
    return "ok"

@app.route("/")
def index():
    return "Bot is running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)