from __future__ import annotations

from datetime import datetime

from model.alarm import Alarm
from model.sensor import Sensor


class AlarmManager:
    def __init__(self) -> None:
        self.active: dict[int, Alarm] = {}

    def evaluate(self, sensor: Sensor) -> list[Alarm]:
        changed: list[Alarm] = []
        alarm_text = ""
        priority = 0
        if not sensor.online:
            alarm_text = f"{sensor.name}: Sensorfehler oder keine gültigen Daten"
            priority = 2
        elif sensor.minimum is not None and sensor.value < sensor.minimum:
            alarm_text = f"{sensor.name}: Wert zu niedrig ({sensor.value} {sensor.unit})"
            priority = 1
        elif sensor.maximum is not None and sensor.value > sensor.maximum:
            alarm_text = f"{sensor.name}: Wert zu hoch ({sensor.value} {sensor.unit})"
            priority = 1

        if alarm_text:
            alarm = Alarm(sensor.sensor_id, alarm_text, priority, True, datetime.now())
            self.active[sensor.sensor_id] = alarm
            changed.append(alarm)
        else:
            old = self.active.pop(sensor.sensor_id, None)
            if old:
                changed.append(Alarm(sensor.sensor_id, f"{sensor.name}: Alarm beendet", 0, False, datetime.now()))
        return changed

    def active_alarms(self) -> list[Alarm]:
        return sorted(self.active.values(), key=lambda a: a.timestamp, reverse=True)
