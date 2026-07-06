@echo off
title Create Local Demo License
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python license_system.py create --customer "Local Development" --days 30 --machine current --type Demo --version 2.4 --output license.mcs
pause
