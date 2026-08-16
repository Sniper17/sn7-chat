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
    raw = msg.strip()
    low = raw.lower()
    parts = raw.split()

    if low == "!rank":
        return call_api("kick/ranking")

    if low in ("!wake", "/wake"):
        return call_api("wake")

    if low in ("!health", "/health"):
        return call_api("health")

    # Kick / Placos
    if low == "!placos" or low == "!pontos":
        return call_api("kick/pontos", {"usuario": "SN7Fps"})

    # Bank robbery: start and result
    if low.startswith("!c4banco"):
        valor = parts[1] if len(parts) > 1 else "1000"
        return call_api("kick/c4banco", {"usuario": "SN7Fps", "valor": valor})

    if low in ("!bancores", "!resultado"):
        return call_api("kick/resultado")

    # Police and bandit: pistol is the default when no kit is supplied.
    if low.startswith("!policia"):
        equipamento = parts[1] if len(parts) > 1 else "pistola"
        return call_api("kick/policia", {
            "usuario": "SN7Fps",
            "equipamento": equipamento
        })

    if low.startswith("!bandido"):
        equipamento = parts[1] if len(parts) > 1 else "pistola"
        return call_api("kick/bandido", {
            "usuario": "SN7Fps",
            "equipamento": equipamento
        })

    # Fight: !briga @usuario (or just username)
    if low.startswith("!briga"):
        if len(parts) < 2:
            return ("⚠️ Use: !briga @jogador", 200)
        jogador2 = parts[1].lstrip("@")
        return call_api("kick/briga", {
            "jogador1": "SN7Fps",
            "jogador2": jogador2
        })

    # Warzone / RedSec
    if low.startswith("!bf "):
        arma = raw.split(maxsplit=1)[1].strip()
        r = requests.get(
            CENTRAL_API.rstrip("/") + "/redsec/classe",
            params={"arma": arma},
            timeout=TIMEOUT,
        )
        return r.text, r.status_code

    if low.startswith("!classe ") or low.startswith("!meta "):
        tipo = raw.split(maxsplit=1)[1].strip()
        r = requests.get(
            CENTRAL_API.rstrip("/") + "/warzone/meta",
            params={"tipo": tipo},
            timeout=TIMEOUT,
        )
        return r.text, r.status_code

    return (
        "🤖 Comandos: !rank, !placos, !bandido, !policia, !c4banco, "
        "!bancores, !briga, !bf, !classe, !meta, !wake e !health.",
        200
    )

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
