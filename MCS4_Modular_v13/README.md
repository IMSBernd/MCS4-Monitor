# MCS4 Modular v1.3

Neue Funktionen in Version 1.3:

- Export-Tab
- CSV-Export der aktuellen Sensordaten nach `exports/`
- Excel-Export der aktuellen Sensordaten nach `exports/`
- Export-Schaltflächen in der Kopfzeile
- Diagnose zeigt den Exportordner an

Test:

1. `python main.py`
2. Simulator starten
3. Warten, bis Werte angezeigt werden
4. `Export CSV` oder `Export Excel` klicken
5. Ordner `exports` prüfen

Hinweis: Für Excel wird `openpyxl` benötigt. Falls es fehlt:

```cmd
pip install openpyxl
```
