from flask import Flask, request
import os
import telegram
from openai import OpenAI

TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY")
BOT = telegram.Bot(token=TOKEN)

client = OpenAI(api_key=OPENAI_KEY)

app = Flask(__name__)

@app.route(f"/{TOKEN}", methods=["POST"])
def receive_update():
    update = telegram.Update.de_json(request.get_json(force=True), BOT)
    message = update.message.text

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # или "gpt-4"
        messages=[
            {"role": "user", "content": message}
        ]
    )

    reply = response.choices[0].message.content
    BOT.send_message(chat_id=update.message.chat.id, text=reply)
    return "ok"

@app.route("/")
def index():
    return "Bot is running"

if __name__ == "__main__":
    app.run(debug=True)

