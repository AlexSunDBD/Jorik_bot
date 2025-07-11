from flask import Flask, request
import os
import telegram
from openai import OpenAI
import logging
import asyncio

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

# Клиент OpenRouter
client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "https://jorik-bot.onrender.com",
        "X-Title": "Jorik Telegram Bot"
    }
)

MODEL = "gryphe/mythomax-l2-13b"

app = Flask(__name__)

async def send_async_message(chat_id, text):
    try:
        await bot.send_message(
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
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "Ты ассистент Жорик. Отвечай дружелюбно."},
                    {"role": "user", "content": message}
                ],
                max_tokens=800
            )
            
            reply = response.choices[0].message.content
            asyncio.run(send_async_message(chat_id, reply))
            
        except Exception as api_error:
            error_msg = str(api_error)
            logger.error(f"API error: {error_msg}")
            asyncio.run(send_async_message(chat_id, "⚠️ Ошибка обработки запроса"))
            
    except Exception as e:
        logger.error(f"System error: {str(e)}")
    
    return "ok", 200

@app.route("/")
def home():
    return "🤖 Бот активен", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)