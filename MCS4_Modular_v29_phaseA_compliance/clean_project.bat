@echo off
cd /d "%~dp0"
title MCS4 Monitor - Clean Project

echo This will remove temporary build/cache files only.
echo Recordings, exports, config and source files will NOT be deleted.
echo.
pause

rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
rmdir /s /q __pycache__ 2>nul
for /d /r %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d" 2>nul

echo.
echo Project cleaned.
pause
