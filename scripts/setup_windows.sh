#!/bin/bash
# =====================================================
# CodeHero Windows Development Setup
# Installs: .NET SDK 8.0, PowerShell, Wine, Mono,
#           NuGet, MSBuild tools
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
echo -e "${GREEN}  CodeHero Windows Development Setup${NC}"
echo -e "${GREEN}========================================${NC}"

# Check root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root (sudo)${NC}"
    exit 1
fi

# =====================================================
# [1/6] .NET SDK 8.0
# =====================================================
echo -e "${YELLOW}[1/6] .NET SDK 8.0...${NC}"

if command -v dotnet &> /dev/null; then
    DOTNET_VERSION=$(dotnet --version 2>/dev/null || echo "unknown")
    echo -e "${BLUE}  ✓ Already installed (v$DOTNET_VERSION)${NC}"
else
    echo -e "  Installing .NET SDK 8.0..."
    apt-get update
    apt-get install -y dotnet-sdk-8.0
    echo -e "${GREEN}  ✓ Installed${NC}"
fi

# =====================================================
# [2/6] POWERSHELL
# =====================================================
echo -e "${YELLOW}[2/6] PowerShell...${NC}"

if command -v pwsh &> /dev/null; then
    PWSH_VERSION=$(pwsh --version 2>/dev/null || echo "unknown")
    echo -e "${BLUE}  ✓ Already installed ($PWSH_VERSION)${NC}"
else
    echo -e "  Adding Microsoft repository..."

    # Download and install Microsoft signing key
    curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-archive-keyring.gpg 2>/dev/null || true

    # Add repository
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-archive-keyring.gpg] https://packages.microsoft.com/ubuntu/24.04/prod noble main" > /etc/apt/sources.list.d/microsoft-prod.list

    apt-get update
    apt-get install -y powershell
    echo -e "${GREEN}  ✓ Installed${NC}"
fi

# =====================================================
# [3/6] WINE (Windows compatibility layer)
# =====================================================
echo -e "${YELLOW}[3/6] Wine...${NC}"

if command -v wine &> /dev/null; then
    echo -e "${BLUE}  ✓ Already installed${NC}"
else
    echo -e "  Enabling 32-bit architecture..."
    dpkg --add-architecture i386

    echo -e "  Adding WineHQ repository..."
    mkdir -p /etc/apt/keyrings
    curl -sSL https://dl.winehq.org/wine-builds/winehq.key | gpg --dearmor -o /etc/apt/keyrings/winehq-archive.key 2>/dev/null || true

    echo "deb [arch=amd64,i386 signed-by=/etc/apt/keyrings/winehq-archive.key] https://dl.winehq.org/wine-builds/ubuntu/ noble main" > /etc/apt/sources.list.d/winehq.list

    apt-get update

    # Install Wine stable (or fallback to distro version)
    apt-get install -y --install-recommends winehq-stable 2>/dev/null || apt-get install -y wine 2>/dev/null || apt-get install -y wine64 wine32 2>/dev/null || true

    if command -v wine &> /dev/null; then
        echo -e "${GREEN}  ✓ Installed${NC}"
    else
        echo -e "${RED}  ✗ Installation failed (optional)${NC}"
    fi
fi

# =====================================================
# [4/6] MONO (.NET Framework runtime)
# =====================================================
echo -e "${YELLOW}[4/6] Mono Runtime...${NC}"

if command -v mono &> /dev/null; then
    MONO_VERSION=$(mono --version 2>/dev/null | head -1 || echo "unknown")
    echo -e "${BLUE}  ✓ Already installed${NC}"
else
    echo -e "  Adding Mono repository..."

    apt-get install -y ca-certificates gnupg
    gpg --homedir /tmp --no-default-keyring --keyring /usr/share/keyrings/mono-official-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF 2>/dev/null || true

    echo "deb [signed-by=/usr/share/keyrings/mono-official-archive-keyring.gpg] https://download.mono-project.com/repo/ubuntu stable-focal main" > /etc/apt/sources.list.d/mono-official-stable.list

    apt-get update
    apt-get install -y mono-complete 2>/dev/null || apt-get install -y mono-runtime mono-devel 2>/dev/null || true

    if command -v mono &> /dev/null; then
        echo -e "${GREEN}  ✓ Installed${NC}"
    else
        echo -e "${RED}  ✗ Installation failed (optional)${NC}"
    fi
