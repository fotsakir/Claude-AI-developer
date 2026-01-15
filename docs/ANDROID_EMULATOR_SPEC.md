# Android Emulator Integration - Specifications

## Overview
Integration of Android 15 emulator (Redroid) into CodeHero for Android app development and testing.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    CodeHero Server                       │
│                                                          │
│  ┌──────────────┐    ┌──────────────────────────────┐   │
│  │   Redroid    │───▶│   ws-scrcpy (HTTPS :8443)    │   │
│  │  (Android)   │    │   Built-in SSL/TLS           │   │
│  │  port 5556   │    └──────────────────────────────┘   │
│  └──────────────┘                  │                     │
│         │                          ▼                     │
│         ▼                                                │
│  ┌─────────────────────────────────────────────────────┐│
│  │              CodeHero Admin Panel                   ││
│  │  Ticket Detail → Emulator Tab                       ││
│  │  ┌─────────────────────────────────────────────────┐││
│  │  │ Status: ● Running / ○ Stopped                   │││
│  │  │ [Start Emulator] [Stop Emulator]                │││
│  │  │ ┌─────────────────────────────────────────────┐ │││
│  │  │ │                                             │ │││
│  │  │ │          Android Stream (iframe)            │ │││
│  │  │ │                                             │ │││
│  │  │ └─────────────────────────────────────────────┘ │││
│  │  └─────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Project Settings - Mobile Project Types

| Type | Live Preview | Emulator | Build Command |
|------|-------------|----------|---------------|
| **Capacitor.js** | ✅ `ionic serve` | ✅ `npx cap run android` | `ionic build && npx cap sync` |
| **React Native** | ✅ Expo web | ✅ `npx react-native run-android` | `npx react-native build-android` |
| **Flutter** | ✅ `flutter run -d chrome` | ✅ `flutter run` | `flutter build apk` |
| **Native Android** | ❌ | ✅ `./gradlew installDebug` | `./gradlew assembleDebug` |

**App Path:** Uses existing `/opt/apps/PROJECT_CODE/` structure

### Project Type Detection (Auto)

```
/opt/apps/PROJECT_CODE/
├── capacitor.config.ts  → Capacitor.js
├── app.json + metro     → React Native
├── pubspec.yaml         → Flutter
├── build.gradle         → Native Android
```

### Project Settings - Android Device

```
┌─────────────────────────────────────────────────────┐
│ Android Device                                      │
├─────────────────────────────────────────────────────┤
│ ○ None (no Android testing)                         │
│ ● Server Emulator (Redroid)                         │
│ ○ Remote ADB                                        │
│   └─ Host: [192.168.1.100] Port: [5555]            │
└─────────────────────────────────────────────────────┘
```

| Option | Περιγραφή | ADB Target |
|--------|-----------|------------|
| **None** | Χωρίς Android testing | - |
| **Server Emulator** | Redroid στο server (default) | `localhost:5556` |
| **Remote ADB** | Σύνδεση σε device/emulator του χρήστη | `user_ip:port` |

### Remote ADB Setup (για τον χρήστη)

```bash
# Στο Android device/emulator του χρήστη
adb tcpip 5555

# Ή στον emulator του χρήστη (π.χ. Android Studio)
# Ήδη ακούει στο 5555
```

**Database fields (projects table):**
```sql
-- Project type
project_type ENUM('web', 'capacitor', 'react_native', 'flutter', 'native_android') DEFAULT 'web'

-- Android device settings
android_device_type ENUM('none', 'server', 'remote') DEFAULT 'none'
android_remote_host VARCHAR(255) DEFAULT NULL
android_remote_port INT DEFAULT 5555

-- Screen size (for server emulator)
android_screen_size ENUM('phone', 'phone_small', 'tablet_7', 'tablet_10') DEFAULT 'phone'
```

### Project Settings UI

