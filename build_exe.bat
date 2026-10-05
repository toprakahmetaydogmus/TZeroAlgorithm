@echo off
setlocal
title SIBER AKADEMI - T-Zero V3 EXE Builder
color 0E

echo.
echo ============================================================
echo   SIBER AKADEMI T-ZERO V3 EXE BUILDER
echo   Developer: Toprak Ahmet Aydogmus
echo   LinkedIn: Toprak Ahmet Aydogmus  https://hopp.bio/siberegitim
echo ============================================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Run install_requirements.bat first.
    pause
    exit /b 1
)

:: Check and install PyInstaller
echo [INFO] Checking PyInstaller...
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing PyInstaller...
    python -m pip install pyinstaller
)

:: Install deps
echo [INFO] Checking dependencies...
python -m pip install requests keyring darkdetect pygments Pillow >nul 2>&1

:: Clean old builds
echo [INFO] Cleaning old build files...
if exist build rmdir /s /q build >nul 2>&1
if exist dist rmdir /s /q dist >nul 2>&1

:: Icon check
set "ICON_PATH=siber_akademi.ico"

:: Build EXE
echo.
echo ============================================================
echo   Starting PyInstaller EXE compilation...
echo ============================================================
echo.

if exist "%ICON_PATH%" (
    pyinstaller --onefile --noconsole --clean --name=TZeroAlgorithm --collect-submodules=keyring.backends --hidden-import=win32ctypes.core --icon="%ICON_PATH%" main.py
) else (
    pyinstaller --onefile --noconsole --clean --name=TZeroAlgorithm --collect-submodules=keyring.backends --hidden-import=win32ctypes.core main.py
)

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] EXE compilation failed!
    pause
    exit /b 1
)

echo.
if exist "dist\TZeroAlgorithm.exe" (
    echo ============================================================
    echo   SUCCESS! EXE file created:
    echo   dist\TZeroAlgorithm.exe
    echo ============================================================
    echo.
    echo Location: %cd%\dist\TZeroAlgorithm.exe
) else (
    echo [ERROR] EXE file not found!
)

echo.
pause
endlocal
exit /b 0
