from __future__ import annotations
import math
import random


def make_packet(channel: int, unit_code: int, value: int) -> bytes:
    value = max(0, min(value, 0x3FFF))
    return bytes([
        0xFF, 0x00, 0x01, 0x02,
        channel & 0xFF,
        unit_code & 0x0F,
        (value >> 8) & 0x3F,
        value & 0xFF,
    ])

class MCSSimulator:
    def __init__(self) -> None:
        self.t = 0.0

    def next_bytes(self, dt: float = 0.25) -> bytes:
        self.t += dt
        oil_temp = 82 + 3 * math.sin(self.t)
        oil_pressure = 5.2 + 0.2 * math.sin(self.t / 2)
        rpm = 1480 + 60 * math.sin(self.t / 3)
        coolant = 79 + 2.5 * math.cos(self.t)
        exhaust = 460 + random.randint(-8, 8)

        packets = bytearray()
        packets += make_packet(1, 1, int(oil_temp * 10))
        packets += make_packet(2, 2, int(oil_pressure * 100))
        packets += make_packet(3, 3, int(rpm))
        packets += make_packet(4, 1, int(coolant * 10))
        packets += make_packet(5, 1, int(exhaust * 10))
        return bytes(packets)
