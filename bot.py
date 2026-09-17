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

# --- Telegram Bot Logik mit Groq API ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

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
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]
    }
    try:
        response = requests.post(url, json=data, headers=headers)
        res_json = response.json()
        return res_json["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Es gab einen kleinen Fehler: {e}"

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
                        
                        reply_text = call_groq(user_text)
                        
                        send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                        requests.post(send_url, json={"chat_id": chat_id, "text": reply_text})
        except Exception as e:
            print(f"Fehler beim Polling: {e}")
            time.sleep(5)

if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    poll_telegram()
