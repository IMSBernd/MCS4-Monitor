from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class SensorState:
    sensor_id: int
    name: str
    value: float
    unit: str
    status: str
    timestamp: datetime


class SensorStore:
    def __init__(self) -> None:
        self._sensors: dict[int, SensorState] = {}

    def update(self, sensor_id: int, name: str, value: float, unit: str, timestamp: datetime) -> SensorState:
        status = "OK"
        if sensor_id == 1 and value > 90:
            status = "ALARM"
        if sensor_id == 2 and value < 4.5:
            status = "ALARM"
        state = SensorState(sensor_id, name, value, unit, status, timestamp)
        self._sensors[sensor_id] = state
        return state

    def all(self) -> list[SensorState]:
        return [self._sensors[k] for k in sorted(self._sensors)]
