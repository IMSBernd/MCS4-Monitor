# MCS4 Modular Version 1.1

Diese Version erweitert den Telegramm-Explorer und den Decoder:

- MCS-4 Basisdecoder mit Word-Type-Anzeige
- erweiterte Einheitentabelle
- Sensorfehlerbit-Auswertung in Byte 7 / Bit 6
- Telegramm-Explorer zeigt Sensorfehler, Rohwert, Skalierung und Word Type
- bestehende Funktionen bleiben erhalten: Simulator, RS422, Recorder, Player, Trend, Alarm

Start:

```cmd
python main.py
```

Test:
1. Simulator starten
2. Telegramm-Explorer öffnen
3. Word Type, Rohwert, Einheit, Sensorfehler und skalierten Wert prüfen