```
┌─────────────────────────────────────────────────────┐
│ Project Settings                                    │
├─────────────────────────────────────────────────────┤
│ Project Type:                                       │
│ [Web ▼]                                             │
│  - Web (default)                                    │
│  - Capacitor.js                                     │
│  - React Native                                     │
│  - Flutter                                          │
│  - Native Android                                   │
├─────────────────────────────────────────────────────┤
│ Android Device:              (εμφανίζεται αν mobile)│
│ ○ None                                              │
│ ● Server Emulator                                   │
│ ○ Remote ADB                                        │
│   Host: [___________] Port: [5555]                  │
├─────────────────────────────────────────────────────┤
│ Screen Size:                 (αν Server Emulator)   │
│ [Phone (1080x1920) ▼]                               │
│  - Phone (1080x1920)                                │
│  - Phone Small (720x1280)                           │
│  - Tablet 7" (1200x1920)                            │
│  - Tablet 10" (1600x2560)                           │
└─────────────────────────────────────────────────────┘
```

### 2. Ticket Detail Tabs (Mobile Projects)

```
┌─────────┬──────────────┬────────────┐
│ Console │ Live Preview │ Emulator   │
└─────────┴──────────────┴────────────┘
```

| Tab | Capacitor | React Native | Flutter | Native Android |
|-----|-----------|--------------|---------|----------------|
| Console | ✅ | ✅ | ✅ | ✅ |
| Live Preview | ✅ Web app | ✅ Expo web | ✅ Web | ❌ Hidden |
| Emulator | ✅ | ✅ | ✅ | ✅ |

### 3. Emulator Tab Details
Location: Next to existing tabs (Console, Live Preview)

**UI Elements:**
| Element | Description |
|---------|-------------|
| Status Indicator | ● Running (green) / ○ Stopped (gray) |
| Start Button | Starts Redroid container |
| Stop Button | Stops Redroid container |
| Stream Area | iframe with ws-scrcpy stream |
| Message | "Emulator stopped" when not running |

### 3. API Endpoints

```
POST /api/emulator/start
Response: { "status": "running", "message": "Emulator started" }

POST /api/emulator/stop
Response: { "status": "stopped", "message": "Emulator stopped" }

GET /api/emulator/status
Response: { "status": "running|stopped", "device": "localhost:5556" }
```

### 4. Docker Container
- **Image:** `redroid/redroid:15.0.0_64only-latest`
- **Container name:** `redroid`
- **Port mapping:** `5556:5555`
- **1 global emulator** shared across all tickets

---

## User Flow

1. User opens ticket for Android project
2. Clicks "Emulator" tab
3. Sees status: "Stopped"
4. Clicks "Start Emulator"
5. Waits ~10 seconds for boot
6. Stream appears showing Android home screen
7. User can interact with emulator (touch, type)
8. When done, clicks "Stop Emulator" to free RAM

---

## Technical Details

### Start Emulator
```bash
docker start redroid || docker run -d --name redroid \
  --privileged \
  -p 5556:5555 \
  redroid/redroid:15.0.0_64only-latest \
  androidboot.redroid_gpu_mode=guest

adb connect localhost:5556
```

### Stop Emulator
```bash
docker stop redroid
```

### Check Status
```bash
docker ps --filter name=redroid --format "{{.Status}}"
```

### Stream URL
```
https://SERVER:8443/#!action=stream&udid=localhost%3A5556&player=mse&ws=wss%3A%2F%2FSERVER%3A8443%2F%3Faction%3Dproxy-adb%26remote%3Dtcp%253A8886%26udid%3Dlocalhost%253A5556
```

### ws-scrcpy Config
```yaml
# /opt/ws-scrcpy/dist/config.yaml
runGoogTracker: true
runApplTracker: false

server:
  - secure: true
    port: 8443
    hostname: 0.0.0.0
    options:
      certPath: /etc/codehero/ssl/cert.pem
      keyPath: /etc/codehero/ssl/key.pem
```

