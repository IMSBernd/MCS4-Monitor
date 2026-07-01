from dataclasses import dataclass
from datetime import datetime

@dataclass
class SensorValue:
    sensor_id: int
    name: str
    value: float
    unit: str
    timestamp: datetime
    fault: bool = False
