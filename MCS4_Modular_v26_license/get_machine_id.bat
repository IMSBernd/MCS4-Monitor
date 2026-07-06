@echo off
title MCS4 Machine ID
cd /d "%~dp0"
if exist ".venv\Scripts\activate.bat" call .venv\Scripts\activate.bat
python license_system.py machine-id
echo.
echo Send this Machine ID to the license issuer.
pause
