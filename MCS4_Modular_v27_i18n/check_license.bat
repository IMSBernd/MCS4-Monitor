@echo off
title Check MCS4 License
cd /d "%~dp0"
if exist ".venv\Scripts\activate.bat" call .venv\Scripts\activate.bat
python license_system.py check
pause
