@echo off
setlocal
cd /d "%~dp0"
title MCS4 Monitor - Environment Check

echo ==========================================
echo      MCS4 Monitor Environment Check
echo ==========================================
echo.

echo Project folder:
echo %CD%
echo.

echo Python on PATH:
python --version 2>nul
where python 2>nul
echo.

if exist ".venv\Scripts\python.exe" (
    echo Virtual environment found.
    call ".venv\Scripts\activate.bat"
    echo.
    echo VENV Python:
    python --version
    where python
    echo.
    echo Installed package check:
    python -c "import PySide6, pyqtgraph, serial, openpyxl; print('OK: required packages import successfully')"
) else (
    echo Virtual environment NOT found.
)

echo.
pause
