import os
import threading
import time
import requests
from flask import Flask

# --- Mini-Webserver für Render ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Sara Bot läuft 24/7 in der Cloud!", 200

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- Feste Tokens direkt im Code für diesen Test ---
TELEGRAM_TOKEN = "8820827837:AAG38KWi7Xiy2gmrr2Tszd7HzfEtPFi4omo"
GROQ_API_KEY = "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"

# Saras neue Persönlichkeit: Extrem herzlich, Komplimente, Hocharabisch + Irakisch, A1-Lehrerin
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
        "Authorization": f"Bearer {GROQ_API_KEY}",
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
        if "choices" in res_json:
            return res_json["choices"][0]["message"]["content"]
        else:
            return f"API-Antwort unerwartet: {res_json}"
    except Exception as e:
        return f"Es gab einen kleinen Fehler: {e}"

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Fehler beim Senden an Telegram: {e}")

def poll_telegram():
    offset = 0
    print("Telegram Polling gestartet...")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={offset}&timeout=30"
            response = requests.get(url, timeout=35)
            data = response.json()
            
            if "result" in data:
                for update in data["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        user_text = update["message"]["text"]
                        
                        print(f"Nachricht erhalten von {chat_id}: {user_text}")
                        
                        # Antwort von Groq (Sara) generieren lassen
                        bot_reply = call_groq(user_text)
                        
                        # An Telegram zurückschicken
                        send_telegram_message(chat_id, bot_reply)
        except Exception as e:
            print(f"Polling-Fehler: {e}")
            time.sleep(5)

# --- Start der Anwendung ---
if __name__ == '__main__':
    # Starte den Telegram-Polling-Loop in einem separaten Hintergrund-Thread
    t = threading.Thread(target=poll_telegram)
    t.daemon = True
    t.start()
    
    # Starte den Flask-Webserver im Hauptthread (für Render Port-Binding)
    run_server()
