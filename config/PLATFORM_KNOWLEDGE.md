# Fotios Claude System - Platform Knowledge Base

**This file is automatically loaded by Claude Assistant to help users with platform questions, troubleshooting, and development.**

---

## Platform Overview

Fotios Claude System is a self-hosted autonomous AI coding platform that uses Claude AI to process development tickets. The system consists of:

- **Web App** (Flask + SocketIO) - Admin panel at port 9453
- **Daemon** - Background worker that processes tickets using Claude Code CLI
- **OpenLiteSpeed** - Web server with SSL termination
- **MySQL** - Database for projects, tickets, conversations

---

## File Locations

### Source Code (Edit Here)
| Component | Path |
|-----------|------|
| Web App | `/home/claude/fotios-claude-system/web/app.py` |
| Daemon | `/home/claude/fotios-claude-system/scripts/claude-daemon.py` |
| Templates | `/home/claude/fotios-claude-system/web/templates/*.html` |
| Config | `/home/claude/fotios-claude-system/config/` |
| Scripts | `/home/claude/fotios-claude-system/scripts/` |
| Database Schema | `/home/claude/fotios-claude-system/database/schema.sql` |
| Migrations | `/home/claude/fotios-claude-system/database/migrations/` |

### Production (Running)
| Component | Path |
|-----------|------|
| Web App | `/opt/fotios-claude/web/app.py` |
| Daemon | `/opt/fotios-claude/scripts/claude-daemon.py` |
| Templates | `/opt/fotios-claude/web/templates/*.html` |
| Config | `/etc/fotios-claude/system.conf` |
| SSL Certs | `/etc/fotios-claude/ssl/` |
| Logs | `/var/log/fotios-claude/` |

### Important Configuration Files
| File | Purpose |
|------|---------|
| `/etc/fotios-claude/system.conf` | Database credentials, MAX_PARALLEL_PROJECTS |
| `/etc/fotios-claude/global-context.md` | Global context sent to all projects |
| `/home/claude/fotios-claude-system/config/project-template.md` | Blueprint planner template |

---

## Services

### Service Names (IMPORTANT!)
```bash
# Correct service names
fotios-claude-web      # Flask web interface
fotios-claude-daemon   # Background ticket processor
mysql                  # Database
lshttpd                # OpenLiteSpeed
```

### Commands
```bash
# Check status
systemctl status fotios-claude-web fotios-claude-daemon mysql lshttpd

# Restart after code changes
sudo systemctl restart fotios-claude-web fotios-claude-daemon

# View logs
journalctl -u fotios-claude-web -f
journalctl -u fotios-claude-daemon -f
tail -f /var/log/fotios-claude/daemon.log
tail -f /var/log/fotios-claude/web.log
```

### Ports
| Port | Service | Purpose |
|------|---------|---------|
| 5000 | Flask (internal) | Web app |
| 9453 | OpenLiteSpeed | Admin Panel (SSL) |
| 9867 | OpenLiteSpeed | Project websites (SSL) |
| 7080 | OpenLiteSpeed | WebAdmin |
| 3306 | MySQL | Database |

---

## Database

### Connection
```bash
# Read credentials from config
source /etc/fotios-claude/system.conf
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME

# Or directly
mysql -u claude_user -p claude_knowledge
```

### Important Tables
| Table | Purpose |
|-------|---------|
| `projects` | Project definitions with database credentials |
| `tickets` | Work items/tasks |
| `conversation_messages` | Claude chat history per ticket |
| `execution_sessions` | Daemon run sessions |
| `execution_logs` | Detailed execution logs |
| `daemon_status` | Current daemon state (id=1) |
| `daemon_logs` | System logs |
| `user_messages` | Messages from user to Claude (kill commands) |
| `developers` | Admin users |
| `project_backups` | Backup records |

### Common Queries
```sql
-- System status
SELECT * FROM daemon_status WHERE id=1;

-- Open tickets
SELECT id, ticket_number, title, status FROM tickets WHERE status='open';

-- Stuck tickets (in_progress for too long)
SELECT * FROM tickets WHERE status='in_progress' AND updated_at < DATE_SUB(NOW(), INTERVAL 2 HOUR);

-- Reset stuck tickets
UPDATE tickets SET status='open' WHERE status='in_progress' AND updated_at < DATE_SUB(NOW(), INTERVAL 2 HOUR);

-- View conversation for ticket
SELECT role, content, created_at FROM conversation_messages WHERE ticket_id=? ORDER BY created_at;
```

---

## Features (v2.32.0)

### 1. SmartContext
Intelligent context management that auto-detects project structure and sends only relevant files to Claude.

