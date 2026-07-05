# Servidor de Seguridad Defensiva

Suite de herramientas para protección física y lógica de un servidor Linux mediante cifrado LUKS, control de dispositivos USB y switches de emergencia.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---
## Arquitectura general

```
USB llave presente ──────────────────────────────► Sistema armado (usbkill)
USB llave removida ──────────────────────────────► LUKS erase + reboot

Heartbeat /live cada <24h ───────────────────────► Deadman reseteado
Sin heartbeat por 24h ───────────────────────────► Alerta Discord (1h gracia)
Sin respuesta en 1h ─────────────────────────────► LUKS erase + reboot

Interfaz web /kill + token ──────────────────────► Kill manual inmediato

USB conectado ──► USBGuard bloquea ──► Web UI + token ──► usbguard allow-device
```

## Componentes

### `usbkill.sh` — USB Kill Switch
Monitorea la presencia de un dispositivo USB específico (identificado por UUID). Mientras el dispositivo esté conectado, el sistema está armado. Si se desconecta, ejecuta el borrado de claves LUKS y reinicia.

**Configurar antes de usar:**
- `KILL_UUID` → el UUID de tu USB llave (`lsblk -f` para obtenerlo)
- `WEBHOOK` → URL del webhook de Discord para notificaciones
- Descomentar las líneas de `cryptsetup` y `sysrq` con tu volumen correcto

---

### `deadman.sh` — Dead Man's Switch
Requiere que el operador confirme actividad cada 24 horas mediante un heartbeat. Si no se recibe señal en ese período, envía una alerta a Discord con 1 hora de gracia. Si tampoco se responde en esa hora, ejecuta el borrado de claves LUKS.

**Configurar antes de usar:**
- `WEBHOOK` → URL del webhook de Discord
- `WARNING_INTERVAL` → intervalo de heartbeat en segundos (default: 86400 = 24h)
- `KILL_AFTER` → período de gracia tras la alerta (default: 3600 = 1h)
- Descomentar las líneas de `cryptsetup` y `sysrq` con tu volumen correcto

> **Nota:** El archivo `WARNING_FILE` debe limpiarse manualmente si el servicio se reinicia inesperadamente, para evitar que el temporizador de gracia se dispare de inmediato.

---

### `heartbeat_server.py` — Servidor de Heartbeat
Servidor Flask que expone dos endpoints para interactuar con el dead man's switch.

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/live` | GET | Registra un heartbeat y resetea el timer del deadman |
| `/status` | GET | Muestra cuándo fue el último heartbeat recibido |

**Configurar antes de usar:**
- `WEBHOOK` → URL del webhook de Discord
- `HOST` → cambiar `0.0.0.0` por la IP de Tailscale
- Puerto por defecto: `8888`

---

### `manual_kill.py` — Kill Switch Manual
Servidor Flask con interfaz web para ejecutar el borrado de claves LUKS de forma manual, autenticado por token.

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Interfaz web del kill switch |
| `/kill` | POST | Ejecuta el borrado (requiere token) |

**Configurar antes de usar:**
- `TOKEN` → reemplazar `"1234"` por un token fuerte
- `WEBHOOK` → URL del webhook de Discord
- `HOST` → cambiar `0.0.0.0` por la IP de Tailscale
- Puerto por defecto: `5463`
- Descomentar las líneas de `cryptsetup` y `sysrq` con tu volumen correcto

---

### `usb_auth_server_v2.py` — Control de Acceso USB (USBGuard)
Servidor Flask con interfaz web para autorizar dispositivos USB bloqueados por USBGuard. Requiere token para aprobar cada dispositivo.

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Interfaz web de autorización |
| `/api/devices` | GET | Lista dispositivos bloqueados |
| `/api/allowed` | GET | Lista dispositivos autorizados |
| `/api/allow` | POST | Autoriza un dispositivo (requiere token) |

**Configurar antes de usar:**
- `TOKEN` → reemplazar `"1234"` por un token fuerte
- `HOST` → cambiar `0.0.0.0` por la IP de Tailscale
- Puerto por defecto: `5555`
- Revisar la lista de exclusiones en `get_allowed_devices()` — está ajustada al hardware del autor, puede necesitar cambios según tu máquina

> **Nota:** La autorización es solo por sesión. Para persistencia agregar el flag `-p` en `allow_device()`.

---

### `setup_services.sh` — Instalación de Servicios
Crea e instala todos los componentes como servicios de systemd y los activa.

```bash
sudo bash setup_services.sh
```

Copia los scripts a `/usr/local/bin/` antes de ejecutar:

```bash
sudo cp usbkill.sh deadman.sh /usr/local/bin/
sudo cp heartbeat_server.py manual_kill.py usb_auth_server_v2.py /usr/local/bin/
sudo bash setup_services.sh
```

> Todos los servicios corren como `root` — necesario para acceso a `cryptsetup` y `sysrq`.

---

## Dependencias

```bash
pip install flask
apt install usbguard cryptsetup curl
```

---

## Notas de seguridad

- Exponer estos servicios solo vía **Tailscale / VPN**, nunca a internet
- Cambiar todos los tokens por valores fuertes antes de producción
- Verificar el volumen LUKS correcto (`/dev/sda3` es un placeholder) antes de descomentar los comandos destructivos
- Las operaciones de borrado son **irreversibles**
