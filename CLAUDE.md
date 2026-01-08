# Claude Instructions - Fotios Claude System

**READ THIS BEFORE MAKING ANY CHANGES**

## Project Structure

```
/home/claude/fotios-claude-system/    <- SOURCE (make changes here)
/opt/fotios-claude/                   <- PRODUCTION (installed files)
/home/claude/fotios-claude-system-X.Y.Z.zip  <- BACKUPS (DON'T DELETE!)
```

## Workflow for Changes

### 1. Make changes in SOURCE
```
/home/claude/fotios-claude-system/
```

### 2. Copy to PRODUCTION
```bash
sudo cp /home/claude/fotios-claude-system/web/app.py /opt/fotios-claude/web/
sudo cp /home/claude/fotios-claude-system/scripts/claude-daemon.py /opt/fotios-claude/scripts/
sudo cp -r /home/claude/fotios-claude-system/web/templates/* /opt/fotios-claude/web/templates/
sudo cp /home/claude/fotios-claude-system/scripts/*.sh /opt/fotios-claude/scripts/
```

### 3. Restart services if needed
```bash
sudo systemctl restart fotios-claude-web fotios-claude-daemon
```

### 4. Update version numbers
- `README.md` - Header version
- `setup.sh` - Version comments and banner
- `CLAUDE_OPERATIONS.md` - Footer version
- `CHANGELOG.md` - New entry at the top

### 5. Create NEW zip (DON'T DELETE THE OLD ONE!)
```bash
cd /home/claude
# DON'T rm the old zip! It's a backup!
zip -r fotios-claude-system-X.Y.Z.zip fotios-claude-system -x "*.pyc" -x "*__pycache__*" -x "*.git*"
```

## Service Names (IMPORTANT!)

The correct names are:
- `fotios-claude-web` (NOT fotios-web)
- `fotios-claude-daemon` (NOT fotios-daemon)

## Check Sync with Production

```bash
diff /home/claude/fotios-claude-system/web/app.py /opt/fotios-claude/web/app.py
diff /home/claude/fotios-claude-system/scripts/claude-daemon.py /opt/fotios-claude/scripts/claude-daemon.py
```

## Check Services

```bash
systemctl status fotios-claude-web fotios-claude-daemon
```

## Version History

The zip files are BACKUPS. Keep them all:
- fotios-claude-system-2.20.0.zip
- fotios-claude-system-2.21.0.zip
- ... etc

## Files that must be SYNCED

| Source | Production |
|--------|------------|
| web/app.py | /opt/fotios-claude/web/app.py |
| scripts/claude-daemon.py | /opt/fotios-claude/scripts/claude-daemon.py |
| scripts/change-passwords.sh | /opt/fotios-claude/scripts/change-passwords.sh |
| web/templates/*.html | /opt/fotios-claude/web/templates/*.html |

## After Reboot

Check that services are running:
```bash
systemctl status fotios-claude-web fotios-claude-daemon mysql lshttpd
```

---
**Last updated:** 2026-01-08
**Version:** 2.26.2
