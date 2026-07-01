from __future__ import annotations

import math
import random


class MCSSimulator:
    def __init__(self) -> None:
        self.t = 0.0

    def next_data(self, interval: float = 0.25) -> bytes:
        self.t += interval
        packets = bytearray()
        packets += self._packet(1, 1, int(820 + 30 * math.sin(self.t)))
        packets += self._packet(2, 2, int(520 + 20 * math.sin(self.t / 2)))
        packets += self._packet(3, 3, int(1480 + 60 * math.sin(self.t / 3)))
        packets += self._packet(4, 1, int(790 + 25 * math.cos(self.t)))
        packets += self._packet(5, 1, int(4600 + random.randint(-40, 40)))
        return bytes(packets)

    def _packet(self, channel: int, unit_code: int, value: int) -> bytes:
        value = max(0, min(value, 0x3FFF))
        header = 0x00
        destination = 0x01
        source = 0x02
        info = unit_code & 0x0F
        msb = (value >> 8) & 0x3F
        lsb = value & 0xFF
        return bytes([0xFF, header, destination, source, channel, info, msb, lsb])
