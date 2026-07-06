@echo off
setlocal
cd /d "%~dp0"
title MCS4 Monitor - Install Requirements

echo ==========================================
echo      Install / Update Requirements
echo ==========================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment .venv not found. Creating it now...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Could not create virtual environment.
        pause
        exit /b 1
    )
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo Requirements installed.
pause
