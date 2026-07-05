#!/usr/bin/env python3
"""
USB Authorization Server — USBGuard
Flujo: dispositivo conectado → USBGuard bloquea → usuario entra a la webapp
       → selecciona dispositivo → ingresa token → se autoriza con usbguard allow-device
"""

from flask import Flask, request, jsonify, Response
import subprocess
import re
import os

app = Flask(__name__)

# ── CONFIG ────────────────────────────────────────────────────────────────────
HOST  = "0.0.0.0"  # direccion de la webapp, 0.0.0.0 escucha todas las interfaces, se recomienda cambiar por ip de taiscale
PORT  = 5555    # puerto de la webapp
TOKEN = "1234"  # clave para autorizar el dispositivo
# ─────────────────────────────────────────────────────────────────────────────


# ── HTML EMBEBIDO ─────────────────────────────────────────────────────────────
HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CONTROL DE ACCESO USB</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@300;400;500;600&family=Barlow:wght@300;400&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:      #F0EFED;
    --surface: #FAFAF8;
    --ink:     #111010;
    --mid:     #6B6B6B;
    --rule:    #D4D3D0;
    --accent:  #E8B800;
    --danger:  #CC2200;
    --green:   #1A7A3A;
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
  }

  .panel {
    background: var(--surface);
    border: 1px solid var(--rule);
    width: 100%;
    max-width: 480px;
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

  .indicator {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--accent);
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
  }

  .info-row .val {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 13px;
    font-weight: 500;
    letter-spacing: 1px;
    color: var(--ink);
  }

  .info-row .val.accent { color: var(--accent); }

  /* ── Lista de dispositivos bloqueados ── */
  #devices-section {
    margin-bottom: 24px;
  }

  .section-label {
    font-size: 10px;
    letter-spacing: 2.5px;
    text-transform: uppercase;
    color: var(--mid);
    margin-bottom: 10px;
  }

  #devices-list {
    border: 1px solid var(--rule);
    min-height: 56px;
    display: flex;
    flex-direction: column;
    gap: 0;
  }

  .device-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    border-bottom: 1px solid var(--rule);
    cursor: pointer;
    transition: background 0.1s;
    gap: 12px;
  }

  .device-row:last-child { border-bottom: none; }

  .device-row:hover { background: var(--bg); }

  .device-row.selected {
    background: var(--ink);
    color: var(--bg);
  }

  .device-row.selected .dev-port { color: var(--accent); }

  .dev-name {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 14px;
    font-weight: 500;
    letter-spacing: 1px;
    flex: 1;
  }

  .dev-port {
    font-size: 10px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--mid);
    white-space: nowrap;
  }

  .empty-msg {
    font-size: 11px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--rule);
    text-align: center;
    padding: 16px;
    align-self: center;
    width: 100%;
  }

  /* ── Confirm section ── */
  #confirm-section {
    display: none;
    flex-direction: column;
    gap: 10px;
    animation: slideIn 0.2s ease;
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

  #btn-allow {
    background: var(--ink);
    color: var(--bg);
    border: 1px solid var(--ink);
  }

  #btn-allow:hover:not(:disabled) { background: #2a2a2a; }
  #btn-allow:disabled { opacity: 0.35; cursor: not-allowed; }

  #btn-cancel {
    background: transparent;
    border: 1px solid var(--rule);
    color: var(--mid);
    font-size: 11px;
    letter-spacing: 2px;
    padding: 10px 20px;
  }

  #btn-cancel:hover { border-color: var(--mid); color: var(--ink); }

  #btn-refresh {
    background: transparent;
    border: 1px solid var(--rule);
    color: var(--mid);
    font-size: 10px;
    letter-spacing: 2px;
    padding: 8px 14px;
    cursor: pointer;
    font-family: 'Barlow Condensed', sans-serif;
    text-transform: uppercase;
    transition: all 0.15s;
    margin-bottom: 8px;
    width: 100%;
  }

  #btn-refresh:hover { border-color: var(--mid); color: var(--ink); }

  #status {
    margin-top: 16px;
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
<div class="site-header"></div>

<div class="panel">
  <div class="panel-label">
    <span>Control de Acceso USB — USBGuard</span>
    <div class="indicator"></div>
  </div>

  <div class="panel-body">
    <div class="symbol">Autorización Manual</div>
    <h1>USB<br>Guard</h1>

    <div class="info-block">
      <div class="info-row">
        <span class="key">Política por defecto</span>
        <span class="val">Bloquear</span>
      </div>
      <div class="info-row">
        <span class="key">Modo</span>
        <span class="val">Manual — token requerido</span>
      </div>
      <div class="info-row">
        <span class="key">Persistencia</span>
        <span class="val accent">Solo sesión</span>
      </div>
    </div>

    <div id="devices-section">
      <div class="section-label">Dispositivos bloqueados</div>
      <div id="devices-list">
        <div class="empty-msg" id="empty-msg">Cargando...</div>
      </div>
      <button id="btn-refresh" onclick="loadDevices()" style="margin-top:8px;">↻ Actualizar</button>
    </div>

    <div id="confirm-section">
      <label>Token de confirmación</label>
      <input type="password" id="token-input" placeholder="••••••••••" autocomplete="off" spellcheck="false">
      <button class="btn" id="btn-allow" onclick="authorizeDevice()">
        Autorizar dispositivo
      </button>
      <button class="btn" id="btn-cancel" onclick="cancelAuth()">Cancelar</button>
    </div>

    <div id="status"></div>

    <div id="allowed-section" style="margin-top:28px;">
      <div class="section-label">Dispositivos permitidos</div>
      <div id="allowed-list">
        <div class="empty-msg">Cargando...</div>
      </div>
    </div>
  </div>

  <div class="panel-footer">
    <span class="ts" id="ts"></span>
    <span class="version">v1.0</span>
  </div>
