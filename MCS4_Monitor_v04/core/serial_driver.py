from __future__ import annotations

import threading
import time
from typing import Callable

import serial
from core.com_port_manager import ComPortManager


class SerialDriver:
    """Robuster serieller Treiber für RS422/USB-COM-Adapter.

    Version 0.4 erweitert die einfache Leseschleife um Status-Callbacks,
    Bytezähler und eine sauberere Fehlerbehandlung. RS422 erscheint unter
    Windows als normaler COM-Port; deshalb ist pySerial ausreichend.
    """

    def __init__(
        self,
        port: str,
        baudrate: int = 38400,
        bytesize: int = 8,
        parity: str = "O",
        stopbits: int = 1,
        timeout: float = 0.1,
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.parity = parity
        self.stopbits = stopbits
        self.timeout = timeout
        self._serial: serial.Serial | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self.on_data: Callable[[bytes], None] | None = None
        self.on_log: Callable[[str], None] | None = None
        self.on_status: Callable[[str], None] | None = None
        self.bytes_received = 0
        self.read_errors = 0

    @staticmethod
    def available_ports() -> list[tuple[str, str]]:
        return [(p.device, p.display_name) for p in ComPortManager.list_ports()]

    def connect(self) -> None:
        if not self.port:
            raise ValueError("Kein COM-Port ausgewählt")
        self._serial = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            bytesize=self.bytesize,
            parity=self.parity,
            stopbits=self.stopbits,
            timeout=self.timeout,
        )
        self._stop.clear()
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()
        self._status("connected")
        self._log(f"Verbunden mit {self.port} ({self.baudrate} Baud, 8{self.parity}1)")

    def disconnect(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._status("disconnected")
        self._log("Verbindung getrennt")

    def is_connected(self) -> bool:
        return bool(self._serial and self._serial.is_open)

    def write(self, data: bytes) -> int:
        if not self._serial or not self._serial.is_open:
            raise RuntimeError("Serielle Verbindung ist nicht geöffnet")
        written = self._serial.write(data)
        self._log(f"TX {data.hex(' ').upper()}")
        return written

    def _read_loop(self) -> None:
        while not self._stop.is_set():
            try:
                if self._serial is None:
                    time.sleep(0.1)
                    continue
                data = self._serial.read(256)
                if data:
                    self.bytes_received += len(data)
                    if self.on_data:
                        self.on_data(data)
            except Exception as exc:
                self.read_errors += 1
                self._status("error")
                self._log(f"Lesefehler: {exc}")
                time.sleep(0.5)

    def _log(self, message: str) -> None:
        if self.on_log:
            self.on_log(message)

    def _status(self, status: str) -> None:
        if self.on_status:
            self.on_status(status)
