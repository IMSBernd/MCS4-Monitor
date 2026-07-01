from datetime import datetime


class SensorManager:
    def __init__(self):
        self.values = {}

    def update(self, decoded, state: str, alarm_text: str):
        now = datetime.now().strftime("%H:%M:%S")
        old = self.values.get(decoded.channel)
        min_value = decoded.value if old is None else min(old["min"], decoded.value)
        max_value = decoded.value if old is None else max(old["max"], decoded.value)
        self.values[decoded.channel] = {
            "id": decoded.channel,
            "name": decoded.name,
            "value": decoded.value,
            "unit": decoded.unit,
            "state": state,
            "alarm": alarm_text,
            "time": now,
            "min": min_value,
            "max": max_value,
            "last_seen": datetime.now(),
        }

    def all(self):
        return [self.values[k] for k in sorted(self.values)]
