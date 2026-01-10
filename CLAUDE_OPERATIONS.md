# Claude Operations Guide - Fotios Claude System

**This guide is for Claude (AI) to manage and operate the Fotios Claude System platform.**

## Quick Reference

### Database Connection
```bash
# Connect to MySQL
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME

# Or read credentials from config
source /etc/fotios-claude/system.conf 2>/dev/null || source /etc/fotios-claude/credentials.conf
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME
```

### Service Commands
```bash
# Web Panel (Flask)
sudo systemctl start|stop|restart|status fotios-claude-web

# Daemon (Ticket Processor)
sudo systemctl start|stop|restart|status fotios-claude-daemon

# OpenLiteSpeed
sudo systemctl restart lsws
sudo /usr/local/lsws/bin/lswsctrl status
```

---

## 0. Post-Restart Checklist

**When the user asks "did everything start after reboot?" or similar, run these checks:**

### Quick Health Check (One Command)
```bash
echo "=== FOTIOS CLAUDE SYSTEM - Health Check ===" && \
echo "" && \
echo "Services:" && \
systemctl is-active mysql > /dev/null 2>&1 && echo "  MySQL:           ✓ running" || echo "  MySQL:           ✗ NOT RUNNING" && \
systemctl is-active fotios-claude-web > /dev/null 2>&1 && echo "  Flask Web:       ✓ running" || echo "  Flask Web:       ✗ NOT RUNNING" && \
systemctl is-active fotios-claude-daemon > /dev/null 2>&1 && echo "  Daemon:          ✓ running" || echo "  Daemon:          ✗ NOT RUNNING" && \
pgrep -f "litespeed" > /dev/null && echo "  OpenLiteSpeed:   ✓ running" || echo "  OpenLiteSpeed:   ✗ NOT RUNNING" && \
echo "" && \
echo "Ports:" && \
ss -tlnp | grep -q ":5000 " && echo "  :5000 (Flask):   ✓ listening" || echo "  :5000 (Flask):   ✗ NOT listening" && \
ss -tlnp | grep -q ":9453 " && echo "  :9453 (Admin):   ✓ listening" || echo "  :9453 (Admin):   ✗ NOT listening" && \
ss -tlnp | grep -q ":9867 " && echo "  :9867 (Projects):✓ listening" || echo "  :9867 (Projects):✗ NOT listening" && \
ss -tlnp | grep -q ":3306 " && echo "  :3306 (MySQL):   ✓ listening" || echo "  :3306 (MySQL):   ✗ NOT listening" && \
echo "" && \
echo "Database:" && \
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME -e "SELECT 1" > /dev/null 2>&1 && echo "  Connection:      ✓ OK" || echo "  Connection:      ✗ FAILED" && \
echo "" && \
echo "Daemon Status:" && \
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME -N -e "SELECT CONCAT('  Status: ', status) FROM daemon_status WHERE id=1" 2>/dev/null && \
echo "" && \
echo "Tickets:" && \
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME -N -e "SELECT CONCAT('  Open: ', COUNT(*)) FROM tickets WHERE status='open'" 2>/dev/null && \
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME -N -e "SELECT CONCAT('  In Progress: ', COUNT(*)) FROM tickets WHERE status='in_progress'" 2>/dev/null && \
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME -N -e "SELECT CONCAT('  Pending Review: ', COUNT(*)) FROM tickets WHERE status='pending_review'" 2>/dev/null
```

### Individual Service Checks

#### 1. MySQL
```bash
# Check if running
sudo systemctl status mysql

# Test connection
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME -e "SELECT 1"

# If not running:
sudo systemctl start mysql
```

#### 2. Flask Web Panel (fotios-claude-web)
```bash
# Check if running
sudo systemctl status fotios-claude-web

# Check if port 5000 is listening
ss -tlnp | grep :5000

# Check logs for errors
journalctl -u fotios-claude-web -n 20

# If not running:
sudo systemctl start fotios-claude-web
```

