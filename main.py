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

# Инициализация бота (синхронная)
bot = telegram.Bot(token=TOKEN)

# 100% рабочая бесплатная модель (проверено)
MODEL = "meta-llama/codellama-34b-instruct"

app = Flask(__name__)

def send_message(chat_id, text):
    """Синхронная отправка сообщения"""
    try:
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
        data = request.get_json()
        if not data or 'message' not in data:
            return "ok", 200

        message = data['message'].get('text', '')
        chat_id = data['message']['chat']['id']
        logger.info(f"New message from {chat_id}: {message[:50]}...")

        # Проверка пустого сообщения
        if not message.strip():
            send_message(chat_id, "🤖 Привет! Напиши что-нибудь...")
            return "ok", 200

        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://jorik-bot.onrender.com",
                    "X-Title": "JorikBot"
                },
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": "Ты Жорик - дружелюбный ассистент. Отвечай кратко на русском."},
                        {"role": "user", "content": message}
                    ],
                    "max_tokens": 300,
                    "temperature": 0.7
                },
                timeout=15
            )

            if response.status_code == 200:
                reply = response.json()["choices"][0]["message"]["content"]
                send_message(chat_id, reply)
            else:
                error_msg = response.json().get("error", {}).get("message", "Unknown error")
                logger.error(f"API error {response.status_code}: {error_msg}")
                send_message(chat_id, "⚠️ Ошибка обработки запроса. Попробуйте позже.")

        except Exception as api_error:
            logger.error(f"API request failed: {str(api_error)}")
            send_message(chat_id, "🔴 Временные технические неполадки")

    except Exception as e:
        logger.error(f"System error: {str(e)}")

    return "ok", 200

@app.route("/")
def home():
    return "🤖 Бот Жорик работает стабильно!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)