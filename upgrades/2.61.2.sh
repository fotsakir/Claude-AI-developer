#!/bin/bash
# Upgrade to version 2.61.2
# Fixes systemd service files (user permissions)

log_info() { echo -e "\033[0;36m[2.61.2]\033[0m $1"; }

CLAUDE_USER="claude"
INSTALL_DIR="/opt/codehero"

# Update daemon service if user is wrong
if grep -q "User=claude-worker" /etc/systemd/system/codehero-daemon.service 2>/dev/null; then
    log_info "Fixing codehero-daemon.service user..."

    cat > /etc/systemd/system/codehero-daemon.service << SVCEOF
[Unit]
Description=CodeHero Daemon
After=network.target mysql.service codehero-web.service
Wants=mysql.service

[Service]
Type=simple
User=${CLAUDE_USER}
Group=${CLAUDE_USER}
WorkingDirectory=${INSTALL_DIR}
ExecStart=/usr/bin/python3 ${INSTALL_DIR}/scripts/claude-daemon.py
Restart=always
RestartSec=5
StandardOutput=append:/var/log/codehero/daemon.log
StandardError=append:/var/log/codehero/daemon.log
Environment=PYTHONUNBUFFERED=1
Environment=PATH=/home/${CLAUDE_USER}/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=HOME=/home/${CLAUDE_USER}

[Install]
WantedBy=multi-user.target
SVCEOF
    log_info "Fixed codehero-daemon.service"
fi

# Update web service if user is wrong
if grep -q "User=root" /etc/systemd/system/codehero-web.service 2>/dev/null; then
    log_info "Fixing codehero-web.service user..."

    cat > /etc/systemd/system/codehero-web.service << SVCEOF
[Unit]
Description=CodeHero Web Interface
After=network.target mysql.service
Wants=mysql.service

[Service]
Type=simple
User=${CLAUDE_USER}
Group=${CLAUDE_USER}
WorkingDirectory=${INSTALL_DIR}
ExecStart=/usr/bin/python3 ${INSTALL_DIR}/web/app.py
ExecStopPost=/bin/bash -c 'fuser -k 5000/tcp 2>/dev/null || true'
Restart=always
RestartSec=5
StandardOutput=append:/var/log/codehero/web.log
StandardError=append:/var/log/codehero/web.log
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SVCEOF
    log_info "Fixed codehero-web.service"
fi

systemctl daemon-reload
