@echo off
chcp 65001 > nul
title T-ZERO JARVIS AUTONOMOUS AGENT ORCHESTRATOR (v4.2.0)
color 0b
echo ===============================================================================
echo    T-ZERO JARVIS AUTONOMOUS SUPER-AGENT ORCHESTRATOR
echo    Developer: Siber Akademi / Toprak Ahmet Aydogmus (v4.2.0)
echo ===============================================================================
echo.
cd /d "%~dp0"
python -c "from tzero_jarvis.orchestrator import JarvisOrchestrator; orch = JarvisOrchestrator(); res = orch.execute_goal('ESP32 ve nRF24L01 haberlesme mimarisini analiz et ve guvenlik denetimi yap.'); print('\n[+] Gorev Basari:', res.success); print('[+] Sifir Maliyet:', res.cost); print('[+] Adimlar:'); [print('   -', s['stage'], ':', s['message']) for s in res.steps]"
echo.
pause
