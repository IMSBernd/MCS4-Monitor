@echo off
title MCS4 Phase A Regression Tests
cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"

python tests\regression_phase_a.py %*

pause
