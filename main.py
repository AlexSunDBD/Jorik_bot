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

# Заголовки для OpenRouter
headers = {
    "HTTP-Referer": "https://jorik-bot.onrender.com",
    "X-Title": "Jorik Telegram Bot"
}

# Клиент OpenRouter с headers
client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
    default_headers=headers
)

# Выбранная модель (бесплатная)
MODEL = "gryphe/mythomax-l2-13b"  # Изменено на mythomax

app = Flask(__name__)

def sync_send_message(chat_id, text):
    try:
        bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Telegram send error: {e}")

def check_credits():
    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/auth/key",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
            timeout=5
        )
        return response.json().get("data", {}).get("credits", 0)
    except Exception as e:
        logger.error(f"Credit check failed: {e}")
        return 0

@app.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
    try:
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        
        if not update.message or not update.message.text:
            return "ok", 200
            
        message = update.message.text
        chat_id = update.message.chat.id
        logger.info(f"New message from {chat_id}: {message[:50]}...")

        credits = check_credits()
        if credits < 1:
            sync_send_message(chat_id, "⚠️ Проверка кредитов не удалась. Попробуйте позже.")
            return "ok", 200

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "Ты ассистент Жорик. Отвечай дружелюбно и кратко."},
                    {"role": "user", "content": message}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            reply = response.choices[0].message.content
            sync_send_message(chat_id, reply)
            
        except Exception as api_error:
            error_msg = str(api_error)
            logger.error(f"API error: {error_msg}")
            
            if "402" in error_msg:
                sync_send_message(chat_id, "🔴 Ошибка доступа к модели\nПопробуйте позже")
            elif "model" in error_msg.lower():
                sync_send_message(chat_id, f"⚠️ Проблема с моделью {MODEL}")
            else:
                sync_send_message(chat_id, "⚠️ Временная ошибка API")

    except Exception as e:
        logger.error(f"System error: {str(e)}")
    
    return "ok", 200

@app.route("/")
def home():
    return "🤖 Бот Жорик работает! 🚀", 200

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        debug=False
    )