import os
import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
CENTRAL_API = os.getenv("CENTRAL_API_URL", "https://api-central-sn7.onrender.com")
TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "25"))

def call_api(path, params=None):
    r = requests.get(CENTRAL_API.rstrip("/") + "/" + path.lstrip("/"),
                     params=params or {}, timeout=TIMEOUT)
    return r.text, r.status_code

def handle_message(msg):
    low = msg.strip().lower()
    if low == "!rank":
        return call_api("kick/ranking")
    if low in ("!wake", "/wake"):
        return call_api("wake")
    if low in ("!health", "/health"):
        return call_api("health")
    if low.startswith("!bf "):
        return ("🎮 O chat já está pronto para o BF/RedSec. "
                "Só precisamos ligar a rota exata do seu !bf atual.", 200)
    if low.startswith("!classe "):
        return ("🔫 O chat já está pronto para classes. "
                "Só precisamos ligar a rota exata do seu !classe atual.", 200)
    if low.startswith("!meta"):
        return ("🔥 O chat já está pronto para a meta. "
                "Só precisamos ligar a rota atual da Warzone.", 200)
    return ("🤖 Por enquanto: !rank, !wake e !health. "
            "Na próxima etapa ligamos !bf, !classe e !meta.", 200)

@app.get("/")
def home():
    return render_template("index.html")

@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "sn7-chat", "version": "1.0.0"})

@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    msg = str(data.get("message", "")).strip()
    if not msg:
        return jsonify({"ok": False, "reply": "Digite alguma coisa. 😎"}), 400
    try:
        reply, status = handle_message(msg)
        return jsonify({"ok": status < 400, "reply": reply})
    except requests.RequestException:
        return jsonify({"ok": False, "reply":
            "⚠️ A API ainda está acordando. Tente novamente em alguns segundos."}), 502
    except Exception:
        app.logger.exception("Erro no chat")
        return jsonify({"ok": False, "reply": "⚠️ Erro interno no chat."}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
