from __future__ import annotations

from datetime import datetime
from pathlib import Path


class TelegramRecorder:
    """Schreibt empfangene Rohdaten in eine Textdatei.

    Format je Zeile:
    ISO-Zeitstempel;Richtung;HEX-Daten
    Beispiel:
    2026-07-01T17:40:00.123456;RX;FF 00 01 02 01 01 03 4A
    """

    def __init__(self) -> None:
        self.path: Path | None = None
        self._file = None
        self.enabled = False

    def start(self, path: str | Path) -> None:
        self.stop()
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.path.open("a", encoding="utf-8")
        self.enabled = True
        self.write_comment("Recorder gestartet")

    def stop(self) -> None:
        if self._file:
            self.write_comment("Recorder gestoppt")
            self._file.close()
        self._file = None
        self.enabled = False

    def record_rx(self, data: bytes) -> None:
        self._write("RX", data)

    def record_tx(self, data: bytes) -> None:
        self._write("TX", data)

    def write_comment(self, text: str) -> None:
        if not self._file:
            return
        timestamp = datetime.now().isoformat(timespec="microseconds")
        self._file.write(f"{timestamp};INFO;{text}\n")
        self._file.flush()

    def _write(self, direction: str, data: bytes) -> None:
        if not self.enabled or not self._file:
            return
        timestamp = datetime.now().isoformat(timespec="microseconds")
        hex_data = data.hex(" ").upper()
        self._file.write(f"{timestamp};{direction};{hex_data}\n")
        self._file.flush()