**Σημαντικό:** Το config φορτώνεται μέσω environment variable:
```
Environment=WS_SCRCPY_CONFIG=/opt/ws-scrcpy/dist/config.yaml
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `web/app.py` | Add API endpoints |
| `web/templates/ticket_detail.html` | Add Emulator tab |
| `scripts/setup_android.sh` | Setup script (done) |
| `database/schema.sql` | Add project_type if needed |

---

## Installed Packages (setup_android.sh)

### Core Components

| Package | Purpose |
|---------|---------|
| Docker | Container runtime για Redroid |
| Redroid | Android emulator (Docker image) |
| ADB | Android Debug Bridge |
| ws-scrcpy | Web streaming για Android |

### Android Development Tools

| Package | Purpose | Required For |
|---------|---------|--------------|
| `openjdk-17-jdk` | Java Development Kit | Native Android, Flutter |
| `gradle` | Build automation | Native Android |
| `aapt` | Android Asset Packaging Tool | APK analysis |
| `apksigner` | APK signing | Release builds |
| `zipalign` | APK optimization | Release builds |

### Flutter SDK

| Component | Path |
|-----------|------|
| Flutter SDK | `/opt/flutter` |
| Flutter binary | `/opt/flutter/bin/flutter` |

### Environment Variables

Αρχείο: `/etc/profile.d/android-dev.sh`

```bash
# Android Java (separate from system GraalVM)
export ANDROID_JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# Flutter
export PATH=/opt/flutter/bin:$PATH

# Function to switch to Android Java when needed
android-java() {
    export JAVA_HOME=$ANDROID_JAVA_HOME
    export PATH=$JAVA_HOME/bin:$PATH
}
```

### Java Configuration (GraalVM Compatibility)

Το σύστημα μπορεί να έχει **GraalVM** ως default Java. Για να αποφύγουμε conflicts:

| Variable | Value | Purpose |
|----------|-------|---------|
| `JAVA_HOME` | GraalVM (system default) | System applications |
| `ANDROID_JAVA_HOME` | OpenJDK 17 | Android builds |

**Για Android builds:**
```bash
# Option 1: Χρήση της function
android-java
./gradlew assembleDebug

# Option 2: Inline
JAVA_HOME=$ANDROID_JAVA_HOME ./gradlew assembleDebug

# Option 3: Στο gradle.properties του project
org.gradle.java.home=/usr/lib/jvm/java-17-openjdk-amd64
```

---

## RAM Considerations

- **Emulator stopped:** ~0 MB
- **Emulator running:** ~1-2 GB
- **Start on-demand** to conserve resources
- Auto-stop after inactivity (optional future feature)

---

## Android Versions

Ο χρήστης μπορεί να ζητήσει από τον Assistant να αλλάξει έκδοση Android.

### Available Images

| Version | Image | Size |
|---------|-------|------|
| Android 15 | `redroid/redroid:15.0.0_64only-latest` | ~800MB |
| Android 14 | `redroid/redroid:14.0.0_64only-latest` | ~750MB |
| Android 13 | `redroid/redroid:13.0.0-latest` | ~700MB |
| Android 12 | `redroid/redroid:12.0.0-latest` | ~650MB |
| Android 11 | `redroid/redroid:11.0.0-latest` | ~600MB |

### With GApps (Play Services)

| Version | Image |
|---------|-------|
| Android 15 + GApps | `kylindemons/redroid:15.0.0_amd64-GApps-Magisk-latest` |
| Android 14 + GApps | `kylindemons/redroid:14.0.0_amd64-GApps-Magisk-latest` |
| Android 13 + GApps | `kylindemons/redroid:13.0.0_amd64-GApps-Magisk-latest` |

### How to Change Version (Assistant Instructions)

Όταν ο χρήστης ζητήσει αλλαγή έκδοσης:

```bash
# 1. Stop current emulator
docker stop redroid
docker rm redroid

# 2. Pull new image
docker pull redroid/redroid:VERSION-latest

# 3. Start with new version
docker run -d --name redroid \
  --privileged \
  -p 5556:5555 \
  redroid/redroid:VERSION-latest \
  androidboot.redroid_gpu_mode=guest

