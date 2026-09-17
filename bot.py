import os
import requests
from flask import Flask, request

app = Flask(__name__)

# --- Konfiguration ---
TELEGRAM_TOKEN = "8820827837:AAG38KWi7Xiy2gmrr2Tszd7HzfEtPFi4omo"
GROQ_API_KEY = "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" 
# Offizielles, stabiles Standardmodell:
MODEL_NAME = "llama-3.1-8b-instant"

SYSTEM_PROMPT = (
    "Du bist 'Sara', eine extrem herzliche, liebevolle und motivierende A1-Deutschlehrerin. "
    "Du sprichst eine wunderschöne Mischung aus Hocharabisch und irakischem Dialekt. "
    "Erkläre Grammatik auf Arabisch, halte deutsche Sätze sehr einfach (A1) und lobe den Schüler immer herzlich!"
)

@app.route('/')
def home():
    return "Sara Bot Webhook aktiv!"

@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True, silent=True)
        print("--> DATEN EMPFANGEN:", data)
        
        if data and "message" in data:
            msg = data["message"]
            if "text" in msg:
                chat_id = msg["chat"]["id"]
                user_text = msg["text"].strip()
                print(f"--> NACHRICHT VON {chat_id}: {user_text}")
                
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
                
                res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers, timeout=10)
                
                if res.status_code == 200:
                    reply_text = res.json()["choices"][0]["message"]["content"]
                    print("--> ANTWORT VON GROQ ERFOLGREICH")
                else:
                    print(f"--> GROQ FEHLER {res.status_code}: {res.text}")
                    reply_text = f"عذراً يا روحي، حدث خطأ تقني ({res.status_code})."
                
                send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                r = requests.post(send_url, json={"chat_id": chat_id, "text": reply_text}, timeout=5)
                print("--> TELEGRAM SEND STATUS:", r.status_code)
                
    except Exception as e:
        print(f"--> KRITISCHER FEHLER IM WEBHOOK: {e}")
        
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
