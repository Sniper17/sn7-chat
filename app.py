import os
from flask import Flask, jsonify, request, render_template_string
import requests

app = Flask(__name__)

WORKER_COMMAND_URL = os.getenv("WORKER_COMMAND_URL", "https://sn7-kick-worker.onrender.com/command").strip().rstrip("/")
WORKER_COMMAND_KEY = os.getenv("WORKER_COMMAND_KEY", "").strip()
TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "180"))

CHAT_HTML = r'''<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, interactive-widget=resizes-content">
<meta name="theme-color" content="#09090d">
<title>Baguncinha</title>
<style>
:root{--bg:#08090d;--text:#f5f7fb;--muted:#8e94a3;--accent:#8b5cf6;--accent2:#6d28d9;--user:#242735;--bot:#171a24;--line:rgba(255,255,255,.08);--composer:74px}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;width:100%;height:100%;background:var(--bg);color:var(--text);font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;overflow:hidden}
body{overscroll-behavior:none}.app{height:100dvh;height:100svh;display:flex;flex-direction:column;min-height:0;background:radial-gradient(circle at 50% -20%,rgba(139,92,246,.14),transparent 42%),var(--bg)}
.header{height:58px;min-height:58px;display:flex;align-items:center;padding:0 16px;border-bottom:1px solid var(--line);background:rgba(8,9,13,.92);backdrop-filter:blur(14px);z-index:20}
.logo{width:34px;height:34px;border-radius:11px;display:grid;place-items:center;background:linear-gradient(135deg,var(--accent),var(--accent2));font-weight:900;margin-right:11px}.title{font-weight:800;font-size:16px}.subtitle{font-size:11px;color:var(--muted);margin-top:1px}.status{margin-left:auto;display:flex;align-items:center;gap:6px;font-size:11px;color:#aeb4c3}.dot{width:7px;height:7px;border-radius:50%;background:#22c55e;box-shadow:0 0 9px #22c55e}
.chat{flex:1;min-height:0;overflow-y:auto;overflow-x:hidden;padding:16px 13px calc(var(--composer) + 22px + env(safe-area-inset-bottom));scroll-behavior:smooth;-webkit-overflow-scrolling:touch}
.empty{height:100%;display:flex;align-items:center;justify-content:center;text-align:center;color:var(--muted);padding:30px}.empty b{display:block;color:var(--text);font-size:22px;margin-bottom:7px}.empty p{margin:0;line-height:1.5;font-size:13px}
.msg{display:flex;margin:0 0 12px;max-width:92%;animation:in .16s ease-out}.msg.user{margin-left:auto;justify-content:flex-end}.bubble{border:1px solid var(--line);border-radius:17px;padding:10px 13px;line-height:1.4;font-size:14px;white-space:pre-wrap;overflow-wrap:anywhere;box-shadow:0 5px 20px rgba(0,0,0,.12)}.bot .bubble{background:var(--bot);border-top-left-radius:6px}.user .bubble{background:var(--user);border-top-right-radius:6px}.meta{font-size:10px;color:var(--muted);margin:0 5px 4px}.user .meta{text-align:right}.bot .meta{display:none}
.composer-wrap{position:fixed;left:0;right:0;bottom:0;z-index:50;padding:8px 12px calc(8px + env(safe-area-inset-bottom));background:linear-gradient(to top,rgba(8,9,13,.99) 70%,rgba(8,9,13,.72),transparent)}.composer{display:flex;align-items:flex-end;gap:8px;max-width:820px;margin:auto;background:rgba(21,23,32,.98);border:1px solid rgba(255,255,255,.12);border-radius:18px;padding:7px 7px 7px 14px;box-shadow:0 12px 35px rgba(0,0,0,.35)}
.input{flex:1;min-width:0;max-height:112px;resize:none;border:0;outline:0;background:transparent;color:var(--text);font:inherit;font-size:15px;line-height:21px;padding:7px 0;overflow-y:auto}.input::placeholder{color:#737988}.send{width:42px;height:42px;flex:0 0 42px;border:0;border-radius:13px;background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;font-size:18px;font-weight:800;display:grid;place-items:center}.send:disabled{opacity:.45}.hint{text-align:center;color:#555b69;font-size:10px;padding-top:6px}.loading{display:inline-flex;gap:4px;align-items:center}.loading i{width:5px;height:5px;border-radius:50%;background:#9ca3af;animation:b 1s infinite}.loading i:nth-child(2){animation-delay:.15s}.loading i:nth-child(3){animation-delay:.3s}@keyframes b{0%,70%,100%{opacity:.25;transform:translateY(0)}35%{opacity:1;transform:translateY(-3px)}}@keyframes in{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}
@media(min-width:700px){.chat{padding-left:max(18px,calc((100vw - 820px)/2));padding-right:max(18px,calc((100vw - 820px)/2))}.composer-wrap{padding-left:18px;padding-right:18px}.header{padding-left:max(18px,calc((100vw - 820px)/2));padding-right:max(18px,calc((100vw - 820px)/2))}}
</style></head>
<body><div class="app">
<header class="header"><div class="logo">B</div><div><div class="title">Baguncinha</div><div class="subtitle">Ambiente privado de testes</div></div><div class="status"><span class="dot"></span> online</div></header>
<main id="chat" class="chat"><div id="empty" class="empty"><div><b>👋 Baguncinha</b><p>Digite um comando abaixo para testar.<br>Ex.: <strong>!placos</strong>, <strong>!rank</strong> ou <strong>!meta mxr</strong></p></div></div></main>
<div id="composerWrap" class="composer-wrap"><form id="form" class="composer"><textarea id="input" class="input" rows="1" autocomplete="off" autocorrect="off" autocapitalize="sentences" spellcheck="false" enterkeyhint="send" placeholder="Digite uma mensagem..."></textarea><button id="send" class="send" type="submit" aria-label="Enviar">➤</button></form><div class="hint">Enter envia • Shift+Enter quebra linha</div></div></div>
<script>
const chat=document.getElementById('chat'),empty=document.getElementById('empty'),form=document.getElementById('form'),input=document.getElementById('input'),send=document.getElementById('send'),wrap=document.getElementById('composerWrap');let busy=false;
function scrollBottom(){requestAnimationFrame(()=>chat.scrollTo({top:chat.scrollHeight,behavior:'smooth'}))}
function addMessage(text,who){if(empty)empty.remove();const row=document.createElement('div');row.className='msg '+who;const w=document.createElement('div');const meta=document.createElement('div');meta.className='meta';meta.textContent=who==='user'?'Você':'';const b=document.createElement('div');b.className='bubble';b.textContent=text;w.append(meta,b);row.append(w);chat.append(row);scrollBottom();return row}
function addLoading(){if(empty)empty.remove();const row=document.createElement('div');row.className='msg bot';const w=document.createElement('div');const b=document.createElement('div');b.className='bubble';b.innerHTML='<span class="loading"><i></i><i></i><i></i></span>';w.append(b);row.append(w);chat.append(row);scrollBottom();return row}
function resizeInput(){input.style.height='auto';input.style.height=Math.min(input.scrollHeight,112)+'px'}input.addEventListener('input',resizeInput);input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();form.requestSubmit()}});
form.addEventListener('submit',async e=>{e.preventDefault();if(busy)return;const message=input.value.trim();if(!message)return;addMessage(message,'user');input.value='';resizeInput();busy=true;send.disabled=true;const loading=addLoading();try{const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message,username:'SN7Fps'})});const data=await r.json();loading.remove();addMessage(data.reply||'⚠️ Sem resposta.','bot')}catch(err){loading.remove();addMessage('⚠️ Não foi possível conectar ao Baguncinha.','bot')}finally{busy=false;send.disabled=false;input.focus({preventScroll:true});scrollBottom()}});
function keyboardSafe(){const vv=window.visualViewport;if(!vv)return;const overlap=Math.max(0,window.innerHeight-vv.height-vv.offsetTop);wrap.style.bottom=overlap+'px';document.documentElement.style.setProperty('--composer',(wrap.offsetHeight+overlap)+'px');if(document.activeElement===input)setTimeout(scrollBottom,60)}if(window.visualViewport){visualViewport.addEventListener('resize',keyboardSafe);visualViewport.addEventListener('scroll',keyboardSafe)}window.addEventListener('resize',keyboardSafe);window.addEventListener('load',()=>{keyboardSafe();resizeInput()});
</script></body></html>'''

