# Global Project Context

> **MISSION:** Build simple, testable code that AI can maintain without human help.

---

## ⛔ PART 1: CRITICAL RULES (Read FIRST!)

### 1.1 PROTECTED PATHS - FORBIDDEN!
```
/opt/codehero/           ← Platform will break
/etc/codehero/           ← Platform config
/var/backups/codehero/   ← Backups
/etc/nginx/              ← Web server
/etc/systemd/            ← System services
/home/claude/.claude*    ← Claude CLI
```

**YOUR WORKSPACE ONLY:**
- Web projects: `/var/www/projects/{project}/`
- App projects: `/opt/apps/{project}/`

**IF USER ASKS:**
- "Fix 403 error" → Only inside PROJECT folder
- "Fix nginx" → REFUSE, tell them to do it manually
- "Fix the app" → ASK which app, NOT CodeHero

### 1.2 SECURITY - NON-NEGOTIABLE
```python
# SQL - ALWAYS prepared statements
# ❌ NEVER: f"SELECT * FROM users WHERE id = {id}"
# ✅ ALWAYS: db.query("SELECT * FROM users WHERE id = ?", [id])

# Output - ALWAYS escape
# ❌ NEVER: echo $userInput
# ✅ ALWAYS: echo htmlspecialchars($userInput, ENT_QUOTES, 'UTF-8')

# Passwords - ALWAYS hash
# ❌ NEVER: db.save(password)
# ✅ ALWAYS: db.save(bcrypt.hash(password))
```

### 1.3 CREDENTIALS - NEVER HARDCODED
```python
# ❌ NEVER
db = connect("mysql://admin:secret123@localhost/app")

# ✅ ALWAYS .env
load_dotenv()
db = connect(os.getenv('DATABASE_URL'))
```

---

## 📋 PART 2: BEFORE WRITING CODE

### 2.1 TEAM MINDSET
- Write as if a junior developer reads it at 3am
- If you leave, can someone else continue?
- Comment the WHY, not the WHAT

### 2.2 PROJECT STRUCTURE
```
/src
  /services
    UserService.py       ← Code
    UserService.md       ← API docs (REQUIRED)
    UserService_test.py  ← Tests (REQUIRED)
```

### 2.3 FILE HEADER (in EVERY file)
```python
"""
@file: UserService.py
@description: User registration, login, profile
@tags: #auth #users #login
@dependencies: db.py, validators.py
"""
```

### 2.4 NAMING CONVENTIONS
| Type | Convention | Example |
|------|------------|---------|
| Python files | snake_case | `user_service.py` |
| PHP files | PascalCase | `UserService.php` |
| Classes | PascalCase | `UserService` |
| Functions | camelCase | `createUser()` |
| Constants | UPPER_SNAKE | `MAX_RETRIES` |
| DB tables | snake_case plural | `order_items` |

---

## 💻 PART 3: WRITING CODE

### 3.1 ERROR HANDLING - Never silent failures!
```python
# ❌ BAD - Nobody knows what happened
try:
    do_something()
except:
    pass

# ✅ GOOD
try:
    do_something()
except SpecificError as e:
    logger.error(f"Failed to do X: {e}")
    raise
```

### 3.2 NULL CHECKS - Always check first!
```python
# ❌ Crash if user=None
return f"Hello {user.name}"

# ✅ Safe
if not user:
    return "Hello Guest"
return f"Hello {user.name}"

# ✅ Safe dict access
name = data.get('name', 'Unknown')
```

### 3.3 TIMEOUTS - Never wait forever!
```python
# ❌ Hangs forever
response = requests.get(url)

# ✅ Timeout required
response = requests.get(url, timeout=10)
```

| Operation | Timeout |
|-----------|---------|
| HTTP API | 10-30s |
| DB query | 5-30s |
| File upload | 60-120s |

### 3.4 TRANSACTIONS - All or nothing
```python
# ❌ Crash after charge = money taken, no order
charge_card(user, amount)
create_order(user, amount)  # <-- crash here

# ✅ Transaction
try:
    db.begin()
    order = create_order(user, amount)
    charge_card(user, amount)
    db.commit()
except:
    db.rollback()
    raise
```

