import os
from flask import Flask, request
import openai

# Создание клиента OpenRouter
client = openai.OpenAI(
    api_key=os.environ.get("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

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

    try:
        response = client.chat.completions.create(
            model="openai/gpt-4o",  # или другую: see https://openrouter.ai/docs#models
            messages=[
                {"role": "user", "content": message}
            ]
        )
        reply_text = response.choices[0].message.content
        return {"text": reply_text}, 200
    except Exception as e:
        return {"text": f"Ошибка: {str(e)}"}, 200

if __name__ == "__main__":
    app.run(debug=True)

