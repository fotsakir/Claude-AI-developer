# Global Project Context

## THE MISSION
```
Human + Machine = EVOLUTION
We build simple systems that AI can test, fix, and evolve.
Adapt or die. Simplicity is survival.
```

---

## ⛔ PROTECTED PATHS - NEVER MODIFY!

**These directories are OFF-LIMITS. Do not read, write, delete, or change permissions:**

| Path | Reason |
|------|--------|
| `/opt/codehero/` | Platform admin panel & daemon |
| `/etc/codehero/` | Platform configuration |
| `/var/backups/codehero/` | Project backups - NEVER touch! |
| `/etc/nginx/` | Web server configuration |
| `/etc/systemd/` | System service files |
| `/var/www/html/` | Default web root |
| `/home/claude/.claude*` | Claude CLI configuration |

**If user asks to:**
- Fix 403/permission errors → Only fix within the PROJECT directory, not system paths
- Change nginx config → REFUSE and ask user to do it manually
- Restore from backup → REFUSE and tell user to use the Admin Panel
- Fix "the app" → Clarify WHICH app - never touch CodeHero itself

**Your workspace is ONLY:**
- `/var/www/projects/{project}/` - for web projects
- `/opt/apps/{project}/` - for app projects

Everything else is READ-ONLY or OFF-LIMITS!

---

## CORE RULES (Memorize These!)

### 1. TEAM MINDSET
Code like you're in a 10-person team. Ask: "Can someone else continue this at 3am?"
- Bus Factor Test: If you're gone, can others continue?
- Comment the WHY, not the WHAT
- Document everything in TECHNOLOGIES.md

### 2. SIMPLE CODE
- Junior developer must understand it
- Descriptive names: `calculateTotal()` not `calc()`
- No clever tricks - readable beats clever

### 3. SMALL BLACK BOXES
- Each function = ONE job
- Clear inputs → Process → Clear outputs
- Test each piece alone, then connect
- Build bottom-up: Utilities → Core → Services → App

### 4. ASK WHEN < 90% CONFIDENT
Multiple options? Unclear requirements? Could break something? → ASK FIRST

### 5. SECURITY (MANDATORY)
```php
// ❌ NEVER: $sql = "SELECT * FROM users WHERE id = $id";
// ✅ ALWAYS: $stmt = $pdo->prepare("SELECT * FROM users WHERE id = ?");

// ❌ NEVER: echo $userInput;
// ✅ ALWAYS: echo htmlspecialchars($userInput, ENT_QUOTES, 'UTF-8');
```
- ALL SQL = Prepared statements
- ALL inputs = Validated
- ALL outputs = Escaped

**NO PERSONAL INFO in config files!**
When creating composer.json, package.json, or any config with author fields:
```json
// ✅ ALWAYS use project name:
"author": "ProjectName Team"
// ✅ Or generic:
"author": "Development Team"
// ❌ NEVER use personal emails or real names
```

### 6. PLAYWRIGHT-READY
All UI elements need `data-testid` so AI can test:
```html
<button data-testid="submit-login-btn">Login</button>
<input data-testid="email-input" type="email">
<div data-testid="error-message">...</div>
```

### 7. ARCHITECTURE
- **UI**: Grid-based, minimalist, mobile-first, fast
- **Libraries**: Popular (Tailwind, Alpine.js, PDO) - avoid bloat
- **Wrappers**: Every external service gets a wrapper (DB, Email, Payment)
- **Size matters**: Smaller = fewer tokens = faster AI = lower cost
- **Future-proof**: Standard features, no framework magic

### 8. DOCUMENTATION
Create `TECHNOLOGIES.md` in every project listing:
- Stack (PHP/Python/Node, framework, DB)
- APIs & Services (Google Maps, Stripe, etc.)
- Libraries with versions
- Environment variables

### 9. PROJECT MAP (Bird's Eye View)
**Create and UPDATE `PROJECT_MAP.md` as you work on tickets!**

When starting a ticket:
1. Read PROJECT_MAP.md first (if exists)
2. Understand the big picture before coding

While working:
3. Add new files/folders you create
4. Update data flow if it changes
5. Add new API endpoints

When finishing:
6. Make sure map reflects current state

```markdown
# Project Map (updated: 2024-01-15)

## Structure
/src
  /controllers    → Handle requests (UserController, OrderController)
  /models         → Database entities (User, Order, Product)
  /services       → Business logic (AuthService, PaymentService)
  /utils          → Helpers (validation, formatting)

## Data Flow
User → Controller → Service → Model → Database

## Key Files
- index.php         → Entry point, routing
- Database.php      → DB wrapper (all queries go through here)
- AuthService.php   → Login, logout, 2FA, sessions

## API Endpoints
POST /api/login     → AuthController::login
GET  /api/users     → UserController::list
```

**This is your GPS - keep it updated!**

---

## CHECKLIST (Before finishing ANY code)
- [ ] Junior can understand?
- [ ] Comments explain WHY?
- [ ] Names are descriptive?
- [ ] Functions are small (one job)?
- [ ] Tests exist?
- [ ] TECHNOLOGIES.md updated?
- [ ] PROJECT_MAP.md updated?
- [ ] data-testid on all UI elements?
- [ ] SQL uses prepared statements?
- [ ] Inputs validated, outputs escaped?

---

## SERVER ENVIRONMENT

| Tool | Version | Notes |
|------|---------|-------|
| Ubuntu | 24.04 LTS | |
| PHP | 8.3 | + extensions |
| Node.js | 22.x | |
| MySQL | 8.0 | |
| .NET | 8.0 | + PowerShell 7.5 |
| Java | GraalVM 24 | |
| Playwright | Python | Chromium included |

**Ports**: Admin=9453, Projects=9867, MySQL=3306

**Paths**:
- PHP: `/var/www/projects/[code]/`
- Apps: `/opt/apps/[code]/`

**Multimedia**: ffmpeg, ImageMagick, tesseract-ocr, sox, poppler

---

## AI BEHAVIOR

### Visual Testing (Playwright)

**Web Project URLs** (projects in `/var/www/projects/`):
- Internal URL: `https://127.0.0.1:9867/{folder_name}/`
- folder_name = last part of web_path (e.g., `/var/www/projects/mysite` → `mysite`)
- **ALWAYS use `ignore_https_errors=True`** (self-signed certificate)

```python
from playwright.sync_api import sync_playwright

# Get folder name from web_path
web_path = "/var/www/projects/dellaportadr"
folder_name = web_path.rstrip('/').split('/')[-1]  # "dellaportadr"
url = f"https://127.0.0.1:9867/{folder_name}/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    # IMPORTANT: ignore_https_errors for self-signed cert
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    page.goto(url)
    page.screenshot(path='/tmp/screenshot.png')
    browser.close()
```

**Playwright Config (playwright.config.js)**:
```javascript
module.exports = {
    use: {
        baseURL: 'https://127.0.0.1:9867/folder_name/',
        ignoreHTTPSErrors: true,  // REQUIRED for self-signed cert
    }
};
```

### Before Installing
Check first: `which [tool]` or `[tool] --version`
Most tools are already installed!

---

**Remember: Simple rules → Big projects. Black boxes → Easy maintenance. Evolution → Survival.**
