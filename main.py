from flask import Flask, request
import os
import telegram
import requests

TOKEN = os.environ.get("TELEGRAM_TOKEN")
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY")  # Новый ключ
BOT = telegram.Bot(token=TOKEN)

app = Flask(__name__)

@app.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
    update = telegram.Update.de_json(request.get_json(force=True), BOT)
    message = update.message.text

    # Вызов DeepSeek API
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
        json=data
    )
    reply = response.json()["choices"][0]["message"]["content"]

    BOT.send_message(chat_id=update.message.chat.id, text=reply)
    return "ok"

@app.route("/")
def index():
    return "Bot is running"

if __name__ == "__main__":
    app.run(debug=True)