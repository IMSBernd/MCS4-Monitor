from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Sensor:
    sensor_id: int
    name: str
    value: float
    unit: str
    minimum: float
    maximum: float
    status: str = "OK"
    last_update: datetime | None = None

    @property
    def is_alarm(self) -> bool:
        return self.value < self.minimum or self.value > self.maximum or self.status != "OK"
