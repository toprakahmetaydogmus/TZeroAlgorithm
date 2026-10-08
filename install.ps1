# ==============================================================================
# SİBER AKADEMİ — T-Zero Context Architect 1-Click Installer (Windows PowerShell)
# Developer: Toprak Ahmet Aydoğmuş
# Usage:
#   irm https://raw.githubusercontent.com/toprakahmetaydogmus/TZeroAlgorithm/main/install.ps1 | iex
# ==============================================================================

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "   ⚡ SİBER AKADEMİ — T-ZERO CONTEXT ARCHITECT & MCP INSTALLER   " -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check Python
$pyCmd = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $pyCmd = "py"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pyCmd = "python"
}

if (-not $pyCmd) {
    Write-Host "[ERROR] Python 3.9+ is not installed or not in PATH." -ForegroundColor Red
    Write-Host "Please install Python from https://python.org and rerun this script." -ForegroundColor Yellow
    exit 1
}

$pyVersion = & $pyCmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "[✓] Found Python $pyVersion ($pyCmd)" -ForegroundColor Green

# 2. Install tzero-mcp via pip
Write-Host "[*] Installing/upgrading tzero-mcp package from PyPI..." -ForegroundColor Cyan
& $pyCmd -m pip install --upgrade pip tzero-mcp --disable-pip-version-check
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] pip install failed." -ForegroundColor Red
    exit 1
}
Write-Host "[✓] tzero-mcp package successfully installed." -ForegroundColor Green

# 3. Verify environment & auto-configure PATH
Write-Host "[*] Verifying environment & system PATH..." -ForegroundColor Cyan
& $pyCmd -m tzero_deps

# 4. Integrate with IDEs
Write-Host ""
Write-Host "[*] Configuring MCP servers for Cursor, Claude Desktop, Antigravity, VS Code, Cline..." -ForegroundColor Cyan
if (Get-Command tzero-add-mcp -ErrorAction SilentlyContinue) {
    & tzero-add-mcp --all
} else {
    & $pyCmd -m addmcp --all
}

Write-Host ""
Write-Host "==================================================================" -ForegroundColor Green
Write-Host "   🎉 T-ZERO BAŞARIYLA KURULDU VE TÜM IDE'LERE ENTEGRE EDİLDİ!   " -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Kullanabileceğiniz Komutlar:" -ForegroundColor Yellow
Write-Host "  1. Masaüstü Arayüzü:     tzero-gui" -ForegroundColor White
Write-Host "  2. Terminal Sihirbazı:   tzero --cli" -ForegroundColor White
Write-Host "  3. Kod Taraması:         tzero --scan ." -ForegroundColor White
Write-Host "  4. MCP Sunucusu:         tzero-mcp" -ForegroundColor White
Write-Host ""