### 3.5 IDEMPOTENCY - Safe to run twice
```python
# ❌ 2 runs = 2 users!
db.execute("INSERT INTO users (email) VALUES (?)", [email])

# ✅ Check first
existing = db.query("SELECT id FROM users WHERE email = ?", [email])
if existing:
    return existing['id']
db.execute("INSERT INTO users (email) VALUES (?)", [email])
```

```sql
-- ✅ MySQL idempotent
INSERT INTO users (email, name) VALUES (?, ?)
ON DUPLICATE KEY UPDATE name = VALUES(name);
```

### 3.6 RACE CONDITIONS - Atomic operations
```python
# ❌ 2 users buy last item = stock -1!
item = db.query("SELECT stock FROM items WHERE id = ?", [id])
if item['stock'] > 0:
    db.execute("UPDATE items SET stock = stock - 1 WHERE id = ?", [id])

# ✅ Atomic
result = db.execute("""
    UPDATE items SET stock = stock - 1
    WHERE id = ? AND stock > 0
""", [id])
if result.affected_rows == 0:
    raise OutOfStockError()
```

### 3.7 DATABASE CONSTRAINTS
```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_email (email)
);

CREATE TABLE orders (
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE RESTRICT
);
```

### 3.8 INPUT VALIDATION
```python
def validate_email(email):
    if not email:
        raise ValidationError("Email required")
    if len(email) > 254:
        raise ValidationError("Email too long")
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        raise ValidationError("Invalid email")
    return email.strip().lower()
```

**File uploads:**
```python
ALLOWED = {'jpg', 'png', 'pdf'}
MAX_SIZE = 10 * 1024 * 1024  # 10MB

def validate_file(file):
    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED:
        raise ValidationError(f"Type not allowed: {ext}")
    if file.size > MAX_SIZE:
        raise ValidationError("File too large")
```

### 3.9 ATOMIC FILE WRITES
```python
# ❌ Crash = corrupted file
with open(path, 'w') as f:
    f.write(data)

# ✅ Write temp, then rename
import tempfile
fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path))
with os.fdopen(fd, 'w') as f:
    f.write(data)
os.rename(tmp, path)
```

### 3.10 RESOURCE CLEANUP
```python
# ❌ Connection leak
conn = db.connect()
result = conn.query("SELECT * FROM users")
return result  # Connection never closed!

# ✅ Context manager
with db.connect() as conn:
    return conn.query("SELECT * FROM users")
# Auto-closed!
```

### 3.11 RETRY LOGIC
```python
import time

def retry(func, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            return func()
        except (ConnectionError, TimeoutError) as e:
            if attempt == max_attempts - 1:
                raise
            time.sleep(2 ** attempt)  # 1s, 2s, 4s
```

### 3.12 LOGGING
```python
import logging
logger = logging.getLogger('myapp')

# ✅ Log with context
logger.info(f"Order created: user={user_id}, order={order_id}, total={total}")
logger.error(f"Payment failed: user={user_id}, error={e}")

# ❌ Never log passwords, credit cards
```

| Level | Usage |
|-------|-------|
| DEBUG | Development only |
| INFO | Normal operations |
| WARNING | Recoverable issues |
| ERROR | Failures |
| CRITICAL | System broken |

### 3.13 DATE/TIME - Always UTC!
```python
from datetime import datetime, timezone

# ❌ Local time = bugs
now = datetime.now()

# ✅ UTC internally
now = datetime.now(timezone.utc)

# Convert for display only
from zoneinfo import ZoneInfo
local = utc_time.astimezone(ZoneInfo('Europe/Athens'))
```

**DB:** Store as `TIMESTAMP` (auto UTC)
**API:** ISO 8601 format `"2024-01-15T14:30:00Z"`

### 3.14 UTF-8 - Everywhere!
```python
# Files
with open('file.txt', 'r', encoding='utf-8') as f:

# PHP
mb_strlen($text, 'UTF-8');
```

```sql
-- Database
CREATE DATABASE myapp CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3.15 PAGINATION - Never unlimited!
```python
# ❌ 1M records = crash
users = db.query("SELECT * FROM users")

# ✅ Always LIMIT
def get_users(page=1, per_page=50):
    per_page = min(per_page, 100)  # Max 100!
    offset = (page - 1) * per_page
    return db.query("SELECT * FROM users LIMIT ? OFFSET ?", [per_page, offset])
