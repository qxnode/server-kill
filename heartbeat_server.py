from flask import Flask, jsonify
import os
import time

app = Flask(__name__)

# ── CORS ──────────────────────────────────────────────────────────────────────
@app.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response
# ─────────────────────────────────────────────────────────────────────────────

HEARTBEAT_FILE = "/var/run/deadman_heartbeat"
WARNING_FILE = "/var/run/deadman_warning_sent"
WEBHOOK = "discord_webhook_aca"

def send_discord(msg):
    os.system(f'curl -s -X POST "{WEBHOOK}" -H "Content-Type: application/json" -d \'{{"content": "{msg}"}}\' ')

def tiempo_legible(segundos):
    if segundos < 60:
        return f"{segundos} segundos"
    elif segundos < 3600:
        minutos = segundos // 60
        segs = segundos % 60
        return f"{minutos} minutos y {segs} segundos"
    else:
        horas = segundos // 3600
        minutos = (segundos % 3600) // 60
        segs = segundos % 60
        return f"{horas} horas, {minutos} minutos y {segs} segundos"

@app.route('/live', methods=['GET'])
def live():
    with open(HEARTBEAT_FILE, "w") as f:
        f.write(str(int(time.time())))
    if os.path.exists(WARNING_FILE):
        os.remove(WARNING_FILE)
    send_discord("✅ Heartbeat confirmado - Sistema activo")
    return jsonify({"status": "ok", "timestamp": int(time.time())})

@app.route('/status', methods=['GET'])
def status():
    if os.path.exists(HEARTBEAT_FILE):
        last = int(open(HEARTBEAT_FILE).read())
        diff = int(time.time()) - last
        return jsonify({"ultimo_heartbeat": f"hace {tiempo_legible(diff)}"})
    return jsonify({"status": "no heartbeat registrado"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8888)  # 0.0.0.0 escucha todas las interfaces, se recomienda cambiar por ip de taiscale