#### 3. Claude Daemon (fotios-claude-daemon)
```bash
# Check if running
sudo systemctl status fotios-claude-daemon

# Check daemon status in database
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME -e "SELECT * FROM daemon_status"

# Check logs
journalctl -u fotios-claude-daemon -n 20

# If not running:
sudo systemctl start fotios-claude-daemon
```

#### 4. OpenLiteSpeed
```bash
# Check if running
sudo /usr/local/lsws/bin/lswsctrl status
pgrep -f litespeed

# Check if ports are listening
ss -tlnp | grep -E ":(9453|9867|7080)"

# If not running:
sudo /usr/local/lsws/bin/lswsctrl start
```

#### 5. Test Web Access
```bash
# Test Flask internally
curl -s -k https://localhost:9453/login | head -5

# Test from command line (should return HTML)
curl -s -k https://localhost:9453/login | grep -o "<title>.*</title>"
```

### Fix Common Issues After Restart

#### All services not starting
```bash
# Start all services in order
sudo systemctl start mysql
sleep 2
sudo systemctl start fotios-claude-web
sleep 2
sudo systemctl start fotios-claude-daemon
sudo /usr/local/lsws/bin/lswsctrl start
```

#### Daemon stuck or not processing
```bash
# Reset daemon status
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME -e "UPDATE daemon_status SET status='stopped', current_ticket_id=NULL WHERE id=1"

# Reset any stuck tickets
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME -e "UPDATE tickets SET status='open' WHERE status='in_progress'"

# Restart daemon
sudo systemctl restart fotios-claude-daemon
```

#### Check if services are enabled for auto-start
```bash
systemctl is-enabled mysql
systemctl is-enabled fotios-claude-web
systemctl is-enabled fotios-claude-daemon
systemctl is-enabled lshttpd

# Enable if not:
sudo systemctl enable mysql fotios-claude-web fotios-claude-daemon lshttpd
```

### Expected Output When Everything is OK
```
=== FOTIOS CLAUDE SYSTEM - Health Check ===

Services:
  MySQL:           ✓ running
  Flask Web:       ✓ running
  Daemon:          ✓ running
  OpenLiteSpeed:   ✓ running

Ports:
  :5000 (Flask):   ✓ listening
  :9453 (Admin):   ✓ listening
  :9867 (Projects):✓ listening
  :3306 (MySQL):   ✓ listening

Database:
  Connection:      ✓ OK

Daemon Status:
  Status: running

Tickets:
  Open: X
  In Progress: X
  Pending Review: X
```

---

## Global Context Configuration

The daemon loads a global context file that provides environment information to Claude for ALL projects. This prevents Claude from making incorrect assumptions about installed tools, servers, or ports.

### File Location
```
/etc/fotios-claude/global-context.md
```

### How to Edit
```bash
# Edit the global context
sudo nano /etc/fotios-claude/global-context.md

# Changes take effect on next ticket (no restart needed)
# The daemon reloads on startup, but workers pick up the context when created
```

### What to Include
- Server environment (web server type, PHP version, OS)
- Available ports and their purposes
- Pre-installed tools (MySQL, Composer, Git, etc.)
- Tools that are NOT installed (Node.js, npm, Docker, etc.)
- Important rules for Claude to follow

### Example Content
```markdown
## Server Environment
- Web Server: OpenLiteSpeed
- PHP Version: LSPHP 8.1

## NOT Installed
- Node.js / npm
- Playwright
- Docker

## Rules
- Never install system packages without permission
- Always check if a tool exists before using it
```

---

## 1. System Architecture

### Components
| Component | Location | Purpose |
|-----------|----------|---------|
| Flask Web App | `/opt/fotios-claude/web/app.py` | Admin panel UI |
| Daemon | `/opt/fotios-claude/scripts/claude-daemon.py` | Processes tickets with Claude Code |
| CLI | `/opt/fotios-claude/scripts/claude-cli.py` | Command-line interface |
| Templates | `/opt/fotios-claude/web/templates/` | HTML templates |
| Config | `/etc/fotios-claude/system.conf` | System configuration |
| SSL Certs | `/etc/fotios-claude/ssl/` | SSL certificates |

