import time
import requests
import threading
import os
from flask import Flask

# --- Mini-Webserver für Render ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Sara Bot läuft 24/7 in der Cloud!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- Konfiguration ---
TELEGRAM_TOKEN = "8820827837:AAG38KWi7Xiy2gmrr2Tszd7HzfEtPFi4omo"
GROQ_API_KEY = "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"
MODEL_NAME = "llama3-8b-8192"

SYSTEM_INSTRUCTION = (
    "Du bist 'Sara', eine extrem herzliche, liebevolle und motivierende A1-Deutschlehrerin. "
    "Du sprichst eine wunderschöne Mischung aus Hocharabisch und irakischem Dialekt. "
    "Erkläre Grammatik auf Arabisch, halte deutsche Sätze sehr einfach (A1) und lobe den Schüler immer herzlich! "
    "Hier ist die Nachricht des Schülers: "
)

conversations = {}

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=5)

def ask_ai(chat_id, user_text):
    if chat_id not in conversations:
        conversations[chat_id] = []
    
    # Wir hängen die Rolle direkt als "user" an, um 400er API-Fehler zu umgehen
    full_prompt = SYSTEM_INSTRUCTION + user_text if len(conversations[chat_id]) == 0 else user_text
    
    conversations[chat_id].append({"role": "user", "content": full_prompt})
    if len(conversations[chat_id]) > 10:
        conversations[chat_id] = conversations[chat_id][-8:]

    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json={"model": MODEL_NAME, "messages": conversations[chat_id], "temperature": 0.5, "max_tokens": 300},
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            timeout=10
        )
        if res.status_code == 200:
            bot_reply = res.json()["choices"][0]["message"]["content"]
            conversations[chat_id].append({"role": "assistant", "content": bot_reply})
            return bot_reply
        else:
            print(f"Groq API Fehler Details: {res.text}")
            return f"عذراً يا روحي، حدث خطأ ({res.status_code}). قل لي مجدداً! 😊"
    except Exception as e:
        print(f"Exception: {e}")
        return "عذراً، لم أفهَم جيدا. هل نعود إلى درس الألمانية؟ 🇩🇪"

def main():
    offset = 0
    while True:
        try:
            res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={offset}&timeout=10", timeout=12)
            data = res.json()
            if data.get("ok"):
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        txt = update["message"]["text"].strip()
                        reply = ask_ai(chat_id, txt)
                        send_message(chat_id, reply)
        except Exception:
            time.sleep(1)

if __name__ == "__main__":
    t = threading.Thread(target=run_server)
    t.start()
    main()
