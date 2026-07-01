from __future__ import annotations

from dataclasses import dataclass

from model.packet import MCSPacket


@dataclass(frozen=True)
class DecodedValue:
    sensor_id: int
    name: str
    value: float
    unit: str
    sensor_fault: bool
    source: int
    destination: int
    word_type: int


class MCS4Decoder:
    """Vorläufiger Decoder.

    Die Telegrammstruktur ist vorbereitet. Die exakten Word-Type-Bitmasken,
    Skalierungsfaktoren und CRC-Regeln werden nach weiterer PDF-Auswertung ergänzt.
    Für Version 0.1 liefert der Decoder stabile Testwerte aus realen oder simulierten
    8-Byte-Telegrammen.
    """

    UNITS = {
        0: "",
        1: "°C",
        2: "bar",
        3: "rpm",
        4: "V",
        5: "A",
        6: "%",
    }

    SENSOR_NAMES = {
        1: "Öltemperatur",
        2: "Öldruck",
        3: "Drehzahl",
        4: "Kühlwasser",
        5: "Abgastemperatur",
        6: "Ladedruck",
    }

    def decode(self, packet: MCSPacket) -> DecodedValue:
        unit_code = packet.info & 0x0F
        unit = self.UNITS.get(unit_code, "")
        raw_value = packet.raw_value
        value = self._scale_value(raw_value, unit)
        name = self.SENSOR_NAMES.get(packet.channel, f"Sensor {packet.channel}")
        return DecodedValue(
            sensor_id=packet.channel,
            name=name,
            value=value,
            unit=unit,
            sensor_fault=packet.sensor_fault,
            source=packet.source,
            destination=packet.destination,
            word_type=packet.word_type,
        )

    def _scale_value(self, raw_value: int, unit: str) -> float:
        if unit in {"bar", "V", "A"}:
            return round(raw_value / 100.0, 2)
        if unit == "°C":
            return round(raw_value / 10.0, 1)
        return float(raw_value)