### Services
| Service | Port | Description |
|---------|------|-------------|
| fotios-claude-web | 5000 (internal) | Flask + SocketIO |
| fotios-claude-daemon | - | Background ticket processor |
| lsws | 9453, 9867 | OpenLiteSpeed (SSL proxy) |

### Database Tables
| Table | Purpose |
|-------|---------|
| `projects` | Project definitions with database credentials |
| `tickets` | Work items |
| `conversation_messages` | Claude chat history per ticket |
| `execution_sessions` | Daemon run sessions |
| `execution_logs` | Detailed execution logs |
| `daemon_status` | Current daemon state (id=1) |
| `developers` | Admin users |
| `user_messages` | Messages from user to Claude (via console) |

### Project Database Credentials
Each project can have auto-created or manually configured database credentials:
| Field | Description |
|-------|-------------|
| `db_host` | Database host (default: localhost) |
| `db_name` | Database name (e.g., ecom_db) |
| `db_user` | Database username (e.g., ecom_user) |
| `db_password` | Database password (auto-generated 16 chars) |

---

## 2. Common Database Queries

### Check System Status
```sql
-- Overall status
SELECT
  (SELECT COUNT(*) FROM projects WHERE status='active') as active_projects,
  (SELECT COUNT(*) FROM tickets WHERE status='open') as open_tickets,
  (SELECT COUNT(*) FROM tickets WHERE status='in_progress') as in_progress,
  (SELECT COUNT(*) FROM tickets WHERE status='pending_review') as pending_review,
  (SELECT COUNT(*) FROM tickets WHERE status='done') as done_tickets;

-- Daemon status
SELECT * FROM daemon_status WHERE id=1;
```

### Projects
```sql
-- List all projects with database info
SELECT id, code, name, status, db_name, db_user, db_host FROM projects ORDER BY created_at DESC;

-- List active projects
SELECT id, code, name FROM projects WHERE status='active';

-- Get project database credentials
SELECT code, db_host, db_name, db_user, db_password FROM projects WHERE id=?;

-- Update project database credentials (for remote database)
UPDATE projects SET
  db_host='remote-server.com',
  db_name='myapp_production',
  db_user='prod_user',
  db_password='secure_password'
WHERE id=?;

-- Archive a project
UPDATE projects SET status='archived', updated_at=NOW() WHERE id=?;

-- Reopen a project
UPDATE projects SET status='active', updated_at=NOW() WHERE id=?;

-- Get project with ticket count
SELECT p.*, COUNT(t.id) as ticket_count
FROM projects p
LEFT JOIN tickets t ON p.id = t.project_id
GROUP BY p.id;
```

### Tickets
```sql
-- List all tickets
SELECT t.id, t.ticket_number, t.title, t.status, t.priority, p.code as project
FROM tickets t
JOIN projects p ON t.project_id = p.id
ORDER BY t.created_at DESC;

-- Tickets by status
SELECT * FROM tickets WHERE status='open' ORDER BY priority DESC, created_at ASC;
SELECT * FROM tickets WHERE status='in_progress';
SELECT * FROM tickets WHERE status='pending_review';

-- Stuck tickets (in_progress for too long)
SELECT * FROM tickets
WHERE status='in_progress'
AND updated_at < DATE_SUB(NOW(), INTERVAL 2 HOUR);

-- Pending review past deadline
SELECT * FROM tickets
WHERE status='pending_review'
AND review_deadline < NOW();

-- Update ticket status
UPDATE tickets SET status='open', updated_at=NOW() WHERE id=?;
UPDATE tickets SET status='done', closed_at=NOW(), close_reason='approved' WHERE id=?;

-- Reset stuck ticket
UPDATE tickets SET status='open', updated_at=NOW() WHERE id=? AND status='in_progress';
```

### Conversations
```sql
-- Get conversation for a ticket
SELECT role, content, tool_name, created_at
FROM conversation_messages
WHERE ticket_id=?
ORDER BY created_at;

-- Last N messages
SELECT role, LEFT(content, 200) as content, created_at
FROM conversation_messages
WHERE ticket_id=?
ORDER BY created_at DESC
LIMIT 20;

-- Clear conversation (start fresh)
DELETE FROM conversation_messages WHERE ticket_id=?;
```

