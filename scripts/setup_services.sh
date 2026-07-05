#!/bin/bash

cat > /etc/systemd/system/usbkill.service << 'EOF'
[Unit]
Description=USB Kill Switch
After=network.target

[Service]
ExecStart=/bin/bash /usr/local/bin/usbkill.sh
Restart=always
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/deadman.service << 'EOF'
[Unit]
Description=Dead Man Switch
After=network.target heartbeat.service
Requires=heartbeat.service

[Service]
ExecStart=/bin/bash /usr/local/bin/deadman.sh
Restart=always
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/heartbeat.service << 'EOF'
[Unit]
Description=Heartbeat Server
After=network.target

[Service]
ExecStart=/usr/bin/python3 /usr/local/bin/heartbeat_server.py
Restart=always
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/manualkill.service << 'EOF'
[Unit]
Description=Manual Kill Switch
After=network.target

[Service]
ExecStart=/usr/bin/python3 /usr/local/bin/manual_kill.py
Restart=always
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/usb-auth.service << 'EOF'
[Unit]
Description=USB Auth Server - USBGuard
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 /usr/local/bin/usb_auth_server_v2.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now usbkill deadman heartbeat manualkill usb-auth
echo "Servicios instalados y activos"