# 4. Reconnect ADB
sleep 10
adb connect localhost:5556
```

### Example User Requests

- "Θέλω Android 13" → χρησιμοποίησε `redroid/redroid:13.0.0-latest`
- "Βάλε Android με Play Services" → χρησιμοποίησε `kylindemons/redroid:15.0.0_amd64-GApps-Magisk-latest`
- "Χρειάζομαι παλιά έκδοση για testing" → ρώτα ποια έκδοση, χρησιμοποίησε την αντίστοιχη

---

## Screen Size / Form Factor

Ο Redroid υποστηρίζει διαφορετικά μεγέθη οθόνης (phone, tablet) μέσω boot parameters.

### Available Presets

| Preset | Resolution | DPI | Use Case |
|--------|-----------|-----|----------|
| **Phone (Default)** | 1080x1920 | 440 | Standard smartphone |
| **Phone Small** | 720x1280 | 320 | Budget smartphones |
| **Tablet 7"** | 1200x1920 | 240 | Small tablets |
| **Tablet 10"** | 1600x2560 | 320 | Large tablets |

### Boot Parameters

```bash
# Phone (default - δεν χρειάζεται configuration)
docker run -d --name redroid \
  --privileged \
  -p 5556:5555 \
  redroid/redroid:15.0.0_64only-latest \
  androidboot.redroid_gpu_mode=guest

# Tablet 10"
docker run -d --name redroid \
  --privileged \
  -p 5556:5555 \
  redroid/redroid:15.0.0_64only-latest \
  androidboot.redroid_gpu_mode=guest \
  androidboot.redroid_width=1600 \
  androidboot.redroid_height=2560 \
  androidboot.redroid_dpi=320
```

### Database Field

```sql
-- Screen size preset
android_screen_size ENUM('phone', 'phone_small', 'tablet_7', 'tablet_10') DEFAULT 'phone'
```

### Presets Configuration

```python
SCREEN_PRESETS = {
    'phone': {
        'width': 1080,
        'height': 1920,
        'dpi': 440,
        'label': 'Phone (1080x1920)'
    },
    'phone_small': {
        'width': 720,
        'height': 1280,
        'dpi': 320,
        'label': 'Phone Small (720x1280)'
    },
    'tablet_7': {
        'width': 1200,
        'height': 1920,
        'dpi': 240,
        'label': 'Tablet 7" (1200x1920)'
    },
    'tablet_10': {
        'width': 1600,
        'height': 2560,
        'dpi': 320,
        'label': 'Tablet 10" (1600x2560)'
    }
}
```

### Docker Run με Screen Size

```python
def start_redroid(screen_size='phone'):
    preset = SCREEN_PRESETS.get(screen_size, SCREEN_PRESETS['phone'])

    cmd = [
        'docker', 'run', '-d', '--name', 'redroid',
        '--privileged',
        '-p', '5556:5555',
        'redroid/redroid:15.0.0_64only-latest',
        'androidboot.redroid_gpu_mode=guest',
        f'androidboot.redroid_width={preset["width"]}',
        f'androidboot.redroid_height={preset["height"]}',
        f'androidboot.redroid_dpi={preset["dpi"]}'
    ]

    subprocess.run(cmd)
```

### Αλλαγή Screen Size (requires restart)

```bash
# 1. Stop και remove τον emulator
docker stop redroid
docker rm redroid

# 2. Start με νέο screen size
docker run -d --name redroid \
  --privileged \
  -p 5556:5555 \
  redroid/redroid:15.0.0_64only-latest \
  androidboot.redroid_gpu_mode=guest \
  androidboot.redroid_width=1600 \
  androidboot.redroid_height=2560 \
  androidboot.redroid_dpi=320

# 3. Reconnect ADB
sleep 10
adb connect localhost:5556
```

---

## Assistant Testing (ADB Commands)

Ο Assistant μπορεί να δοκιμάζει Android εφαρμογές χρησιμοποιώντας ADB commands.

> **Σημείωση:** Το Playwright δεν υποστηρίζει Android. Χρησιμοποιούμε ADB για automation.

### Πώς "Βλέπει" ο Assistant την Οθόνη

Ο Assistant **δεν μπορεί** να δει το web stream (ws-scrcpy) γιατί:
- Είναι CLI-based, δεν έχει browser
- Το ws-scrcpy είναι real-time video (WebSocket + H264)

**Λύση: Screenshots μέσω ADB**

```bash
# Ο Assistant παίρνει screenshot
adb exec-out screencap -p > /tmp/android-screen.png

