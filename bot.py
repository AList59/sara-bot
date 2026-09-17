import os
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = "8820827837:AAG38KWi7Xiy2gmrr2Tszd7HzfEtPFi4omo"
GROQ_API_KEY = "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" 

SYSTEM_PROMPT = (
    "Du bist 'Sara', eine extrem herzliche, liebevolle und motivierende A1-Deutschlehrerin. "
    "Du sprichst eine wunderschöne Mischung aus Hocharabisch und irakischem Dialekt. "
    "Erkläre Grammatik auf Arabisch, halte deutsche Sätze sehr einfach (A1) und lobe den Schüler immer herzlich!"
)

def get_dynamic_model():
    """Wählt automatisch ein echtes Chat-Modell aus und ignoriert Guard-/Sicherheitsmodelle."""
    try:
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
        res = requests.get("https://api.groq.com/openai/v1/models", headers=headers, timeout=5)
        if res.status_code == 200:
            models = res.json().get("data", [])
            model_ids = [m["id"] for m in models]
            
            # Suche nach Llama-Chat-Modellen, schließe Guard/Vision aus
            for m in model_ids:
                m_lower = m.lower()
                if "llama" in m_lower and "guard" not in m_lower and "vision" not in m_lower:
                    return m
            if model_ids:
                return model_ids[0]
    except Exception as e:
        print(f"Fehler beim Abrufen der Modelle: {e}")
    
    return "llama-3.3-70b-versatile"

@app.route('/')
def home():
    return "Sara Bot läuft!"

@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True, silent=True)
        if data and "message" in data:
            msg = data["message"]
            if "text" in msg:
                chat_id = msg["chat"]["id"]
                user_text = msg["text"].strip()
                
                chosen_model = get_dynamic_model()
                print(f"Verwende Chat-Modell: {chosen_model}")

                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": chosen_model,
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
                else:
                    reply_text = f"⚠️ Groq API Fehler: Status {res.status_code}\nAntwort: {res.text}"
                
                send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                requests.post(send_url, json={"chat_id": chat_id, "text": reply_text}, timeout=5)
                
    except Exception as e:
        print(f"Fehler: {e}")
        
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
