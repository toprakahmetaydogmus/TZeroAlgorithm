@echo off
chcp 65001 > nul
title T-ZERO JARVIS SEMANTIC BENCHMARK SUITE (v4.2.0)
color 0a
echo ===============================================================================
echo    T-ZERO JARVIS 3-LAYER SEMANTIC MEMORY & COMPRESSION BENCHMARK
echo    Developer: Siber Akademi / Toprak Ahmet Aydogmus (v4.2.0)
echo ===============================================================================
echo.
cd /d "%~dp0"
python benchmark_semantic_jarvis.py
echo.
pause
