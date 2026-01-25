# Global Project Context v4.0

> **MISSION:** Build production-ready code that works correctly the first time.

---

## MANDATORY WORKFLOW

### Step 1: Analyze Request
- Understand what the user is asking for
- Assess complexity

### Step 2: Break Into Parts
- Split the request into small, manageable pieces
- Each part must be testable

### Step 3: Implementation Plan
- Write which parts you will implement and in what order
- Document in the project's map.md

### Step 4: Implement Part by Part
- Implement one part at a time
- DO NOT proceed to the next without verification

### Step 5: Verify Each Part
- MANDATORY: Run the checks from the VERIFICATION PROTOCOL
- If it fails, fix it BEFORE proceeding

### Step 6: Full Test
- After all parts are completed
- End-to-end testing of all functionality

### Step 7: Final Report
- What was implemented
- What technologies were used
- Any notes for the user

---

## VERIFICATION PROTOCOL (MANDATORY!)

### 1. Syntax Check
Check syntax by language:
```bash
# PHP
php -l filename.php

# Python
python3 -m py_compile filename.py

# JavaScript
node --check filename.js

# HTML (via validator)
tidy -e -q filename.html 2>&1 || true
```

### 2. Log Check
Check relevant log files:
```bash
# PHP/Nginx errors
sudo tail -30 /var/log/nginx/codehero-projects-error.log

# PHP-FPM errors
sudo tail -30 /var/log/php8.3-fpm.log

# System logs
sudo journalctl -u nginx --since "5 minutes ago" --no-pager
```

### 3. Visual Verification (MANDATORY for UI!)

Choose the appropriate method based on project type:

#### Web Projects (PHP, HTML, Node.js, Python web, .NET Blazor)
**Use Playwright:**
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()

    # Desktop test
    page.set_viewport_size({"width": 1920, "height": 1080})
    page.goto('https://127.0.0.1:9867/project/')
    page.wait_for_load_state("networkidle")

    # Console errors check
    console_errors = []
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

    # Full page screenshot
    page.screenshot(path='/tmp/desktop.png', full_page=True)

    # Mobile test
    page.set_viewport_size({"width": 375, "height": 812})
    page.screenshot(path='/tmp/mobile.png', full_page=True)

    browser.close()
```

#### Android (Java/Kotlin, React Native, Capacitor, Flutter)
**Use ADB with emulator:**
```bash
# Start emulator (if not running)
emulator -avd Pixel_6_API_33 -no-audio -no-window &

# Wait for device
adb wait-for-device

# Install APK
adb install -r app/build/outputs/apk/debug/app-debug.apk

# Launch app
adb shell am start -n com.package.name/.MainActivity

# Wait for app to load
sleep 3

# Take screenshot
adb exec-out screencap -p > /tmp/android_screenshot.png

# Get logs
adb logcat -d -s "AppTag:*" > /tmp/android_logs.txt
```

#### iOS (Swift, React Native, Capacitor, Flutter)
**Use Xcode Simulator:**
```bash
# List available simulators
xcrun simctl list devices

# Boot simulator
xcrun simctl boot "iPhone 15 Pro"

# Install app
xcrun simctl install booted /path/to/MyApp.app

# Launch app
xcrun simctl launch booted com.bundle.identifier

# Take screenshot
xcrun simctl io booted screenshot /tmp/ios_screenshot.png

# Get logs
xcrun simctl spawn booted log show --predicate 'subsystem == "com.bundle.identifier"' --last 5m
```

#### Desktop Apps (.NET WinForms/WPF, Java Swing/JavaFX, Electron)
**Use platform screenshot tools:**
```bash
# Linux (for Electron or Java desktop)
import -window root /tmp/desktop_app.png

# Or with specific window
xdotool search --name "App Title" | xargs -I {} import -window {} /tmp/app.png

# For headless Java apps testing
java -Djava.awt.headless=false -jar app.jar &
sleep 3
import -window root /tmp/java_app.png
```

#### React Native / Expo
**Use Expo or platform-specific:**
```bash
# With Expo (web preview)
npx expo start --web &
sleep 5
# Then use Playwright for web testing