@app.get("/")
def home():
    return render_template_string(CHAT_HTML)

@app.get("/api")
def api_info():
    return jsonify({"ok": True, "service": "Baguncinha", "version": "3.0-worker", "worker_command_url": WORKER_COMMAND_URL})

@app.get("/health")
def health():
    return jsonify({"ok": True, "service": "baguncinha", "worker_configured": bool(WORKER_COMMAND_URL and WORKER_COMMAND_KEY), "version": "3.0-worker"})

@app.post("/chat")
def chat():
    data=request.get_json(silent=True) or {}
    message=str(data.get("message", "")).strip()
    username=str(data.get("username", "SN7Fps")).strip() or "SN7Fps"
    if not message:
        return jsonify({"ok": False, "reply": "Digite um comando.", "status": 400}), 200
    if not WORKER_COMMAND_KEY:
        app.logger.error("WORKER_COMMAND_KEY não configurada")
        return jsonify({"ok": False, "reply": "⚠️ Worker não configurado no Baguncinha.", "status": 500}), 200
    try:
        r=requests.post(WORKER_COMMAND_URL,headers={"X-Worker-Key":WORKER_COMMAND_KEY,"Content-Type":"application/json","Accept":"application/json"},json={"message":message,"username":username,"broadcaster_user_id":os.getenv("BROADCASTER_USER_ID","").strip()},timeout=TIMEOUT)
        try:data=r.json()
        except Exception:data={"reply":r.text.strip()}
        reply=str(data.get("reply") or "⚠️ O Worker não retornou resposta.")
        return jsonify({"ok":bool(data.get("ok",r.status_code<400)),"reply":reply,"status":int(data.get("status",r.status_code))}),200
    except requests.RequestException as exc:
        app.logger.warning("Worker request error: %s",exc)
        return jsonify({"ok":False,"reply":"⚠️ O Worker está acordando ou indisponível. Tente novamente em alguns segundos.","status":502}),200
    except Exception as exc:
        app.logger.exception("Chat error: %s",exc)
        return jsonify({"ok":False,"reply":"⚠️ Ocorreu um erro no Baguncinha.","status":500}),200

if __name__=="__main__":
    app.run(host="0.0.0.0",port=int(os.getenv("PORT","10000")))
