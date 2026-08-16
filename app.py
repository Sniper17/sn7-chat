import os
import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
CENTRAL_API = os.getenv("CENTRAL_API_URL", "https://api-central-sn7.onrender.com")
KICK_API = os.getenv("KICK_API_URL", "https://kick-duelo-api.onrender.com")
WARZONE_API = os.getenv("WARZONE_API_URL", "https://warzone-api-qbn9.onrender.com")
REDSEC_API = os.getenv("REDSEC_API_URL", "https://redsec-loadout-api.onrender.com")
TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "25"))

def call_url(base, path, params=None):
    r = requests.get(
        base.rstrip("/") + "/" + path.lstrip("/"),
        params=params or {},
        timeout=TIMEOUT
    )
    return r.text, r.status_code

def call_api(path, params=None):
    # Central-only routes.
    return call_url(CENTRAL_API, path, params)

def call_kick(path, params=None):
    # Kick routes are called directly. This avoids the central proxy returning
    # its Render 404 HTML for a route it does not currently expose.
    return call_url(KICK_API, path, params)

def call_warzone(path, params=None):
    return call_url(WARZONE_API, path, params)

def call_redsec(path, params=None):
    return call_url(REDSEC_API, path, params)

def handle_message(msg):
    raw = msg.strip()
    low = raw.lower()
    parts = raw.split()

    if low == "!rank":
        return call_kick("/ranking")

    if low in ("!wake", "/wake"):
        return call_api("wake")

    if low in ("!health", "/health"):
        return call_api("health")

    # Kick / pontos
    if low in ("!placos", "!pontos"):
        return call_kick("/pontos", {"usuario": "SN7Fps"})

    # Reset individual: resets points, V/D and ranking data for SN7Fps.
    # This route is not assumed to exist in the central proxy yet, so V3.3
    # calls the existing Kick API directly.
    if low in ("!reset", "!zerar"):
        return call_kick("/zerar", {"usuario": "SN7Fps"})

    # Equipment list
    if low == "!kit":
        return call_kick("/kit")

    # Latest history
    if low == "!ultimabriga":
        return call_kick("/ultimabriga")

    if low == "!ultimobanco":
        return call_kick("/ultimobanco")

    # Bank robbery
    if low.startswith("!c4banco"):
        valor = parts[1] if len(parts) > 1 else "1000"
        return call_kick("/c4banco", {"usuario": "SN7Fps", "valor": valor})

    if low in ("!bancores", "!resultado"):
        return call_kick("/resultado")

    # Police / bandit: pistol is the default.
    if low.startswith("!policia"):
        equipamento = parts[1] if len(parts) > 1 else "pistola"
        return call_kick("/policia", {
            "usuario": "SN7Fps",
            "equipamento": equipamento
        })

    if low.startswith("!bandido"):
        equipamento = parts[1] if len(parts) > 1 else "pistola"
        return call_kick("/bandido", {
            "usuario": "SN7Fps",
            "equipamento": equipamento
        })

    # Fight
    if low.startswith("!briga"):
        if len(parts) < 2:
            return ("⚠️ Use: !briga @jogador", 200)
        jogador2 = parts[1].lstrip("@")
        return call_kick("/briga", {
            "jogador1": "SN7Fps",
            "jogador2": jogador2
        })

    # Warzone / RedSec
    if low.startswith("!bf "):
        arma = raw.split(maxsplit=1)[1].strip()
        return call_redsec("/classe", {"arma": arma})

    if low.startswith("!classe ") or low.startswith("!meta "):
        tipo = raw.split(maxsplit=1)[1].strip()
        return call_warzone("/meta", {"tipo": tipo})

    return (
        "🤖 Comandos: !rank, !placos, !reset, !zerar, !kit, !bandido, "
        "!policia, !c4banco, !bancores, !ultimabriga, !ultimobanco, !briga, !bf, !classe, !meta, "
        "!wake e !health.",
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
        if isinstance(reply, str) and "<svg" in reply.lower():
            return jsonify({
                "ok": False,
                "reply": "⚠️ O serviço respondeu com uma página de erro. Tente novamente em alguns segundos."
            })
        if isinstance(reply, str) and "<!doctype html" in reply.lower() and "render" in reply.lower():
            return jsonify({
                "ok": False,
                "reply": "⚠️ O serviço ainda não respondeu corretamente. Tente novamente em alguns segundos."
            })
        return jsonify({"ok": status < 400, "reply": reply})
    except requests.RequestException:
        return jsonify({"ok": False, "reply":
            "⚠️ A API ainda está acordando. Tente novamente em alguns segundos."}), 502
    except Exception:
        app.logger.exception("Erro no chat")
        return jsonify({"ok": False, "reply": "⚠️ Erro interno no chat."}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
