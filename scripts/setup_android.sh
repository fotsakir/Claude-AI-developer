#!/bin/bash
# =====================================================
# CodeHero Android Emulator Setup
# Installs: Docker, Redroid (Android 15), ws-scrcpy,
#           Java, Gradle, Flutter, Android SDK tools
#
# Safe to run multiple times (idempotent)
# =====================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  CodeHero Android Emulator Setup${NC}"
echo -e "${GREEN}========================================${NC}"

# Check root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo)${NC}"
    exit 1
fi

# =====================================================
# [1/8] DOCKER
# =====================================================
echo -e "${YELLOW}[1/8] Docker...${NC}"

if command -v docker &> /dev/null; then
    echo -e "${BLUE}  ✓ Already installed${NC}"
else
    echo -e "  Installing Docker..."
    apt-get update
    apt-get install -y ca-certificates curl gnupg

    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Add claude user to docker group
    usermod -aG docker claude 2>/dev/null || true

    echo -e "${GREEN}  ✓ Installed${NC}"
fi

# =====================================================
# [2/8] REDROID (Android 15)
# =====================================================
echo -e "${YELLOW}[2/8] Redroid (Android 15)...${NC}"

# Check if container exists and is running
if docker ps --format '{{.Names}}' | grep -q "^redroid$"; then
    echo -e "${BLUE}  ✓ Already running${NC}"
elif docker ps -a --format '{{.Names}}' | grep -q "^redroid$"; then
    echo -e "  Starting existing container..."
    docker start redroid
    echo -e "${GREEN}  ✓ Started${NC}"
else
    echo -e "  Pulling image and creating container..."
    docker pull redroid/redroid:15.0.0_64only-latest

    docker run -d --name redroid \
        --privileged \
        --restart unless-stopped \
        -p 5556:5555 \
        redroid/redroid:15.0.0_64only-latest \
        androidboot.redroid_gpu_mode=guest

    echo -e "${GREEN}  ✓ Created and started${NC}"
fi

# =====================================================
# [3/8] ADB & ANDROID TOOLS
# =====================================================
echo -e "${YELLOW}[3/8] ADB & Android tools...${NC}"

MISSING_TOOLS=""
command -v adb &> /dev/null || MISSING_TOOLS="$MISSING_TOOLS adb"
command -v aapt &> /dev/null || MISSING_TOOLS="$MISSING_TOOLS aapt"
command -v apksigner &> /dev/null || MISSING_TOOLS="$MISSING_TOOLS apksigner"
command -v zipalign &> /dev/null || MISSING_TOOLS="$MISSING_TOOLS zipalign"

if [ -z "$MISSING_TOOLS" ]; then
    echo -e "${BLUE}  ✓ Already installed${NC}"
else
    echo -e "  Installing:$MISSING_TOOLS"
    apt-get install -y adb aapt apksigner zipalign 2>/dev/null || apt-get install -y android-tools-adb 2>/dev/null || true
    echo -e "${GREEN}  ✓ Installed${NC}"
fi

# Connect ADB (always try)
echo -e "  Connecting ADB..."
sleep 3
su - claude -c "adb kill-server" 2>/dev/null || true
su - claude -c "adb start-server" 2>/dev/null || true
su - claude -c "adb connect localhost:5556" 2>/dev/null || true
echo -e "${GREEN}  ✓ ADB connected${NC}"

# =====================================================
# [4/8] JAVA JDK (for Android)
# =====================================================
echo -e "${YELLOW}[4/8] Java JDK 17 (for Android)...${NC}"

if [ -d /usr/lib/jvm/java-17-openjdk-amd64 ]; then
    echo -e "${BLUE}  ✓ Already installed${NC}"
else
    echo -e "  Installing OpenJDK 17..."
    apt-get install -y openjdk-17-jdk openjdk-17-jdk-headless
    echo -e "${GREEN}  ✓ Installed${NC}"
fi

# Setup environment (check if already configured)
if [ ! -f /etc/profile.d/android-dev.sh ] || ! grep -q "ANDROID_JAVA_HOME" /etc/profile.d/android-dev.sh 2>/dev/null; then
    echo -e "  Configuring environment..."
    cat >> /etc/profile.d/android-dev.sh << 'EOF'
# Android Development - Java 17 (separate from system GraalVM)
export ANDROID_JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

# Function to switch to Android Java when needed
android-java() {
    export JAVA_HOME=$ANDROID_JAVA_HOME
    export PATH=$JAVA_HOME/bin:$PATH
    echo "Switched to Android Java: $(java -version 2>&1 | head -1)"
}
EOF
    echo -e "${GREEN}  ✓ Environment configured${NC}"
else
    echo -e "${BLUE}  ✓ Environment already configured${NC}"
fi

# =====================================================
# [5/8] GRADLE
# =====================================================
echo -e "${YELLOW}[5/8] Gradle...${NC}"

if command -v gradle &> /dev/null; then
    echo -e "${BLUE}  ✓ Already installed${NC}"
else
    echo -e "  Installing Gradle..."
    apt-get install -y gradle
    echo -e "${GREEN}  ✓ Installed${NC}"
fi

# =====================================================
# [6/8] FLUTTER SDK
# =====================================================
echo -e "${YELLOW}[6/8] Flutter SDK...${NC}"

if [ -d /opt/flutter ] && [ -x /opt/flutter/bin/flutter ]; then
    echo -e "${BLUE}  ✓ Already installed${NC}"
