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

### 3. SELF-DOCUMENTING MODULES (Black Boxes)
Every script/module = **mini library with documented API + test file**

**Structure for EVERY backend script:**
```
/src
  /services
    UserService.py        ← Implementation
    UserService.md        ← API Documentation
    UserService_test.py   ← Test script with examples
```

**API Documentation (script_name.md) - REQUIRED:**
```markdown
# UserService API

## Purpose
Handles user registration, authentication, and profile management.

## Functions

### create_user(email, password, name) → User
Creates a new user account.
- **email**: Valid email address
- **password**: Min 8 chars
- **name**: Display name
- **Returns**: User object with id, email, name, created_at
- **Raises**: ValidationError, DuplicateEmailError

### get_user(user_id) → User | None
Retrieves user by ID.

## Usage Example
```python
from services.UserService import create_user, get_user
user = create_user("test@example.com", "password123", "John")
print(user.id)
```

## Dependencies
- Database connection (db.py)
- EmailValidator (utils/validators.py)
```

**Test Script (script_name_test.py) - REQUIRED:**
```python
"""
Test script for UserService
Run: python UserService_test.py
"""
from UserService import create_user, get_user

# Test 1: Create user
user = create_user("test@example.com", "pass123", "Test")
assert user.id is not None
print("✓ create_user works")

# Test 2: Get user
found = get_user(user.id)
assert found.email == "test@example.com"
print("✓ get_user works")

print("All tests passed!")
```

**Why this matters:**
- AI reads `.md` file → knows what script does WITHOUT opening it
- AI runs test script → verifies it works
- AI uses the API → doesn't need to understand implementation
- AI only opens source code IF there's a bug to fix

**Build bottom-up:** Utilities → Core → Services → App

### 4. CODE COMMENTS & SEARCH TAGS
**Every file must have searchable comments for AI navigation.**

**File Header (REQUIRED at top of every file):**
```python
"""
@file: UserService.py
@description: Handles user registration, authentication, profile management
@author: ProjectName Team
@created: 2024-01-15
@modified: 2024-01-20
@dependencies: db.py, validators.py
@tags: #auth #users #login #registration
"""
```

**Function/Method Comments (REQUIRED):**
```python
def create_user(email: str, password: str, name: str) -> User:
    """
    Creates a new user account with validation.

    @param email: Valid email address (will be validated)
    @param password: Plain text password (min 8 chars, will be hashed)
    @param name: Display name for the user
    @returns: User object with id, email, name, created_at
    @raises: ValidationError if email/password invalid
    @raises: DuplicateEmailError if email exists
    @example: user = create_user("test@example.com", "pass123", "John")
    @see: get_user(), delete_user()
    @tags: #user #create #registration
    """
```

**Inline Tags for Search:**
```python
# @TODO: Implement email verification (ticket #123)
# @FIXME: Race condition when multiple users register same email
# @HACK: Temporary fix until we upgrade the library
# @NOTE: This must run before database connection
# @SECURITY: Validate input to prevent SQL injection
# @PERFORMANCE: Cache this result, called 1000x/sec
# @DEPRECATED: Use create_user_v2() instead
# @CONFIG: Change this value in .env file
```

**Why tags matter:**
- AI searches `@TODO` → finds all pending work
- AI searches `#auth` → finds all authentication code
- AI searches `@SECURITY` → finds security-critical code
- AI searches `@see: delete_user` → finds related functions

### 5. ERROR HANDLING (Never Silent Failures!)
**Every error must be caught, logged, and reported.**

```python
# ❌ BAD - Silent failure
def get_user(id):
    try:
        return db.query(f"SELECT * FROM users WHERE id={id}")
    except:
        return None  # SILENT FAILURE - NO ONE KNOWS!

# ✅ GOOD - Proper error handling
def get_user(id: int) -> User | None:
    """
    @raises: DatabaseError on connection issues
    @raises: ValueError if id is invalid
    """
    if not isinstance(id, int) or id < 1:
        raise ValueError(f"Invalid user id: {id}")

    try:
        result = db.query("SELECT * FROM users WHERE id = ?", [id])
        if not result:
            logger.info(f"User not found: {id}")  # Log it
            return None
        return User(**result)
    except DatabaseError as e:
        logger.error(f"Database error fetching user {id}: {e}")
        raise  # Re-raise so caller knows!
```

**Error Handling Rules:**
| Rule | Example |
|------|---------|
| Never empty `except:` | Always specify exception type |
| Never `pass` in except | At minimum, log the error |
| Validate inputs first | Check before processing |
| Use meaningful messages | `"User 123 not found"` not `"Error"` |
| Log with context | Include IDs, values, state |
| Fail fast | Don't continue with bad data |

### 6. VERIFY BEFORE COMPLETING TASK
**NEVER mark a task complete without verification!**

**Verification Checklist:**
```
□ Code runs without syntax errors
□ Main functionality works (tested manually or with script)
□ Edge cases handled (empty input, null, large data)
□ Error cases return proper messages
□ No console errors in browser (for frontend)
□ Test script passes (if exists)
□ Visual check with Playwright (for UI changes)
```

**How to verify:**
```bash
# 1. Syntax check
python -m py_compile my_script.py

# 2. Run the code
python my_script.py

# 3. Run tests
python my_script_test.py

# 4. Check for errors in logs
tail -f /var/log/app.log
```

**If you can't verify → ASK USER to test it!**

### 7. NAMING CONVENTIONS
**Consistent naming = Easy searching**

