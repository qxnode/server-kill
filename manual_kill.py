#!/usr/bin/env python3
from flask import Flask, request, jsonify, Response
import os
import time

app = Flask(__name__)

# ── CONFIG ────────────────────────────────────────────────────────────────────
HOST    = "0.0.0.0"   # 0.0.0.0 escucha todas las interfaces, se recomienda cambiar por ip de taiscale
PORT    = 5463         
TOKEN   = "1234"  # usar token mas fuerte
WEBHOOK = "discord_webhook_aca"
# ─────────────────────────────────────────────────────────────────────────────

HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>KILL SWITCH</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;500;600&family=Barlow:wght@300;400&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:       #F0EFED;
    --surface:  #FAFAF8;
    --ink:      #111010;
    --mid:      #6B6B6B;
    --rule:     #D4D3D0;
    --accent:   #E8B800;
    --danger:   #CC2200;
    --green:    #1A7A3A;
  }

  body {
    background: var(--bg);
    color: var(--ink);
    font-family: 'Barlow', 'Helvetica Neue', Helvetica, Arial, sans-serif;
    font-weight: 300;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  .site-header {
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--accent);
    transition: background 0.4s ease;
  }

  body.armed .site-header { background: var(--danger); }

  .panel {
    background: var(--surface);
    border: 1px solid var(--rule);
    width: 100%;
    max-width: 440px;
    padding: 0;
    position: relative;
  }

  .panel-label {
    border-bottom: 1px solid var(--rule);
    padding: 10px 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .panel-label span {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--mid);
  }

  .panel-label .indicator {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--accent);
    transition: background 0.4s ease;
  }

  body.armed .panel-label .indicator {
    background: var(--danger);
    box-shadow: 0 0 0 3px rgba(204,34,0,0.15);
  }

  .panel-body { padding: 40px 28px 32px; }

  .symbol {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: var(--mid);
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .symbol::before {
    content: '';
    display: block;
    width: 20px; height: 1px;
    background: var(--mid);
  }

  h1 {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 52px;
    font-weight: 600;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--ink);
    line-height: 1;
    margin-bottom: 28px;
  }

  .info-block {
    border-top: 1px solid var(--rule);
    border-bottom: 1px solid var(--rule);
    padding: 18px 0;
    margin-bottom: 28px;
  }

  .info-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding: 4px 0;
  }

  .info-row .key {
    font-size: 11px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--mid);
    font-weight: 400;
  }

  .info-row .val {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 13px;
    font-weight: 500;
    letter-spacing: 1px;
    color: var(--ink);
    text-align: right;
  }

  .info-row .val.danger { color: var(--danger); }

  .btn {
    border: none;
    cursor: pointer;
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 13px;
    font-weight: 500;
    letter-spacing: 3px;
    text-transform: uppercase;
    padding: 13px 20px;
    width: 100%;
    transition: all 0.15s;
    display: block;
  }

  #btn-arm {
    background: var(--ink);
    color: var(--bg);
    border: 1px solid var(--ink);
  }

  #btn-arm:hover { background: #2a2a2a; }

  #confirm-section {
    display: none;
    flex-direction: column;
    gap: 10px;
    animation: slideIn 0.25s ease;
  }

  @keyframes slideIn {
    from { opacity: 0; transform: translateY(-6px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  #confirm-section label {
    font-size: 10px;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--mid);
  }

  #token-input {
    background: var(--bg);
    border: 1px solid var(--rule);
    border-radius: 0;
    color: var(--ink);
    font-family: 'Barlow Condensed', monospace;
    font-size: 15px;
    font-weight: 400;
    padding: 12px 14px;
    letter-spacing: 3px;
    outline: none;
    transition: border-color 0.2s;
    width: 100%;
  }

  #token-input:focus { border-color: var(--ink); }
  #token-input::placeholder { color: var(--rule); letter-spacing: 2px; }

  #btn-kill {
    background: var(--danger);
    color: #fff;
    border: 1px solid var(--danger);
  }

  #btn-kill:hover:not(:disabled) {
    background: #a81c00;
    border-color: #a81c00;
  }

  #btn-kill:disabled { opacity: 0.35; cursor: not-allowed; }

  #btn-cancel {
    background: transparent;
    border: 1px solid var(--rule);
    color: var(--mid);
    font-size: 11px;
    letter-spacing: 2px;
    padding: 10px 20px;
  }

  #btn-cancel:hover { border-color: var(--mid); color: var(--ink); }

  #status {
    margin-top: 20px;
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    min-height: 16px;
    color: var(--mid);
  }

  #status.ok    { color: var(--green); }
  #status.error { color: var(--danger); }

  .panel-footer {
    border-top: 1px solid var(--rule);
    padding: 12px 28px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .panel-footer .ts {
    font-size: 10px;
    letter-spacing: 1.5px;
    color: var(--rule);
    font-family: 'Barlow Condensed', monospace;
  }

  .panel-footer .version {
    font-size: 10px;
    letter-spacing: 1.5px;
    color: var(--rule);
    font-family: 'Barlow Condensed', sans-serif;
    text-transform: uppercase;
  }
</style>
</head>
<body>
<div class="site-header" id="header-strip"></div>

<div class="panel">
  <div class="panel-label">
    <span>Sistema de Eliminación Segura</span>
    <div class="indicator"></div>
  </div>

  <div class="panel-body">
    <div class="symbol">Cifrado LUKS</div>
    <h1>Kill<br>Switch</h1>

    <div class="info-block">
      <div class="info-row">
        <span class="key">Alcance</span>
        <span class="val">Todos los volúmenes LUKS</span>
      </div>
      <div class="info-row">
        <span class="key">Operación</span>
        <span class="val">Borrado de claves</span>
      </div>
      <div class="info-row">
        <span class="key">Recuperación</span>
        <span class="val danger">Imposible</span>
      </div>
      <div class="info-row">
        <span class="key">Confirmación</span>
        <span class="val">Token requerido</span>
      </div>
    </div>

    <button class="btn" id="btn-arm" onclick="arm()">
      Activar secuencia de destrucción
    </button>

    <div id="confirm-section">
      <label>Token de confirmación</label>
      <input type="text" id="token-input" placeholder="••••••••••" autocomplete="off" spellcheck="false">
      <button class="btn" id="btn-kill" onclick="executeKill()">
        Destruir ahora
      </button>
      <button class="btn" id="btn-cancel" onclick="cancel()">Cancelar</button>
    </div>

    <div id="status"></div>
  </div>

  <div class="panel-footer">
    <span class="ts" id="ts"></span>
    <span class="version">v2.1</span>
  </div>
</div>

<script>
  function updateTS() {
    document.getElementById('ts').textContent = new Date().toISOString();
  }
  updateTS();
  setInterval(updateTS, 1000);

  function arm() {
    document.body.classList.add('armed');
    document.getElementById('btn-arm').style.display = 'none';
    const cs = document.getElementById('confirm-section');
    cs.style.display = 'flex';
    document.getElementById('token-input').focus();
    setStatus('Armado \u2014 ingres\u00e1 el token para confirmar', '');
  }

  function cancel() {
    document.body.classList.remove('armed');
    document.getElementById('btn-arm').style.display = 'block';
    document.getElementById('confirm-section').style.display = 'none';
    document.getElementById('token-input').value = '';
    setStatus('', '');
  }

  function setStatus(msg, cls) {
    const el = document.getElementById('status');
    el.textContent = msg;
    el.className = cls;
  }

  async function executeKill() {
    const token = document.getElementById('token-input').value.trim();
    if (!token) { setStatus('Token requerido', 'error'); return; }

    document.getElementById('btn-kill').disabled = true;
    setStatus('Enviando orden de destrucci\u00f3n...', '');

    try {
      const res = await fetch('/kill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token })
      });

      const data = await res.json();

      if (res.ok && data.status === 'ok') {
        setStatus('Destrucci\u00f3n ejecutada \u2014 ' + data.message, 'ok');
        document.getElementById('confirm-section').style.display = 'none';
        document.body.classList.remove('armed');
      } else {
        setStatus('Error: ' + (data.message || 'respuesta inv\u00e1lida'), 'error');
        document.getElementById('btn-kill').disabled = false;
      }
    } catch (e) {
      setStatus('Error de conexi\u00f3n: ' + e.message, 'error');
      document.getElementById('btn-kill').disabled = false;
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('token-input').addEventListener('keydown', e => {
      if (e.key === 'Enter') executeKill();
    });
  });
