@echo off
if exist "%~dp0tzero.py" (
    python "%~dp0tzero.py" %*
) else (
    python -m tzero %*
)
