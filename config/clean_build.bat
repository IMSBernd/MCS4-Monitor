@echo off
cd /d "%~dp0"
title MCS4 Monitor - Clean Build

rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
rmdir /s /q __pycache__ 2>nul
del /q MCS4_Monitor.spec 2>nul

echo Build folders cleaned.
pause
