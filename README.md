# MCS-4 Monitor

Professionelle Windows-Software zur Visualisierung von MCS-4 Sensorwerten über RS422.

## Version 0.1

Enthält:
- PySide6 GUI
- COM-Port-Erkennung
- Simulator-Modus
- 8-Byte-Telegramm-Grundparser mit Sync 0xFF
- Sensorliste
- Alarmfenster
- Diagnoseanzeige

## Start

```cmd
.venv\Scripts\activate.bat
pip install -r requirements.txt
python main.py
```

## EXE bauen

```cmd
build_windows.bat
```
