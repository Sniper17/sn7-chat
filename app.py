import os
import random
import re
import sqlite3
from flask import Flask, jsonify, request

import requests

app = Flask(__name__)

CENTRAL_API = os.getenv("CENTRAL_API_URL", "https://api-central-sn7.onrender.com").rstrip("/")
KICK_API = os.getenv("KICK_API_URL", "https://kick-duelo-api.onrender.com").rstrip("/")
WARZONE_API = os.getenv("WARZONE_API_URL", "https://warzone-api-qbn9.onrender.com").rstrip("/")
REDSEC_API = os.getenv("REDSEC_API_URL", "https://redsec-loadout-api.onrender.com").rstrip("/")
TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "30"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "SN7Fps").strip().lower()
DB_FILE = os.getenv("SN7_CHAT_DB", "sn7_chat.sqlite3")

LATEST_BRIGA = None
LATEST_BANCO = None


def db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS custom_commands (
            command TEXT PRIMARY KEY,
            response TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def custom_get(command):
    conn = db()
    try:
        row = conn.execute(
            "SELECT response FROM custom_commands WHERE command = ?",
            (command.lower(),)
        ).fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def custom_set(command, response):
    conn = db()
    try:
        conn.execute(
            "INSERT INTO custom_commands(command,response) VALUES(?,?) "
            "ON CONFLICT(command) DO UPDATE SET response=excluded.response",
            (command.lower(), response)
        )
        conn.commit()
    finally:
        conn.close()


def custom_delete(command):
    conn = db()
    try:
        cur = conn.execute(
            "DELETE FROM custom_commands WHERE command = ?",
            (command.lower(),)
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def custom_list():
    conn = db()
    try:
        rows = conn.execute(
            "SELECT command FROM custom_commands ORDER BY command"
        ).fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


def call_url(base, path, params=None, timeout=None):
    r = requests.get(
        base.rstrip("/") + "/" + path.lstrip("/"),
        params=params or {},
        timeout=timeout or TIMEOUT,
        allow_redirects=True,
    )
    return r.text, r.status_code


def kick(path, params=None):
    return call_url(KICK_API, path, params)


def warzone(path, params=None):
    return call_url(WARZONE_API, path, params)


def redsec(path, params=None):
    return call_url(REDSEC_API, path, params)


def central(path, params=None):
    return call_url(CENTRAL_API, path, params)


def wake(base):
    try:
        return call_url(base, "/wake", timeout=12)
    except Exception as exc:
        return str(exc), 599


def admin(username):
    return (username or "").strip().lower() == ADMIN_USERNAME


def expand_custom(text, username):
    return (
        text.replace("$user", username)
            .replace("{user}", username)
            .replace("@user", f"@{username}")
    )


def safe_result(result):
    text, status = result
    if status >= 400:
        return (f"⚠️ API indisponível no momento. HTTP {status}.", status)
    if "<html" in text.lower() or "<!doctype" in text.lower():
        return ("⚠️ O serviço respondeu com uma página de erro.", 502)
    return (text, status)


def handle_message(message, username="SN7Fps"):
    global LATEST_BRIGA, LATEST_BANCO

    raw = str(message or "").strip()
    if not raw:
        return "Digite um comando. 😎", 200

    parts = raw.split()
    command = parts[0].lower()
    args = parts[1:]
    argument = " ".join(args).strip()

    aliases = {
        "!placo": "!placos",
        "!ponto": "!placos",
        "!pontos": "!placos",
        "!ranking": "!rank",
        "!top": "!rank",
        "!addpoints": "!addplaco",
        "!setpoints": "!setplaco",
        "!polícia": "!policia",
        "!resultado": "!bancores",
        "!duelo": "!batalha",
        "!doce": "!xdoce",
    }
    command = aliases.get(command, command)

    # Gerenciamento de comandos personalizados
    if command == "!add" and len(args) >= 3 and args[0].lower() == "cmd":
        if not admin(username):
            return "❌ Você não tem permissão para criar comandos.", 403

        name = args[1].lower()
        response = " ".join(args[2:]).strip()
        if not re.fullmatch(r"![a-z0-9_][a-z0-9_-]{0,31}", name):
            return "❌ Nome de comando inválido.", 400
        if name in NATIVE_COMMANDS:
            return "❌ Esse comando é reservado pelo bot.", 400
        custom_set(name, response)
        return f"✅ Comando {name} salvo!", 200

    if command == "!edit" and len(args) >= 3 and args[0].lower() == "cmd":
        if not admin(username):
            return "❌ Você não tem permissão para editar comandos.", 403
        name = args[1].lower()
        response = " ".join(args[2:]).strip()
        if custom_get(name) is None:
            return f"❌ O comando {name} não existe.", 404
        custom_set(name, response)
        return f"✏️ Comando {name} atualizado!", 200

    if command == "!del" and len(args) >= 2 and args[0].lower() == "cmd":
        if not admin(username):
            return "❌ Você não tem permissão para apagar comandos.", 403
        name = args[1].lower()
        if custom_delete(name):
            return f"🗑️ Comando {name} apagado!", 200
        return f"❌ O comando {name} não existe.", 404

    if command == "!cmds":
        commands = custom_list()
        return (
            ("📋 Comandos personalizados: " + ", ".join(commands))
            if commands else "📋 Ainda não há comandos personalizados.",
            200,
        )

    # Comandos personalizados têm prioridade depois da administração.
    custom = custom_get(command)
    if custom is not None:
        return expand_custom(custom, username), 200

    if command == "!rank":
        return safe_result(kick("/ranking"))

    if command == "!placos":
        return safe_result(kick("/placo", {"usuario": username}))

    if command in {"!addplaco", "!setplaco"}:
        if not admin(username):
            return "🚫 Você não tem permissão para alterar Placos.", 403
        if len(args) < 2:
            usage = "!addplaco @usuario quantidade" if command == "!addplaco" else "!setplaco @usuario quantidade"
            return f"⚠️ Use: {usage}", 200

        target = args[0].lstrip("@")
        amount = args[1]
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,22}", target):
            return "⚠️ Usuário inválido.", 400
        if not re.fullmatch(r"\d+", amount):
            return "⚠️ Quantidade inválida.", 400

        endpoint = "addplaco" if command == "!addplaco" else "setplaco"
        return safe_result(kick(f"/{endpoint}", {
            "usuario": target,
            "quantidade": amount,
        }))

    if command == "!kit":
        return safe_result(kick("/kit"))

    if command == "!c4banco":
        value = args[0] if args else "1000"
        return safe_result(kick("/c4banco", {
            "usuario": username,
            "valor": value,
        }))

    if command == "!policia":
        equipamento = argument or "pistola"
        return safe_result(kick("/policia", {
            "usuario": username,
            "equipamento": equipamento,
        }))

    if command == "!bandido":
        equipamento = argument or "pistola"
        return safe_result(kick("/bandido", {
            "usuario": username,
            "equipamento": equipamento,
        }))

    if command == "!banco":
        return safe_result(kick("/banco"))

    if command == "!bancores":
        result = safe_result(kick("/resultado"))
        if result[1] < 400:
            LATEST_BANCO = result[0]
        return result

    if command == "!ultimobanco":
        if LATEST_BANCO:
            return LATEST_BANCO, 200
        return "🏦 Ainda não há resultado de banco registrado neste chat.", 200

    if command == "!briga":
        if not args:
            return "⚠️ Use: !briga @jogador", 200
        result = safe_result(kick("/briga", {
            "jogador1": username,
            "jogador2": args[0].lstrip("@"),
        }))
        if result[1] < 400:
            LATEST_BRIGA = result[0]
        return result

    if command == "!batalha":
        if not args:
            return "⚔️ Use: !batalha @jogador", 200
        return safe_result(kick("/duelo", {
            "jogador1": username,
            "jogador2": args[0].lstrip("@"),
        }))

    if command == "!ultimabriga":
        if LATEST_BRIGA:
            return LATEST_BRIGA, 200
        return "⚔️ Ainda não há uma briga registrada neste chat.", 200

    if command == "!bf":
        if not argument:
            return "⚠️ Use: !bf <arma>", 200
        wake(REDSEC_API)
        return safe_result(redsec("/classe", {"arma": argument}))

    if command == "!classe":
        if not argument:
            return "⚠️ Use: !classe <arma>", 200
        wake(REDSEC_API)
        return safe_result(redsec("/classe", {"arma": argument}))

    if command == "!meta":
        # Mantém o comportamento do bot principal: meta é consultada diretamente.
        if argument:
            wake(WARZONE_API)
            return safe_result(warzone("/meta", {"tipo": argument}))
        wake(WARZONE_API)
        return safe_result(warzone("/meta"))

    if command == "!wake":
        results = {
            "Kick": wake(KICK_API),
            "RedSec": wake(REDSEC_API),
            "Warzone": wake(WARZONE_API),
        }
        ok = sum(1 for _, status in results.values() if status < 400)
        return f"⚡ Serviços acionados: {ok}/3 responderam.", 200

    if command == "!health":
        checks = {
            "Kick": call_url(KICK_API, "/"),
            "RedSec": call_url(REDSEC_API, "/"),
            "Warzone": call_url(WARZONE_API, "/"),
        }
        details = " • ".join(
            f"{name} {'🟢' if status < 500 else '🔴'}"
            for name, (_, status) in checks.items()
        )
        return f"🩺 HEALTH • {details}", 200

    if command in {"!reset", "!zerar", "!faliu"}:
        if not admin(username):
            return "🚫 Você não tem permissão para zerar os dados.", 403
        result = safe_result(kick("/zerar", {"usuario": username}))
        return result

    if command == "!xdoce":
        return random.choice([
            f"🍬 {username} mandou doces!",
            f"🍭 {username} distribuiu doces no chat!",
            f"🍫 {username} apareceu com uma chuva de doces!",
        ]), 200

    if command in {"!ajuda", "!comandos", "!help"}:
        return (
            "🤖 !rank !placos !addplaco !setplaco !kit !c4banco "
            "!policia !bandido !banco !bancores !briga !batalha "
            "!bf !classe !meta !xdoce !wake !health !add cmd !edit cmd !del cmd !cmds",
            200,
        )

    return "❓ Comando não encontrado. Use !comandos.", 200


NATIVE_COMMANDS = {
    "!add", "!edit", "!del", "!cmds",
    "!rank", "!ranking", "!top",
    "!placo", "!placos", "!ponto", "!pontos",
    "!addplaco", "!addpoints", "!setplaco", "!setpoints",
    "!kit", "!c4banco", "!policia", "!polícia", "!bandido",
    "!banco", "!bancores", "!resultado", "!ultimobanco",
    "!briga", "!batalha", "!duelo", "!ultimabriga",
    "!bf", "!classe", "!meta",
    "!wake", "!health", "!reset", "!zerar", "!faliu",
    "!xdoce", "!doce", "!ajuda", "!comandos", "!help",
}


@app.get("/")
def home():
    return jsonify({
        "ok": True,
        "service": "SN7 Chat",
        "version": "2.0-full-commands",
        "commands": sorted(NATIVE_COMMANDS),
    })


@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "sn7-chat", "version": "2.0-full-commands"})


@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    username = str(data.get("username", "SN7Fps")).strip() or "SN7Fps"

    try:
        reply, status = handle_message(message, username)
        return jsonify({
            "ok": status < 400,
            "reply": reply,
            "status": status,
        }), 200
    except requests.RequestException as exc:
        app.logger.warning("API request error: %s", exc)
        return jsonify({
            "ok": False,
            "reply": "⚠️ A API ainda está acordando. Tente novamente em alguns segundos.",
        }), 200
    except Exception:
        app.logger.exception("Erro no SN7 Chat")
        return jsonify({
            "ok": False,
            "reply": "⚠️ Erro interno no SN7 Chat.",
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
