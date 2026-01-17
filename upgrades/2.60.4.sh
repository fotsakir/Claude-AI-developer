#!/bin/bash
# Upgrade to version 2.60.4
# Fixes PID directory and log permissions

log_info() { echo -e "\033[0;36m[2.60.4]\033[0m $1"; }

CLAUDE_USER="claude"

# Fix log file permissions
log_info "Fixing log permissions..."
touch /var/log/codehero/daemon.log /var/log/codehero/web.log 2>/dev/null || true
chown ${CLAUDE_USER}:${CLAUDE_USER} /var/log/codehero/daemon.log /var/log/codehero/web.log 2>/dev/null || true

# Fix projects folder permissions (setgid for proper group inheritance)
if [ -d "/var/www/projects" ]; then
    chown -R ${CLAUDE_USER}:${CLAUDE_USER} /var/www/projects 2>/dev/null || true
    chmod 2775 /var/www/projects 2>/dev/null || true
    log_info "Fixed /var/www/projects permissions"
fi

# Fix apps folder permissions
if [ -d "/opt/apps" ]; then
    chown -R ${CLAUDE_USER}:${CLAUDE_USER} /opt/apps 2>/dev/null || true
    chmod 2775 /opt/apps 2>/dev/null || true
    log_info "Fixed /opt/apps permissions"
fi

# Fix /var/run/codehero permissions (PID file directory)
mkdir -p /var/run/codehero
chown -R ${CLAUDE_USER}:${CLAUDE_USER} /var/run/codehero 2>/dev/null || true
log_info "Fixed /var/run/codehero permissions"

# Ensure tmpfiles.d config exists for reboot persistence
cat > /etc/tmpfiles.d/codehero.conf << TMPEOF
# Create runtime directory for CodeHero
d /var/run/codehero 0755 ${CLAUDE_USER} ${CLAUDE_USER} -
TMPEOF
log_info "Updated tmpfiles.d config"