</script>
</body>
</html>"""


# agrega CORS de ser necesario

# ── CORS ──────────────────────────────────────────────────────────────────────
# @app.after_request
# def add_cors(response):
#     response.headers['Access-Control-Allow-Origin'] = '*'           
#     return response
# ─────────────────────────────────────────────────────────────────────────────


def send_discord(msg):
    os.system(f'curl -s -X POST "{WEBHOOK}" -H "Content-Type: application/json" -d \'{{"content": "{msg}"}}\' ')


@app.route('/', methods=['GET'])
def index():
    return Response(HTML, mimetype='text/html')


@app.route('/kill', methods=['POST'])
def kill():
    data = request.get_json(silent=True) or {}
    token = data.get('token', '')

    if token != TOKEN:
        return jsonify({"status": "error", "message": "token inválido"}), 403

    send_discord("🔴 KILL MANUAL EJECUTADO - Borrando claves LUKS...")
    time.sleep(2)

    # os.system("cryptsetup luksErase /dev/sda3 --batch-mode")    # cambia /dev/sda3 por tu volumen LUKS
    # os.system("echo 1 > /proc/sys/kernel/sysrq")
    # os.system("echo b > /proc/sysrq-trigger")

    return jsonify({"status": "ok", "message": "claves borradas, reiniciando"})


if __name__ == '__main__':
    app.run(host=HOST, port=PORT)
