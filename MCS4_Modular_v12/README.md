# MCS-4 Monitor Version 1.2

Neu in Version 1.2:

- Sensor-Konfiguration über Tab `Sensor-Konfiguration`
- Speicherung in `sensor_config.json`
- Namen, Unit-Code und Warn-/Alarmgrenzen ohne Codeänderung editierbar
- Simulator verwendet die konfigurierten Unit-Codes
- Dashboard, Trend, Recorder, Player und Telegramm-Explorer bleiben erhalten

Start:

```cmd
python main.py
```

Test:

1. Simulator starten
2. Tab `Sensor-Konfiguration` öffnen
3. Grenzwerte oder Namen ändern
4. `Sensor-Konfiguration speichern` drücken
5. Simulator neu starten
