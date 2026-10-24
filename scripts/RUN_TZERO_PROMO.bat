@echo off
title T-Zero 35s Viral Promo Video Generator
echo ===================================================
echo   T-ZERO ENTERPRISE VIRAL PROMO GENERATOR (35s)
echo   Remotion 1080p + Edge-TTS AI Voiceover + FFmpeg
echo ===================================================
cd /d "%~dp0tzero-showcase"
python generate_promo.py
pause
