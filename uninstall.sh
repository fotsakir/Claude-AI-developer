#!/bin/bash
# =====================================================
# CODEHERO - Uninstall Script
# For testing purposes - removes everything
# =====================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

echo -e "${RED}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║       CODEHERO - UNINSTALL                    ║"
echo "║                                                           ║"
echo "║   WARNING: This will remove EVERYTHING!                   ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo ""
echo "This will remove:"
echo "  - Nginx and PHP-FPM"
echo "  - MySQL server and all databases"
echo "  - Node.js"
echo "  - GraalVM"
echo "  - Playwright"
echo "  - All configuration files"
echo "  - All project files in /var/www/projects"
echo "  - Claude user (optional)"
echo ""

read -p "Are you sure you want to continue? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
read -p "Also remove claude user? (yes/no): " REMOVE_USER

echo ""
echo -e "${YELLOW}[1/8] Stopping services...${NC}"
# Stop CodeHero services
systemctl stop codehero-web 2>/dev/null || true
systemctl stop codehero-daemon 2>/dev/null || true
systemctl disable codehero-web 2>/dev/null || true
systemctl disable codehero-daemon 2>/dev/null || true
# Stop Nginx and PHP-FPM
systemctl stop nginx 2>/dev/null || true
systemctl stop php8.3-fpm 2>/dev/null || true
systemctl disable nginx 2>/dev/null || true
systemctl disable php8.3-fpm 2>/dev/null || true
# Stop MySQL
systemctl stop mysql 2>/dev/null || true

# Kill any remaining processes
pkill -f "app.py" 2>/dev/null || true
pkill -f "claude-daemon" 2>/dev/null || true
pkill -f "nginx" 2>/dev/null || true

echo -e "${YELLOW}[2/8] Removing Nginx and PHP-FPM...${NC}"
apt-get purge -y nginx nginx-common php8.3-fpm php8.3-* 2>/dev/null || true
rm -rf /etc/nginx 2>/dev/null || true
rm -rf /var/log/nginx 2>/dev/null || true

echo -e "${YELLOW}[3/8] Removing MySQL...${NC}"
apt-get purge -y mysql-server mysql-client mysql-common mysql-community-* 2>/dev/null || true
apt-get autoremove -y 2>/dev/null || true
rm -rf /var/lib/mysql 2>/dev/null || true
rm -rf /var/log/mysql 2>/dev/null || true
rm -rf /etc/mysql 2>/dev/null || true
rm -f /etc/apt/sources.list.d/mysql.list 2>/dev/null || true

echo -e "${YELLOW}[4/8] Removing Node.js...${NC}"
apt-get purge -y nodejs 2>/dev/null || true
rm -f /etc/apt/sources.list.d/nodesource.list 2>/dev/null || true
rm -rf /usr/lib/node_modules 2>/dev/null || true

echo -e "${YELLOW}[5/8] Removing GraalVM...${NC}"
rm -rf /opt/graalvm 2>/dev/null || true
rm -f /etc/profile.d/graalvm.sh 2>/dev/null || true
rm -f /usr/local/bin/java 2>/dev/null || true
rm -f /usr/local/bin/javac 2>/dev/null || true
rm -f /usr/local/bin/native-image 2>/dev/null || true

echo -e "${YELLOW}[6/8] Removing Playwright...${NC}"
pip3 uninstall -y playwright 2>/dev/null || true
rm -rf /root/.cache/ms-playwright 2>/dev/null || true
rm -rf /home/claude/.cache/ms-playwright 2>/dev/null || true

echo -e "${YELLOW}[7/8] Removing application files...${NC}"
rm -rf /opt/codehero 2>/dev/null || true
rm -rf /opt/apps 2>/dev/null || true
rm -rf /var/www/projects 2>/dev/null || true
rm -rf /var/log/codehero 2>/dev/null || true
rm -rf /var/run/codehero 2>/dev/null || true
rm -rf /etc/codehero 2>/dev/null || true
rm -f /etc/systemd/system/codehero-web.service 2>/dev/null || true
rm -f /etc/systemd/system/codehero-daemon.service 2>/dev/null || true
# Remove old service names (for backwards compatibility)
rm -f /etc/systemd/system/fotios-web.service 2>/dev/null || true
rm -f /etc/systemd/system/fotios-daemon.service 2>/dev/null || true
rm -f /usr/local/bin/claude-cli 2>/dev/null || true
systemctl daemon-reload 2>/dev/null || true

echo -e "${YELLOW}[8/8] Cleaning up...${NC}"
# Restore SSH config if backup exists
if [ -f /etc/ssh/sshd_config.backup ]; then
    cp /etc/ssh/sshd_config.backup /etc/ssh/sshd_config
    systemctl restart ssh 2>/dev/null || systemctl restart sshd 2>/dev/null || true
fi

# Remove claude user if requested
if [ "$REMOVE_USER" = "yes" ]; then
    echo "Removing claude user..."
    userdel -r claude 2>/dev/null || true
    rm -f /etc/sudoers.d/claude 2>/dev/null || true
fi

# Clean apt cache
apt-get autoremove -y 2>/dev/null || true
apt-get autoclean 2>/dev/null || true
apt-get update 2>/dev/null || true

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗"
echo "║              UNINSTALL COMPLETE!                          ║"
echo "╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "The system has been cleaned. You can now run setup.sh again."
echo ""
