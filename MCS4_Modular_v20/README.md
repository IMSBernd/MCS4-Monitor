# MCS4 Modular v20 / Version 1.9

Neu in Version 1.9:

- Neuer Reiter **MCS-4 Analyzer**
- Anzeige aller erkannten Messwerte nach eindeutigem Schlüssel: Messpunkt + Page + Line
- Analyzer zeigt MP, Page, Line, Name, Einheit, Wert, Rohwert, Min, Max, Zähler, letztes Telegramm und Status
- **Lernmodus**: erkannte Messpunkte können direkt benannt und dauerhaft in `sensor_config.json` gespeichert werden
- Excel-Export enthält zusätzlich den Reiter **MCS-4 Analyzer**

Testablauf:

1. `python main.py`
2. Simulator starten oder Player/RS422 verwenden
3. Reiter **MCS-4 Analyzer** öffnen
4. Einen erkannten Key auswählen, Namen eingeben und speichern
5. Reiter **Sensor-Konfiguration** prüfen

Hinweis:

Die endgültige projektbezogene Zuordnung der Messpunkte ist anlagenabhängig. Der Lernmodus dient dazu, echte Messpunkte der jeweiligen MCS-4-Anlage dauerhaft zu benennen.
