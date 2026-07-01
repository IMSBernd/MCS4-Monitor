from __future__ import annotations

import math
import random


class MCSSimulator:
    """Deterministischer Simulator ohne Threading.

    Die GUI ruft `next_bytes()` per Qt-Timer auf. Dadurch werden keine
    Qt-Widgets aus Hintergrund-Threads aktualisiert.
    """

    def __init__(self) -> None:
        self.t = 0.0

    def next_bytes(self, interval_s: float = 0.25) -> bytes:
        self.t += interval_s
        packets = bytearray()
        packets += self._packet(channel=1, unit_code=1, value=int(820 + 30 * math.sin(self.t)))
        packets += self._packet(channel=2, unit_code=2, value=int(520 + 20 * math.sin(self.t / 2)))
        packets += self._packet(channel=3, unit_code=3, value=int(1480 + 60 * math.sin(self.t / 3)))
        packets += self._packet(channel=4, unit_code=1, value=int(790 + 25 * math.cos(self.t)))
        packets += self._packet(channel=5, unit_code=1, value=int(4600 + random.randint(-40, 40)))
        return bytes(packets)

    @staticmethod
    def _packet(channel: int, unit_code: int, value: int) -> bytes:
        value = max(0, min(value, 0x3FFF))
        header = 0x00
        destination = 0x01
        source = 0x02
        info = unit_code & 0x0F
        msb = (value >> 8) & 0x3F
        lsb = value & 0xFF
        return bytes([0xFF, header, destination, source, channel, info, msb, lsb])
