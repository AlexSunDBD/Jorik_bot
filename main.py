import os
from flask import Flask, request
import openai

# Настройки OpenRouter
openai.api_key = os.environ.get("OPENROUTER_API_KEY")
openai.base_url = "https://openrouter.ai/api/v1"

app = Flask(__name__)

@app.route("/")
def home():
    return "Бот работает!"

@app.route("/<token>", methods=["POST"])
def receive_update(token):
    data = request.get_json()

    if "message" not in data or "text" not in data["message"]:
        return "Пропущено: нет текста сообщения", 200

    message = data["message"]["text"]

    response = openai.ChatCompletion.create(
        model="openai/gpt-4o",  # Можно выбрать другую модель
        messages=[
            {"role": "user", "content": message}
        ]
    )

    reply_text = response.choices[0].message["content"]

    return {"text": reply_text}, 200

if __name__ == "__main__":
    app.run(debug=True)

