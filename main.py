from flask import Flask, request
import os
import telegram
import requests
import json
import asyncio

TOKEN = os.environ.get("TELEGRAM_TOKEN")
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY")
BOT = telegram.Bot(token=TOKEN)

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

        # Проверка баланса перед запросом
        if not DEEPSEEK_KEY:
            asyncio.run(send_async_message(update.message.chat.id, "Ошибка: Не настроен API-ключ"))
            return "ok"

        headers = {"Authorization": f"Bearer {DEEPSEEK_KEY}"}
        data = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": message}]
        }

        response = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=10
        )
        
        response_data = response.json()
        
        if "error" in response_data:
            error_msg = f"DeepSeek error: {response_data['error']['message']}"
            print(error_msg)
            asyncio.run(send_async_message(update.message.chat.id, "Ошибка API: " + response_data['error']['message']))
        else:
            reply = response_data["choices"][0]["message"]["content"]
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