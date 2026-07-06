@echo off
setlocal
cd /d "%~dp0"
title MCS4 Monitor - Git Update

echo ==========================================
echo      Update Project from GitHub
echo ==========================================
echo.

git pull

if exist ".venv\Scripts\python.exe" (
    call ".venv\Scripts\activate.bat"
    python -m pip install -r requirements.txt
)

echo.
echo Update finished.
pause
