#!/usr/bin/env bash
# ==============================================================================
# ⚡ T-ZERO CONTEXT ARCHITECT & MCP SERVER — ZERO-CONFIG ONE-LINE INSTALLER
# Supported: Linux, macOS, WSL
# Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
# ==============================================================================

set -e

CYAN='\033[0;36m'
PURPLE='\033[0;35m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
cat << "EOF"
  _____ _____ _____ ____   ___  
 |_   _|__  /| ____|  _ \ / _ \ 
   | |   / / |  _| | |_) | | | |
   | |  / /_ | |___|  _ <| |_| |
   |_| /____|_____|_| \_\\___/ 
      SOVEREIGN MASTER v10.7.0 EDITION
EOF
echo -e "${NC}"

echo -e "${PURPLE}[1/4] Checking Python environment...${NC}"
if command -v python3 &>/dev/null; then
    PY_CMD="python3"
elif command -v python &>/dev/null; then
    PY_CMD="python"
else
    echo -e "${YELLOW}[!] Python 3.10+ required. Please install Python first.${NC}"
    exit 1
fi

PY_VER=$($PY_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo -e "${GREEN}✓ Found Python $PY_VER${NC}"

echo -e "${PURPLE}[2/4] Installing T-Zero MCP Engine via pip...${NC}"
$PY_CMD -m pip install --upgrade tzero-mcp

echo -e "${PURPLE}[3/4] Linking MCP Server into detected IDEs (Cursor, Claude, Antigravity)...${NC}"
$PY_CMD -m tzero_mcp --install || true

echo -e "${GREEN}"
echo "================================================================================"
echo "⚡ T-ZERO v10.7.0 INSTALLED SUCCESSFULLY!"
echo "================================================================================"
echo -e "${NC}"
echo "Key Capabilities:"
echo "  - 1-Click Auto-Vault  : tzero --vault --migrate"
echo "  - Pre-Flight Guard    : tzero --guard <file_or_code>"
echo "  - Change Blast Radius : tzero --impact <symbol>"
echo "  - Autonomous Doctor   : tzero pc-fixer"
echo "  - Zero-GPU Web Studio : tzero space"
echo "  - Start MCP Server    : uvx tzero-mcp (or tzero --mcp)"
echo ""
echo -e "${YELLOW}┌──────────────────────────────────────────────────────────────────────────────┐${NC}"
echo -e "${YELLOW}│  ⭐ A MESSAGE FROM THE CREATOR                                               │${NC}"
echo -e "${YELLOW}│                                                                              │${NC}"
echo -e "${YELLOW}│  Hi! I'm Toprak Ahmet Aydogmus, a 15-year-old self-taught developer from     │${NC}"
echo -e "${YELLOW}│  Siber Akademi. I built T-Zero from scratch to eliminate token bloat and     │${NC}"
echo -e "${YELLOW}│  AI hallucinations for programmers worldwide (\$0.00 cloud cost).             │${NC}"
echo -e "${YELLOW}│                                                                              │${NC}"
echo -e "${YELLOW}│  If this open-source tool saved you tokens or helped your coding flow:       │${NC}"
echo -e "${YELLOW}│  👉 Please consider giving it a ⭐ on GitHub:                                │${NC}"
echo -e "${CYAN}│     https://github.com/toprakahmetaydogmus/TZeroAlgorithm                    │${NC}"
echo -e "${YELLOW}│                                                                              │${NC}"
echo -e "${YELLOW}│  Every star means the world and helps a young open-source developer grow! 🚀 │${NC}"
echo -e "${YELLOW}└──────────────────────────────────────────────────────────────────────────────┘${NC}"
echo ""
