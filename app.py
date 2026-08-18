import os
import random
import re
import sqlite3
from flask import Flask, jsonify, request, render_template_string
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
    conn.execute("CREATE TABLE IF NOT EXISTS custom_commands (command TEXT PRIMARY KEY, response TEXT NOT NULL)")
    conn.commit()
    return conn


def custom_get(command):
    conn = db()
    try:
        row = conn.execute("SELECT response FROM custom_commands WHERE command = ?", (command.lower(),)).fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def custom_set(command, response):
    conn = db()
    try:
        conn.execute("INSERT INTO custom_commands(command,response) VALUES(?,?) ON CONFLICT(command) DO UPDATE SET response=excluded.response", (command.lower(), response))
        conn.commit()
    finally:
        conn.close()


def custom_delete(command):
    conn = db()
    try:
        cur = conn.execute("DELETE FROM custom_commands WHERE command = ?", (command.lower(),))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def custom_list():
    conn = db()
    try:
        return [r[0] for r in conn.execute("SELECT command FROM custom_commands ORDER BY command").fetchall()]
    finally:
        conn.close()


def call_url(base, path, params=None, timeout=None):
    r = requests.get(base.rstrip("/") + "/" + path.lstrip("/"), params=params or {}, timeout=timeout or TIMEOUT, allow_redirects=True)
    return r.text, r.status_code


def kick(path, params=None):
    return call_url(KICK_API, path, params)


def warzone(path, params=None):
    return call_url(WARZONE_API, path, params)


def redsec(path, params=None):
    return call_url(REDSEC_API, path, params)


def wake(base):
    try:
        return call_url(base, "/wake", timeout=12)
    except Exception as exc:
        return str(exc), 599


def admin(username):
    return (username or "").strip().lower() == ADMIN_USERNAME


def expand_custom(text, username):
    return text.replace("$user", username).replace("{user}", username).replace("@user", f"@{username}")


