# MCS-4 Professional Monitor - Version 1.8

Änderungen:

- Sensoren werden nun eindeutig über **Messpunkt + Page + Line** verwaltet.
- Das Dashboard zeigt mehrere Werte mit gleicher Messpunktnummer separat an.
- Der Sensor-Konfigurator enthält eine neue Spalte **Key** im Format `Messpunkt:Page:Line`.
- Neue erkannte Sensoren werden automatisch mit eindeutigem Key in `sensor_config.json` angelegt.
- Dashboard zeigt jetzt Key, Messpunkt, Page und Line.
- Export und Trenddaten nutzen ebenfalls den eindeutigen Sensor-Key.

Hintergrund:

Nach MCS-4-Dokumentation ist Byte 5 die Measuring-Point-Nummer und Byte 6 besteht aus Page/Line. Einige Anlagen senden mehrere Werte mit gleicher Messpunktnummer aber unterschiedlicher Page/Line-Kombination. Frühere Versionen haben solche Werte überschrieben.

Start:

```cmd
python main.py
```

Test:

1. Simulator starten.
2. Dashboard prüfen: Es müssen wieder fünf Sensorzeilen erscheinen.
3. Tab Sensor-Konfiguration prüfen: Einträge mit Key, Messpunkt, Page und Line.
