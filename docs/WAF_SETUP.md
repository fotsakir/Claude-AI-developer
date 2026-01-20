# Web Application Firewall (WAF) Setup

CodeHero includes optional ModSecurity WAF with OWASP Core Rule Set for protection against common web attacks.

## Features

- **ModSecurity 3.x** - Industry-standard open-source WAF
- **OWASP CRS 3.3.5** - ~2,800 rules covering OWASP Top 10
- **Automatic Protection** - SQL injection, XSS, command injection, path traversal
- **Custom Exclusions** - Pre-configured for CodeHero functionality

---

## Quick Install

### Option 1: Web UI (Recommended)

1. Go to **Dashboard** → **Packages**
2. Find **"WAF Security Setup"** in Configuration Scripts
3. Click **"Run Setup"**
4. Wait for installation to complete

### Option 2: Command Line

```bash
sudo /opt/codehero/scripts/setup_waf.sh
```

---

## What Gets Protected

| Port | Service | Protection |
|------|---------|------------|
| 9453 | Admin Panel | Full WAF |
| 9867 | Web Projects | Full WAF |
| 9454 | phpMyAdmin | Full WAF |

---

## Attack Protection

The WAF blocks these attack types:

| Attack Type | Examples |
|-------------|----------|
| **SQL Injection** | `' OR '1'='1`, `UNION SELECT`, `; DROP TABLE` |
| **Cross-Site Scripting (XSS)** | `<script>alert(1)</script>`, `javascript:` |
| **Local File Inclusion** | `../../../etc/passwd`, `file://` |
| **Remote File Inclusion** | `http://evil.com/shell.php` |
| **Command Injection** | `; ls -la`, `| cat /etc/passwd` |
| **Protocol Attacks** | HTTP smuggling, header injection |

---

## CodeHero Exclusions

To prevent false positives, these areas have relaxed or disabled WAF rules:

| Area | Reason |
|------|--------|
| `/socket.io/` | WebSocket connections |
| `/terminal` | Shell commands (expected) |
| `/console` | Claude output (contains code) |
| `/claude-assistant` | AI responses with code |
| `/editor/`, `/save_file` | Code editing |
| `/api/` | JSON payloads |
| `/ticket/`, `/send_message` | Code snippets in chat |

---

## Verify Installation

### Check Status

```bash
# Check if ModSecurity is loaded
nginx -t 2>&1 | grep -i modsecurity

# Expected output:
# ModSecurity-nginx v1.0.3 (rules loaded inline/local/remote: 0/2784/0)
```

### Test Protection

```bash
# Test XSS blocking (should return 403)
curl -k -o /dev/null -w "%{http_code}" "https://localhost:9453/?q=<script>alert(1)</script>"

# Test SQL injection blocking (should return 403)
curl -k -o /dev/null -w "%{http_code}" "https://localhost:9453/?id=1' OR '1'='1"
```

---

## Logs

WAF blocks are logged to Nginx error logs:

```bash
# View recent blocks
sudo tail -f /var/log/nginx/codehero-admin-error.log | grep ModSecurity

# Example log entry:
# ModSecurity: Access denied with code 403 (phase 2).
# Matched "Operator `Ge' with parameter `5' against variable `TX:ANOMALY_SCORE'
# [msg "Inbound Anomaly Score Exceeded (Total Score: 18)"]
```

---

## Configuration

### Main Config File

```
/etc/modsecurity/main.conf
```

This file includes:
- Base ModSecurity settings
- OWASP CRS rules
- CodeHero custom exclusions

### Adjust Sensitivity

Edit `/etc/modsecurity/crs/crs-setup.conf`:

```bash
# Lower = more strict, Higher = more permissive
# Default is 5 (balanced)
SecAction "id:900110,phase:1,nolog,pass,t:none,setvar:tx.inbound_anomaly_score_threshold=5"
```

### Add Custom Exclusions

Edit `/etc/modsecurity/main.conf` and add rules like:

```apache
# Allow specific parameter
SecRule REQUEST_URI "@contains /my-endpoint" \
    "id:1100,phase:1,pass,nolog,ctl:ruleRemoveById=942100"

# Disable WAF for specific path
SecRule REQUEST_URI "@beginsWith /unsafe-but-trusted/" \
    "id:1101,phase:1,pass,nolog,ctl:ruleEngine=Off"
```

After changes:
```bash
sudo nginx -t && sudo systemctl restart nginx
```

---

## Disable WAF

### Temporarily (per request)

Not recommended for production.

### Permanently

Remove ModSecurity lines from Nginx configs:

```bash
# Edit each config
sudo nano /etc/nginx/sites-available/codehero-admin

# Remove these lines:
#     modsecurity on;
#     modsecurity_rules_file /etc/modsecurity/main.conf;

# Test and restart
sudo nginx -t && sudo systemctl restart nginx
```

---

## Troubleshooting

### "403 Forbidden" on legitimate requests

1. Check the error log for the rule ID:
   ```bash
   sudo tail -20 /var/log/nginx/codehero-admin-error.log | grep ModSecurity
   ```

2. Find the rule ID (e.g., `[id "942100"]`)

3. Add exclusion to `/etc/modsecurity/main.conf`:
   ```apache
   SecRule REQUEST_URI "@contains /my-path" \
       "id:1200,phase:1,pass,nolog,ctl:ruleRemoveById=942100"
   ```

4. Restart Nginx:
   ```bash
   sudo nginx -t && sudo systemctl restart nginx
   ```

### Nginx won't start

```bash
# Check syntax
sudo nginx -t

# Common issues:
# - Missing unicode.mapping file
# - Invalid rule syntax in main.conf
# - Missing CRS files
```

### WAF not blocking attacks

```bash
# Verify ModSecurity is enabled
grep -r "modsecurity on" /etc/nginx/sites-available/

# Check SecRuleEngine is On (not DetectionOnly)
grep "SecRuleEngine" /etc/modsecurity/modsecurity.conf
```

---

## Uninstall

```bash
# Remove from Nginx configs
sudo sed -i '/modsecurity/d' /etc/nginx/sites-available/codehero-*

# Restart Nginx
sudo systemctl restart nginx

# Optionally remove packages
sudo apt remove libmodsecurity3 libnginx-mod-http-modsecurity
```

---

## Security Recommendations

1. **Keep CRS Updated** - Check for updates periodically
2. **Monitor Logs** - Review blocked requests for false positives
3. **Test After Changes** - Always verify WAF works after config changes
4. **Backup Configs** - Save working configurations before modifications

---

## Resources

- [ModSecurity Documentation](https://github.com/SpiderLabs/ModSecurity/wiki)
- [OWASP CRS Documentation](https://coreruleset.org/docs/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
