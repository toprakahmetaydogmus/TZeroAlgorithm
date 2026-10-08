#!/usr/bin/env bash
# ==============================================================================
# SİBER AKADEMİ — T-Zero Context Architect 1-Click Installer (Linux & macOS)
# Developer: Toprak Ahmet Aydoğmuş
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/toprakahmetaydogmus/TZeroAlgorithm/main/install.sh | bash
# ==============================================================================

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "\n${CYAN}==================================================================${NC}"
echo -e "${CYAN}   ⚡ SİBER AKADEMİ — T-ZERO CONTEXT ARCHITECT & MCP INSTALLER   ${NC}"
echo -e "${CYAN}==================================================================${NC}\n"

# 1. Check Python
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD="python"
else
    echo -e "${RED}[ERROR] Python 3.9+ is not installed.${NC}"
    echo -e "${YELLOW}Please install Python 3.9+ and try again.${NC}"
    exit 1
fi

PY_VER=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}[✓] Found Python ${PY_VER} (${PYTHON_CMD})${NC}"

# 2. Install tzero-mcp via pip
echo -e "${CYAN}[*] Installing/upgrading tzero-mcp from PyPI...${NC}"
$PYTHON_CMD -m pip install --upgrade pip tzero-mcp --disable-pip-version-check

# 3. Configure system PATH & verify dependencies
echo -e "${CYAN}[*] Verifying environment & PATH configuration...${NC}"
$PYTHON_CMD -m tzero_deps || true

# 4. Integrate into IDEs
echo -e "\n${CYAN}[*] Auto-configuring IDEs (Cursor, Claude, Antigravity, VS Code, Cline)...${NC}"
if command -v tzero-add-mcp >/dev/null 2>&1; then
    tzero-add-mcp --all || true
else
    $PYTHON_CMD -m addmcp --all || true
fi

echo -e "\n${GREEN}==================================================================${NC}"
echo -e "${GREEN}   🎉 T-ZERO SUCCESSFULLY INSTALLED & CONFIGURED!   ${NC}"
echo -e "${GREEN}==================================================================${NC}\n"
echo -e "${YELLOW}Quick Commands to get started:${NC}"
echo -e "  - Desktop GUI:       ${CYAN}tzero-gui${NC}  (or ${CYAN}tzero --gui${NC})"
echo -e "  - Terminal Wizard:   ${CYAN}tzero --cli${NC}"
echo -e "  - Codebase Scan:     ${CYAN}tzero --scan .${NC}"
echo -e "  - MCP Server:        ${CYAN}tzero-mcp${NC}\n"
