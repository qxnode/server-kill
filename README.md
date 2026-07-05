# Defensive Security Server

A toolkit for physical and logical protection of a Linux server using LUKS encryption, USB device control, and emergency kill switches.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[🇪🇸 Versión en Español](README.es.md)

---

## Architecture

```
USB key present ─────────────────────────────────► System armed (usbkill)
USB key removed ─────────────────────────────────► LUKS erase + reboot

Heartbeat /live every <24h ──────────────────────► Deadman reset
No heartbeat for 24h ────────────────────────────► Discord alert (1h grace period)
No response in 1h ───────────────────────────────► LUKS erase + reboot

Web UI /kill + token ────────────────────────────► Immediate manual kill

USB connected ──► USBGuard blocks ──► Web UI + token ──► usbguard allow-device
```

## Components

### `usbkill.sh` — USB Kill Switch
Monitors the presence of a specific USB device (identified by UUID). While the device is connected, the system is armed. If it is unplugged, LUKS keys are wiped and the system reboots.

**Configure before use:**
- `KILL_UUID` → UUID of your USB key (`lsblk -f` to get it)
- `WEBHOOK` → Discord webhook URL for notifications
- Uncomment the `cryptsetup` and `sysrq` lines with your correct volume

---

### `deadman.sh` — Dead Man's Switch
Requires the operator to confirm activity every 24 hours via a heartbeat. If no signal is received within that period, a Discord alert is sent with a 1-hour grace period. If there is still no response, LUKS keys are wiped and the system reboots.

**Configure before use:**
- `WEBHOOK` → Discord webhook URL
- `WARNING_INTERVAL` → heartbeat interval in seconds (default: 86400 = 24h)
- `KILL_AFTER` → grace period after alert (default: 3600 = 1h)
- Uncomment the `cryptsetup` and `sysrq` lines with your correct volume

> **Note:** The `WARNING_FILE` must be manually cleared if the service restarts unexpectedly, to prevent the grace period timer from firing immediately.

---

### `heartbeat_server.py` — Heartbeat Server
Flask server exposing two endpoints to interact with the dead man's switch.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/live` | GET | Registers a heartbeat and resets the deadman timer |
| `/status` | GET | Shows when the last heartbeat was received |

**Configure before use:**
- `WEBHOOK` → Discord webhook URL
- `HOST` → replace `0.0.0.0` with your Tailscale IP
- Default port: `8888`

---

### `manual_kill.py` — Manual Kill Switch
Flask server with a web interface to manually wipe LUKS keys, authenticated by token.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Kill switch web interface |
| `/kill` | POST | Executes the wipe (requires token) |

**Configure before use:**
- `TOKEN` → replace `"1234"` with a strong token
- `WEBHOOK` → Discord webhook URL
- `HOST` → replace `0.0.0.0` with your Tailscale IP
- Default port: `5463`
- Uncomment the `cryptsetup` and `sysrq` lines with your correct volume

---

### `usb_auth_server_v2.py` — USB Access Control (USBGuard)
Flask server with a web interface to authorize USB devices blocked by USBGuard. Requires a token to approve each device.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Authorization web interface |
| `/api/devices` | GET | Lists blocked devices |
| `/api/allowed` | GET | Lists authorized devices |
| `/api/allow` | POST | Authorizes a device (requires token) |

**Configure before use:**
- `TOKEN` → replace `"1234"` with a strong token
- `HOST` → replace `0.0.0.0` with your Tailscale IP
- Default port: `5555`
- Review the exclusion list in `get_allowed_devices()` — it is tuned to the author's hardware and may need adjustments for your machine

> **Note:** Authorization is session-only. For persistence, add the `-p` flag in `allow_device()`.

---

### `setup_services.sh` — Service Installer
Creates and installs all components as systemd services and enables them.

```bash
sudo bash setup_services.sh
```

Copy the scripts to `/usr/local/bin/` before running:

```bash
sudo cp usbkill.sh deadman.sh /usr/local/bin/
sudo cp heartbeat_server.py manual_kill.py usb_auth_server_v2.py /usr/local/bin/
sudo bash setup_services.sh
```

> All services run as `root` — required for access to `cryptsetup` and `sysrq`.

---

## Dependencies

```bash
pip install flask
apt install usbguard cryptsetup curl
```

---

## Security Notes

- Expose these services only via **Tailscale / VPN**, never to the internet
- Replace all tokens with strong values before deploying
- Verify the correct LUKS volume (`/dev/sda3` is a placeholder) before uncommenting destructive commands
- Wipe operations are **irreversible**
