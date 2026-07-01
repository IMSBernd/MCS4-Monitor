from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Alarm:
    sensor_id: int
    text: str
    priority: int
    active: bool
    timestamp: datetime