### Sessions & Logs
```sql
-- Recent sessions
SELECT s.id, s.ticket_id, t.ticket_number, s.status, s.started_at, s.ended_at
FROM execution_sessions s
LEFT JOIN tickets t ON s.ticket_id = t.id
ORDER BY s.started_at DESC
LIMIT 20;

-- Logs for a session
SELECT log_type, message, created_at
FROM execution_logs
WHERE session_id=?
ORDER BY created_at;

-- Running sessions
SELECT * FROM execution_sessions WHERE status='running';
```

### User Messages (Console Input)
```sql
-- Pending messages for a ticket
SELECT * FROM user_messages WHERE ticket_id=? AND processed=0;

-- Mark as processed
UPDATE user_messages SET processed=1 WHERE id=?;
```

---

## 3. Daemon Management

### Understanding the Daemon
The daemon (`claude-daemon.py`) is a multi-worker system that:
1. Picks up tickets with status `open` (priority order)
2. Creates an execution session
3. Runs Claude Code CLI to process the ticket
4. Sets status to `pending_review` when done
5. Auto-closes tickets after 7 days if not reviewed

### Worker Configuration
```bash
# Check current max workers (in config)
grep MAX_PARALLEL /etc/fotios-claude/system.conf
# MAX_PARALLEL_PROJECTS=3

# To change: edit config and restart daemon
sudo nano /etc/fotios-claude/system.conf
sudo systemctl restart fotios-claude-daemon
```

### Daemon Control
```bash
# Check status
sudo systemctl status fotios-claude-daemon
ps aux | grep claude-daemon

# View logs (live)
journalctl -u fotios-claude-daemon -f

# View recent logs
journalctl -u fotios-claude-daemon -n 100

# Restart daemon
sudo systemctl restart fotios-claude-daemon

# Stop daemon (tickets in progress will be marked stuck)
sudo systemctl stop fotios-claude-daemon
```

### Check Active Workers
```sql
-- See what the daemon is working on
SELECT * FROM daemon_status;

-- See tickets currently being processed
SELECT t.id, t.ticket_number, t.title, t.status, s.started_at
FROM tickets t
JOIN execution_sessions s ON s.ticket_id = t.id
WHERE t.status = 'in_progress' AND s.status = 'running';
```

### Fix Stuck Tickets
```sql
-- Find stuck tickets
SELECT id, ticket_number, title, status, updated_at
FROM tickets
WHERE status='in_progress'
AND updated_at < DATE_SUB(NOW(), INTERVAL 1 HOUR);

-- Reset them to open
UPDATE tickets SET status='open' WHERE status='in_progress'
AND updated_at < DATE_SUB(NOW(), INTERVAL 1 HOUR);

-- Also close any orphaned sessions
UPDATE execution_sessions SET status='stuck', ended_at=NOW()
WHERE status='running' AND started_at < DATE_SUB(NOW(), INTERVAL 1 HOUR);
```

---

## 4. Web Panel Management

### Flask App
```bash
# Check status
sudo systemctl status fotios-claude-web
curl -k https://localhost:9453/login

# Restart
sudo systemctl restart fotios-claude-web

# View logs
journalctl -u fotios-claude-web -f

# Test Flask directly
cd /opt/fotios-claude/web && python3 app.py
```

### Templates Location
```
/opt/fotios-claude/web/templates/
├── login.html              # Login page
├── dashboard.html          # Main dashboard with stats
├── tickets_list.html       # All tickets with filters
├── ticket_detail.html      # Single ticket view + chat
├── projects.html           # Project list + "Plan with AI" button
├── project_detail.html     # Project view + tickets
├── console.html            # Live console for tickets
├── terminal.html           # Web Terminal (xterm.js)
├── claude_assistant.html   # Claude Assistant with model selection
├── history.html            # Execution history
└── session_detail.html     # Session details + logs
```

