@echo off
setlocal
cd /d "%~dp0"
title T-ZERO JARVIS - 5-AGENT AUTONOMOUS SWARM ORCHESTRATOR

echo ================================================================================
echo    [SWARM] T-ZERO JARVIS 5-AGENT AUTONOMOUS SWARM ORCHESTRATOR (v4.4.0)
echo    Developer: Toprak Ahmet Aydogmus (Siber Akademi)
echo    Zero-Cost / Zero-Leak Guarantee: 0.00$
echo ================================================================================
echo.
echo [1/3] Guvenlik ve Donanim Uzman Surusu Hazirlaniyor...
echo [2/3] Ajanlar: SecuritySentinel, EmbeddedHardware, ASTOptimizer, DevOps, JARVIS Prime
echo [3/3] Gorev Kosuluyor: ESP32 + nRF24L01 + SPI Guvenli Haberlesme Dogrulamasi...
echo.

python run_swarm.py %*

echo.
echo ================================================================================
echo    [OK] SWARM GOREVI BASARIYLA TAMAMLANDI!
echo ================================================================================
pause
