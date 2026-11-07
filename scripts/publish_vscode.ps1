# T-Zero VS Code Extension Automated Publisher
# Siber Akademi - 100% Free & Zero-Leak Tooling

param(
    [string]$PatToken = $env:VSCE_PAT
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$ExtensionDir = Join-Path $RepoRoot "extensions\vscode"
$DistDir = Join-Path $RepoRoot "dist"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "⚡ T-ZERO VS CODE EXTENSION AUTOMATED PUBLISHER" -ForegroundColor Yellow
Write-Host "================================================================================" -ForegroundColor Cyan

# 1. Package fresh VSIX
Write-Host "[1/3] Packaging fresh VSIX..." -ForegroundColor Green
Set-Location $ExtensionDir
npx --yes @vscode/vsce package --no-dependencies

$vsixFiles = Get-ChildItem -Path $ExtensionDir -Filter "*.vsix"
if ($vsixFiles.Count -eq 0) {
    Write-Error "No VSIX file was produced!"
}
$latestVsix = $vsixFiles[0].FullName
Copy-Item -Path $latestVsix -Destination $DistDir -Force
Write-Host "  -> Produced: $latestVsix" -ForegroundColor Gray

# 2. Check for PAT
if (-not $PatToken) {
    Write-Host "`n[!] VSCE Personal Access Token (PAT) not found in `$env:VSCE_PAT." -ForegroundColor Yellow
    Write-Host "    To publish automatically from CLI:" -ForegroundColor Gray
    Write-Host "    1. Go to: https://marketplace.visualstudio.com/manage" -ForegroundColor Gray
    Write-Host "    2. Create a PAT with 'Marketplace (Acquisition and Manage)' scope." -ForegroundColor Gray
    Write-Host "    3. Run: `n       `$env:VSCE_PAT='your-token'`n       .\scripts\publish_vscode.ps1" -ForegroundColor Cyan
    Write-Host "`n[+] Copied VSIX path to clipboard for web upload:" -ForegroundColor Green
    Set-Clipboard -Value $latestVsix
    Write-Host "    $latestVsix" -ForegroundColor White
    exit 0
}

# 3. Publish via CLI
Write-Host "`n[2/3] Publishing to VS Code Marketplace via VSCE CLI..." -ForegroundColor Green
npx --yes @vscode/vsce publish --packagePath $latestVsix -p $PatToken

Write-Host "`n[3/3] Successfully published to VS Code Marketplace!" -ForegroundColor Green
