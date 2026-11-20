@echo off
title T-Zero 35s Viral Promo Video Generator
echo ===================================================
echo   T-ZERO ENTERPRISE VIRAL PROMO GENERATOR (35s)
echo   Remotion 1080p + Edge-TTS AI Voiceover + FFmpeg
echo ===================================================
if exist "%~dp0..\tzero-showcase" (
    cd /d "%~dp0..\tzero-showcase"
) else if exist "%~dp0tzero-showcase" (
    cd /d "%~dp0tzero-showcase"
) else if exist "tzero-showcase" (
    cd /d "tzero-showcase"
) else (
    echo [ERROR] Could not find tzero-showcase directory.
    pause
    exit /b 1
)
python generate_promo.py
pause
