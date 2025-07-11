from flask import Flask, request
import os
import telegram
import requests
import logging

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

# Гарантированно рабочая бесплатная модель
MODEL = "openchat/openchat-7b"  # Проверенная рабочая модель

app = Flask(__name__)

def send_message(chat_id, text):
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
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://jorik-bot.onrender.com",
                    "X-Title": "Jorik Telegram Bot"
                },
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": "Ты ассистент Жорик. Отвечай дружелюбно на русском."},
                        {"role": "user", "content": message}
                    ],
                    "max_tokens": 500
                },
                timeout=10
            )
            
            if response.status_code == 200:
                reply = response.json()["choices"][0]["message"]["content"]
                send_message(chat_id, reply)
            else:
                error_msg = response.json().get("error", {}).get("message", "Unknown error")
                logger.error(f"API error: {error_msg}")
                send_message(chat_id, "🤖 Извините, сервис временно недоступен. Попробуйте позже.")
            
        except Exception as api_error:
            logger.error(f"API request failed: {str(api_error)}")
            send_message(chat_id, "🔴 Технические неполадки. Мы уже работаем над исправлением.")
            
    except Exception as e:
        logger.error(f"System error: {str(e)}")
    
    return "ok", 200

@app.route("/")
def home():
    return "🤖 Бот Жорик работает!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)