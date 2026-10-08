@echo off
setlocal
title SIBER AKADEMI - T-Zero Windows Executables Builder
color 0E

echo.
echo ============================================================
echo   SIBER AKADEMI T-ZERO 3.0.5 EXECUTABLE BUILDER
echo   Builds TZeroAlgorithm.exe, TZeroMCP.exe, and AddMCP.exe
echo ============================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Run install_requirements.bat first.
    pause
    exit /b 1
)

echo [INFO] Installing project build/runtime requirements...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Dependency installation failed.
    pause
    exit /b 1
)

echo.
echo [INFO] Building all Windows executables...
python compile.py
if %errorlevel% neq 0 (
    echo [ERROR] Executable build failed.
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Built executables:
echo   dist\TZeroAlgorithm.exe
echo   dist\TZeroMCP.exe
echo   dist\AddMCP.exe
echo.
pause
endlocal
exit /b 0