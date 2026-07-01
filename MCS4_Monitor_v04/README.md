# MCS4 Monitor

Professionelle MCS-4 RS422 Monitoring- und Diagnosesoftware.

## Version 0.4

Diese Version ergänzt die Kommunikationsgrundlage:

- Simulatorbetrieb ohne Hardware
- RS422-Betrieb über Windows-COM-Port
- COM-Port-Erkennung
- COM-Port-Details
- HEX-Telegrammmonitor
- Telegramm-Aufzeichnung
- Dashboard mit Live-Sensorwerten
- Trenddiagramm
- Diagnoseanzeige

## Start

```cmd
.venv\Scripts\activate.bat
python main.py
```

## Exsys USB-RS422 Adapter

Der Adapter muss von Windows als COM-Port erkannt werden. Prüfen:

```cmd
python -m serial.tools.list_ports -v
```

Wenn kein Port erscheint, ist der Adapter nicht eingesteckt oder der Treiber fehlt.

## Nächste Version

Version 0.5 wird den MCS-4-Paketreader und Parser weiter ausbauen: Sync `0xFF`, WordType-Grundlage, CRC-Platzhalter und erste Rohtelegramm-Auswertung.
