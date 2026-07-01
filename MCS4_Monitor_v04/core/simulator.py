from __future__ import annotations

import math
import random
import threading
import time
from typing import Callable


class MCSSimulator:
    """Virtueller MCS-4 Datenstrom für Entwicklung ohne RS422-Hardware."""

    def __init__(self, interval: float = 0.25) -> None:
        self.interval = interval
        self.on_data: Callable[[bytes], None] | None = None
        self.on_log: Callable[[str], None] | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._t = 0.0

    def start(self) -> None:
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self._log("Simulator gestartet")

    def stop(self) -> None:
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._log("Simulator gestoppt")

    def _loop(self) -> None:
        while not self._stop.is_set():
            self._t += self.interval
            rpm = 1480 + 420 * (0.5 + 0.5 * math.sin(self._t / 8)) + random.randint(-20, 20)
            load = max(0.0, min(1.0, (rpm - 1450) / 450))
            oil_temp = 78 + 16 * load + 2.0 * math.sin(self._t / 6)
            oil_pressure = 4.8 + 1.2 * load + 0.12 * math.sin(self._t / 3)
            coolant = 76 + 10 * load + 1.4 * math.cos(self._t / 5)
            exhaust = 420 + 140 * load + random.randint(-8, 8)
            boost = 0.8 + 1.1 * load + 0.04 * math.sin(self._t)

            packets = bytearray()
            packets += self._packet(1, 1, int(oil_temp * 10))       # °C / 10
            packets += self._packet(2, 2, int(oil_pressure * 100))  # bar / 100
            packets += self._packet(3, 3, int(rpm))                 # rpm
            packets += self._packet(4, 1, int(coolant * 10))        # °C / 10
            packets += self._packet(5, 1, int(exhaust * 10))        # °C / 10
            packets += self._packet(6, 2, int(boost * 100))         # bar / 100
            if self.on_data:
                self.on_data(bytes(packets))
            time.sleep(self.interval)

    def _packet(self, channel: int, unit_code: int, value: int) -> bytes:
        value = max(0, min(value, 0x3FFF))
        header = 0x00
        destination = 0x01
        source = 0x02
        info = unit_code & 0x0F
        msb = (value >> 8) & 0x3F
        lsb = value & 0xFF
        return bytes([0xFF, header, destination, source, channel, info, msb, lsb])

    def _log(self, message: str) -> None:
        if self.on_log:
            self.on_log(message)
