#!/bin/bash
# =====================================================
# CODEHERO - Upgrade Script
# =====================================================
# Usage:
#   sudo ./upgrade.sh           # Interactive mode
#   sudo ./upgrade.sh -y        # Auto-confirm all
#   sudo ./upgrade.sh --dry-run # Show what would be done
# =====================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

# Paths
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="/opt/codehero"
BACKUP_DIR="/var/backups/codehero"
CONFIG_DIR="/etc/codehero"

# Options
DRY_RUN=false
AUTO_YES=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -y|--yes)
            AUTO_YES=true
            shift
            ;;
        -h|--help)
            echo "Usage: sudo ./upgrade.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -y, --yes      Auto-confirm all prompts"
            echo "  --dry-run      Show what would be done without making changes"
            echo "  -h, --help     Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Functions
log_info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_dry() {
    echo -e "${BLUE}[DRY-RUN]${NC} Would: $1"
}

confirm() {
    if [ "$AUTO_YES" = true ]; then
        return 0
    fi
    read -p "$1 [y/N]: " response
    case "$response" in
        [yY][eE][sS]|[yY]) return 0 ;;
        *) return 1 ;;
    esac
}

version_compare() {
    # Returns: 0 if equal, 1 if $1 > $2, 2 if $1 < $2
    if [ "$1" = "$2" ]; then
        return 0
    fi
    local IFS=.
    local i ver1=($1) ver2=($2)
    for ((i=0; i<${#ver1[@]}; i++)); do
        if [ -z "${ver2[i]}" ]; then
            return 1
        fi
        if ((10#${ver1[i]} > 10#${ver2[i]})); then
            return 1
        fi
        if ((10#${ver1[i]} < 10#${ver2[i]})); then
            return 2
        fi
    done
    return 0
}

get_db_credentials() {
    source ${CONFIG_DIR}/system.conf 2>/dev/null || {
        log_error "Cannot read ${CONFIG_DIR}/system.conf"
        exit 1
    }
    DB_USER="${DB_USER:-claude_user}"
    DB_PASS="${DB_PASSWORD:-claudepass123}"
    DB_NAME="${DB_NAME:-claude_knowledge}"
}

run_sql() {
    mysql -u "${DB_USER}" -p"${DB_PASS}" "${DB_NAME}" -e "$1" 2>/dev/null
}

run_sql_file() {
    mysql -u "${DB_USER}" -p"${DB_PASS}" "${DB_NAME}" < "$1" 2>/dev/null
}

# =====================================================
# MAIN SCRIPT
# =====================================================

echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║         CODEHERO - Upgrade Script             ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

if [ "$DRY_RUN" = true ]; then
    echo -e "${BLUE}>>> DRY-RUN MODE - No changes will be made <<<${NC}"
    echo ""
fi

# Check root
if [ "$EUID" -ne 0 ]; then
    log_error "Please run as root or with sudo"
    exit 1
fi

# Check if installation exists
if [ ! -d "$INSTALL_DIR" ]; then
    log_error "CodeHero is not installed at $INSTALL_DIR"
    log_info "Please run setup.sh for fresh installation"
    exit 1
fi

# Get versions
NEW_VERSION=$(cat "${SOURCE_DIR}/VERSION" 2>/dev/null || echo "0.0.0")
CURRENT_VERSION=$(cat "${INSTALL_DIR}/VERSION" 2>/dev/null || echo "0.0.0")

echo -e "Current version: ${YELLOW}${CURRENT_VERSION}${NC}"
echo -e "New version:     ${GREEN}${NEW_VERSION}${NC}"
echo ""

# Compare versions
set +e
version_compare "$NEW_VERSION" "$CURRENT_VERSION"
VCOMP=$?
set -e
case $VCOMP in
    0)
        log_warning "Versions are the same. Nothing to upgrade."
        if ! confirm "Continue anyway?"; then
            exit 0
        fi
        ;;
    2)
        log_warning "New version ($NEW_VERSION) is older than current ($CURRENT_VERSION)"
        if ! confirm "Downgrade?"; then
            exit 0
        fi
        ;;
esac

# Show what will be upgraded
echo -e "${CYAN}=== Upgrade Summary ===${NC}"
echo ""

# Check for file changes
log_info "Files to be updated:"
CHANGED_FILES=0
for dir in web scripts docs; do
    if [ -d "${SOURCE_DIR}/${dir}" ]; then
        while IFS= read -r -d '' file; do
            rel_path="${file#$SOURCE_DIR/}"
            target="${INSTALL_DIR}/${rel_path}"
            if [ -f "$target" ]; then
                if ! diff -q "$file" "$target" > /dev/null 2>&1; then
                    echo "  [MODIFIED] $rel_path"
                    CHANGED_FILES=$((CHANGED_FILES + 1))
                fi
            else
                echo "  [NEW] $rel_path"
                CHANGED_FILES=$((CHANGED_FILES + 1))
            fi
        done < <(find "${SOURCE_DIR}/${dir}" -type f -print0)
    fi
done

if [ $CHANGED_FILES -eq 0 ]; then
    echo "  (no file changes detected)"
fi
echo ""

# Check for migrations
get_db_credentials

# Ensure schema_migrations table exists
if [ "$DRY_RUN" = false ]; then
    run_sql "CREATE TABLE IF NOT EXISTS schema_migrations (
        version VARCHAR(20) PRIMARY KEY,
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );" 2>/dev/null || true
fi

log_info "Database migrations to apply:"
MIGRATIONS_DIR="${SOURCE_DIR}/database/migrations"
PENDING_MIGRATIONS=()

if [ -d "$MIGRATIONS_DIR" ]; then
    for migration in $(ls -1 "${MIGRATIONS_DIR}"/*.sql 2>/dev/null | sort -V); do
        migration_name=$(basename "$migration" .sql)
        # Check if already applied
        applied=$(run_sql "SELECT version FROM schema_migrations WHERE version='${migration_name}';" 2>/dev/null | tail -1)
        if [ -z "$applied" ]; then
            echo "  [PENDING] $migration_name"
            PENDING_MIGRATIONS+=("$migration")
        fi
    done
fi

if [ ${#PENDING_MIGRATIONS[@]} -eq 0 ]; then
    echo "  (no pending migrations)"
fi
echo ""

# Confirm upgrade
if [ "$DRY_RUN" = true ]; then
    echo -e "${BLUE}=== Dry-run complete ===${NC}"
    echo "Run without --dry-run to apply changes."
    exit 0
fi

if ! confirm "Proceed with upgrade?"; then
    log_info "Upgrade cancelled."
    exit 0
fi

echo ""
echo -e "${CYAN}=== Starting Upgrade ===${NC}"
echo ""

# Step 1: Create backup
BACKUP_NAME="codehero-${CURRENT_VERSION}-$(date +%Y%m%d_%H%M%S)"
log_info "Creating backup: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
mkdir -p "$BACKUP_DIR"
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" -C /opt codehero 2>/dev/null
log_success "Backup created"

# Step 2: Install new packages (if any)
log_info "Checking for new packages..."

# Multimedia tools (added in v2.42.0)
NEW_PACKAGES=""
command -v ffmpeg >/dev/null 2>&1 || NEW_PACKAGES="$NEW_PACKAGES ffmpeg"
command -v convert >/dev/null 2>&1 || NEW_PACKAGES="$NEW_PACKAGES imagemagick"
command -v tesseract >/dev/null 2>&1 || NEW_PACKAGES="$NEW_PACKAGES tesseract-ocr tesseract-ocr-eng tesseract-ocr-ell"
command -v sox >/dev/null 2>&1 || NEW_PACKAGES="$NEW_PACKAGES sox"
command -v pdftotext >/dev/null 2>&1 || NEW_PACKAGES="$NEW_PACKAGES poppler-utils"
command -v gs >/dev/null 2>&1 || NEW_PACKAGES="$NEW_PACKAGES ghostscript"
command -v mediainfo >/dev/null 2>&1 || NEW_PACKAGES="$NEW_PACKAGES mediainfo"
command -v cwebp >/dev/null 2>&1 || NEW_PACKAGES="$NEW_PACKAGES webp"
command -v optipng >/dev/null 2>&1 || NEW_PACKAGES="$NEW_PACKAGES optipng"
command -v jpegoptim >/dev/null 2>&1 || NEW_PACKAGES="$NEW_PACKAGES jpegoptim"
command -v rsvg-convert >/dev/null 2>&1 || NEW_PACKAGES="$NEW_PACKAGES librsvg2-bin"
command -v vips >/dev/null 2>&1 || NEW_PACKAGES="$NEW_PACKAGES libvips-tools"
command -v qpdf >/dev/null 2>&1 || NEW_PACKAGES="$NEW_PACKAGES qpdf"

if [ -n "$NEW_PACKAGES" ]; then
    echo "  Installing:$NEW_PACKAGES"
    apt-get update -qq
    apt-get install -y $NEW_PACKAGES >/dev/null 2>&1 || log_warning "Some packages failed to install"

    # Python packages
    pip3 install --quiet Pillow opencv-python-headless pydub pytesseract pdf2image --break-system-packages 2>/dev/null || \
    pip3 install --quiet Pillow opencv-python-headless pydub pytesseract pdf2image 2>/dev/null || true

    log_success "New packages installed"
else
    echo "  (all packages already installed)"
fi

# Step 2b: Migrate from OpenLiteSpeed to Nginx (if needed)
if systemctl is-active --quiet lshttpd 2>/dev/null || [ -d "/usr/local/lsws" ]; then
    log_info "Migrating from OpenLiteSpeed to Nginx..."

    # Install Nginx and PHP-FPM
    echo "  Installing Nginx and PHP-FPM..."
    apt-get update -qq
    apt-get install -y nginx php8.3-fpm php8.3-mysql php8.3-curl php8.3-intl \
        php8.3-opcache php8.3-redis php8.3-imagick php8.3-sqlite3 php8.3-imap \
        php8.3-apcu php8.3-igbinary php8.3-tidy php8.3-pgsql php8.3-cli >/dev/null 2>&1 || true

    # Create Nginx configurations
    echo "  Creating Nginx configurations..."
    cat > /etc/nginx/sites-available/codehero-admin << 'NGINXADMIN'
# CodeHero Admin Panel - Port 9453 (HTTPS)
server {
    listen 9453 ssl http2;
    listen [::]:9453 ssl http2;
    server_name _;

    ssl_certificate /etc/codehero/ssl/cert.pem;
    ssl_certificate_key /etc/codehero/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    access_log /var/log/nginx/codehero-admin-access.log;
    error_log /var/log/nginx/codehero-admin-error.log;
    client_max_body_size 500M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
    }

    location /socket.io {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400s;
    }

    location /android/ {
        proxy_pass https://127.0.0.1:8443/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_ssl_verify off;
        proxy_read_timeout 86400s;
    }

    location = /android {
        return 301 /android/;
    }
}
NGINXADMIN

    cat > /etc/nginx/sites-available/codehero-projects << 'NGINXPROJECTS'
# CodeHero Web Projects - Port 9867 (HTTPS)
server {
    listen 9867 ssl http2;
    listen [::]:9867 ssl http2;
    server_name _;

    ssl_certificate /etc/codehero/ssl/cert.pem;
    ssl_certificate_key /etc/codehero/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    root /var/www/projects;
    index index.html index.php;

    access_log /var/log/nginx/codehero-projects-access.log;
    error_log /var/log/nginx/codehero-projects-error.log;
    client_max_body_size 500M;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    location ~ \.php$ {
        fastcgi_pass unix:/var/run/php/php8.3-fpm.sock;
        fastcgi_param SCRIPT_FILENAME $realpath_root$fastcgi_script_name;
        include fastcgi_params;
        fastcgi_read_timeout 300s;
    }

    location ~ /\.ht {
        deny all;
    }

    location ~* \.(jpg|jpeg|png|gif|ico|css|js|woff|woff2|ttf|svg)$ {
        expires 7d;
        add_header Cache-Control "public, immutable";
    }
}
NGINXPROJECTS

    # Enable sites
    ln -sf /etc/nginx/sites-available/codehero-admin /etc/nginx/sites-enabled/
    ln -sf /etc/nginx/sites-available/codehero-projects /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default

    # Stop and disable OpenLiteSpeed
    echo "  Stopping OpenLiteSpeed..."
    systemctl stop lshttpd 2>/dev/null || /usr/local/lsws/bin/lswsctrl stop 2>/dev/null || true
    systemctl disable lshttpd 2>/dev/null || true

    # Start Nginx and PHP-FPM
    echo "  Starting Nginx and PHP-FPM..."
    systemctl enable nginx php8.3-fpm 2>/dev/null || true
    systemctl start php8.3-fpm 2>/dev/null || true
    nginx -t 2>/dev/null && systemctl start nginx 2>/dev/null || log_warning "Nginx config test failed"

    # Disable automatic updates
    echo "  Disabling automatic updates..."
    systemctl stop unattended-upgrades 2>/dev/null || true
    systemctl disable unattended-upgrades 2>/dev/null || true
    systemctl stop apt-daily.timer apt-daily-upgrade.timer 2>/dev/null || true
    systemctl disable apt-daily.timer apt-daily-upgrade.timer 2>/dev/null || true
    cat > /etc/apt/apt.conf.d/20auto-upgrades << 'APTEOF'
APT::Periodic::Update-Package-Lists "0";
APT::Periodic::Unattended-Upgrade "0";
APT::Periodic::Download-Upgradeable-Packages "0";
APT::Periodic::AutocleanInterval "0";
APTEOF

    log_success "Migrated from OpenLiteSpeed to Nginx"
    echo ""
    echo -e "  ${YELLOW}NOTE: OpenLiteSpeed is disabled but not removed.${NC}"
    echo -e "  ${YELLOW}To remove it: apt-get purge openlitespeed lsphp*${NC}"
    echo ""
fi

# Step 2c: Install Claude Code CLI if not present
CLAUDE_USER="claude"
if ! su - ${CLAUDE_USER} -c 'which claude' &>/dev/null; then
    log_info "Installing Claude Code CLI..."
    su - ${CLAUDE_USER} -c 'curl -fsSL https://claude.ai/install.sh | bash' 2>/dev/null || true

    # Add to PATH if not already
    if ! su - ${CLAUDE_USER} -c 'grep -q "\.local/bin" ~/.bashrc' 2>/dev/null; then
        su - ${CLAUDE_USER} -c 'echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> ~/.bashrc'
    fi

    if su - ${CLAUDE_USER} -c 'which claude' &>/dev/null; then
        log_success "Claude Code CLI installed"
    else
        log_warning "Claude Code CLI installation failed - install manually"
    fi
fi

# Step 3: Stop daemon only (web stays running until end)
log_info "Stopping daemon..."
systemctl stop codehero-daemon 2>/dev/null || true
sleep 1
log_success "Daemon stopped"

# Step 4: Apply database migrations
if [ ${#PENDING_MIGRATIONS[@]} -gt 0 ]; then
    log_info "Applying database migrations..."
    for migration in "${PENDING_MIGRATIONS[@]}"; do
        migration_name=$(basename "$migration" .sql)
        echo -n "  Applying $migration_name... "
        if run_sql_file "$migration"; then
            run_sql "INSERT INTO schema_migrations (version) VALUES ('${migration_name}');"
            echo -e "${GREEN}OK${NC}"
        else
            echo -e "${RED}FAILED${NC}"
            log_error "Migration failed: $migration_name"
            log_info "Rolling back: starting services..."
            systemctl start codehero-daemon 2>/dev/null || true
            systemctl start codehero-web 2>/dev/null || true
            exit 1
        fi
    done
    log_success "All migrations applied"
fi

# Step 5: Copy files
log_info "Copying files..."

# Web app
if [ -d "${SOURCE_DIR}/web" ]; then
    cp -r "${SOURCE_DIR}/web/"* "${INSTALL_DIR}/web/" 2>/dev/null || true
    echo "  Copied web files"
fi

# Scripts
if [ -d "${SOURCE_DIR}/scripts" ]; then
    cp "${SOURCE_DIR}/scripts/"*.py "${INSTALL_DIR}/scripts/" 2>/dev/null || true
    cp "${SOURCE_DIR}/scripts/"*.sh "${INSTALL_DIR}/scripts/" 2>/dev/null || true
    chmod +x "${INSTALL_DIR}/scripts/"*.sh 2>/dev/null || true
    echo "  Copied scripts"
fi

# Docs
if [ -d "${SOURCE_DIR}/docs" ]; then
    mkdir -p "${INSTALL_DIR}/docs"
    cp -r "${SOURCE_DIR}/docs/"* "${INSTALL_DIR}/docs/" 2>/dev/null || true
    echo "  Copied docs"
fi

# Config files (knowledge base, templates)
if [ -d "${SOURCE_DIR}/config" ]; then
    mkdir -p "${INSTALL_DIR}/config"
    cp "${SOURCE_DIR}/config/"*.md "${INSTALL_DIR}/config/" 2>/dev/null || true
    cp "${SOURCE_DIR}/config/"*.md "${CONFIG_DIR}/" 2>/dev/null || true
    echo "  Copied config files (knowledge base, templates)"
fi

# VERSION, CHANGELOG, and documentation
cp "${SOURCE_DIR}/VERSION" "${INSTALL_DIR}/"
cp "${SOURCE_DIR}/CHANGELOG.md" "${INSTALL_DIR}/" 2>/dev/null || true
cp "${SOURCE_DIR}/README.md" "${INSTALL_DIR}/" 2>/dev/null || true
cp "${SOURCE_DIR}/CLAUDE_OPERATIONS.md" "${INSTALL_DIR}/" 2>/dev/null || true
cp "${SOURCE_DIR}/CLAUDE_DEV_NOTES.md" "${INSTALL_DIR}/" 2>/dev/null || true
cp "${SOURCE_DIR}/CLAUDE.md" "${INSTALL_DIR}/" 2>/dev/null || true

log_success "Files copied"

# Step 6: Fix permissions
log_info "Fixing permissions..."

# Fix log file permissions (in case they were created as root)
touch /var/log/codehero/daemon.log /var/log/codehero/web.log 2>/dev/null || true
chown claude:claude /var/log/codehero/daemon.log /var/log/codehero/web.log 2>/dev/null || true

# Fix projects folder permissions (setgid for proper group inheritance)
if [ -d "/var/www/projects" ]; then
    chown -R claude:claude /var/www/projects 2>/dev/null || true
    chmod 2775 /var/www/projects 2>/dev/null || true
    echo "  Fixed /var/www/projects permissions"
fi

# Fix apps folder permissions
if [ -d "/opt/apps" ]; then
    chown -R claude:claude /opt/apps 2>/dev/null || true
    chmod 2775 /opt/apps 2>/dev/null || true
    echo "  Fixed /opt/apps permissions"
fi

# Fix /var/run/codehero permissions (PID file directory)
mkdir -p /var/run/codehero
chown -R claude:claude /var/run/codehero 2>/dev/null || true
echo "  Fixed /var/run/codehero permissions"

# Ensure tmpfiles.d config exists for reboot persistence
cat > /etc/tmpfiles.d/codehero.conf << TMPEOF
# Create runtime directory for CodeHero
d /var/run/codehero 0755 claude claude -
TMPEOF
echo "  Updated tmpfiles.d config"

# Step 6b: Update systemd service files (fix user if incorrect)
log_info "Updating systemd services..."
CLAUDE_USER="claude"

# Update daemon service if user is wrong
if grep -q "User=claude-worker" /etc/systemd/system/codehero-daemon.service 2>/dev/null; then
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
    echo "  Updated codehero-daemon.service (fixed user)"
fi

# Update web service if user is wrong
if grep -q "User=root" /etc/systemd/system/codehero-web.service 2>/dev/null; then
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
    echo "  Updated codehero-web.service (fixed user)"
fi

systemctl daemon-reload

# Step 7: Restart services
log_info "Restarting services..."
systemctl restart codehero-daemon
sleep 1
systemctl restart codehero-web
sleep 1
# Reload nginx to ensure it binds to all configured ports
systemctl reload nginx 2>/dev/null || systemctl restart nginx 2>/dev/null || true
sleep 1
log_success "Services restarted"

# Step 8: Verify
log_info "Verifying services..."
VERIFY_OK=true

if systemctl is-active --quiet codehero-web; then
    echo -e "  codehero-web:    ${GREEN}running${NC}"
else
    echo -e "  codehero-web:    ${RED}not running${NC}"
    VERIFY_OK=false
fi

if systemctl is-active --quiet codehero-daemon; then
    echo -e "  codehero-daemon: ${GREEN}running${NC}"
else
    echo -e "  codehero-daemon: ${RED}not running${NC}"
    VERIFY_OK=false
fi

if systemctl is-active --quiet nginx; then
    echo -e "  nginx:           ${GREEN}running${NC}"
else
    echo -e "  nginx:           ${RED}not running${NC}"
    VERIFY_OK=false
fi

if systemctl is-active --quiet php8.3-fpm; then
    echo -e "  php8.3-fpm:      ${GREEN}running${NC}"
else
    echo -e "  php8.3-fpm:      ${YELLOW}not running${NC}"
fi

echo ""

if [ "$VERIFY_OK" = true ]; then
    log_success "Upgrade completed successfully!"
else
    log_warning "Upgrade completed with warnings. Check service status."
fi

# Show changelog for this version
echo ""
echo -e "${CYAN}=== What's New in ${NEW_VERSION} ===${NC}"
if [ -f "${SOURCE_DIR}/CHANGELOG.md" ]; then
    # Extract changelog for this version (between ## [version] markers)
    sed -n "/^## \[${NEW_VERSION}\]/,/^## \[/p" "${SOURCE_DIR}/CHANGELOG.md" | head -n -1 | tail -n +2
else
    echo "See CHANGELOG.md for details"
fi

echo ""
echo -e "${GREEN}Upgrade from ${CURRENT_VERSION} to ${NEW_VERSION} complete!${NC}"
echo ""
echo "Backup saved to: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
