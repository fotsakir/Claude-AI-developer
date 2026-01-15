#!/bin/bash
# =====================================================
# CODEHERO - Development Tools Installation
# =====================================================
# Installs optional development tools:
#   - Node.js 22
#   - GraalVM (Java 24)
#   - Playwright (browser automation)
#   - Multimedia tools (ffmpeg, imagemagick, tesseract)
#
# Run after setup.sh:
#   sudo ./setup_devtools.sh
# =====================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${GREEN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║       CODEHERO - Development Tools                        ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# =====================================================
# ROOT/SUDO CHECK
# =====================================================
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

# Load config
if [ -f "${SCRIPT_DIR}/install.conf" ]; then
    source "${SCRIPT_DIR}/install.conf"
fi
CLAUDE_USER="${CLAUDE_USER:-claude}"

echo ""
echo "This will install:"
echo "  - Node.js 22 (JavaScript runtime)"
echo "  - GraalVM 24 (Java runtime)"
echo "  - Playwright (browser automation)"
echo "  - Multimedia tools (ffmpeg, imagemagick, tesseract)"
echo ""
read -p "Continue? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Aborted."
    exit 0
fi

# =====================================================
# [1/4] NODE.JS
# =====================================================
echo ""
echo -e "${YELLOW}[1/4] Installing Node.js 22...${NC}"

if command -v node &> /dev/null; then
    NODE_VER=$(node --version 2>/dev/null)
    echo -e "${CYAN}  Node.js already installed: ${NODE_VER}${NC}"
else
    curl -fsSL https://deb.nodesource.com/setup_22.x 2>/dev/null | bash - || true
    apt-get install -y nodejs || true
    if command -v node &> /dev/null; then
        echo -e "${GREEN}  ✓ Node.js $(node --version) installed${NC}"
    else
        echo -e "${RED}  ✗ Node.js installation failed${NC}"
    fi
fi

# =====================================================
# [2/4] GRAALVM (Java)
# =====================================================
echo ""
echo -e "${YELLOW}[2/4] Installing GraalVM (Java 24)...${NC}"

GRAALVM_DIR="/opt/graalvm"
if [ -f "$GRAALVM_DIR/bin/java" ]; then
    JAVA_VER=$($GRAALVM_DIR/bin/java --version 2>/dev/null | head -1)
    echo -e "${CYAN}  GraalVM already installed: ${JAVA_VER}${NC}"
else
    cd /tmp
    echo "  Downloading GraalVM..."
    if curl -fsSL "https://download.oracle.com/graalvm/24/latest/graalvm-jdk-24_linux-x64_bin.tar.gz" -o graalvm.tar.gz 2>/dev/null; then
        mkdir -p $GRAALVM_DIR
        tar -xzf graalvm.tar.gz -C $GRAALVM_DIR --strip-components=1 || true
        rm -f graalvm.tar.gz

        # Setup environment
        cat > /etc/profile.d/graalvm.sh << 'EOF'
export GRAALVM_HOME=/opt/graalvm
export JAVA_HOME=$GRAALVM_HOME
export PATH=$GRAALVM_HOME/bin:$PATH
EOF
        ln -sf $GRAALVM_DIR/bin/java /usr/local/bin/java 2>/dev/null || true
        ln -sf $GRAALVM_DIR/bin/javac /usr/local/bin/javac 2>/dev/null || true

        if [ -f "$GRAALVM_DIR/bin/java" ]; then
            echo -e "${GREEN}  ✓ GraalVM installed${NC}"
            $GRAALVM_DIR/bin/java --version 2>/dev/null | head -1
        else
            echo -e "${RED}  ✗ GraalVM installation failed${NC}"
        fi
    else
        echo -e "${RED}  ✗ Failed to download GraalVM${NC}"
    fi
fi

# =====================================================
# [3/4] PLAYWRIGHT (usually already installed by setup.sh)
# =====================================================
echo ""
echo -e "${YELLOW}[3/4] Checking Playwright...${NC}"

