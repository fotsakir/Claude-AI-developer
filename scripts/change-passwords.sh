#!/bin/bash
# =====================================================
# CODEHERO - Change Passwords
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

echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║       CODEHERO - Change Passwords             ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Load current credentials
source /etc/codehero/credentials.conf 2>/dev/null || true
source /etc/codehero/mysql.conf 2>/dev/null || true

echo "Select what to change:"
echo "  1) MySQL root password"
echo "  2) MySQL application user password"
echo "  3) Admin Panel password"
echo "  4) All passwords"
echo "  5) Exit"
echo ""
read -p "Choice [1-5]: " CHOICE

change_mysql_root() {
    echo ""
    read -sp "Enter new MySQL root password: " NEW_PASS
    echo ""
    read -sp "Confirm password: " CONFIRM_PASS
    echo ""

    if [ "$NEW_PASS" != "$CONFIRM_PASS" ]; then
        echo -e "${RED}Passwords do not match!${NC}"
        return 1
    fi

    # Get current password
    CURRENT_PASS="${MYSQL_ROOT_PASSWORD:-rootpass123}"

    mysql -u root -p"${CURRENT_PASS}" -e "ALTER USER 'root'@'localhost' IDENTIFIED BY '${NEW_PASS}';" 2>/dev/null
    if [ $? -eq 0 ]; then
        # Update config files
        sed -i "s/MYSQL_ROOT_PASSWORD=.*/MYSQL_ROOT_PASSWORD=${NEW_PASS}/" /etc/codehero/mysql.conf
        sed -i "s/MYSQL_ROOT_PASSWORD=.*/MYSQL_ROOT_PASSWORD=${NEW_PASS}/" /etc/codehero/credentials.conf
        echo -e "${GREEN}MySQL root password changed successfully${NC}"
    else
        echo -e "${RED}Failed to change MySQL root password${NC}"
        return 1
    fi
}

change_mysql_app() {
    echo ""
    read -sp "Enter new MySQL app user password: " NEW_PASS
    echo ""
    read -sp "Confirm password: " CONFIRM_PASS
    echo ""

    if [ "$NEW_PASS" != "$CONFIRM_PASS" ]; then
        echo -e "${RED}Passwords do not match!${NC}"
        return 1
    fi

    CURRENT_ROOT="${MYSQL_ROOT_PASSWORD:-rootpass123}"
    APP_USER="${MYSQL_APP_USER:-claude_user}"

    mysql -u root -p"${CURRENT_ROOT}" -e "ALTER USER '${APP_USER}'@'localhost' IDENTIFIED BY '${NEW_PASS}';" 2>/dev/null
    if [ $? -eq 0 ]; then
        sed -i "s/MYSQL_APP_PASSWORD=.*/MYSQL_APP_PASSWORD=${NEW_PASS}/" /etc/codehero/mysql.conf
        sed -i "s/MYSQL_APP_PASSWORD=.*/MYSQL_APP_PASSWORD=${NEW_PASS}/" /etc/codehero/credentials.conf
        sed -i "s/DB_PASSWORD=.*/DB_PASSWORD=${NEW_PASS}/" /etc/codehero/system.conf

        # Restart services to use new password
        systemctl restart codehero-web 2>/dev/null || true
        systemctl restart codehero-daemon 2>/dev/null || true

        echo -e "${GREEN}MySQL app user password changed successfully${NC}"
        echo -e "${YELLOW}Services restarted to use new password${NC}"
    else
        echo -e "${RED}Failed to change MySQL app user password${NC}"
        return 1
    fi
}

change_admin_panel() {
    echo ""
    echo -e "${YELLOW}Note: Admin Panel password is stored in the database${NC}"
    read -p "Enter new admin username [admin]: " NEW_USER
    NEW_USER="${NEW_USER:-admin}"
    read -sp "Enter new admin password: " NEW_PASS
    echo ""
    read -sp "Confirm password: " CONFIRM_PASS
    echo ""

    if [ "$NEW_PASS" != "$CONFIRM_PASS" ]; then
        echo -e "${RED}Passwords do not match!${NC}"
        return 1
    fi

    # Generate bcrypt hash (using stdin to handle special characters)
    HASH=$(echo -n "$NEW_PASS" | python3 -c "import bcrypt,sys; print(bcrypt.hashpw(sys.stdin.read().encode(), bcrypt.gensalt()).decode())")

    # Use app user credentials from system.conf (readable, has UPDATE privileges)
    source /etc/codehero/system.conf 2>/dev/null
    APP_USER="${DB_USER:-claude_user}"
    APP_PASS="${DB_PASSWORD:-claudepass123}"
    DB_NAME="${DB_NAME:-claude_knowledge}"

    mysql -u "${APP_USER}" -p"${APP_PASS}" ${DB_NAME} -e "UPDATE developers SET username='${NEW_USER}', password_hash='${HASH}' WHERE id=1;" 2>/dev/null
    if [ $? -eq 0 ]; then
        sed -i "s/ADMIN_USER=.*/ADMIN_USER=${NEW_USER}/" /etc/codehero/credentials.conf
        sed -i "s/ADMIN_PASSWORD=.*/ADMIN_PASSWORD=${NEW_PASS}/" /etc/codehero/credentials.conf
        echo -e "${GREEN}Admin Panel password changed successfully${NC}"
    else
        echo -e "${RED}Failed to change Admin Panel password${NC}"
        return 1
    fi
}

case $CHOICE in
    1)
        change_mysql_root
        ;;
    2)
        change_mysql_app
        ;;
    3)
        change_admin_panel
        ;;
    4)
        echo -e "${CYAN}Changing all passwords...${NC}"
        change_mysql_root
        change_mysql_app
        change_admin_panel
        ;;
    5)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Done!${NC}"
echo "Updated credentials saved to /etc/codehero/credentials.conf"
