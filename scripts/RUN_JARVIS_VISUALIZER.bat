@echo off
setlocal
cd /d "%~dp0"
title T-ZERO JARVIS - CYBERPUNK 3D KNOWLEDGE & CAUSAL GRAPH HUD

echo ================================================================================
echo    [HUD] T-ZERO JARVIS CYBERPUNK KNOWLEDGE & CAUSAL GRAPH HUD (v4.4.0)
echo    Developer: Toprak Ahmet Aydogmus (Siber Akademi)
echo    Offline HTML5 / SVG / Canvas Force-Directed Engine
echo ================================================================================
echo.
echo [1/2] 4D Nedensellik ve Bilgi Cizgesi HTML Dosyasi Uretiliyor...
python export_hud.py

echo [2/2] Varsayilan Tarayicida Goruntuleniyor...
start tzero_graph_hud.html

echo.
echo ================================================================================
echo    [OK] INTERAKTIF HUD TARAYICINIZDA ACILDI!
echo ================================================================================
timeout /t 5 >nul
