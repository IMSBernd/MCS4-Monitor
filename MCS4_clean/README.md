# MCS4 Monitor Clean Base 0.6

Stabile saubere Basis für den MCS-4 RS422 Monitor.

Start:

```cmd
.venv\Scripts\activate.bat
pip install -r requirements.txt
python main.py
```

Funktionen:
- PySide6 GUI
- Simulator ohne Hintergrund-Threads
- COM-Port-Erkennung
- Telegrammmonitor
- einfacher 8-Byte Paketparser mit Sync 0xFF
