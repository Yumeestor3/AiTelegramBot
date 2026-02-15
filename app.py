import os
import requests
from flask import Flask, request, jsonify
import logging

app = Flask(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
GROQ = os.environ.get("GROQ_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Bot is running!"

@app.route("/", methods=["POST"])
def webhook():
    try:
        data = request.get_json()

        # Validasi data
        if not data or "message" not in data:
            return jsonify({"status": "no message"}), 400

        if "chat" not in data["message"]:
            return jsonify({"status": "invalid message format"}), 400

        chat_id = data["message"]["chat"].get("id")
        if not chat_id:
            return jsonify({"status": "no chat_id"}), 400

        text = data["message"].get("text", "").strip()

        # Validasi text
        if not text:
            return jsonify({"status": "no text"}), 200

        # Panggil Groq API
        try:
            groq_response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama3-70b-8192",
                    "messages": [{"role": "user", "content": text}]
                },
                timeout=30
            )

            # Cek status Groq
            if groq_response.status_code != 200:
                logger.error(f"Groq error: {groq_response.status_code}")
                reply = "⚠️ AI sedang error."
            else:
                result = groq_response.json()
                
                # Validasi struktur response
                if "choices" not in result or not result["choices"]:
                    logger.error(f"Invalid Groq response: {result}")
                    reply = "⚠️ Format respons tidak valid."
                else:
                    reply = result["choices"][0]["message"]["content"]

        except requests.Timeout:
            logger.error("Groq timeout")
            reply = "⏱️ Permintaan timeout."
        except requests.RequestException as e:
            logger.error(f"Groq request error: {e}")
            reply = "❌ Error koneksi."
        except (KeyError, IndexError) as e:
            logger.error(f"Groq response parse error: {e}")
            reply = "❌ Error parsing respons."

        # Kirim ke Telegram
        telegram_response = requests.post(
            f"https://api.telegram.org/bot{TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": reply
            },
            timeout=30
        )

        if telegram_response.status_code != 200:
            logger.error(f"Telegram send failed: {telegram_response.status_code}")
            return jsonify({"status": "telegram_failed"}), 500

        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify({"status": "error"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
