from __future__ import annotations

import math
import random
from datetime import datetime
from model.sensor import SensorValue


class EngineSimulator:
    """Thread-freier Simulator. Wird ausschließlich vom Qt-Hauptthread per QTimer aufgerufen."""

    def __init__(self) -> None:
        self.t = 0.0

    def next_values(self, dt: float = 0.25) -> list[SensorValue]:
        self.t += dt
        now = datetime.now()
        rpm = 1450 + 120 * math.sin(self.t / 3.0)
        oil_temp = 82 + 4 * math.sin(self.t / 5.0)
        oil_pressure = 5.2 + 0.25 * math.sin(self.t / 2.0)
        coolant = 79 + 3 * math.cos(self.t / 4.0)
        exhaust = 455 + random.randint(-12, 12)

        return [
            SensorValue(1, "Öltemperatur", round(oil_temp, 1), "°C", self._status(oil_temp, 60, 95), now),
            SensorValue(2, "Öldruck", round(oil_pressure, 2), "bar", self._status(oil_pressure, 3.5, 6.5), now),
            SensorValue(3, "Drehzahl", round(rpm, 0), "rpm", self._status(rpm, 500, 2200), now),
            SensorValue(4, "Kühlwasser", round(coolant, 1), "°C", self._status(coolant, 60, 95), now),
            SensorValue(5, "Abgastemperatur", round(exhaust, 0), "°C", self._status(exhaust, 250, 580), now),
        ]

    @staticmethod
    def _status(value: float, minimum: float, maximum: float) -> str:
        return "OK" if minimum <= value <= maximum else "ALARM"
