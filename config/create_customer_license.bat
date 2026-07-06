@echo off
setlocal
cd /d "%~dp0"
title Create Customer License

if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"

set /p CUSTOMER=Customer name: 
set /p MACHINE=Customer Machine ID: 
set /p DAYS=License days [30]: 
if "%DAYS%"=="" set DAYS=30

python license_system.py create --customer "%CUSTOMER%" --days %DAYS% --machine "%MACHINE%" --type Demo --version 2.4 --output license.mcs

echo.
echo Created license.mcs for %CUSTOMER%.
echo Send this file together with the customer build.
pause
