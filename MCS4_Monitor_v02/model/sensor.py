from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Sensor:
    sensor_id: int
    name: str
    value: float = 0.0
    unit: str = ""
    minimum: float | None = None
    maximum: float | None = None
    online: bool = False
    alarm: bool = False
    status_text: str = "Offline"
    last_update: datetime | None = None