def safe_result(result):
    text, status = result
    if status >= 400:
        return f"⚠️ API indisponível no momento. HTTP {status}.", status
    if "<html" in text.lower() or "<!doctype" in text.lower():
        return "⚠️ O serviço respondeu com uma página de erro.", 502
    return text, status


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
        "!placo": "!placos", "!ponto": "!placos", "!pontos": "!placos",
        "!ranking": "!rank", "!top": "!rank",
        "!addpoints": "!addplaco", "!setpoints": "!setplaco",
        "!polícia": "!policia", "!resultado": "!bancores", "!duelo": "!batalha",
        "!doce": "!xdoce",
    }
    command = aliases.get(command, command)

    if command == "!add" and len(args) >= 3 and args[0].lower() == "cmd":
        if not admin(username): return "❌ Você não tem permissão para criar comandos.", 403
        name, response = args[1].lower(), " ".join(args[2:]).strip()
        if not re.fullmatch(r"![a-z0-9_][a-z0-9_-]{0,31}", name): return "❌ Nome de comando inválido.", 400
        if name in NATIVE_COMMANDS: return "❌ Esse comando é reservado pelo bot.", 400
        custom_set(name, response)
        return f"✅ Comando {name} salvo!", 200

    if command == "!edit" and len(args) >= 3 and args[0].lower() == "cmd":
        if not admin(username): return "❌ Você não tem permissão para editar comandos.", 403
        name, response = args[1].lower(), " ".join(args[2:]).strip()
        if custom_get(name) is None: return f"❌ O comando {name} não existe.", 404
        custom_set(name, response)
        return f"✏️ Comando {name} atualizado!", 200

    if command == "!del" and len(args) >= 2 and args[0].lower() == "cmd":
        if not admin(username): return "❌ Você não tem permissão para apagar comandos.", 403
        name = args[1].lower()
        if custom_delete(name): return f"🗑️ Comando {name} apagado!", 200
        return f"❌ O comando {name} não existe.", 404

    if command == "!cmds":
        # Lista todos os comandos que podem ser usados com !, incluindo aliases
        # e comandos personalizados criados pelo administrador.
        commands = sorted(set(NATIVE_COMMANDS) | set(custom_list()))
        return "📋 COMANDOS • " + " ".join(commands), 200

    custom = custom_get(command)
    if custom is not None:
        return expand_custom(custom, username), 200

    if command == "!rank":
        return safe_result(kick("/ranking"))
    if command == "!placos":
        return safe_result(kick("/placo", {"usuario": username}))

    if command in {"!addplaco", "!setplaco"}:
        if not admin(username): return "🚫 Você não tem permissão para alterar Placos.", 403
        if len(args) < 2:
            usage = "!addplaco @usuario quantidade" if command == "!addplaco" else "!setplaco @usuario quantidade"
            return f"⚠️ Use: {usage}", 200
        target, amount = args[0].lstrip("@"), args[1]
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,22}", target): return "⚠️ Usuário inválido.", 400
        if not re.fullmatch(r"\d+", amount): return "⚠️ Quantidade inválida.", 400
        endpoint = "addplaco" if command == "!addplaco" else "setplaco"
        return safe_result(kick(f"/{endpoint}", {"usuario": target, "quantidade": amount}))

    if command == "!kit": return safe_result(kick("/kit"))
    if command == "!c4banco":
        return safe_result(kick("/c4banco", {"usuario": username, "valor": args[0] if args else "1000"}))
    if command == "!policia": return safe_result(kick("/policia", {"usuario": username, "equipamento": argument or "pistola"}))
    if command == "!bandido": return safe_result(kick("/bandido", {"usuario": username, "equipamento": argument or "pistola"}))
    if command == "!banco": return safe_result(kick("/banco"))
    if command == "!bancores":
        result = safe_result(kick("/resultado"))
        if result[1] < 400: LATEST_BANCO = result[0]
        return result
    if command == "!ultimobanco": return (LATEST_BANCO, 200) if LATEST_BANCO else ("🏦 Ainda não há resultado de banco registrado neste chat.", 200)

    if command == "!briga":
        if not args: return "⚠️ Use: !briga @jogador", 200
        result = safe_result(kick("/briga", {"jogador1": username, "jogador2": args[0].lstrip("@")}))
        if result[1] < 400: LATEST_BRIGA = result[0]
        return result
    if command == "!batalha":
        if not args: return "⚔️ Use: !batalha @jogador", 200
        return safe_result(kick("/duelo", {"jogador1": username, "jogador2": args[0].lstrip("@")}))
    if command == "!ultimabriga": return (LATEST_BRIGA, 200) if LATEST_BRIGA else ("⚔️ Ainda não há uma briga registrada neste chat.", 200)

    if command in {"!bf", "!classe"}:
        if not argument: return f"⚠️ Use: {command} <arma>", 200
        wake(REDSEC_API)
        return safe_result(redsec("/classe", {"arma": argument}))
    if command == "!meta":
        wake(WARZONE_API)
        return safe_result(warzone("/meta", {"tipo": argument})) if argument else safe_result(warzone("/meta"))
    if command == "!wake":
        results = [wake(KICK_API), wake(REDSEC_API), wake(WARZONE_API)]
        return f"⚡ Serviços acionados: {sum(1 for _, status in results if status < 400)}/3 responderam.", 200
    if command == "!health":
        checks = {"Kick": call_url(KICK_API, "/"), "RedSec": call_url(REDSEC_API, "/"), "Warzone": call_url(WARZONE_API, "/")}
        details = " • ".join(f"{name} {'🟢' if status < 500 else '🔴'}" for name, (_, status) in checks.items())
        return f"🩺 HEALTH • {details}", 200
    if command in {"!reset", "!zerar", "!faliu"}:
        if not admin(username): return "🚫 Você não tem permissão para zerar os dados.", 403
        return safe_result(kick("/zerar", {"usuario": username}))
    if command == "!xdoce":
        return random.choice([f"🍬 {username} mandou doces!", f"🍭 {username} distribuiu doces no chat!", f"🍫 {username} apareceu com uma chuva de doces!"]), 200
    if command in {"!ajuda", "!comandos", "!help"}:
        return "🤖 !rank !placos !addplaco !setplaco !kit !c4banco !policia !bandido !banco !bancores !briga !batalha !bf !classe !meta !xdoce !wake !health !add cmd !edit cmd !del cmd !cmds", 200
    return "❓ Comando não encontrado. Use !comandos.", 200


# Wrapper compatível com versões anteriores do SN7 Chat.
# Mantém suporte a chamadas com ou sem username.
def handle_message_with_aliases(message, username="SN7Fps"):
    return handle_message(message, username)



NATIVE_COMMANDS = {
    "!add", "!edit", "!del", "!cmds", "!rank", "!ranking", "!top", "!placo", "!placos", "!ponto", "!pontos",
    "!addplaco", "!addpoints", "!setplaco", "!setpoints", "!kit", "!c4banco", "!policia", "!polícia", "!bandido",
    "!banco", "!bancores", "!resultado", "!ultimobanco", "!briga", "!batalha", "!duelo", "!ultimabriga", "!bf", "!classe",
    "!meta", "!wake", "!health", "!reset", "!zerar", "!faliu", "!xdoce", "!doce", "!ajuda", "!comandos", "!help",
}