# Και το διαβάζει (multimodal - μπορεί να δει εικόνες)
# → Αναλύει τι δείχνει η οθόνη
# → Αποφασίζει τι ενέργεια να κάνει
```

**Testing Workflow:**
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  1. Screenshot  │────▶│  2. Read PNG    │────▶│  3. Analyze     │
│  (adb screencap)│     │  (multimodal)   │     │  (what's shown) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  6. Repeat      │◀────│  5. Execute     │◀────│  4. Decide      │
│                 │     │  (tap/swipe/text)│     │  (next action)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Διαθέσιμες Εντολές

| Εντολή | Περιγραφή |
|--------|-----------|
| `adb install app.apk` | Εγκατάσταση APK |
| `adb shell am start -n package/.Activity` | Άνοιγμα εφαρμογής |
| `adb shell input tap X Y` | Tap σε συντεταγμένες |
| `adb shell input swipe X1 Y1 X2 Y2` | Swipe gesture |
| `adb shell input text "text"` | Πληκτρολόγηση κειμένου |
| `adb shell input keyevent CODE` | Πάτημα κουμπιού |
| `adb exec-out screencap -p > screen.png` | Screenshot |
| `adb shell uiautomator dump` | UI hierarchy (XML) |

### Key Events

| Code | Κουμπί |
|------|--------|
| `KEYCODE_HOME` | Home |
| `KEYCODE_BACK` | Back |
| `KEYCODE_ENTER` | Enter |
| `KEYCODE_DEL` | Backspace |
| `KEYCODE_TAB` | Tab |

### Παράδειγμα Testing Flow

```bash
# 1. Εγκατάσταση APK
adb install /opt/apps/myapp/app-debug.apk

# 2. Άνοιγμα εφαρμογής
adb shell am start -n com.example.myapp/.MainActivity

# 3. Περίμενε να φορτώσει
sleep 3

# 4. Screenshot για να δεις την κατάσταση
adb exec-out screencap -p > /tmp/screen1.png

# 5. Tap σε κουμπί (συντεταγμένες από UI dump)
adb shell input tap 540 960

# 6. Πληκτρολόγηση
adb shell input text "hello@example.com"

# 7. Tap στο επόμενο πεδίο
adb shell input tap 540 1100

# 8. Άλλη πληκτρολόγηση
adb shell input text "password123"

# 9. Tap στο Login button
adb shell input tap 540 1300

# 10. Screenshot για επαλήθευση
sleep 2
adb exec-out screencap -p > /tmp/screen2.png
```

### Εύρεση Συντεταγμένων UI Elements

```bash
# Dump UI hierarchy σε XML
adb shell uiautomator dump /sdcard/ui.xml
adb pull /sdcard/ui.xml /tmp/ui.xml

# Το XML περιέχει bounds για κάθε element:
# bounds="[0,0][1080,1920]" → center: (540, 960)
```

### Logcat για Debugging

```bash
# Όλα τα logs
adb logcat

# Φιλτραρισμένα logs για την εφαρμογή
adb logcat | grep "com.example.myapp"

# Τελευταίες 100 γραμμές
adb logcat -d | tail -100

# Clear και fresh logs
adb logcat -c && adb logcat
```

---

## Android Debugging Tools

Όταν δημιουργείται ένα Android project, ο Assistant πρέπει να γνωρίζει τα διαθέσιμα εργαλεία debugging.

### Εργαλεία ανά Project Type

| Project Type | Build Errors | Runtime Errors | UI Testing |
|--------------|--------------|----------------|------------|
| **Capacitor.js** | Terminal output | Chrome DevTools + Logcat | ADB + Screenshots |
| **React Native** | Metro bundler | React Native Debugger + Logcat | ADB + Screenshots |
| **Flutter** | `flutter run` output | Flutter DevTools + Logcat | ADB + Screenshots |
| **Native Android** | Gradle output | Logcat | ADB + Screenshots |

### Debugging Commands

```bash
# Build errors - δες το output της εντολής build
./gradlew assembleDebug 2>&1 | tail -50

# Runtime crashes - logcat με φίλτρο
adb logcat *:E | grep -i "exception\|error\|crash"

# ANR (App Not Responding)
adb logcat -b events | grep "am_anr"

# Memory issues
adb shell dumpsys meminfo com.example.myapp

