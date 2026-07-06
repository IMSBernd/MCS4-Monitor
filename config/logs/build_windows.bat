@echo off
setlocal

echo ============================================
echo MCS-4 Monitor - Windows EXE Build
echo ============================================

REM Ensure we are in the script directory
cd /d "%~dp0"

REM Create required runtime folders if they do not exist
if not exist exports mkdir exports
if not exist recordings mkdir recordings

REM Install/upgrade required packages inside the active Python environment
echo.
echo Installing requirements...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Requirements installation failed.
    pause
    exit /b 1
)

echo.
echo Building EXE with PyInstaller...
pyinstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --windowed ^
  --name MCS4_Monitor ^
  --hidden-import PySide6.QtPrintSupport ^
  --hidden-import openpyxl ^
  --hidden-import serial.tools.list_ports ^
  main.py

if errorlevel 1 (
    echo.
    echo ERROR: EXE build failed.
    pause
    exit /b 1
)

echo.
echo ============================================
echo Build completed successfully.
echo EXE location:
echo %CD%\dist\MCS4_Monitor.exe
echo ============================================
pause
