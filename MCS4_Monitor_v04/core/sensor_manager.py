from __future__ import annotations

from datetime import datetime

from model.sensor import Sensor
from protocol.mcs4_decoder import DecodedValue


class SensorManager:
    def __init__(self) -> None:
        self.sensors: dict[int, Sensor] = {}

    def update_from_decoded(self, decoded: DecodedValue) -> Sensor:
        sensor = self.sensors.get(decoded.sensor_id)
        if sensor is None:
            sensor = Sensor(sensor_id=decoded.sensor_id, name=decoded.name, unit=decoded.unit)
            self.sensors[decoded.sensor_id] = sensor
        sensor.name = decoded.name
        sensor.value = decoded.value
        sensor.unit = decoded.unit
        sensor.online = not decoded.sensor_fault
        sensor.alarm = decoded.sensor_fault
        sensor.status_text = "Sensorfehler" if decoded.sensor_fault else "Online"
        sensor.last_update = datetime.now()
        return sensor

    def all_sensors(self) -> list[Sensor]:
        return sorted(self.sensors.values(), key=lambda s: s.sensor_id)
