import os
import requests
from flask import Flask, request

app = Flask(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
GROQ = os.environ.get("GROQ_API_KEY")

@app.route("/", methods=["POST"])
def webhook():
    data = request.json
    
    if "message" not in data:
        return "ok"

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama3-70b-8192",
            "messages": [{"role": "user", "content": text}]
        }
    )

    reply = r.json()["choices"][0]["message"]["content"]

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": reply}
    )

    return "ok"
