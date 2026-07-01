import math
import random
from communication.utils import make_packet


class MCSSimulator:
    def __init__(self):
        self.t = 0.0

    def next_bytes(self) -> bytes:
        self.t += 0.25
        oil_temp = 82 + 3 * math.sin(self.t)
        oil_pressure = 5.2 + 0.2 * math.sin(self.t / 2)
        rpm = 1480 + 60 * math.sin(self.t / 3)
        coolant = 79 + 2.5 * math.cos(self.t)
        exhaust = 460 + random.randint(-8, 8)

        if int(self.t) % 30 > 24:
            oil_temp += 14
        if int(self.t) % 40 > 34:
            exhaust += 120

        packets = bytearray()
        packets += make_packet(1, 1, int(oil_temp * 10))
        packets += make_packet(2, 2, int(oil_pressure * 100))
        packets += make_packet(3, 3, int(rpm))
        packets += make_packet(4, 1, int(coolant * 10))
        packets += make_packet(5, 1, int(exhaust * 10))
        return bytes(packets)
