@echo off
setlocal enabledelayedexpansion
title SIBER AKADEMI - T-Zero V3 Auto Setup
color 0A

echo.
echo ============================================================
echo   SIBER AKADEMI - T-ZERO CONTEXT ARCHITECT V3
echo   Developer: Toprak Ahmet Aydogmus
echo   LinkedIn: Toprak Ahmet Aydogmus  https://hopp.bio/siberegitim
echo   AUTOMATIC SETUP PIPELINE
echo ============================================================
echo.

:: -------------------------------------------
:: STEP 1: Check Python
:: -------------------------------------------
echo [STEP 1/4] Checking Python installation...

python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python found in PATH.
    goto install_pip
)

py --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python Launcher found.
    goto install_pip
)

echo [WARNING] Python not found! Starting auto-install...
echo.

:: -------------------------------------------
:: STEP 1b: Auto-Install Python
:: -------------------------------------------

:: Method 1: winget
echo [INFO] Method 1: Installing Python 3.12 via winget...
winget --version >nul 2>&1
if %errorlevel% neq 0 goto try_download
winget install -e --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
if %errorlevel% equ 0 (
    echo [SUCCESS] Python 3.12 installed via winget.
    goto refresh_path
)

:try_download
:: Method 2: PowerShell download
echo [INFO] Method 2: Downloading Python 3.12 via PowerShell...
powershell -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe' -OutFile '%TEMP%\python_installer.exe' -UseBasicParsing"

if not exist "%TEMP%\python_installer.exe" (
    echo [ERROR] Failed to download Python installer.
    echo [INFO] Manual install: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [INFO] Installing Python 3.12 silently...
start /wait "" "%TEMP%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_pip=1 Include_launcher=1
del "%TEMP%\python_installer.exe" >nul 2>&1
echo [SUCCESS] Python 3.12 installed.

:refresh_path
echo [INFO] Updating PATH environment...
set "PATH=%PATH%;%USERPROFILE%\AppData\Local\Programs\Python\Python312;%USERPROFILE%\AppData\Local\Programs\Python\Python312\Scripts;C:\Python312;C:\Python312\Scripts;%LOCALAPPDATA%\Programs\Python\Python312;%LOCALAPPDATA%\Programs\Python\Python312\Scripts"

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Python not found in PATH after install.
    echo [INFO] Please restart your computer and try again.
    echo [INFO] Or install manually: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python is active and ready.
echo.

:: -------------------------------------------
:: STEP 2: Update pip
:: -------------------------------------------
:install_pip
echo [STEP 2/4] Updating pip package manager...
python -m ensurepip --upgrade >nul 2>&1
python -m pip install --upgrade pip >nul 2>&1
echo [OK] pip is up to date.
echo.

:: -------------------------------------------
:: STEP 3: Install Dependencies
:: -------------------------------------------
echo [STEP 3/4] Installing required Python packages...
echo.

python -m pip install "requests>=2.28.0"
python -m pip install "keyring>=23.13.1"
python -m pip install "darkdetect>=0.8.0"
python -m pip install "pygments>=2.14.0"
python -m pip install "Pillow>=9.0.0"
python -m pip install "pyinstaller>=6.0.0"

echo.
echo [OK] All dependencies installed successfully.
echo.

:: -------------------------------------------
:: STEP 4: Launch Application
:: -------------------------------------------
echo [STEP 4/4] Launching T-Zero Context Architect V3...
echo.
echo ============================================================
echo   SETUP COMPLETE! Application is starting...
echo ============================================================
echo.

start "" pythonw tzero_v3.py
if %errorlevel% neq 0 (
    python tzero_v3.py
)
endlocal
exit /b 0
