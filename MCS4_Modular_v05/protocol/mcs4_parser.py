from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from models.sensor import SensorValue

@dataclass(frozen=True)
class MCSPacket:
    sync: int
    header: int
    destination: int
    source: int
    channel: int
    info: int
    data_msb: int
    data_lsb: int
    timestamp: datetime
    raw: bytes

    @property
    def word_type(self) -> int:
        return self.header & 0x0F

    @property
    def raw_value(self) -> int:
        return ((self.data_msb & 0x3F) << 8) | self.data_lsb

    @property
    def sensor_fault(self) -> bool:
        return bool(self.data_msb & 0x40)

class MCS4Parser:
    UNITS = {0: "", 1: "°C", 2: "bar", 3: "rpm", 4: "V", 5: "A", 6: "%"}
    SENSOR_NAMES = {
        1: "Öltemperatur",
        2: "Öldruck",
        3: "Drehzahl",
        4: "Kühlwasser",
        5: "Abgastemperatur",
        6: "Ladedruck",
    }

    def parse_packet(self, raw: bytes, timestamp: datetime) -> MCSPacket:
        if len(raw) != 8:
            raise ValueError(f"Telegramm muss 8 Byte haben, ist aber {len(raw)} Byte lang")
        if raw[0] != 0xFF:
            raise ValueError("Telegramm beginnt nicht mit Sync-Byte FF")
        return MCSPacket(
            sync=raw[0], header=raw[1], destination=raw[2], source=raw[3],
            channel=raw[4], info=raw[5], data_msb=raw[6], data_lsb=raw[7],
            timestamp=timestamp, raw=raw,
        )

    def decode_sensor(self, packet: MCSPacket) -> SensorValue:
        unit = self.UNITS.get(packet.info & 0x0F, "")
        value = self._scale(packet.raw_value, unit)
        name = self.SENSOR_NAMES.get(packet.channel, f"Sensor {packet.channel}")
        return SensorValue(packet.channel, name, value, unit, packet.timestamp, packet.sensor_fault)

    def _scale(self, raw_value: int, unit: str) -> float:
        if unit == "°C":
            return round(raw_value / 10.0, 1)
        if unit in {"bar", "V", "A"}:
            return round(raw_value / 100.0, 2)
        return float(raw_value)
