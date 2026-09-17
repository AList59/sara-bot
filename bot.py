import os
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = "8820827837:AAG38KWi7Xiy2gmrr2Tszd7HzfEtPFi4omo"
GROQ_API_KEY = "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"

SYSTEM_PROMPT = (
    "Du bist 'Sara', eine extrem herzliche, liebevolle und motivierende A1-Deutschlehrerin. "
    "Du machst deinem Schüler oft charmante Komplimente, nimmst ihn an die Hand und gibst ihm ein sicheres und geborgenes Gefühl. "
    "Du sprichst eine wunderschöne, natürliche Mischung aus klarem Hocharabisch (Fusha) für Erklärungen "
    "und warmem irakischen Dialekt (Iraqi) für eine vertraute, herzliche Atmosphäre. "
    "Deine Aufgabe ist es, spielerisch und geduldig A1-Deutsch beizubringen: Erkläre Grammatik und Vokabeln auf Arabisch, "
    "halte die deutschen Sätze ganz einfach (A1) und lobe jeden noch so kleinen Fortschritt überschwänglich!"
)

def call_groq(user_message):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY.strip()}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        res_json = response.json()
        if response.status_code == 200 and "choices" in res_json:
            return res_json["choices"][0]["message"]["content"]
        else:
            return f"Groq Fehler: {res_json}"
    except Exception as e:
        return f"Verbindungsfehler: {e}"

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

@app.route('/')
def home():
    return "Sara Bot Webhook läuft!", 200

# Hier empfängt der Bot die Nachrichten direkt von Telegram
@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def telegram_webhook():
    update = request.get_json()
    if "message" in update and "text" in update["message"]:
        chat_id = update["message"]["chat"]["id"]
        user_text = update["message"]["text"]
        print(f"Nachricht erhalten von {chat_id}: {user_text}")
        
        bot_reply = call_groq(user_text)
        send_telegram_message(chat_id, bot_reply)
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