| Type | Convention | Example |
|------|------------|---------|
| Files (Python) | snake_case | `user_service.py` |
| Files (JS/TS) | camelCase or kebab | `userService.js` |
| Files (PHP) | PascalCase | `UserService.php` |
| Classes | PascalCase | `UserService`, `OrderManager` |
| Functions | camelCase | `createUser()`, `getOrderById()` |
| Variables | camelCase | `userName`, `orderTotal` |
| Constants | UPPER_SNAKE | `MAX_RETRIES`, `API_URL` |
| Private | _prefix | `_internalMethod()`, `_cache` |
| Database tables | snake_case plural | `users`, `order_items` |
| Database columns | snake_case | `created_at`, `user_id` |

**Naming Tips:**
- **Be specific**: `getUserById()` not `getUser()`
- **Use verbs for functions**: `create`, `get`, `update`, `delete`, `validate`, `calculate`
- **Use nouns for variables**: `user`, `orderList`, `totalAmount`
- **Boolean prefix**: `isActive`, `hasPermission`, `canEdit`

### 8. DEBUG WORKFLOW
**When something doesn't work, follow this process:**

```
1. READ THE ERROR MESSAGE
   └→ 90% of bugs are explained in the error

2. CHECK THE BASICS
   ├→ Syntax errors? (missing brackets, typos)
   ├→ Imports correct?
   ├→ File exists at path?
   └→ Permissions OK?

3. ADD LOGGING
   └→ print() or logger.debug() at key points

4. ISOLATE THE PROBLEM
   ├→ Comment out code until it works
   ├→ Test each function separately
   └→ Find the exact line that fails

5. CHECK INPUTS/OUTPUTS
   ├→ What value is actually being passed?
   ├→ Is it the type you expect?
   └→ Is it None/null when it shouldn't be?

6. SEARCH FOR SIMILAR CODE
   └→ How is it done elsewhere in the project?

7. IF STILL STUCK → ASK USER
   └→ Include: error message, what you tried, relevant code
```

**Debug Print Template:**
```python
def problematic_function(data):
    print(f"DEBUG: Input data = {data}, type = {type(data)}")  # @DEBUG
    result = process(data)
    print(f"DEBUG: Result = {result}")  # @DEBUG
    return result
```

**Remember to remove @DEBUG comments before completing!**

### 9. ASK WHEN < 90% CONFIDENT
Multiple options? Unclear requirements? Could break something? → ASK FIRST

### 10. SECURITY (MANDATORY)
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

### 11. PLAYWRIGHT-READY
All UI elements need `data-testid` so AI can test:
```html
<button data-testid="submit-login-btn">Login</button>
<input data-testid="email-input" type="email">
<div data-testid="error-message">...</div>
```

### 12. ARCHITECTURE
- **UI**: Grid-based, minimalist, mobile-first, fast
- **Libraries**: Popular (Tailwind, Alpine.js, PDO) - avoid bloat
- **Wrappers**: Every external service gets a wrapper (DB, Email, Payment)
- **Size matters**: Smaller = fewer tokens = faster AI = lower cost
- **Future-proof**: Standard features, no framework magic

### 13. VISUAL CONSISTENCY (UI Polish)
**Every UI must look professional, balanced, and uniform.**

**Core Principles:**
- **Alignment**: All elements align properly (left, center, grid lines)
- **Spacing**: Consistent margins/padding throughout (use a system: 8px, 16px, 24px, 32px)
- **Sizing**: Similar elements = same size (buttons, cards, icons, inputs)
- **Typography**: Same font sizes for same hierarchy levels (all h2 = same size)
- **Colors**: Consistent color palette - don't mix random colors
- **Borders/Shadows**: Same style for similar elements

**Common Problems to CHECK:**
| Problem | Solution |
|---------|----------|
| Cards different heights | Use `display: flex; align-items: stretch` or CSS Grid |
| Text overflows container | Use `overflow: hidden; text-overflow: ellipsis` |
| Uneven spacing | Use consistent padding/margin values |
| Elements not aligned | Use flexbox/grid, not manual positioning |
| Buttons different sizes | Set consistent `min-width` or use same class |
| Icons different sizes | Set fixed `width/height` for all icons |

**Before finishing ANY UI work - use Playwright to screenshot and verify:**
1. Does everything align properly?
2. Are similar elements the same size?
3. Is spacing consistent everywhere?
4. Does text fit in its containers?
5. Does it look **professional and polished**?

**⚠️ If something looks off → FIX IT before completing the task!**

### 14. DOCUMENTATION
Create `TECHNOLOGIES.md` in every project listing:
- Stack (PHP/Python/Node, framework, DB)
- APIs & Services (Google Maps, Stripe, etc.)
- Libraries with versions
- Environment variables

### 15. PROJECT MAP (Bird's Eye View)
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

**Code Quality:**
- [ ] Junior can understand?
- [ ] Comments explain WHY with @tags?
- [ ] File header with @file, @description, @tags?
- [ ] Names are descriptive and consistent?
- [ ] Functions are small (one job)?

**Documentation:**
- [ ] API documentation (.md file) exists?
- [ ] Test script exists and passes?
- [ ] TECHNOLOGIES.md updated?
- [ ] PROJECT_MAP.md updated?

**Verification (CRITICAL!):**
- [ ] Code runs without errors?
- [ ] Main functionality tested?
- [ ] Edge cases handled?
- [ ] Error messages are meaningful?
- [ ] No silent failures?

**Security:**
- [ ] SQL uses prepared statements?
- [ ] Inputs validated, outputs escaped?
- [ ] No sensitive data in logs?

**UI (if applicable):**
- [ ] data-testid on all UI elements?
- [ ] Visual consistency checked with Playwright?
- [ ] All similar elements same size?
- [ ] Text fits in containers?

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