if su - ${CLAUDE_USER} -c "python3 -c 'from playwright.sync_api import sync_playwright'" 2>/dev/null; then
    echo -e "${CYAN}  ✓ Playwright already installed (by setup.sh)${NC}"
else
    echo "  Installing Playwright..."

    # Install system dependencies
    apt-get install -y --no-install-recommends \
        libasound2t64 libatk-bridge2.0-0t64 libatk1.0-0t64 libatspi2.0-0t64 \
        libcairo2 libcups2t64 libdbus-1-3 libdrm2 libgbm1 libglib2.0-0t64 \
        libnspr4 libnss3 libpango-1.0-0 libx11-6 libxcb1 libxcomposite1 \
        libxdamage1 libxext6 libxfixes3 libxkbcommon0 libxrandr2 xvfb \
        fonts-noto-color-emoji fonts-unifont libfontconfig1 libfreetype6 \
        xfonts-cyrillic xfonts-scalable fonts-liberation fonts-ipafont-gothic \
        fonts-wqy-zenhei fonts-tlwg-loma-otf fonts-freefont-ttf 2>/dev/null || true

    # Install Playwright Python package
    pip3 install --ignore-installed playwright --break-system-packages 2>&1 || \
    pip3 install --ignore-installed playwright 2>&1 || true

    # Install browsers for claude user
    echo "  Installing Chromium browser..."
    su - ${CLAUDE_USER} -c "playwright install chromium" 2>/dev/null || \
    playwright install chromium 2>/dev/null || true

    if su - ${CLAUDE_USER} -c "python3 -c 'from playwright.sync_api import sync_playwright'" 2>/dev/null; then
        echo -e "${GREEN}  ✓ Playwright installed${NC}"
    else
        echo -e "${YELLOW}  ⚠ Playwright may need manual setup${NC}"
    fi
fi

# =====================================================
# [4/4] MULTIMEDIA TOOLS
# =====================================================
echo ""
echo -e "${YELLOW}[4/4] Installing multimedia tools...${NC}"

apt-get install -y ffmpeg imagemagick tesseract-ocr tesseract-ocr-eng tesseract-ocr-ell \
    poppler-utils ghostscript sox mediainfo webp optipng jpegoptim \
    librsvg2-bin libvips-tools qpdf 2>/dev/null || true

# Python multimedia libraries
pip3 install --ignore-installed Pillow opencv-python-headless pydub pytesseract pdf2image --break-system-packages 2>&1 || \
pip3 install --ignore-installed Pillow opencv-python-headless pydub pytesseract pdf2image 2>&1 || true

echo -e "${GREEN}  ✓ Multimedia tools installed${NC}"

# =====================================================
# SUMMARY
# =====================================================
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗"
echo "║          DEVELOPMENT TOOLS INSTALLED!                       ║"
echo "╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Installed tools:"

# Node.js
if command -v node &> /dev/null; then
    echo -e "  Node.js:     ${GREEN}$(node --version)${NC}"
else
    echo -e "  Node.js:     ${RED}not installed${NC}"
fi

# Java
if command -v java &> /dev/null; then
    echo -e "  Java:        ${GREEN}$(java --version 2>&1 | head -1)${NC}"
else
    echo -e "  Java:        ${RED}not installed${NC}"
fi

# Playwright
if python3 -c "import playwright" 2>/dev/null; then
    echo -e "  Playwright:  ${GREEN}installed${NC}"
else
    echo -e "  Playwright:  ${RED}not installed${NC}"
fi

# ffmpeg
if command -v ffmpeg &> /dev/null; then
    echo -e "  ffmpeg:      ${GREEN}installed${NC}"
else
    echo -e "  ffmpeg:      ${RED}not installed${NC}"
fi

echo ""
echo -e "${CYAN}Environment variables (for Java):${NC}"
echo "  source /etc/profile.d/graalvm.sh"
echo ""