# Network traffic
adb shell dumpsys connectivity
```

### Crash Analysis

```bash
# Πάρε το stack trace από crash
adb logcat -d | grep -A 20 "FATAL EXCEPTION"

# Tombstone files (native crashes)
adb shell ls /data/tombstones/
adb pull /data/tombstones/tombstone_00 /tmp/
```

---

## Documentation Requirements

> **ΣΗΜΑΝΤΙΚΟ:** Τα παρακάτω πρέπει να ενημερωθούν όταν γίνει implementation.

### Assistant Documentation

| Αρχείο | Τι να προστεθεί |
|--------|-----------------|
| `CLAUDE.md` | Android project instructions |
| `CLAUDE_DEV_NOTES.md` | ADB commands reference |
| `PROJECT_TEMPLATE.md` | Android project template section |

### User Manual

| Section | Περιεχόμενο |
|---------|-------------|
| Project Types | Capacitor, React Native, Flutter, Native Android |
| Emulator Tab | Πώς να ξεκινήσει/σταματήσει ο emulator |
| Debugging | Πώς να δει logs, screenshots |
| Android Versions | Πώς να αλλάξει έκδοση Android |

### System Prompt Update

Όταν το project είναι Android-based, το system prompt του Assistant πρέπει να περιλαμβάνει πληροφορίες με βάση τα project settings.

**Template (δυναμικό):**

```
## Android Development Environment

Project Type: {{project_type}}
Android Device: {{android_device_type}}
ADB Target: {{adb_target}}

### ADB Connection
To connect to the Android device:
adb connect {{adb_target}}

### Available Commands
- Screenshot: adb -s {{adb_target}} exec-out screencap -p > /tmp/screen.png
- UI Dump: adb -s {{adb_target}} shell uiautomator dump /sdcard/ui.xml && adb -s {{adb_target}} pull /sdcard/ui.xml /tmp/
- Logcat: adb -s {{adb_target}} logcat -d | tail -100
- Install APK: adb -s {{adb_target}} install <path>
- Input tap: adb -s {{adb_target}} shell input tap X Y
- Input text: adb -s {{adb_target}} shell input text "text"

### Testing Workflow
1. Build the app ({{build_command}})
2. Connect to device: adb connect {{adb_target}}
3. Install APK to device
4. Take screenshot to see current state
5. Use adb input commands to interact
6. Check logcat for errors
```

**Παραδείγματα:**

| Setting | adb_target | Περιγραφή |
|---------|------------|-----------|
| Server Emulator | `localhost:5556` | Redroid στο server |
| Remote ADB | `192.168.1.100:5555` | Device/emulator του χρήστη |

**Python code για generation:**
```python
def get_android_system_prompt(project):
    if project.android_device_type == 'none':
        return ""

    if project.android_device_type == 'server':
        adb_target = "localhost:5556"
    else:  # remote
        adb_target = f"{project.android_remote_host}:{project.android_remote_port}"

    return f"""
## Android Development Environment

Project Type: {project.project_type}
ADB Target: {adb_target}

Before testing, connect to the device:
adb connect {adb_target}

Use -s {adb_target} for all adb commands to ensure correct device.
"""
```

**Σημαντικό:** Το AI πρέπει να χρησιμοποιεί `-s {adb_target}` σε όλες τις adb εντολές για να συνδέεται στο σωστό device.

---

## iOS Support

**Status: ❌ Not supported**

| Λόγος | Περιγραφή |
|-------|-----------|
| Requires macOS | Xcode & iOS Simulator τρέχουν μόνο σε Mac |
| Security risk | Remote access σε personal Mac = κίνδυνος |
| No Redroid equivalent | Δεν υπάρχει containerized iOS |

**Workflow για iOS:**
1. Develop κώδικα στο CodeHero (Capacitor/React Native/Flutter)
2. Build & test στο δικό σου Mac

---

## Future Enhancements

1. [ ] GApps support via UI selection
2. [ ] Multiple emulators (different versions)
3. [ ] APK auto-install on ticket run
4. [ ] Remote device support (user's own Android phone)
5. [ ] Auto-stop after X minutes idle
6. [ ] Screenshot capture
7. [ ] Logcat viewer

---

**Version:** 1.7
**Date:** 2026-01-15
