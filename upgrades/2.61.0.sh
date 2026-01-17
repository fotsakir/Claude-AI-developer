#!/bin/bash
# Upgrade to version 2.61.0
# Installs Claude Code CLI

log_info() { echo -e "\033[0;36m[2.61.0]\033[0m $1"; }

CLAUDE_USER="claude"

# Install Claude Code CLI if not present
if ! su - ${CLAUDE_USER} -c 'which claude' &>/dev/null; then
    log_info "Installing Claude Code CLI..."
    su - ${CLAUDE_USER} -c 'curl -fsSL https://claude.ai/install.sh | bash' 2>/dev/null || true

    # Add to PATH if not already
    if ! su - ${CLAUDE_USER} -c 'grep -q "\.local/bin" ~/.bashrc' 2>/dev/null; then
        su - ${CLAUDE_USER} -c 'echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> ~/.bashrc'
    fi

    if su - ${CLAUDE_USER} -c 'which claude' &>/dev/null; then
        log_info "Claude Code CLI installed"
    else
        log_info "Claude Code CLI installation failed - install manually"
    fi
else
    log_info "Claude Code CLI already installed"
fi
