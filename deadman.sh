#!/bin/bash

HEARTBEAT_FILE="/var/run/deadman_heartbeat"
WARNING_FILE="/var/run/deadman_warning_sent"
WEBHOOK="discord_webhook_aca"
WARNING_INTERVAL=86400          # reporte cada 24 horas, sino:
KILL_AFTER=3600               # periodo de gracia de 1 hora para reportarte

send_discord() {
    curl -s -X POST "$WEBHOOK" -H "Content-Type: application/json" -d "{\"content\": \"$1\"}"
}

if [ ! -f "$HEARTBEAT_FILE" ]; then
    date +%s > "$HEARTBEAT_FILE"
fi

while true; do
    NOW=$(date +%s)
    LAST=$(cat "$HEARTBEAT_FILE")
    DIFF=$((NOW - LAST))

    if [ $DIFF -gt $WARNING_INTERVAL ] && [ ! -f "$WARNING_FILE" ]; then
        send_discord "⚠️ DEADMAN - No se detectó heartbeat, confirmá que estas vivo. Tenés 1 hora."
        date +%s > "$WARNING_FILE"
    fi

    if [ -f "$WARNING_FILE" ]; then
        WARN_TIME=$(cat "$WARNING_FILE")
        WARN_DIFF=$((NOW - WARN_TIME))
        if [ $WARN_DIFF -gt $KILL_AFTER ]; then
            send_discord "🔴 DEADMAN EJECUTADO - Borrando claves LUKS..."
            sleep 2
        # cryptsetup luksErase /dev/sda3 --batch-mode       # cambia /dev/sda3 por tu volumen LUKS
        # echo 1 > /proc/sys/kernel/sysrq
        # echo b > /proc/sysrq-trigger
        fi
    fi

    sleep 10
done