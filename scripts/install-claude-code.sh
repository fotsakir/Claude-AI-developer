#!/bin/bash
# =====================================================
# Install Claude Code CLI
# Standalone script for Ubuntu/Debian
# =====================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║           CLAUDE CODE INSTALLER                           ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${YELLOW}Running as root - will create 'claude' user${NC}"
    CLAUDE_USER="claude"

    # Create claude user if not exists
    if ! id "$CLAUDE_USER" &>/dev/null; then
        echo "Creating user '$CLAUDE_USER'..."
        useradd -m -s /bin/bash "$CLAUDE_USER"
        echo -e "${GREEN}User '$CLAUDE_USER' created${NC}"
    else
        echo -e "${GREEN}User '$CLAUDE_USER' already exists${NC}"
    fi

    RUN_AS="su - $CLAUDE_USER -c"
else
    CLAUDE_USER="$USER"
    RUN_AS="bash -c"
    echo -e "${YELLOW}Running as user: $CLAUDE_USER${NC}"
fi

echo ""

# Check/Install Node.js
echo "Checking Node.js..."
if ! command -v node &>/dev/null; then
    echo -e "${YELLOW}Node.js not found. Installing...${NC}"
    if [ "$EUID" -eq 0 ]; then
        curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
        apt-get install -y nodejs
    else
        echo -e "${RED}Node.js is required. Please install it first:${NC}"
        echo "  curl -fsSL https://deb.nodesource.com/setup_22.x | sudo bash -"
        echo "  sudo apt-get install -y nodejs"
        exit 1
    fi
fi
echo -e "${GREEN}Node.js: $(node --version)${NC}"

echo ""

# Check if Claude Code already installed
if $RUN_AS "which claude" &>/dev/null; then
    echo -e "${GREEN}Claude Code is already installed!${NC}"
    $RUN_AS "claude --version" 2>/dev/null || true
    echo ""
    echo -e "${YELLOW}To reconfigure, run:${NC}"
    echo "  claude config set apiKey YOUR_API_KEY"
    exit 0
fi

# Install Claude Code
echo "Installing Claude Code..."
echo ""

if [ "$EUID" -eq 0 ]; then
    su - $CLAUDE_USER -c 'curl -fsSL https://claude.ai/install.sh | bash'
    # Add ~/.local/bin to PATH if not already there
    if ! su - $CLAUDE_USER -c 'grep -q "\.local/bin" ~/.bashrc' 2>/dev/null; then
        su - $CLAUDE_USER -c 'echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> ~/.bashrc'
        echo -e "${GREEN}Added ~/.local/bin to PATH${NC}"
    fi
else
    curl -fsSL https://claude.ai/install.sh | bash
    # Add ~/.local/bin to PATH if not already there
    if ! grep -q "\.local/bin" ~/.bashrc 2>/dev/null; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        echo -e "${GREEN}Added ~/.local/bin to PATH${NC}"
    fi
fi

echo ""

# Verify installation
if $RUN_AS "which claude" &>/dev/null; then
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗"
    echo "║           INSTALLATION SUCCESSFUL!                        ║"
    echo "╚═══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo ""
    if [ "$EUID" -eq 0 ]; then
        echo "  1. Switch to claude user and go to home directory:"
        echo "     ${CYAN}su - claude${NC}"
        echo "     ${CYAN}cd /home/claude${NC}"
        echo ""
        echo "  2. Run claude to login (API key or Max subscription):"
        echo "     ${CYAN}claude${NC}"
        echo ""
        echo -e "  ${YELLOW}Or all in one command:${NC}"
        echo "     ${CYAN}su - claude -c 'cd /home/claude && claude'${NC}"
    else
        echo "  1. Go to your home directory:"
        echo "     ${CYAN}cd ~${NC}"
        echo ""
        echo "  2. Run claude to login (API key or Max subscription):"
        echo "     ${CYAN}claude${NC}"
    fi
else
    echo -e "${RED}Installation may have failed.${NC}"
    echo "Try manually:"
    echo "  curl -fsSL https://claude.ai/install.sh | sh"
    exit 1
fi
