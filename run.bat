@echo off
setlocal
title SIBER AKADEMI - T-Zero V3 Launcher
color 0B

echo.
echo ============================================================
echo   SIBER AKADEMI T-ZERO CONTEXT ARCHITECT V3
echo   Developer: Toprak Ahmet Aydogmus
echo   LinkedIn: Toprak Ahmet Aydogmus  https://hopp.bio/siberegitim
echo ============================================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% equ 0 goto check_deps

py --version >nul 2>&1
if %errorlevel% equ 0 goto check_deps

echo [ERROR] Python not found!
echo [INFO] Please run install_requirements.bat first.
pause
exit /b 1

:check_deps
echo [INFO] Verifying dependencies...
python -c "import requests, keyring, darkdetect, pygments" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing missing packages...
    python -m pip install -r requirements.txt >nul 2>&1
)

echo [OK] Starting application...
echo.
start "" pythonw tzero_v3.py
if %errorlevel% neq 0 (
    python tzero_v3.py
)
endlocal
exit /b 0
