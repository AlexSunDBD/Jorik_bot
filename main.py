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

# 100% бесплатная модель (проверено)
MODEL = "huggingface/huggingfaceh4-zephyr-7b-beta"

app = Flask(__name__)

def send_message(chat_id, text):
    try:
        # Явный синхронный вызов
        bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode='Markdown',
            disable_web_page_preview=True
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
                    "X-Title": "Jorik Bot (Telegram)"
                },
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": "Ты ассистент Жорик. Отвечай кратко на русском."},
                        {"role": "user", "content": message}
                    ],
                    "max_tokens": 400,
                    "temperature": 0.7
                },
                timeout=15
            )
            
            if response.status_code == 200:
                reply = response.json()["choices"][0]["message"]["content"]
                send_message(chat_id, reply)
            else:
                error_data = response.json().get("error", {})
                logger.error(f"API error: {error_data}")
                
                if response.status_code == 402:
                    send_message(chat_id, "🔴 Используйте команду /free для бесплатного режима")
                else:
                    send_message(chat_id, "⚠️ Технические проблемы. Попробуйте позже.")
            
        except Exception as api_error:
            logger.error(f"Request failed: {str(api_error)}")
            send_message(chat_id, "⏳ Сервис временно недоступен")
            
    except Exception as e:
        logger.error(f"System error: {str(e)}")
    
    return "ok", 200

@app.route("/free", methods=["POST"])
def free_endpoint():
    """Резервный endpoint для бесплатных запросов"""
    return "В разработке", 200

@app.route("/")
def home():
    return "🤖 Бот Жорик в строю", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)