### WebSocket (SocketIO)
The console page uses WebSocket for real-time updates:
- Events: `ticket_output`, `daemon_status`, `execution_complete`
- Namespace: default `/`

---

## 5. Ticket Status Workflow

```
NEW TICKET
    |
    v
 [open] -----> Daemon picks it up
    |
    v
 [in_progress] -----> Claude Code processes it
    |
    v
 [pending_review] -----> Waiting for human review (7 day deadline)
    |
    +---> [Approve] -----> [done] (close_reason: approved)
    |
    +---> [Request Changes] -----> [in_progress] (goes back to daemon)
    |
    +---> [Auto-approve after 7 days] -----> [done] (close_reason: auto_approved_7days)
```

### Manually Change Status
```sql
-- Reopen a closed ticket
UPDATE tickets SET status='open', closed_at=NULL, close_reason=NULL WHERE id=?;

-- Approve pending review
UPDATE tickets SET status='done', closed_at=NOW(), close_reason='approved' WHERE id=?;

-- Skip a ticket
UPDATE tickets SET status='skipped', closed_at=NOW(), close_reason='skipped' WHERE id=?;

-- Force close a stuck ticket
UPDATE tickets SET status='failed', closed_at=NOW(), close_reason='failed' WHERE id=?;
```

---

## 6. Troubleshooting

### Daemon Not Processing Tickets
```bash
# 1. Check if daemon is running
sudo systemctl status fotios-claude-daemon

# 2. Check logs for errors
journalctl -u fotios-claude-daemon -n 50

# 3. Check if there are open tickets
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME -e \
  "SELECT COUNT(*) FROM tickets WHERE status='open'"

# 4. Check daemon_status table
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME -e \
  "SELECT * FROM daemon_status"

# 5. Restart daemon
sudo systemctl restart fotios-claude-daemon
```

### Web Panel Not Accessible
```bash
# 1. Check Flask service
sudo systemctl status fotios-claude-web

# 2. Check if Flask is listening
netstat -tlnp | grep 5000

# 3. Check OpenLiteSpeed
sudo /usr/local/lsws/bin/lswsctrl status

# 4. Check OLS proxy config
cat /usr/local/lsws/conf/vhosts/vhost-admin.conf

# 5. Restart services
sudo systemctl restart fotios-claude-web
sudo systemctl restart lsws
```

### Database Connection Issues
```bash
# 1. Check MySQL is running
sudo systemctl status mysql

# 2. Test connection
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME -e "SELECT 1"

# 3. Check credentials
cat /etc/fotios-claude/system.conf | grep DB_

# 4. Reset password if needed
sudo mysql -e "ALTER USER 'claude_user'@'localhost' IDENTIFIED BY 'newpassword';"
```

### Tickets Stuck in in_progress
```sql
-- 1. Find stuck tickets
SELECT id, ticket_number, updated_at FROM tickets WHERE status='in_progress';

-- 2. Check if there's an active session
SELECT * FROM execution_sessions WHERE status='running';

-- 3. Reset stuck tickets
UPDATE tickets SET status='open' WHERE status='in_progress'
AND updated_at < DATE_SUB(NOW(), INTERVAL 2 HOUR);

-- 4. Mark sessions as stuck
UPDATE execution_sessions SET status='stuck', ended_at=NOW()
WHERE status='running' AND started_at < DATE_SUB(NOW(), INTERVAL 2 HOUR);
```

---

## 7. Common Operations

### Create a New Project
```sql
INSERT INTO projects (name, code, description, project_type, web_path, context, status)
VALUES ('My Project', 'MYPROJ', 'Description here', 'web', '/var/www/projects/myproj',
        'Context for Claude...', 'active');
```

### Create a New Ticket
```sql
-- First get project_id
SELECT id FROM projects WHERE code='MYPROJ';

-- Then create ticket (auto-generates ticket_number via trigger or app)
INSERT INTO tickets (project_id, ticket_number, title, description, priority, status)
VALUES (1, 'MYPROJ-001', 'Build login page', 'Create a login page with...', 'high', 'open');
```

