from __future__ import annotations
import threading
import time
from datetime import datetime
from typing import Callable

try:
    import serial
except Exception:
    serial = None

from model.telegram import Telegram


class SerialDriver:
    """Einfacher serieller RX-Treiber. GUI-Updates erfolgen über Callbacks/Qt-Signale."""

    def __init__(self, port: str, baudrate: int = 38400, parity: str = "O"):
        self.port = port
        self.baudrate = baudrate
        self.parity = parity
        self._ser = None
        self._running = False
        self._thread: threading.Thread | None = None
        self.on_bytes: Callable[[Telegram], None] | None = None
        self.on_status: Callable[[str], None] | None = None
        self.on_diagnostics: Callable[[dict], None] | None = None
        self._byte_count = 0
        self._telegram_count = 0
        self._start = time.monotonic()

    def start(self) -> None:
        if serial is None:
            raise RuntimeError("pyserial ist nicht installiert. Bitte: pip install pyserial")
        if self._running:
            return
        self._ser = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_ODD if self.parity.upper() == "O" else serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.05,
        )
        self._running = True
        self._start = time.monotonic()
        if self.on_status:
            self.on_status(f"Verbunden: {self.port}")
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        if self._ser:
            try:
                self._ser.close()
            except Exception:
                pass
        if self.on_status:
            self.on_status("Getrennt")

    def _loop(self) -> None:
        buffer = bytearray()
        while self._running:
            try:
                data = self._ser.read(64) if self._ser else b""
                if data:
                    self._byte_count += len(data)
                    buffer.extend(data)
                    # Rohdaten ebenfalls anzeigen
                    if self.on_bytes:
                        self.on_bytes(Telegram(raw=bytes(data), timestamp=datetime.now(), source=self.port))
                    # Diagnose grob aktualisieren
                    elapsed = max(0.001, time.monotonic() - self._start)
                    if self.on_diagnostics:
                        self.on_diagnostics({
                            "Quelle": self.port,
                            "Telegramme/s": f"{self._telegram_count / elapsed:.1f}",
                            "Telegramme": str(self._telegram_count),
                            "Bytes": str(self._byte_count),
                            "CRC-Fehler": "0",
                            "Timeouts": "0",
                        })
                else:
                    time.sleep(0.01)
            except Exception as exc:
                if self.on_status:
                    self.on_status(f"Serieller Fehler: {exc}")
                time.sleep(0.5)
