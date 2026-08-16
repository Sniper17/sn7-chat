import os
import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
CENTRAL_API = os.getenv("CENTRAL_API_URL", "https://api-central-sn7.onrender.com")
KICK_API = os.getenv("KICK_API_URL", "https://kick-duelo-api.onrender.com")
WARZONE_API = os.getenv("WARZONE_API_URL", "https://warzone-api-qbn9.onrender.com")
REDSEC_API = os.getenv("REDSEC_API_URL", "https://redsec-loadout-api.onrender.com")
TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "25"))

LATEST_BRIGA = None
LATEST_BANCO = None


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

def wake_service(base):
    try:
        return call_url(base, "/wake")
    except Exception as e:
        return (f"wake error: {e}", 599)

def wake_all_services():
    # Wake the three Render services directly. This makes the private chat
    # independent of the central proxy for cold-starting Warzone/RedSec/Kick.
    results = {
        "kick": wake_service(KICK_API),
        "redsec": wake_service(REDSEC_API),
        "warzone": wake_service(WARZONE_API),
    }
    # If the direct wake endpoint is unavailable on any service, keep the
    # central wake as a fallback rather than breaking the command.
    if any(status >= 400 for _, status in results.values()):
        try:
            central = call_api("/wake")
            results["central"] = central
        except Exception as e:
            results["central"] = (f"central wake error: {e}", 599)
    return results

def handle_message(msg):
    global LATEST_BRIGA, LATEST_BANCO

    raw = msg.strip()
    low = raw.lower()
    parts = raw.split()

    if low == "!rank":
        return call_kick("/ranking")

    if low in ("!wake", "/wake"):
        results = wake_all_services()
        primary = {k:v for k,v in results.items() if k in ("kick","redsec","warzone")}
        ok = sum(1 for _, status in primary.values() if status < 400)
        return (f"⚡ Serviços acionados: {ok}/3 responderam.", 200)

    if low in ("!health", "/health"):
        checks = {
            "kick": call_url(KICK_API, "/"),
            "redsec": call_url(REDSEC_API, "/"),
            "warzone": call_url(WARZONE_API, "/"),
        }
        ok = sum(1 for _, status in checks.values() if status < 500)
        details = " • ".join(
            f"{name} {'🟢' if status < 500 else '🔴'}"
            for name, (_, status) in checks.items()
        )
        return (f"🩺 HEALTH • {details} • {ok}/3 online", 200)

    if low in ("!placos", "!pontos"):
        return call_kick("/pontos", {"usuario": "SN7Fps"})

    if low in ("!reset", "!zerar"):
        return call_kick("/zerar", {"usuario": "SN7Fps"})

    if low == "!kit":
        return call_kick("/kit")

    # History is kept by this chat instance from commands that already exist.
    # No new /ultimabriga or /ultimobanco endpoint is required.
    if low == "!ultimabriga":
        if not LATEST_BRIGA:
            return ("⚔️ Ainda não há uma briga registrada neste chat.", 200)
        return (LATEST_BRIGA, 200)

    if low == "!ultimobanco":
        if not LATEST_BANCO:
            return ("🏦 Ainda não há um resultado de banco registrado neste chat.", 200)
        return (LATEST_BANCO, 200)

    if low.startswith("!c4banco"):
        valor = parts[1] if len(parts) > 1 else "1000"
        return call_kick("/c4banco", {"usuario": "SN7Fps", "valor": valor})

    if low in ("!bancores", "!resultado"):
        result = call_kick("/resultado")
        if isinstance(result, tuple) and result[1] < 400:
            LATEST_BANCO = result[0]
        return result

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

    if low.startswith("!briga"):
        if len(parts) < 2:
            return ("⚠️ Use: !briga @jogador", 200)
        jogador2 = parts[1].lstrip("@")
        result = call_kick("/briga", {
            "jogador1": "SN7Fps",
            "jogador2": jogador2
        })
        if isinstance(result, tuple) and result[1] < 400:
            LATEST_BRIGA = result[0]
        return result

    # RedSec / Battlefield: !bf <arma>
    if low.startswith("!bf "):
        arma = raw.split(maxsplit=1)[1].strip()
        wake_service(REDSEC_API)
        result = call_redsec("/classe", {"arma": arma})
        if isinstance(result, tuple) and result[1] >= 400:
            wake_service(REDSEC_API)
            result = call_redsec("/classe", {"arma": arma})
        return result

    # Warzone: !meta <tipo> and !classe <arma> are the SAME command.
    # Both use the Warzone /meta endpoint.
    if low.startswith("!meta ") or low.startswith("!classe "):
        valor = raw.split(maxsplit=1)[1].strip()
        wake_service(WARZONE_API)
        result = call_warzone("/meta", {"tipo": valor})
        if isinstance(result, tuple) and result[1] >= 400:
            wake_service(WARZONE_API)
            result = call_warzone("/meta", {"tipo": valor})
        if isinstance(result, tuple) and result[1] >= 400:
            result = call_api("/warzone/meta", {"tipo": valor})
        return result

    return (
        "🤖 Comandos: !rank, !placos, !reset, !zerar, !kit, !bandido, "
        "!policia, !c4banco, !bancores, !ultimabriga, !ultimobanco, "
        "!briga, !bf, !classe, !meta, !wake e !health.",
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
        if isinstance(reply, str):
            lower_reply = reply.lower()
            if "<!doctype html" in lower_reply or "<html" in lower_reply or "<svg" in lower_reply:
                return jsonify({
                    "ok": False,
                    "reply": "⚠️ O serviço respondeu com uma página de erro. Tente novamente em alguns segundos."
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
