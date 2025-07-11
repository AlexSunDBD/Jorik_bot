from flask import Flask, request
import os
import telegram
from openai import OpenAI
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
BOT = telegram.Bot(token=TOKEN)

# Клиент OpenRouter
client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Правильное имя модели DeepSeek в OpenRouter
DEEPSEEK_MODEL = "deepseek/deepseek-v3"  # Рабочая модель DeepSeek

app = Flask(__name__)

def sync_send_message(chat_id, text):
    try:
        BOT.send_message(
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
        update = telegram.Update.de_json(request.get_json(force=True), BOT)
        
        if not update.message or not update.message.text:
            logger.warning("Empty message received")
            return "ok", 200
            
        message = update.message.text
        chat_id = update.message.chat.id
        logger.info(f"Received message from {chat_id}: {message[:50]}...")

        if not OPENROUTER_API_KEY:
            logger.error("OpenRouter API key not configured")
            sync_send_message(
                chat_id, 
                "❌ Ошибка: Не настроен API-ключ OpenRouter"
            )
            return "ok", 200

        try:
            logger.info(f"Sending request to {DEEPSEEK_MODEL}: {message[:50]}...")
            
            response = client.chat.completions.create(
                model=DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": "Ты полезный ассистент Жорик. Отвечай дружелюбно и кратко."},
                    {"role": "user", "content": message}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            reply = response.choices[0].message.content
            logger.info(f"Received response: {reply[:50]}...")
            
            sync_send_message(chat_id, reply)
            
        except Exception as api_error:
            error_msg = f"API error: {str(api_error)}"
            logger.error(error_msg)
            
            if "402" in str(api_error):
                msg = "❌ Закончились кредиты\nПополните: [OpenRouter Credits](https://openrouter.ai/settings/credits)"
            elif "model" in str(api_error).lower():
                msg = "❌ Проблема с моделью\nИспользуется: " + DEEPSEEK_MODEL
            else:
                msg = "❌ Ошибка API\nПопробуйте позже"
            
            sync_send_message(chat_id, msg)
            
    except Exception as e:
        error_msg = f"System error: {str(e)}"
        logger.error(error_msg)
        sync_send_message(
            chat_id,
            "❌ Техническая ошибка\nМы уже работаем над исправлением"
        )
    
    return "ok", 200

@app.route("/")
def index():
    return "🤖 Бот Жорик работает! 🚀", 200

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        debug=False
    )