### Add Message to Ticket (for Claude to read)
```sql
INSERT INTO user_messages (ticket_id, content, message_type)
VALUES (?, 'Please also add password reset functionality', 'message');
```

### View Ticket Conversation
```sql
SELECT
  CASE role
    WHEN 'user' THEN '>> USER'
    WHEN 'assistant' THEN '<< CLAUDE'
    ELSE CONCAT('[', role, ']')
  END as who,
  LEFT(content, 300) as message,
  created_at
FROM conversation_messages
WHERE ticket_id = ?
ORDER BY created_at;
```

### Clear Ticket History (Start Fresh)
```sql
-- Delete conversation
DELETE FROM conversation_messages WHERE ticket_id=?;

-- Reset ticket status
UPDATE tickets SET status='open', result_summary=NULL WHERE id=?;
```

### Check Token Usage
```sql
-- Per ticket
SELECT ticket_id, SUM(tokens_used) as total_tokens
FROM conversation_messages
GROUP BY ticket_id
ORDER BY total_tokens DESC;

-- Per session
SELECT s.id, t.ticket_number, s.tokens_used, s.started_at
FROM execution_sessions s
JOIN tickets t ON s.ticket_id = t.id
ORDER BY s.started_at DESC
LIMIT 20;
```

---

## 8. File Editing Locations

When making changes to the platform:

| What | Source (sync here) | Installed (running) |
|------|-------------------|---------------------|
| Flask App | `/home/claude/fotios-claude-system/web/app.py` | `/opt/fotios-claude/web/app.py` |
| Daemon | `/home/claude/fotios-claude-system/scripts/claude-daemon.py` | `/opt/fotios-claude/scripts/claude-daemon.py` |
| Templates | `/home/claude/fotios-claude-system/web/templates/` | `/opt/fotios-claude/web/templates/` |
| Schema | `/home/claude/fotios-claude-system/database/schema.sql` | (applied to MySQL) |

**After editing:**
```bash
# Copy to installed location
sudo cp /home/claude/fotios-claude-system/web/app.py /opt/fotios-claude/web/
sudo cp -r /home/claude/fotios-claude-system/web/templates/* /opt/fotios-claude/web/templates/
sudo cp /home/claude/fotios-claude-system/scripts/claude-daemon.py /opt/fotios-claude/scripts/

# Restart services
sudo systemctl restart fotios-claude-web fotios-claude-daemon
```

---

## 9. Emergency Procedures

### Stop All Processing
```bash
sudo systemctl stop fotios-claude-daemon
```

### Reset Everything
```sql
-- Reset all in_progress tickets
UPDATE tickets SET status='open' WHERE status='in_progress';

-- Reset daemon status
UPDATE daemon_status SET status='stopped', current_ticket_id=NULL, current_session_id=NULL WHERE id=1;

-- Mark running sessions as stopped
UPDATE execution_sessions SET status='stopped', ended_at=NOW() WHERE status='running';
```

### Database Backup
```bash
mysqldump -u $DB_USER -p$DB_PASSWORD $DB_NAME > /tmp/backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore Database
```bash
mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME < backup_file.sql
```

---

## 10. API Endpoints Reference

### Web Panel Routes
| Method | Path | Description |
|--------|------|-------------|
| GET | `/login` | Login page |
| POST | `/login` | Process login |
| GET | `/logout` | Logout |
| GET | `/dashboard` | Main dashboard |
| GET | `/tickets` | Tickets list (with filters) |
| GET | `/ticket/<id>` | Ticket detail |
| GET | `/projects` | Projects list |
| GET | `/project/<id>` | Project detail |
| GET | `/console` | Live console |
| GET | `/history` | Execution history |
| GET | `/session/<id>` | Session detail |

### API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/projects` | List all projects |
| POST | `/api/projects` | Create project (auto-creates database) |
| GET | `/api/project/<id>` | Get project details |
| PUT | `/api/project/<id>` | Update project (name, paths, db credentials) |
| POST | `/api/project/<id>/archive` | Archive project |
| POST | `/api/project/<id>/reopen` | Reopen project |
| POST | `/api/tickets` | Create ticket |
| POST | `/api/ticket/<id>/approve` | Approve pending review |
| POST | `/api/ticket/<id>/reopen` | Reopen/request changes |
| POST | `/api/send_message` | Send message to ticket |
| GET | `/api/ticket/<id>/conversation` | Get conversation |
| GET | `/api/daemon/status` | Daemon status |
| POST | `/api/daemon/start` | Start daemon |
| POST | `/api/daemon/stop` | Stop daemon |

