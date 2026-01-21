# Domain & SSL Setup Guide

Configure custom domains with Let's Encrypt SSL certificates for CodeHero.

## Overview

CodeHero runs on two ports by default:
- **Port 9453** - Admin Panel (Dashboard)
- **Port 9867** - Web Apps (Your projects)

This script allows you to:
- Add custom domain names
- Get free Let's Encrypt SSL certificates
- Password-protect web apps from external access
- Manage certificate renewals

## Quick Start

### Interactive Mode (Recommended)

```bash
sudo /opt/codehero/scripts/setup_domain.sh
```

This opens a menu:
```
╔═══════════════════════════════════════════════════════════╗
║           CODEHERO - Domain & SSL Setup                   ║
╚═══════════════════════════════════════════════════════════╝

What would you like to configure?

  1) Admin Panel domain & SSL
  2) Web Apps domain & SSL
  3) Web Apps password protection
  4) Renew SSL certificates
  5) Auto-renewal settings
  6) Show current status
  7) Revert to self-signed certificates
  0) Exit
```

### Command Line Mode

```bash
# Configure admin panel with domain
sudo ./setup_domain.sh --admin --domain example.com --port 9453

# Configure web apps with same domain
sudo ./setup_domain.sh --webapps --domain example.com --port 9867

# Enable password protection
sudo ./setup_domain.sh --password

# Check current status
sudo ./setup_domain.sh --status
```

## Prerequisites

Before setting up a domain:

1. **DNS Configuration** - Point your domain to your server's IP
   ```
   A Record: example.com → YOUR_SERVER_IP
   ```

2. **Port Access** - Ensure ports 80, 443, 9453, and 9867 are open
   ```bash
   # Check if ports are accessible
   sudo ufw status
   ```

3. **Wait for DNS** - DNS propagation can take up to 48 hours (usually minutes)
   ```bash
   # Verify DNS is working
   dig example.com
   ```

## Setup Scenarios

### Scenario 1: Same Domain, Different Ports

Most common setup - one domain for everything:

```bash
# Step 1: Configure admin panel
sudo ./setup_domain.sh --admin --domain mysite.com --port 9453

# Step 2: Configure web apps (reuses the certificate)
sudo ./setup_domain.sh --webapps --domain mysite.com --port 9867
```

Access:
- Dashboard: `https://mysite.com:9453`
- Web Apps: `https://mysite.com:9867`

### Scenario 2: Different Domains

Separate domains for admin and projects:

```bash
# Admin panel
sudo ./setup_domain.sh --admin --domain admin.mysite.com --port 9453

# Web apps
sudo ./setup_domain.sh --webapps --domain apps.mysite.com --port 9867
```

### Scenario 3: IP Access Only (Default)

Keep using IP addresses with self-signed certificates:

```bash
# Just check status
sudo ./setup_domain.sh --status
```

Access:
- Dashboard: `https://YOUR_IP:9453`
- Web Apps: `https://YOUR_IP:9867`

## Password Protection

Protect your web apps from public access while allowing local/LAN access without password.

### Enable Password Protection

```bash
# Interactive
sudo ./setup_domain.sh
# Choose option 3

# Or via command line
sudo ./setup_domain.sh --password
```

You'll be prompted to create a password for the `admin` user.

### How It Works

| Access From | Password Required? |
|-------------|-------------------|
| localhost (127.0.0.1) | No |
| LAN (192.168.x.x, 10.x.x.x) | No |
| External IPs | Yes |

### Custom Whitelist

Add more IPs that can access without password:

```bash
sudo ./setup_domain.sh --password --whitelist "127.0.0.1,192.168.0.0/16,10.0.0.0/8,203.0.113.50"
```

### Disable Password Protection

```bash
sudo ./setup_domain.sh --no-password
```

## Certificate Management

### Check Certificate Status

```bash
sudo ./setup_domain.sh --status
```

Shows:
```
Admin Panel:
  Port: 9453
  URLs: https://IP:9453
        https://example.com:9453
  SSL:  letsencrypt
  Cert: Expires in 45 days

Web Apps:
  Port: 9867
  URLs: https://IP:9867
        https://example.com:9867
  SSL:  letsencrypt
  Cert: Expires in 45 days
  Auth: true
```

