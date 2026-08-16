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
        arma = msg.split(maxsplit=1)[1].strip()
        r = requests.get(
            CENTRAL_API.rstrip("/") + "/redsec/classe",
            params={"arma": arma},
            timeout=TIMEOUT,
        )
        return r.text, r.status_code

    # StreamElements treats !classe and !meta as secondary names for the
    # same command, so both intentionally use the same Warzone route.
    if low.startswith("!classe ") or low.startswith("!meta "):
        tipo = msg.split(maxsplit=1)[1].strip()
        r = requests.get(
            CENTRAL_API.rstrip("/") + "/warzone/meta",
            params={"tipo": tipo},
            timeout=TIMEOUT,
        )
        return r.text, r.status_code

    return ("🤖 Comandos: !rank, !bf <arma>, !classe <tipo>, !meta <tipo>, "
            "!wake e !health.", 200)

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
