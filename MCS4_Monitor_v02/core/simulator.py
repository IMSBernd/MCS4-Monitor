from __future__ import annotations

import math
import random
import threading
import time
from typing import Callable


class MCSSimulator:
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
            packets = bytearray()
            packets += self._packet(1, 1, int(820 + 30 * math.sin(self._t)))  # °C /10
            packets += self._packet(2, 2, int(520 + 20 * math.sin(self._t / 2)))  # bar /100
            packets += self._packet(3, 3, int(1480 + 60 * math.sin(self._t / 3)))
            packets += self._packet(4, 1, int(790 + 25 * math.cos(self._t)))
            packets += self._packet(5, 1, int(4600 + random.randint(-40, 40)))
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
