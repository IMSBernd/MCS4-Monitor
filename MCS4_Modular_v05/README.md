# MCS-4 Monitor Version 0.5

Stabile modulare Version mit:

- Simulator
- RS422 COM-Port-Öffnung
- TelegramBuffer mit Sync `0xFF`
- 8-Byte-Telegrammerkennung
- vorläufigem Decoder für simulierte MCS-4-Telegramme
- Dashboard
- Telegrammmonitor
- Decoder-Tab
- Diagnose-Tab
- Telegramm-Aufzeichnung in `recordings/*.mcslog`

Start:

```cmd
python main.py
```

Erst im Simulator testen. Danach RS422 mit Exsys-Adapter testen.
