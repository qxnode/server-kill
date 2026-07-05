#!/bin/bash
KILL_UUID="UUID_de_tu_dispositivo" # obtenelo con lsblk -f  
WEBHOOK="discord_webhook_aca"

send_discord() {
    curl -s -X POST "$WEBHOOK" -H "Content-Type: application/json" -d "{\"content\": \"$1\"}"
}

echo "Esperando USB llave..."
while ! lsblk -o UUID | grep -q "$KILL_UUID"; do
    sleep 3
done
echo "USB detectado - sistema ARMADO"
send_discord "✅ USBKILL ARMADO - Sistema protegido"
while true; do
    if ! lsblk -o UUID | grep -q "$KILL_UUID"; then
        send_discord "🔴 USBKILL ACTIVADO - Borrando claves LUKS..."
        sleep 2
        # cryptsetup luksErase /dev/sda3 --batch-mode       # cambia /dev/sda3 por tu volumen LUKS
        # echo 1 > /proc/sys/kernel/sysrq
        # echo b > /proc/sysrq-trigger
    fi
    sleep 3
done