# For native, use ADB (Android) or simctl (iOS) as above
```

#### Flutter
**Use Flutter integration test:**
```bash
# Run with screenshots
flutter drive --driver=test_driver/integration_test.dart \
  --target=integration_test/app_test.dart \
  --screenshot=/tmp/flutter_screenshots/

# Or use platform tools (ADB/simctl) after building
flutter build apk --debug
adb install build/app/outputs/flutter-apk/app-debug.apk
```

### UI Checklist (All Platforms)
- [ ] No console/logcat errors
- [ ] All interactive elements work (buttons, inputs, navigation)
- [ ] Colors: Consistency, good contrast
- [ ] Alignment: Proper alignment
- [ ] Sizing: Appropriate element/font sizes
- [ ] Text: Readable, no truncation
- [ ] Loading states: Shown correctly
- [ ] **Web**: Desktop + Mobile responsive
- [ ] **Mobile apps**: Portrait + Landscape orientation

---

## CODE QUALITY RULES (MANDATORY!)

### ALWAYS DO:
| Rule | Why |
|------|-----|
| Clean, readable code | Junior dev must understand |
| Comments that explain WHY | Not just what it does |
| Descriptive variable names | `$userEmail` not `$ue` |
| Small functions, one purpose | Easier testing |
| **RELATIVE PATHS** | Avoid broken links |

### NEVER DO:
| Bad | Why |
|-----|-----|
| Minified code | We want readable source |
| Obfuscated code | We want readable source |
| CDN for libraries | Download locally! |
| Absolute paths | Break in different environments |

---

## LIBRARIES RULE

**ALWAYS download locally:**
```bash
mkdir -p libs
curl -o libs/vue.global.min.js https://unpkg.com/vue@3/dist/vue.global.prod.js
curl -o libs/tailwind.min.css https://cdn.tailwindcss.com/...
```

**EXCEPTIONS** (external APIs that can't be local):
- Google Maps API
- Stripe.js
- PayPal SDK
- reCAPTCHA

---

## PROJECT DOCUMENTATION

### Mandatory files:
1. **technologies.md** - Technologies, versions, libraries
2. **map.md** - Project structure, database schema, page flow

### While working, keep track of:
- **Index** of what you did (for navigation)
- **Notes** of commands you used
- **Log** of technologies

---

## SERVER ENVIRONMENT

- **OS**: Ubuntu 24.04 LTS
- **Web Server**: Nginx
- **PHP**: 8.3 | **Node.js**: v22.x | **Python**: 3.12 | **MySQL**: 8.0

## PORTS

| Service | Port | Protocol |
|---------|------|----------|
| Admin Panel | 9453 | HTTPS |
| Web Projects | 9867 | HTTPS |
| MySQL | 3306 | TCP (localhost only) |

## FILE LOCATIONS

- **PHP/Web Projects**: `/var/www/projects/{project}/`
- **App Projects**: `/opt/apps/{project}/`

---

## QUICK SECURITY REFERENCE

### ALWAYS DO:
| Category | Rule |
|----------|------|
| **SQL** | Prepared statements: `$stmt->execute([$id])` |
| **XSS** | Escape output: `htmlspecialchars($x, ENT_QUOTES, 'UTF-8')` |
| **Passwords** | Hash: `password_hash($p, PASSWORD_BCRYPT)` |
| **Forms** | CSRF token on every POST |
| **Sessions** | `session_regenerate_id(true)` after login |

### NEVER DO:
| Bad | Good |
|-----|------|
| `"WHERE id=$id"` | `"WHERE id=?"` + bind |
| `echo $userInput` | `echo htmlspecialchars($userInput)` |
| Passwords in code | Use `.env` files |

---

## NO BUILD WORKFLOW

**NEVER use build tools** (Vite, Webpack, npm run build)

Write Vue/React in plain .js files:
```javascript
const MyComponent = {
  template: `<div>{{ message }}</div>`,
  data() { return { message: 'Hello' } }
}
```

---

## WORKSPACE PATHS

```
Allowed:    /var/www/projects/{name}/
            /opt/apps/{name}/

FORBIDDEN:  /opt/codehero/
            /etc/nginx/
            /etc/systemd/
```