CHAT_HTML = r'''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, interactive-widget=resizes-content">
<meta name="theme-color" content="#09090d">
<title>SN7 Chat</title>
<style>
:root{--bg:#08090d;--panel:#101118;--panel2:#151720;--text:#f5f7fb;--muted:#8e94a3;--accent:#8b5cf6;--accent2:#6d28d9;--user:#242735;--bot:#171a24;--line:rgba(255,255,255,.08);--composer:74px}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;width:100%;height:100%;background:var(--bg);color:var(--text);font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;overflow:hidden}
body{overscroll-behavior:none}
.app{height:100dvh;height:100svh;display:flex;flex-direction:column;min-height:0;background:radial-gradient(circle at 50% -20%,rgba(139,92,246,.14),transparent 42%),var(--bg)}
.header{height:58px;min-height:58px;display:flex;align-items:center;padding:0 16px;border-bottom:1px solid var(--line);background:rgba(8,9,13,.92);backdrop-filter:blur(14px);z-index:20}
.logo{width:34px;height:34px;border-radius:11px;display:grid;place-items:center;background:linear-gradient(135deg,var(--accent),var(--accent2));font-weight:900;margin-right:11px;box-shadow:0 5px 20px rgba(109,40,217,.25)}
.title{font-weight:800;font-size:16px}.subtitle{font-size:11px;color:var(--muted);margin-top:1px}.status{margin-left:auto;display:flex;align-items:center;gap:6px;font-size:11px;color:#aeb4c3}.dot{width:7px;height:7px;border-radius:50%;background:#22c55e;box-shadow:0 0 9px #22c55e}
.chat{flex:1;min-height:0;overflow-y:auto;overflow-x:hidden;padding:16px 13px calc(var(--composer) + 22px + env(safe-area-inset-bottom));scroll-behavior:smooth;-webkit-overflow-scrolling:touch}
.empty{height:100%;display:flex;align-items:center;justify-content:center;text-align:center;color:var(--muted);padding:30px}.empty b{display:block;color:var(--text);font-size:22px;margin-bottom:7px}.empty p{margin:0;line-height:1.5;font-size:13px}
.msg{display:flex;margin:0 0 12px;max-width:92%;animation:in .16s ease-out}.msg.user{margin-left:auto;justify-content:flex-end}.bubble{border:1px solid var(--line);border-radius:17px;padding:10px 13px;line-height:1.4;font-size:14px;white-space:pre-wrap;overflow-wrap:anywhere;box-shadow:0 5px 20px rgba(0,0,0,.12)}.bot .bubble{background:var(--bot);border-top-left-radius:6px}.user .bubble{background:var(--user);border-top-right-radius:6px}.meta{font-size:10px;color:var(--muted);margin:0 5px 4px}.msgwrap{min-width:0}.user .meta{text-align:right}
.composer-wrap{position:fixed;left:0;right:0;bottom:0;z-index:50;padding:8px 12px calc(8px + env(safe-area-inset-bottom));background:linear-gradient(to top,rgba(8,9,13,.99) 70%,rgba(8,9,13,.72),transparent);transform:translateY(0);transition:transform .12s ease}
.composer{display:flex;align-items:flex-end;gap:8px;max-width:820px;margin:auto;background:rgba(21,23,32,.98);border:1px solid rgba(255,255,255,.12);border-radius:18px;padding:7px 7px 7px 14px;box-shadow:0 12px 35px rgba(0,0,0,.35)}
.input{flex:1;min-width:0;max-height:112px;resize:none;border:0;outline:0;background:transparent;color:var(--text);font:inherit;font-size:15px;line-height:21px;padding:7px 0;overflow-y:auto}.input::placeholder{color:#737988}.send{width:42px;height:42px;flex:0 0 42px;border:0;border-radius:13px;background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;font-size:18px;font-weight:800;display:grid;place-items:center}.send:disabled{opacity:.45}.hint{text-align:center;color:#555b69;font-size:10px;padding-top:6px}
.loading{display:inline-flex;gap:4px;align-items:center}.loading i{width:5px;height:5px;border-radius:50%;background:#9ca3af;animation:b 1s infinite}.loading i:nth-child(2){animation-delay:.15s}.loading i:nth-child(3){animation-delay:.3s}
@keyframes b{0%,70%,100%{opacity:.25;transform:translateY(0)}35%{opacity:1;transform:translateY(-3px)}}@keyframes in{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}
@media(min-width:700px){.chat{padding-left:max(18px,calc((100vw - 820px)/2));padding-right:max(18px,calc((100vw - 820px)/2))}.composer-wrap{padding-left:18px;padding-right:18px}.header{padding-left:max(18px,calc((100vw - 820px)/2));padding-right:max(18px,calc((100vw - 820px)/2))}}
</style>
</head>
<body>
<div class="app">
<header class="header"><div class="logo">S</div><div><div class="title">SN7 Chat</div><div class="subtitle">Ambiente privado de testes</div></div><div class="status"><span class="dot"></span> online</div></header>
<main id="chat" class="chat"><div id="empty" class="empty"><div><b>👋 SN7 Chat</b><p>Digite um comando abaixo para testar.<br>Ex.: <strong>!placos</strong>, <strong>!rank</strong> ou <strong>!meta mxr</strong></p></div></div></main>
<div id="composerWrap" class="composer-wrap"><form id="form" class="composer"><textarea id="input" class="input" rows="1" autocomplete="off" autocorrect="off" autocapitalize="sentences" spellcheck="false" enterkeyhint="send" placeholder="Digite uma mensagem..."></textarea><button id="send" class="send" type="submit" aria-label="Enviar">➤</button></form><div class="hint">Enter envia • Shift+Enter quebra linha</div></div>
</div>
<script>
const chat=document.getElementById('chat'), empty=document.getElementById('empty'), form=document.getElementById('form'), input=document.getElementById('input'), send=document.getElementById('send'), wrap=document.getElementById('composerWrap');
let busy=false;
function scrollBottom(){requestAnimationFrame(()=>chat.scrollTo({top:chat.scrollHeight,behavior:'smooth'}));}
function addMessage(text,who){empty?.remove();const row=document.createElement('div');row.className='msg '+who;const w=document.createElement('div');w.className='msgwrap';const meta=document.createElement('div');meta.className='meta';meta.textContent=who==='user'?'Você':'SN7 Chat';const b=document.createElement('div');b.className='bubble';b.textContent=text;w.append(meta,b);row.append(w);chat.append(row);scrollBottom();return row}
function addLoading(){empty?.remove();const row=document.createElement('div');row.className='msg bot';const w=document.createElement('div');w.className='msgwrap';const meta=document.createElement('div');meta.className='meta';meta.textContent='SN7 Chat';const b=document.createElement('div');b.className='bubble';b.innerHTML='<span class="loading"><i></i><i></i><i></i></span>';w.append(meta,b);row.append(w);chat.append(row);scrollBottom();return row}
function resizeInput(){input.style.height='auto';input.style.height=Math.min(input.scrollHeight,112)+'px';}
input.addEventListener('input',resizeInput);
input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();form.requestSubmit();}});
form.addEventListener('submit',async e=>{e.preventDefault();if(busy)return;const message=input.value.trim();if(!message)return;addMessage(message,'user');input.value='';resizeInput();busy=true;send.disabled=true;const loading=addLoading();try{const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message,username:'SN7Fps'})});const data=await r.json();loading.remove();addMessage(data.reply||'⚠️ Sem resposta.','bot');}catch(err){loading.remove();addMessage('⚠️ Não foi possível conectar ao SN7 Chat.','bot');}finally{busy=false;send.disabled=false;input.focus({preventScroll:true});scrollBottom();}});
function keyboardSafe(){
  const vv=window.visualViewport;
  if(!vv)return;
  const overlap=Math.max(0,window.innerHeight-vv.height-vv.offsetTop);
  wrap.style.bottom=overlap+'px';
  document.documentElement.style.setProperty('--composer',(wrap.offsetHeight+overlap)+'px');
  if(document.activeElement===input) setTimeout(scrollBottom,60);
}
if(window.visualViewport){visualViewport.addEventListener('resize',keyboardSafe);visualViewport.addEventListener('scroll',keyboardSafe)}
window.addEventListener('resize',keyboardSafe);window.addEventListener('load',()=>{keyboardSafe();resizeInput()});
</script>
</body></html>'''


@app.get("/")
def home():
    return render_template_string(CHAT_HTML)

@app.get("/api")
def api_info():
    return jsonify({"ok": True, "service": "SN7 Chat", "version": "2.2-mobile-chat", "commands": sorted(NATIVE_COMMANDS)})

@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "sn7-chat", "version": "2.2-mobile-chat"})

@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    username = str(data.get("username", "SN7Fps")).strip() or "SN7Fps"
    try:
        reply, status = handle_message_with_aliases(message, username)
        return jsonify({"ok": status < 400, "reply": reply, "status": status}), 200
    except requests.RequestException as exc:
        app.logger.warning("API request error: %s", exc)
        return jsonify({"ok": False, "reply": "⚠️ A API ainda está acordando. Tente novamente em alguns segundos.", "status": 502}), 200
    except Exception as exc:
        app.logger.exception("Chat error: %s", exc)
        return jsonify({"ok": False, "reply": "⚠️ Ocorreu um erro no SN7 Chat.", "status": 500}), 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
