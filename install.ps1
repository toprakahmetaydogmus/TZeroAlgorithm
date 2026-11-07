# ==============================================================================
# ⚡ T-ZERO CONTEXT ARCHITECT & MCP SERVER — ZERO-CONFIG POWERSHELL INSTALLER
# Supported: Windows 10, Windows 11, Windows Server (PowerShell 5.1+ / PS Core)
# Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
# ==============================================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "  _____ _____ _____ ____   ___  " -ForegroundColor Cyan
Write-Host " |_   _|__  /| ____|  _ \ / _ \ " -ForegroundColor Cyan
Write-Host "   | |   / / |  _| | |_) | | | |" -ForegroundColor Cyan
Write-Host "   | |  / /_ | |___|  _ <| |_| |" -ForegroundColor Cyan
Write-Host "   |_| /____|_____|_| \_\\___/ " -ForegroundColor Cyan
Write-Host "      SOVEREIGN MASTER v10.7.0 EDITION" -ForegroundColor Yellow
Write-Host ""

Write-Host "[1/4] Checking Python environment..." -ForegroundColor Magenta
$pyCmd = $null
if (Get-Command "python" -ErrorAction SilentlyContinue) {
    $pyCmd = "python"
} elseif (Get-Command "py" -ErrorAction SilentlyContinue) {
    $pyCmd = "py"
} else {
    Write-Host "[!] Python 3.10+ required. Please install Python from https://python.org or winget install Python.Python.3.12" -ForegroundColor Red
    exit 1
}

$pyVer = & $pyCmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "✓ Found Python $pyVer" -ForegroundColor Green

Write-Host "[2/4] Installing / Upgrading T-Zero MCP Engine via pip..." -ForegroundColor Magenta
& $pyCmd -m pip install --upgrade tzero-mcp

Write-Host "[3/4] Linking MCP Server into detected IDEs (Cursor, Claude Desktop, Antigravity, VS Code)..." -ForegroundColor Magenta
try {
    & $pyCmd -m tzero_mcp --install
} catch {
    Write-Host "[!] Auto-linking encountered a non-fatal warning." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Green
Write-Host "⚡ T-ZERO v10.7.0 INSTALLED SUCCESSFULLY ON WINDOWS!" -ForegroundColor Green
Write-Host "================================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Key Capabilities:" -ForegroundColor White
Write-Host "  - 1-Click Auto-Vault  : tzero --vault --migrate" -ForegroundColor Cyan
Write-Host "  - Pre-Flight Guard    : tzero --guard <file_or_code>" -ForegroundColor Cyan
Write-Host "  - Change Blast Radius : tzero --impact <symbol>" -ForegroundColor Cyan
Write-Host "  - Autonomous Doctor   : tzero pc-fixer" -ForegroundColor Cyan
Write-Host "  - Zero-GPU Web Studio : tzero space" -ForegroundColor Cyan
Write-Host "  - Start MCP Server    : uvx tzero-mcp (or tzero --mcp)" -ForegroundColor Cyan
Write-Host ""
Write-Host "┌──────────────────────────────────────────────────────────────────────────────┐" -ForegroundColor Yellow
Write-Host "│  ⭐ A MESSAGE FROM THE CREATOR                                               │" -ForegroundColor Yellow
Write-Host "│                                                                              │" -ForegroundColor Yellow
Write-Host "│  Hi! I'm Toprak Ahmet Aydogmus, a 15-year-old self-taught developer from     │" -ForegroundColor Yellow
Write-Host "│  Siber Akademi. I built T-Zero from scratch to eliminate token bloat and     │" -ForegroundColor Yellow
Write-Host "│  AI hallucinations for programmers worldwide ($0.00 cloud cost).             │" -ForegroundColor Yellow
Write-Host "│                                                                              │" -ForegroundColor Yellow
Write-Host "│  If this open-source tool saved you tokens or helped your coding flow:       │" -ForegroundColor Yellow
Write-Host "│  👉 Please consider giving it a ⭐ on GitHub:                                │" -ForegroundColor Yellow
Write-Host "│     https://github.com/toprakahmetaydogmus/TZeroAlgorithm                    │" -ForegroundColor Cyan
Write-Host "│                                                                              │" -ForegroundColor Yellow
Write-Host "│  Every star means the world and helps a young open-source developer grow! 🚀 │" -ForegroundColor Yellow
Write-Host "└──────────────────────────────────────────────────────────────────────────────┘" -ForegroundColor Yellow
Write-Host ""
