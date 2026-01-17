#!/bin/bash
# Upgrade to version 2.65.0
# Installs phpMyAdmin with signon authentication

log_info() { echo -e "\033[0;36m[2.65.0]\033[0m $1"; }
log_warning() { echo -e "\033[1;33m[2.65.0]\033[0m $1"; }

# Install phpMyAdmin if not present
if [ ! -d /usr/share/phpmyadmin ]; then
    log_info "Installing phpMyAdmin..."
    DEBIAN_FRONTEND=noninteractive apt-get install -y phpmyadmin >/dev/null 2>&1 || true

    if [ -d /usr/share/phpmyadmin ]; then
        log_info "phpMyAdmin installed"
    else
        log_warning "phpMyAdmin installation failed - skipping"
        exit 0
    fi
fi

# Configure phpMyAdmin signon (if not configured)
if [ -d /usr/share/phpmyadmin ] && [ ! -f /usr/share/phpmyadmin/signon.php ]; then
    log_info "Configuring phpMyAdmin signon authentication..."

    cat > /usr/share/phpmyadmin/signon.php << 'PMASIGNON'
<?php
/**
 * CodeHero phpMyAdmin Single Sign-On Script
 * Auto-login with project database credentials
 */
session_name('PMA_signon');
session_start();

// Get credentials from query parameters (base64 encoded for safety)
$user = isset($_GET['u']) ? base64_decode($_GET['u']) : '';
$pass = isset($_GET['p']) ? base64_decode($_GET['p']) : '';
$db = isset($_GET['db']) ? base64_decode($_GET['db']) : '';

if (empty($user)) {
    die('Missing credentials');
}

// Store credentials in session for phpMyAdmin
$_SESSION['PMA_single_signon_user'] = $user;
$_SESSION['PMA_single_signon_password'] = $pass;
$_SESSION['PMA_single_signon_host'] = 'localhost';

// Redirect to phpMyAdmin with selected database
$redirect = 'index.php';
if (!empty($db)) {
    $redirect .= '?db=' . urlencode($db);
}

header('Location: ' . $redirect);
exit;
PMASIGNON

    mkdir -p /etc/phpmyadmin/conf.d
    cat > /etc/phpmyadmin/conf.d/codehero-signon.php << 'PMACONFIG'
<?php
/**
 * CodeHero phpMyAdmin Single Sign-On Configuration
 */

// Override default server config to use signon auth
$cfg['Servers'][1]['auth_type'] = 'signon';
$cfg['Servers'][1]['SignonSession'] = 'PMA_signon';
$cfg['Servers'][1]['SignonURL'] = '/signon.php';
$cfg['Servers'][1]['LogoutURL'] = '/';
PMACONFIG

    log_info "phpMyAdmin signon configured"
fi

# Create phpMyAdmin nginx config if missing
if [ -d /usr/share/phpmyadmin ] && [ ! -f /etc/nginx/sites-available/codehero-phpmyadmin ]; then
    log_info "Creating phpMyAdmin nginx configuration..."

    cat > /etc/nginx/sites-available/codehero-phpmyadmin << 'NGINXPMA'
# CodeHero phpMyAdmin - Database Administration
# Port: 9454 (HTTPS)

server {
    listen 9454 ssl http2;
    server_name _;

    ssl_certificate /etc/codehero/ssl/cert.pem;
    ssl_certificate_key /etc/codehero/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;

    root /usr/share/phpmyadmin;
    index index.php index.html;

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    location / {
        try_files $uri $uri/ /index.php?$args;
    }

    location ~ \.php$ {
        include snippets/fastcgi-php.conf;
        fastcgi_pass unix:/var/run/php/php8.3-fpm.sock;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    }

    location ~ /\.ht {
        deny all;
    }

    location /setup {
        deny all;
    }
}
NGINXPMA

    ln -sf /etc/nginx/sites-available/codehero-phpmyadmin /etc/nginx/sites-enabled/
    log_info "phpMyAdmin nginx config created (port 9454)"
fi