### Create Project API Example
```bash
curl -X POST http://localhost:5000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "E-Commerce",
    "code": "ECOM",
    "project_type": "web",
    "skip_database": false
  }'

# Response:
# {"success": true, "project_id": 1, "db_created": true, "db_name": "ecom_db", "db_user": "ecom_user"}
```

### Update Project API Example
```bash
curl -X PUT http://localhost:5000/api/project/1 \
  -H "Content-Type: application/json" \
  -d '{
    "db_host": "remote-db.example.com",
    "db_name": "production_db",
    "db_user": "prod_user",
    "db_password": "secure_password"
  }'
```

---

---

## 11. New Features (v2.32.0)

### Web Terminal
Full Linux terminal in browser via WebSocket.

**Route:** `/terminal`
**Template:** `terminal.html`

**Features:**
- Real PTY via WebSocket (`pty` module)
- Popup support for multi-monitor
- 256-color support with xterm.js
- Runs as user `claude` with sudo access

**WebSocket Events:**
```python
@socketio.on('terminal_create')  # Create new terminal session
@socketio.on('terminal_input')   # Send input to terminal
@socketio.on('terminal_resize')  # Resize terminal
@socketio.on('terminal_kill')    # Kill terminal session
```

### Claude Assistant
Interactive Claude terminal with model selection.

**Route:** `/claude-assistant`
**Template:** `claude_assistant.html`

**Features:**
- AI Model Selection: `opus`, `sonnet` (default), `haiku`
- Popup window support
- Blueprint mode for project planning

**URL Parameters:**
- `popup=1` - Open in popup mode (minimal UI)
- `mode=blueprint` - Auto-load project template and start guided planning

**Implementation:**
```python
def start(self, model='sonnet'):
    # Use simple model aliases (opus, sonnet, haiku)
    os.execvpe(claude_path, [claude_path, '--dangerously-skip-permissions', '--model', model], env)
```

### AI Project Manager (Blueprint Planner)
Helps users design projects before coding.

**Button Location:** Projects page ("Plan with AI" button)
**Template File:** `config/project-template.md`

**How it works:**
1. User clicks "Plan with AI" on Projects page
2. Opens Claude Assistant in blueprint mode
3. Claude reads `/home/claude/fotios-claude-system/config/project-template.md`
4. Guided questionnaire about project requirements
5. Generates complete blueprint

### Kill Switch Commands (Instant)
Commands show immediately in conversation and console.

**Commands:**
- `/stop` - Pause and wait for correction
- `/skip` - Stop and reopen ticket
- `/done` - Force complete ticket

**Implementation:**
```python
# In app.py send_message route:
cursor.execute("""INSERT INTO conversation_messages (ticket_id, role, content, created_at)
                  VALUES (%s, 'user', %s, NOW())""", (ticket_id, content))
msg_id = cursor.lastrowid
# Fetch and broadcast immediately
socketio.emit('new_message', msg, room=f'ticket_{ticket_id}')
socketio.emit('new_message', msg, room='console')
```

### SmartContext
Intelligent context management for reduced token usage.

**Location:** `scripts/smart_context.py`

**Features:**
- Auto-detects framework, language, architecture
- Finds relevant files based on task
- Builds minimal context
- Reduces token usage by up to 70%

### AI Failsafe (Watchdog)
Protection against runaway AI sessions.

**Features:**
- Monitors tickets every 30 minutes
- Detects stuck patterns (repeated errors, circular behavior)
- Auto-pauses problematic tickets
- Email notifications when issues detected

---

**Last Updated:** 2026-01-10
**Version:** 2.32.0
