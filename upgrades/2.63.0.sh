#!/bin/bash
# Upgrade to version 2.63.0
# Migrates from OpenLiteSpeed to Nginx (if needed)

log_info() { echo -e "\033[0;36m[2.63.0]\033[0m $1"; }
log_warning() { echo -e "\033[1;33m[2.63.0]\033[0m $1"; }

# Check if migration needed
if ! systemctl is-active --quiet lshttpd 2>/dev/null && [ ! -d "/usr/local/lsws" ]; then
    log_info "OpenLiteSpeed not found - skipping migration"
    exit 0
fi

log_info "Migrating from OpenLiteSpeed to Nginx..."

# Install Nginx and PHP-FPM
log_info "Installing Nginx and PHP-FPM..."
apt-get update -qq
apt-get install -y nginx php8.3-fpm php8.3-mysql php8.3-curl php8.3-intl \
    php8.3-opcache php8.3-redis php8.3-imagick php8.3-sqlite3 php8.3-imap \
    php8.3-apcu php8.3-igbinary php8.3-tidy php8.3-pgsql php8.3-cli >/dev/null 2>&1 || true

# Create Nginx configurations
log_info "Creating Nginx configurations..."

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
log_info "Stopping OpenLiteSpeed..."
systemctl stop lshttpd 2>/dev/null || /usr/local/lsws/bin/lswsctrl stop 2>/dev/null || true
systemctl disable lshttpd 2>/dev/null || true

# Start Nginx and PHP-FPM
log_info "Starting Nginx and PHP-FPM..."
systemctl enable nginx php8.3-fpm 2>/dev/null || true
systemctl start php8.3-fpm 2>/dev/null || true
nginx -t 2>/dev/null && systemctl start nginx 2>/dev/null || log_warning "Nginx config test failed"

# Disable automatic updates
log_info "Disabling automatic updates..."
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

log_info "Migration from OpenLiteSpeed to Nginx complete"
log_warning "NOTE: OpenLiteSpeed is disabled but not removed."
log_warning "To remove it: apt-get purge openlitespeed lsphp*"
