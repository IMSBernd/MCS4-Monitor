from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class DecodedSensorValue:
    sensor_id: int
    name: str
    value: float
    unit: str
    timestamp: datetime


class BasicMCS4Decoder:
    """Vorläufiger Decoder für Simulator-/Rohpakete.

    Noch nicht die finale MTU-MCS-4-Spezifikation. Diese Klasse bleibt absichtlich
    klein und wird später durch Word-Type-Decoder ersetzt.
    """

    SENSOR_NAMES = {
        1: "Öltemperatur",
        2: "Öldruck",
        3: "Drehzahl",
        4: "Kühlwasser",
        5: "Abgastemperatur",
    }
    UNITS = {1: "°C", 2: "bar", 3: "rpm"}

    def decode(self, packet: bytes) -> DecodedSensorValue:
        if len(packet) != 8:
            raise ValueError("Ungültige Paketlänge")
        if packet[0] != 0xFF:
            raise ValueError("Ungültiges Sync-Byte")

        channel = packet[4]
        unit_code = packet[5] & 0x0F
        raw_value = ((packet[6] & 0x3F) << 8) | packet[7]
        unit = self.UNITS.get(unit_code, "")

        if unit_code == 1:
            value = raw_value / 10.0
        elif unit_code == 2:
            value = raw_value / 100.0
        else:
            value = float(raw_value)

        return DecodedSensorValue(
            sensor_id=channel,
            name=self.SENSOR_NAMES.get(channel, f"Sensor {channel}"),
            value=value,
            unit=unit,
            timestamp=datetime.now(),
        )
