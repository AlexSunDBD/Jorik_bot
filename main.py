from flask import Flask, request
import os
import telegram
from openai import OpenAI
import logging
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Настройки
TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
bot = telegram.Bot(token=TOKEN)

# Полностью бесплатная модель (проверенная)
MODEL = "mistralai/mistral-7b-instruct"

app = Flask(__name__)

def sync_send_message(chat_id, text):
    try:
        bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Telegram send error: {e}")

@app.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
    try:
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        
        if not update.message or not update.message.text:
            return "ok", 200
            
        message = update.message.text
        chat_id = update.message.chat.id
        logger.info(f"New message from {chat_id}: {message[:50]}...")

        try:
            # Используем прямой HTTP-запрос как временное решение
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://jorik-bot.onrender.com",
                    "X-Title": "Jorik Bot"
                },
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": "Ты ассистент Жорик. Отвечай кратко."},
                        {"role": "user", "content": message}
                    ],
                    "max_tokens": 500
                },
                timeout=10
            )
            
            if response.status_code == 200:
                reply = response.json()["choices"][0]["message"]["content"]
                sync_send_message(chat_id, reply)
            else:
                error_msg = response.json().get("error", {}).get("message", "Unknown error")
                logger.error(f"API error: {error_msg}")
                sync_send_message(chat_id, "⚠️ Ошибка сервера. Попробуйте позже.")
            
        except Exception as api_error:
            logger.error(f"API request failed: {str(api_error)}")
            sync_send_message(chat_id, "🔴 Временные технические проблемы")
            
    except Exception as e:
        logger.error(f"System error: {str(e)}")
    
    return "ok", 200

@app.route("/")
def home():
    return "🤖 Бот работает", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)