**How it works:**
- Detects framework (React, Flask, Laravel, etc.)
- Finds relevant files based on task
- Reduces token usage by up to 70%

### 2. AI Failsafe (Watchdog)
Protection against runaway AI sessions:
- Monitors tickets every 30 minutes
- Detects stuck patterns (repeated errors, circular behavior)
- Auto-pauses problematic tickets
- Email notifications when issues detected

### 3. AI Project Manager (Blueprint Planner)
- "Plan with AI" button on Projects page
- Reads `/home/claude/fotios-claude-system/config/project-template.md`
- Guided questionnaire for requirements
- Generates complete blueprint: tech stack, database schema, API design

### 4. Claude Assistant
Interactive terminal for direct Claude access:
- **AI Model Selection**: Opus, Sonnet (default), Haiku
- **Popup Window**: Open in separate window for multi-monitor
- **Blueprint Mode**: Auto-loads project template

**File:** `web/templates/claude_assistant.html`

### 5. Web Terminal
Full Linux terminal in browser:
- Real PTY via WebSocket
- Popup support for multi-monitor
- Full sudo access (runs as user `claude`)
- 256-color support with xterm.js

**File:** `web/templates/terminal.html`

### 6. Kill Switch Commands
Instant control while Claude is working:
- `/stop` - Pause and wait for correction (shows immediately)
- `/skip` - Stop and reopen ticket (shows immediately)
- `/done` - Force complete ticket (shows immediately)

**Implementation:** Commands saved to `user_messages` table and broadcast via SocketIO

---

## Development Workflow

### Making Changes

1. **Edit in source directory:**
   ```
   /home/claude/fotios-claude-system/
   ```

2. **Deploy to production:**
   ```bash
   sudo cp /home/claude/fotios-claude-system/web/app.py /opt/fotios-claude/web/
   sudo cp /home/claude/fotios-claude-system/scripts/claude-daemon.py /opt/fotios-claude/scripts/
   sudo cp -r /home/claude/fotios-claude-system/web/templates/* /opt/fotios-claude/web/templates/
   ```

3. **Restart services:**
   ```bash
   sudo systemctl restart fotios-claude-web fotios-claude-daemon
   ```

4. **Verify:**
   ```bash
   systemctl status fotios-claude-web --no-pager | head -10
   ```

### Creating New Versions

1. Update these files:
   - `VERSION` - Single source of truth
   - `web/app.py` - VERSION constant
   - `README.md` - Badge version and zip filename
   - `INSTALL.md` - Zip filename and footer
   - `CHANGELOG.md` - New entry at top

2. Create zip:
   ```bash
   cd /home/claude
   zip -r fotios-claude-system-X.Y.Z.zip fotios-claude-system -x "*.pyc" -x "*__pycache__*" -x "*.git*"
   ```

---

## Troubleshooting

### Quick Health Check
```bash
echo "=== Health Check ===" && \
systemctl is-active mysql > /dev/null && echo "MySQL: OK" || echo "MySQL: FAILED" && \
systemctl is-active fotios-claude-web > /dev/null && echo "Web: OK" || echo "Web: FAILED" && \
systemctl is-active fotios-claude-daemon > /dev/null && echo "Daemon: OK" || echo "Daemon: FAILED"
```

### Daemon Not Processing Tickets
```bash
# 1. Check if running
sudo systemctl status fotios-claude-daemon

# 2. Check logs
journalctl -u fotios-claude-daemon -n 50

# 3. Check daemon_status table
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME -e "SELECT * FROM daemon_status"

# 4. Restart
sudo systemctl restart fotios-claude-daemon
```

### Web Panel Not Accessible
```bash
# 1. Check Flask
sudo systemctl status fotios-claude-web

# 2. Check if listening
ss -tlnp | grep 5000

# 3. Check OpenLiteSpeed
sudo /usr/local/lsws/bin/lswsctrl status

# 4. Restart
sudo systemctl restart fotios-claude-web
sudo systemctl restart lsws
```

### Tickets Stuck in in_progress
```sql
-- Find stuck tickets
SELECT id, ticket_number, updated_at FROM tickets WHERE status='in_progress';

-- Reset them
UPDATE tickets SET status='open' WHERE status='in_progress' AND updated_at < DATE_SUB(NOW(), INTERVAL 2 HOUR);

-- Mark sessions as stuck
UPDATE execution_sessions SET status='stuck', ended_at=NOW() WHERE status='running' AND started_at < DATE_SUB(NOW(), INTERVAL 2 HOUR);
```

### Claude Assistant Not Starting
```bash
# Check if Claude Code CLI is installed
which claude

# If not installed:
/opt/fotios-claude/scripts/install-claude-code.sh

# Check API key
cat ~/.claude/.credentials.json
```

