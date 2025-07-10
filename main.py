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

async def send_telegram_message(chat_id, text):
    try:
        await BOT.send_message(chat_id=chat_id, text=text)
    except Exception as e:
        print(f"Telegram send error: {e}")

@app.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
    try:
        update = telegram.Update.de_json(request.get_json(force=True), BOT)
        message = update.message.text

        headers = {
            "Authorization": f"Bearer {DEEPSEEK_KEY}",
            "Content-Type": "application/json"
        }
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
        print("Full API Response:", json.dumps(response_data, indent=2))
        
        if "choices" not in response_data:
            raise ValueError(f"Unexpected API response format: {response_data}")

        reply = response_data["choices"][0]["message"]["content"]
        asyncio.run(send_telegram_message(update.message.chat.id, reply))
        
    except Exception as e:
        print(f"Error: {str(e)}")
        asyncio.run(send_telegram_message(update.message.chat.id, "Произошла ошибка, попробуйте позже"))
    
    return "ok"

@app.route("/")
def index():
    return "Bot is running"

if __name__ == "__main__":
    app.run(debug=True)