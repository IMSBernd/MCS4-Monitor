# MCS-4 Monitor – Version 1.5

Version 1.5 ergänzt den Windows-Build für eine eigenständige EXE-Datei.

## Start aus Python

```cmd
python main.py
```

## EXE erstellen

Im Projektordner ausführen:

```cmd
build_windows.bat
```

Nach erfolgreichem Build liegt die Anwendung hier:

```text
dist\MCS4_Monitor.exe
```

## Enthaltene Funktionen

- Dashboard
- Trenddiagramm
- Telegrammmonitor
- Decoder
- Telegramm-Explorer
- Alarmanzeige
- Sensor-Konfiguration
- Recorder und Player
- Export nach CSV, Excel, PDF und PNG
- Excel-Gesamtexport mit mehreren Reitern
- COM-Port-Erkennung für USB-RS422-Adapter

## Hinweise

- Für den Build wird PyInstaller verwendet.
- Die EXE ist für Windows 10/11 64 Bit vorgesehen.
- Die Ordner `exports` und `recordings` werden bei Bedarf automatisch erstellt.
