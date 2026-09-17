import os
import threading
import time
import requests
from flask import Flask

# --- Mini-Webserver für Render ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Sara Bot läuft 24/7 in der Cloud!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- Feste Tokens & Konfiguration ---
TELEGRAM_TOKEN = "8820827837:AAG38KWi7Xiy2gmrr2Tszd7HzfEtPFi4omo"
GROQ_API_KEY = "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"
MODEL_NAME = "llama3-70b-8192"

conversations = {}

# Saras liebevolle A1-Lehrerin Persönlichkeit (Hocharabisch + Irakisch)
SYSTEM_PROMPT = (
    "Du bist 'Sara', eine extrem herzliche, liebevolle und motivierende A1-Deutschlehrerin. "
    "Du machst deinem Schüler oft charmante Komplimente, nimmst ihn an die Hand und gibst ihm ein sicheres und geborgenes Gefühl. "
    "Du sprichst eine wunderschöne, natürliche Mischung aus klarem Hocharabisch (Fusha) für Erklärungen "
    "und warmem irakischen Dialekt (Iraqi) für eine vertraute, herzliche Atmosphäre. "
    "Deine Aufgabe ist es, spielerisch und geduldig A1-Deutsch beizubringen: Erkläre Grammatik und Vokabeln auf Arabisch, "
    "halte die deutschen Sätze ganz einfach (A1) und lobe jeden noch so kleinen Fortschritt überschwänglich!"
)

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=5)

def ask_ai(chat_id, user_text):
    if chat_id not in conversations:
        conversations[chat_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    conversations[chat_id].append({"role": "user", "content": user_text})
    if len(conversations[chat_id]) > 10:
        conversations[chat_id] = [conversations[chat_id][0]] + conversations[chat_id][-8:]

    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json={"model": MODEL_NAME, "messages": conversations[chat_id], "temperature": 0.6, "max_tokens": 400},
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            timeout=10
        )
        if res.status_code == 200:
            bot_reply = res.json()["choices"][0]["message"]["content"]
            conversations[chat_id].append({"role": "assistant", "content": bot_reply})
            return bot_reply
        return "أهلاً بك يا عيوني! دعنا نواصل التعلم. ما القاعدة التي تريد أن نتدرب عليها الآن؟ 😊"
    except Exception:
        return "عذراً يا روحي، لم أفهَم جيداً. هل نعود إلى درس الألمانية؟ 🇩🇪"

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