</div>

<script>
  let selectedDeviceId = null;

  function updateTS() {
    document.getElementById('ts').textContent = new Date().toISOString();
  }
  updateTS();
  setInterval(updateTS, 1000);

  async function loadDevices() {
    const list = document.getElementById('devices-list');
    const empty = document.getElementById('empty-msg');
    list.innerHTML = '<div class="empty-msg">Consultando USBGuard...</div>';
    cancelAuth(true);

    try {
      const res = await fetch('/api/devices');
      const data = await res.json();

      if (data.status === 'error') {
        list.innerHTML = '<div class="empty-msg" style="color:var(--danger)">' + data.message + '</div>';
        return;
      }

      if (!data.devices || data.devices.length === 0) {
        list.innerHTML = '<div class="empty-msg">Sin dispositivos bloqueados</div>';
        setStatus('', '');
        return;
      }

      list.innerHTML = '';
      data.devices.forEach(dev => {
        const row = document.createElement('div');
        row.className = 'device-row';
        row.dataset.id = dev.id;
        row.innerHTML = `
          <span class="dev-name">${dev.name}</span>
          <span class="dev-port">Puerto ${dev.via}</span>
        `;
        row.onclick = () => selectDevice(dev.id, dev.name, row);
        list.appendChild(row);
      });

      setStatus('', '');
    } catch (e) {
      list.innerHTML = '<div class="empty-msg" style="color:var(--danger)">Error de conexión</div>';
      setStatus('Error de conexión', 'error');
    }
  }

  function selectDevice(id, name, rowEl) {
    // Deseleccionar anterior
    document.querySelectorAll('.device-row').forEach(r => r.classList.remove('selected'));
    rowEl.classList.add('selected');
    selectedDeviceId = id;

    // Mostrar confirm
    const cs = document.getElementById('confirm-section');
    cs.style.display = 'flex';
    document.getElementById('token-input').focus();
    setStatus('Dispositivo seleccionado — ingresá el token para autorizar', '');
  }

  function cancelAuth(silent) {
    selectedDeviceId = null;
    document.querySelectorAll('.device-row').forEach(r => r.classList.remove('selected'));
    document.getElementById('confirm-section').style.display = 'none';
    document.getElementById('token-input').value = '';
    document.getElementById('btn-allow').disabled = false;
    if (!silent) setStatus('', '');
  }

  function setStatus(msg, cls) {
    const el = document.getElementById('status');
    el.textContent = msg;
    el.className = cls;
  }

  async function authorizeDevice() {
    if (!selectedDeviceId) { setStatus('Seleccioná un dispositivo primero', 'error'); return; }
    const token = document.getElementById('token-input').value.trim();
    if (!token) { setStatus('Token requerido', 'error'); return; }

    document.getElementById('btn-allow').disabled = true;
    setStatus('Autorizando...', '');

    try {
      const res = await fetch('/api/allow', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, device_id: selectedDeviceId })
      });

      const data = await res.json();

      if (res.ok && data.status === 'ok') {
        setStatus('Dispositivo autorizado correctamente', 'ok');
        cancelAuth(true);
        setTimeout(() => { loadDevices(); loadAllowed(); }, 1200);
      } else {
        setStatus('Error: ' + (data.message || 'respuesta inválida'), 'error');
        document.getElementById('btn-allow').disabled = false;
      }
    } catch (e) {
      setStatus('Error de conexión: ' + e.message, 'error');
      document.getElementById('btn-allow').disabled = false;
    }
  }

  async function loadAllowed() {
    const list = document.getElementById('allowed-list');
    list.innerHTML = '<div class="empty-msg">Consultando USBGuard...</div>';
    try {
      const res = await fetch('/api/allowed');
      const data = await res.json();
      if (data.status === 'error') {
        list.innerHTML = '<div class="empty-msg" style="color:var(--danger)">' + data.message + '</div>';
        return;
      }
      if (!data.devices || data.devices.length === 0) {
        list.innerHTML = '<div class="empty-msg">Sin dispositivos permitidos</div>';
        return;
      }
      list.innerHTML = '';
      data.devices.forEach(dev => {
        const row = document.createElement('div');
        row.className = 'device-row';
        row.style.cursor = 'default';
        row.innerHTML = `
          <span class="dev-name">${dev.name}</span>
          <span class="dev-port">Puerto ${dev.via}</span>
        `;
        list.appendChild(row);
      });
    } catch (e) {
      list.innerHTML = '<div class="empty-msg" style="color:var(--danger)">Error de conexión</div>';
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    loadDevices();
    loadAllowed();
    document.getElementById('token-input').addEventListener('keydown', e => {
      if (e.key === 'Enter') authorizeDevice();
    });
  });
