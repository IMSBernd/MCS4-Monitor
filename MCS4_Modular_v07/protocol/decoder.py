from dataclasses import dataclass


@dataclass
class DecodedSensorValue:
    channel: int
    name: str
    value: float
    unit: str
    source: int
    destination: int
    header: int


class MCS4Decoder:
    SENSOR_NAMES = {
        1: "Öltemperatur",
        2: "Öldruck",
        3: "Drehzahl",
        4: "Kühlwasser",
        5: "Abgastemperatur",
    }
    UNITS = {1: "°C", 2: "bar", 3: "rpm"}

    def decode(self, packet: bytes) -> DecodedSensorValue | None:
        if len(packet) != 8 or packet[0] != 0xFF:
            return None
        header = packet[1]
        destination = packet[2]
        source = packet[3]
        channel = packet[4]
        unit_code = packet[5] & 0x0F
        raw_value = ((packet[6] & 0x3F) << 8) | packet[7]
        unit = self.UNITS.get(unit_code, "")
        if unit == "°C":
            value = raw_value / 10.0
        elif unit == "bar":
            value = raw_value / 100.0
        else:
            value = float(raw_value)
        return DecodedSensorValue(
            channel=channel,
            name=self.SENSOR_NAMES.get(channel, f"Sensor {channel}"),
            value=value,
            unit=unit,
            source=source,
            destination=destination,
            header=header,
        )