else
    echo -e "  Downloading Flutter SDK..."
    cd /opt

    curl -LO https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_3.24.5-stable.tar.xz
    tar xf flutter_linux_3.24.5-stable.tar.xz
    rm flutter_linux_3.24.5-stable.tar.xz

    chown -R claude:claude /opt/flutter

    # Add to PATH if not already
    if ! grep -q "/opt/flutter/bin" /etc/profile.d/android-dev.sh 2>/dev/null; then
        echo 'export PATH=/opt/flutter/bin:$PATH' >> /etc/profile.d/android-dev.sh
    fi

    # Pre-cache Flutter dependencies
    echo -e "  Pre-caching Flutter..."
    su - claude -c "export PATH=/opt/flutter/bin:\$PATH && flutter precache --android" || true

    echo -e "${GREEN}  ✓ Installed${NC}"
fi

# =====================================================
# [7/8] WS-SCRCPY
# =====================================================
echo -e "${YELLOW}[7/8] ws-scrcpy...${NC}"

# Check npm
if ! command -v npm &> /dev/null; then
    echo -e "  Installing npm..."
    apt-get install -y npm
fi

# Check scrcpy
if ! command -v scrcpy &> /dev/null; then
    echo -e "  Installing scrcpy..."
    apt-get install -y scrcpy 2>/dev/null || true
fi

if [ -d /opt/ws-scrcpy/dist ] && [ -f /opt/ws-scrcpy/dist/index.js ]; then
    echo -e "${BLUE}  ✓ Already installed${NC}"
else
    echo -e "  Cloning and building ws-scrcpy..."
    cd /opt
    rm -rf ws-scrcpy 2>/dev/null || true
    git clone https://github.com/NetrisTV/ws-scrcpy.git
    cd ws-scrcpy
    npm install
    npm run dist
    echo -e "${GREEN}  ✓ Installed${NC}"
fi

# Create/update config (HTTPS on port 8443)
cat > /opt/ws-scrcpy/dist/config.yaml << 'EOF'
runGoogTracker: true
runApplTracker: false

server:
  - secure: true
    port: 8443
    hostname: 0.0.0.0
    options:
      certPath: /etc/codehero/ssl/cert.pem
      keyPath: /etc/codehero/ssl/key.pem
EOF

# =====================================================
# [8/8] SYSTEMD SERVICES
# =====================================================
echo -e "${YELLOW}[8/8] Systemd services...${NC}"

# Create systemd services
SERVICES_UPDATED=false

# ws-scrcpy service (always update to ensure correct config)
cat > /etc/systemd/system/ws-scrcpy.service << 'EOF'
[Unit]
Description=ws-scrcpy Android Screen Mirror
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
WorkingDirectory=/opt/ws-scrcpy/dist
Environment=WS_SCRCPY_CONFIG=/opt/ws-scrcpy/dist/config.yaml
ExecStartPre=/bin/sleep 10
ExecStart=/usr/bin/node index.js
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
SERVICES_UPDATED=true
echo -e "${GREEN}  ✓ ws-scrcpy.service configured${NC}"

# ADB connect service
if [ -f /etc/systemd/system/adb-connect.service ]; then
    echo -e "${BLUE}  ✓ adb-connect.service exists${NC}"
else
    cat > /etc/systemd/system/adb-connect.service << 'EOF'
[Unit]
Description=ADB Connect to Redroid
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStartPre=/bin/sleep 15
ExecStart=/usr/bin/adb connect localhost:5556
RemainAfterExit=yes
User=claude

[Install]
WantedBy=multi-user.target
EOF
    SERVICES_UPDATED=true
    echo -e "${GREEN}  ✓ adb-connect.service created${NC}"
fi

# Reload and enable if needed
if [ "$SERVICES_UPDATED" = true ]; then
    systemctl daemon-reload
fi

systemctl enable ws-scrcpy adb-connect 2>/dev/null || true

# Start services if not running
systemctl is-active --quiet ws-scrcpy || systemctl start ws-scrcpy

# Cleanup old https-proxy service if exists
if [ -f /etc/systemd/system/ws-scrcpy-https.service ]; then
    echo -e "  Removing old https-proxy service..."
    systemctl stop ws-scrcpy-https 2>/dev/null || true
    systemctl disable ws-scrcpy-https 2>/dev/null || true
    rm -f /etc/systemd/system/ws-scrcpy-https.service
    rm -f /opt/ws-scrcpy/https-proxy.js
    systemctl daemon-reload
    echo -e "${GREEN}  ✓ Old https-proxy removed${NC}"
fi

echo -e "${GREEN}  ✓ Services enabled${NC}"

# =====================================================
# DONE
# =====================================================
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Android Emulator Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Access ws-scrcpy:"
echo -e "  https://YOUR_IP:8443/"
echo ""
echo -e "ADB Device: localhost:5556"
echo ""
echo -e "Installed Tools:"
echo -e "  Java:    $(/usr/lib/jvm/java-17-openjdk-amd64/bin/java -version 2>&1 | head -1 || echo 'not found')"
echo -e "  Gradle:  $(gradle -v 2>/dev/null | grep Gradle || echo 'installed')"
echo -e "  Flutter: $(/opt/flutter/bin/flutter --version 2>/dev/null | head -1 || echo 'installed')"
echo ""
echo -e "Services:"
echo -e "  sudo systemctl status ws-scrcpy"
echo ""
echo -e "Environment:"
echo -e "  source /etc/profile.d/android-dev.sh"
echo ""
