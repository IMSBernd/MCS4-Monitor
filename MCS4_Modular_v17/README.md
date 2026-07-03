# MCS4 Monitor Version 1.6

Protocol Analyzer Update:

- variable Telegrammlaenge je nach WordType
- Byte 6 wird als PAGE/LINE nach MCS-4 Appendix 12 ausgewertet
- 12-Bit-Wert korrekt aus Byte 7/8 dekodiert
- Sensorfehlerbit und Vorzeichenbit korrigiert
- formale Telegrammvalidierung
- falsche/unplausible Telegramme werden nicht mehr als Messwerte ins Dashboard übernommen
- Telegramm-Explorer zeigt Page, Line, Skalierung, Rohwert und Fehlergrund

Wichtig: Die Zuordnung Messpunkt -> Sensorname ist projektspezifisch und muss mit echten MCS-4-Daten gepflegt werden.
