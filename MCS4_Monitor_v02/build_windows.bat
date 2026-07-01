@echo off
setlocal
call .venv\Scripts\activate.bat
pyinstaller --noconfirm --onefile --windowed --name MCS4_Monitor main.py
pause
