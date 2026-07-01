from datetime import datetime


class SensorManager:
    def __init__(self, timeout_seconds: float = 3.0):
        self.sensors = {}
        self.timeout_seconds = timeout_seconds

    def update(self, decoded):
        now = datetime.now()
        old = self.sensors.get(decoded.channel, {})
        old_min = old.get("min", decoded.value)
        old_max = old.get("max", decoded.value)
        self.sensors[decoded.channel] = {
            "id": decoded.channel,
            "name": decoded.name,
            "value": decoded.value,
            "unit": decoded.unit,
            "min": min(old_min, decoded.value),
            "max": max(old_max, decoded.value),
            "last_update": now,
            "status": "OK",
            "alarm": "",
        }
        return self.sensors[decoded.channel]

    def check_timeouts(self):
        now = datetime.now()
        for sensor in self.sensors.values():
            age = (now - sensor["last_update"]).total_seconds()
            if age > self.timeout_seconds:
                sensor["status"] = "OFFLINE"
                sensor["alarm"] = f"{sensor['name']}: keine Daten seit {age:.1f}s"

    def all(self):
        self.check_timeouts()
        return [self.sensors[k] for k in sorted(self.sensors)]