</script>
</body>
</html>"""
# ─────────────────────────────────────────────────────────────────────────────


def get_blocked_devices():
    """
    Ejecuta `usbguard list-devices` y devuelve solo los bloqueados.
    """
    try:
        result = subprocess.run(
            ["usbguard", "list-devices"],
            capture_output=True, text=True, timeout=5
        )
        devices = []
        for line in result.stdout.splitlines():
            if "block" not in line:
                continue
            m = re.match(r'^(\d+)', line)
            if not m:
                continue
            dev_id = m.group(1)
            devices.append({
                "id":   dev_id,
                "name": extract_name(line),
                "via":  extract_via(line),
                "raw":  line.strip()
            })
        return devices
    except FileNotFoundError:
        return {"error": "usbguard no encontrado"}
    except subprocess.TimeoutExpired:
        return {"error": "timeout al consultar usbguard"}
    except Exception as e:
        return {"error": str(e)}


def extract_name(line):
    m = re.search(r'name\s+"([^"]+)"', line)
    if m:
        return m.group(1)
    m2 = re.search(r'id\s+([\w:]+)', line)
    return m2.group(1) if m2 else "Dispositivo USB"


def extract_via(line):
    m = re.search(r'via-port\s+"([^"]+)"', line)
    return m.group(1) if m else "USB"


def get_allowed_devices():
    """
    Ejecuta `usbguard list-devices` y devuelve solo los permitidos (excluye controladores internos).
    """
    try:
        result = subprocess.run(
            ["usbguard", "list-devices"],
            capture_output=True, text=True, timeout=5
        )
        devices = []
        for line in result.stdout.splitlines():
            if "allow" not in line:
                continue
            # Excluir controladores xHCI internos y hubs del sistema (AJUSTAR)
            if any(x in line for x in ["xHCI Host Controller", "USB2.0 Hub", "USB 2.0 Camera", "Bluetooth Radio", "USB2.0-CRW", "MDTV Receiver"]):
                continue
            m = re.match(r'^(\d+)', line)
            if not m:
                continue
            dev_id = m.group(1)
            devices.append({
                "id":   dev_id,
                "name": extract_name(line),
                "via":  extract_via(line),
            })
        return devices
    except FileNotFoundError:
        return {"error": "usbguard no encontrado"}
    except subprocess.TimeoutExpired:
        return {"error": "timeout al consultar usbguard"}
    except Exception as e:
        return {"error": str(e)}


def allow_device(device_id):
    """
    Autoriza el dispositivo para esta sesión.
    Para persistencia agregar flag -p: ["usbguard", "allow-device", "-p", str(device_id)]
    """
    try:
        result = subprocess.run(
            ["usbguard", "allow-device", str(device_id)],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return True, "ok"
        else:
            return False, result.stderr.strip() or "error desconocido"
    except subprocess.TimeoutExpired:
        return False, "timeout al ejecutar allow-device"
    except Exception as e:
        return False, str(e)


# ── CORS ──────────────────────────────────────────────────────────────────────
@app.after_request
def add_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


# ── RUTAS ─────────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET"])
def index():
    return Response(HTML, mimetype="text/html")


@app.route("/api/devices", methods=["GET"])
def api_devices():
    devices = get_blocked_devices()
    if isinstance(devices, dict) and "error" in devices:
        return jsonify({"status": "error", "message": devices["error"]}), 500
    return jsonify({"status": "ok", "devices": devices})


@app.route("/api/allowed", methods=["GET"])
def api_allowed():
    devices = get_allowed_devices()
    if isinstance(devices, dict) and "error" in devices:
        return jsonify({"status": "error", "message": devices["error"]}), 500
    return jsonify({"status": "ok", "devices": devices})


@app.route("/api/allow", methods=["POST"])
def api_allow():
    data      = request.get_json(silent=True) or {}
    token     = data.get("token", "")
    device_id = data.get("device_id", "")

    if token != TOKEN:
        return jsonify({"status": "error", "message": "token inválido"}), 403

    if not re.match(r'^\d+$', str(device_id)):
        return jsonify({"status": "error", "message": "device_id inválido"}), 400

    ok, msg = allow_device(device_id)
    if ok:
        return jsonify({"status": "ok", "message": f"dispositivo {device_id} autorizado"})
    else:
        return jsonify({"status": "error", "message": msg}), 500


if __name__ == "__main__":
    print(f"USB Auth Server corriendo en http://{HOST}:{PORT}")
    app.run(host=HOST, port=PORT)
