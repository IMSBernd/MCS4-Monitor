@echo off
call .venv\Scripts\activate.bat
pyinstaller --noconfirm --onefile --windowed --name MCS4-Monitor main.py
pause