```

### 3.16 CONFIG DEFAULTS
```python
# ❌ Crash if missing
api_key = os.environ['API_KEY']

# ✅ Default or fail fast
DEBUG = os.getenv('DEBUG', 'false') == 'true'
DB_HOST = os.getenv('DB_HOST', 'localhost')

def required_env(key):
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(f"Missing: {key}")
    return val

API_KEY = required_env('API_KEY')
```

---

## ✅ PART 4: BEFORE FINISHING

### 4.1 VERIFICATION CHECKLIST
```
□ Runs without errors?
□ Main functionality works?
□ Edge cases (null, empty, large data)?
□ Test script passes?
```

**How to verify:**
```bash
python -m py_compile script.py  # Syntax check
python script_test.py           # Run tests
```

### 4.2 DEBUG WORKFLOW
```
1. READ the error message (90% of solutions are there)
2. Check basics: syntax, imports, file paths, permissions
3. Add logging at key points
4. Isolate: comment out until it works
5. Check inputs: what value is ACTUALLY coming?
6. STILL STUCK → Ask user
```

### 4.3 ASK WHEN < 90% CONFIDENT
- Multiple options? → ASK
- Unclear requirements? → ASK
- Might break something? → ASK

---

## 🎨 PART 5: UI RULES

### 6.1 PLAYWRIGHT TEST IDs
```html
<button data-testid="login-btn">Login</button>
<input data-testid="email-input">
<div data-testid="error-message">
```

### 6.2 VISUAL CONSISTENCY
- Same spacing everywhere (8px, 16px, 24px, 32px)
- Same size for similar elements
- Use flexbox/grid, not manual positioning

**Before finishing UI → Screenshot with Playwright and check if uniform!**

### 6.3 PLAYWRIGHT URL
```python
from playwright.sync_api import sync_playwright

url = "https://127.0.0.1:9867/{folder_name}/"

with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(ignore_https_errors=True)  # REQUIRED!
    page = context.new_page()
    page.goto(url)
    page.screenshot(path='/tmp/screenshot.png')
```

---

## 📄 PART 6: DOCUMENTATION

### 7.1 TECHNOLOGIES.md (in every project)
```markdown
# Technologies

## Stack
- PHP 8.3 / Laravel 10
- MySQL 8.0
- Tailwind CSS

## APIs
- Stripe (payments)
- SendGrid (email)

## Environment Variables
- DB_HOST, DB_NAME, DB_USER, DB_PASS
- STRIPE_KEY
```

### 7.2 PROJECT_MAP.md
```markdown
# Project Map

## Structure
/src
  /controllers  → Handle HTTP requests
  /services     → Business logic
  /models       → Database entities

## Key Files
- index.php → Entry point
- AuthService.php → Login/logout

## API Endpoints
POST /api/login → AuthController::login
```

---

## 🖥️ PART 7: SERVER INFO

| Tool | Version |
|------|---------|
| Ubuntu | 24.04 |
| PHP | 8.3 |
| Node.js | 22.x |
| MySQL | 8.0 |
| Python | 3.12 |

**Ports:** Admin=9453, Projects=9867, MySQL=3306

**Paths:**
- PHP: `/var/www/projects/{code}/`
- Apps: `/opt/apps/{code}/`

**Before installing:** `which tool` - probably already installed!

---

## ✔️ FINAL CHECKLIST

**Security:**
- [ ] SQL prepared statements
- [ ] Inputs validated, outputs escaped
- [ ] Passwords hashed (bcrypt)
- [ ] No hardcoded credentials

**Reliability:**
- [ ] Timeouts on all external calls
- [ ] Transactions for related DB ops
- [ ] Null checks before using values
- [ ] Idempotent operations (safe to run twice)
- [ ] Race conditions prevented (atomic ops)
- [ ] Resources cleaned up (connections, files)
- [ ] Config has defaults or fails fast
- [ ] Dates in UTC
- [ ] UTF-8 everywhere
- [ ] Queries paginated

**Code Quality:**
- [ ] Junior can understand?
- [ ] File headers with @tags
- [ ] API docs (.md) exists
- [ ] Test script exists & passes
- [ ] TECHNOLOGIES.md updated

**UI:**
- [ ] data-testid on elements
- [ ] Visual consistency check

---

> **Remember:** Simple code → Easy maintenance → AI can fix it → Evolution!
