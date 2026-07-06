@echo off
setlocal
cd /d "%~dp0"
title MCS4 Monitor - Development Start

echo ==========================================
echo      MCS4 Monitor - Development Start
echo ==========================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment .venv was not found.
    echo.
    echo Please create it first:
    echo   python -m venv .venv
    echo   .venv\Scripts\activate.bat
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"

echo Python environment:
where python
python --version

echo.
echo Starting MCS4 Monitor...
echo.
python main.py

echo.
echo Program finished.
pause
