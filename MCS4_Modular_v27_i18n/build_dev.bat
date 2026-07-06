@echo off
setlocal
cd /d "%~dp0"
title MCS4 Monitor - Build EXE

echo ==========================================
echo      Build MCS4 Monitor EXE
echo ==========================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment .venv not found.
    echo Run install_requirements.bat first.
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"
python -m pip install -r requirements.txt

rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

pyinstaller --noconfirm --windowed --onedir --name MCS4_Monitor main.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed.
    pause
    exit /b 1
)

echo.
echo EXE created:
echo dist\MCS4_Monitor\MCS4_Monitor.exe
echo.
pause