### Manual Certificate Renewal

```bash
sudo ./setup_domain.sh --renew
```

Shows expiry dates and prompts to renew if needed.

### Auto-Renewal

Let's Encrypt certificates expire every 90 days. Auto-renewal handles this automatically.

```bash
# Enable auto-renewal (recommended)
sudo ./setup_domain.sh --auto-renew on

# Disable auto-renewal
sudo ./setup_domain.sh --auto-renew off

# Check auto-renewal status
sudo ./setup_domain.sh --renew-status
```

When enabled, certbot runs twice daily and renews certificates when they have less than 30 days remaining.

## Reverting to Self-Signed

If you need to remove domain configuration:

```bash
# Revert both admin and web apps
sudo ./setup_domain.sh --revert

# Revert only admin panel
sudo ./setup_domain.sh --revert admin

# Revert only web apps
sudo ./setup_domain.sh --revert webapps
```

This:
- Removes domain from nginx config
- Switches back to self-signed certificate
- Keeps Let's Encrypt certificates on disk (for future use)

## Command Reference

| Command | Description |
|---------|-------------|
| `--admin` | Configure admin panel |
| `--webapps` | Configure web apps |
| `--domain DOMAIN` | Specify domain name |
| `--port PORT` | Specify port number |
| `--email EMAIL` | Email for Let's Encrypt |
| `--password` | Enable password protection |
| `--no-password` | Disable password protection |
| `--whitelist IPS` | IPs to whitelist (comma-separated) |
| `--renew` | Renew certificates |
| `--renew-status` | Check renewal status |
| `--auto-renew on/off` | Enable/disable auto-renewal |
| `--status` | Show current configuration |
| `--revert [target]` | Revert to self-signed |
| `-h, --help` | Show help |

## Files & Locations

| File | Purpose |
|------|---------|
| `/etc/codehero/domains.conf` | Domain configuration |
| `/etc/codehero/.htpasswd` | Password file for web apps |
| `/etc/codehero/ssl/` | Self-signed certificates |
| `/etc/letsencrypt/live/` | Let's Encrypt certificates |
| `/var/backups/codehero/domain/` | Configuration backups |
| `/etc/nginx/sites-available/codehero-admin` | Admin nginx config |
| `/etc/nginx/sites-available/codehero-projects` | Web apps nginx config |

## Troubleshooting

### Certificate Failed to Obtain

**Error:** `Failed to obtain certificate for domain`

**Causes:**
1. DNS not pointing to server
2. Port 80 blocked by firewall
3. Domain already has certificate elsewhere

**Solutions:**
```bash
# Check DNS
dig +short example.com

# Check port 80
sudo ufw allow 80/tcp
curl -I http://example.com

# Check nginx isn't blocking
sudo systemctl stop nginx
sudo certbot certonly --standalone -d example.com
sudo systemctl start nginx
```

### Nginx Configuration Failed

**Error:** `Nginx configuration test failed`

**Solution:**
```bash
# Check nginx error
sudo nginx -t

# View detailed error
sudo tail -50 /var/log/nginx/error.log

# Restore from backup
sudo ./setup_domain.sh --revert
```

### Password Not Working

**Error:** Can access without password from external IP

**Check:**
```bash
# View auth snippet
cat /etc/nginx/snippets/codehero-webapps-auth.conf

# Verify it's included in config
grep -r "codehero-webapps-auth" /etc/nginx/sites-available/
```

### Certificate Not Auto-Renewing

**Check:**
```bash
# Verify timer is running
sudo systemctl status certbot.timer

# Test renewal (dry run)
sudo certbot renew --dry-run

# Check certbot logs
sudo journalctl -u certbot
```

## Security Notes

1. **Always use HTTPS** - HTTP traffic is not supported
2. **Keep auto-renewal enabled** - Expired certificates cause access issues
3. **Use password protection** - Especially if web apps are publicly accessible
4. **Backup before changes** - Script creates automatic backups
5. **Monitor certificate expiry** - Check status periodically

## Related

- [WAF Setup](WAF_SETUP.md) - Web Application Firewall
- [2FA Setup](2FA_SETUP.md) - Two-Factor Authentication
- [User Guide](USER_GUIDE.md) - General usage guide