### WebSocket Connection Issues
```bash
# Check if Flask SocketIO is running
netstat -tlnp | grep 5000

# Check OpenLiteSpeed proxy config
cat /usr/local/lsws/conf/vhosts/vhost-admin.conf

# Restart services
sudo systemctl restart fotios-claude-web lsws
```

---

## Code Architecture

### Web App (app.py)
- Flask + Flask-SocketIO
- Routes: `/dashboard`, `/projects`, `/tickets`, `/console`, `/terminal`, `/claude-assistant`
- WebSocket namespaces for real-time updates
- Session-based authentication with bcrypt

### Daemon (claude-daemon.py)
- Multi-worker ticket processor
- Uses `select.select()` for non-blocking I/O
- Checks `user_messages` table for kill commands
- Creates execution sessions and logs

### Key Patterns

**Broadcasting to rooms:**
```python
socketio.emit('new_message', msg, room=f'ticket_{ticket_id}')
socketio.emit('new_message', msg, room='console')
```

**Non-blocking I/O:**
```python
ready, _, _ = select.select([process.stdout], [], [], 1.0)
```

**Database cursor:**
```python
conn = get_db()
cursor = conn.cursor(dictionary=True)
cursor.execute("SELECT * FROM tickets WHERE id = %s", (ticket_id,))
ticket = cursor.fetchone()
cursor.close(); conn.close()
```

---

## Template Files

| Template | Purpose |
|----------|---------|
| `dashboard.html` | Main dashboard with stats |
| `projects.html` | Project list, create/edit, Plan with AI button |
| `project_detail.html` | Single project view with tickets |
| `tickets_list.html` | All tickets with filters |
| `ticket_detail.html` | Ticket chat interface |
| `console.html` | Live console for all tickets |
| `terminal.html` | Linux terminal (xterm.js) |
| `claude_assistant.html` | Interactive Claude chat with model selection |
| `history.html` | Execution history |
| `session_detail.html` | Session details with logs |

---

## API Endpoints

### Web Routes
| Method | Path | Description |
|--------|------|-------------|
| GET | `/login` | Login page |
| GET | `/dashboard` | Main dashboard |
| GET | `/tickets` | Tickets list |
| GET | `/ticket/<id>` | Ticket detail |
| GET | `/projects` | Projects list |
| GET | `/project/<id>` | Project detail |
| GET | `/console` | Live console |
| GET | `/terminal` | Web terminal |
| GET | `/claude-assistant` | Claude Assistant |
| GET | `/history` | Execution history |

### API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/projects` | Create project |
| PUT | `/api/project/<id>` | Update project |
| POST | `/api/tickets` | Create ticket |
| POST | `/api/ticket/<id>/approve` | Approve ticket |
| POST | `/api/ticket/<id>/reopen` | Reopen ticket |
| POST | `/api/send_message` | Send message to ticket |
| GET | `/api/daemon/status` | Daemon status |

---

## Emergency Procedures

### Stop All Processing
```bash
sudo systemctl stop fotios-claude-daemon
```

### Reset Everything
```sql
UPDATE tickets SET status='open' WHERE status='in_progress';
UPDATE daemon_status SET status='stopped', current_ticket_id=NULL WHERE id=1;
UPDATE execution_sessions SET status='stopped', ended_at=NOW() WHERE status='running';
```

### Database Backup
```bash
source /etc/fotios-claude/system.conf
mysqldump -u $DB_USER -p$DB_PASSWORD $DB_NAME > /tmp/backup_$(date +%Y%m%d_%H%M%S).sql
```

---

## Documentation Files

| File | Description |
|------|-------------|
| `README.md` | Main documentation, features, installation |
| `INSTALL.md` | Detailed installation guide |
| `CLAUDE_OPERATIONS.md` | Operations and troubleshooting guide |
| `CLAUDE_DEV_NOTES.md` | Development notes for Claude |
| `CLAUDE.md` | Development workflow instructions |
| `docs/USER_GUIDE.md` | User guide with screenshots |
| `docs/VM_INSTALLATION.md` | VM installation for all platforms |
| `CHANGELOG.md` | Version history |

---

## Getting Help

When users ask questions, check these files:

1. **Platform usage** - `docs/USER_GUIDE.md`
2. **Troubleshooting** - `CLAUDE_OPERATIONS.md`
3. **Development** - `CLAUDE_DEV_NOTES.md`, `CLAUDE.md`
4. **Installation** - `INSTALL.md`, `docs/VM_INSTALLATION.md`
5. **Features** - `README.md`, `CHANGELOG.md`

---

*Last Updated: 2026-01-10*
*Version: 2.32.0*