fi

# =====================================================
# [5/6] NUGET PACKAGE MANAGER
# =====================================================
echo -e "${YELLOW}[5/6] NuGet...${NC}"

if command -v nuget &> /dev/null || [ -f /usr/local/bin/nuget.exe ]; then
    echo -e "${BLUE}  ✓ Already installed${NC}"
else
    echo -e "  Installing NuGet..."

    # Try apt first
    apt-get install -y nuget 2>/dev/null || {
        # Download nuget.exe manually
        mkdir -p /usr/local/bin
        curl -sSL https://dist.nuget.org/win-x86-commandline/latest/nuget.exe -o /usr/local/bin/nuget.exe

        # Create wrapper script
        cat > /usr/local/bin/nuget << 'EOF'
#!/bin/bash
mono /usr/local/bin/nuget.exe "$@"
EOF
        chmod +x /usr/local/bin/nuget
    }

    if command -v nuget &> /dev/null || [ -f /usr/local/bin/nuget.exe ]; then
        echo -e "${GREEN}  ✓ Installed${NC}"
    else
        echo -e "${BLUE}  ℹ Using dotnet nuget instead${NC}"
    fi
fi

# =====================================================
# [6/6] ENVIRONMENT SETUP
# =====================================================
echo -e "${YELLOW}[6/6] Environment configuration...${NC}"

# Create environment file
if [ ! -f /etc/profile.d/windows-dev.sh ]; then
    cat > /etc/profile.d/windows-dev.sh << 'EOF'
# Windows Development Environment

# .NET environment
export DOTNET_CLI_TELEMETRY_OPTOUT=1
export DOTNET_NOLOGO=1

# Wine prefix (per-user)
export WINEPREFIX=$HOME/.wine

# Aliases for common tasks
alias dotnet-new-console='dotnet new console'
alias dotnet-new-webapi='dotnet new webapi'
alias dotnet-new-mvc='dotnet new mvc'
alias dotnet-new-blazor='dotnet new blazor'

# Function to create and run a quick .NET console app
dotnet-quick() {
    local name=${1:-MyApp}
    mkdir -p "$name" && cd "$name"
    dotnet new console
    dotnet run
}
EOF
    echo -e "${GREEN}  ✓ Environment configured${NC}"
else
    echo -e "${BLUE}  ✓ Environment already configured${NC}"
fi

# =====================================================
# DONE
# =====================================================
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Windows Development Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Installed Tools:"
echo -e "  .NET SDK: $(dotnet --version 2>/dev/null || echo 'not installed')"
echo -e "  PowerShell: $(pwsh --version 2>/dev/null || echo 'not installed')"
echo -e "  Wine: $(wine --version 2>/dev/null || echo 'not installed')"
echo -e "  Mono: $(mono --version 2>/dev/null | head -1 | cut -d' ' -f5 || echo 'not installed')"
echo ""
echo -e "Quick Start:"
echo -e "  # Create console app"
echo -e "  dotnet new console -n MyApp && cd MyApp && dotnet run"
echo ""
echo -e "  # Create web API"
echo -e "  dotnet new webapi -n MyApi && cd MyApi && dotnet run"
echo ""
echo -e "  # Create Blazor app"
echo -e "  dotnet new blazor -n MyBlazor && cd MyBlazor && dotnet run"
echo ""
echo -e "  # Run PowerShell"
echo -e "  pwsh"
echo ""
echo -e "  # Run Windows exe (if Wine installed)"
echo -e "  wine myprogram.exe"
echo ""
echo -e "Environment:"
echo -e "  source /etc/profile.d/windows-dev.sh"
echo ""
