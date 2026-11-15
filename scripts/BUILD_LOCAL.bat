@echo off
chcp 65001 > nul
echo ======================================================================
echo ⚡ SIBER AKADEMI — T-ZERO LOCAL COMPILATION & PACKAGING PIPELINE
echo ======================================================================
echo Building all packages locally on this Windows PC...
echo.

python scripts\build_local_release.py %*

echo.
echo ======================================================================
echo Build pipeline finished. Check the dist\ folder.
echo ======================================================================
pause
