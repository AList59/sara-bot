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
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# --- Konfiguration ---
TELEGRAM_TOKEN = "8820827837:AAG38KWi7Xiy2gmrr2Tszd7HzfEtPFi4omo"
GROQ_API_KEY = "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" 
MODEL_NAME = "llama-3.1-8b-instant"

SYSTEM_PROMPT = (
    "Du bist 'Sara', eine extrem herzliche, liebevolle und motivierende A1-Deutschlehrerin. "
    "Du sprichst eine wunderschöne Mischung aus Hocharabisch und irakischem Dialekt. "
    "Erkläre Grammatik auf Arabisch, halte deutsche Sätze sehr einfach (A1) und lobe den Schüler immer herzlich!"
)

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=5)
    except Exception as e:
        print(f"Fehler beim Senden: {e}")

def ask_ai(user_text):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ],
        "temperature": 0.6,
        "max_tokens": 300
    }

    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if res.status_code == 200:
            res_json = res.json()
            return res_json["choices"][0]["message"]["content"]
        else:
            print(f"🚨 GROQ FEHLER: {res.status_code} - {res.text}")
            return f"عذراً يا روحي، حدث خطأ تقني ({res.status_code}). قل لي مجدداً! 😊"
            
    except Exception as e:
        print(f"🚨 EXCEPTION: {e}")
        return "عذراً يا عيوني، الشبكة بطيئة عندي شوية. اعِد لي رسالتك! 🌸"

def main():
    # Alten Webhook löschen, damit getUpdates funktioniert
    try:
        requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=5)
    except:
        pass

    offset = 0
    print("Bot Polling erfolgreich gestartet...")
    
    while True:
        try:
            res = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={offset}&timeout=25", timeout=30)
            data = res.json()
            if data.get("ok"):
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        txt = update["message"]["text"].strip()
                        print(f"Nachricht empfangen von {chat_id}: {txt}")
                        
                        # KI nach Antwort fragen
                        reply = ask_ai(txt)
                        
                        # Antwort an Telegram senden
                        send_message(chat_id, reply)
        except Exception as ex:
            print(f"Polling-Schleifenfehler: {ex}")
            time.sleep(2)

if __name__ == "__main__":
    # Webserver in einem separaten Hintergrund-Thread starten
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Haupt-Thread für das Telegram-Polling nutzen
    main()
