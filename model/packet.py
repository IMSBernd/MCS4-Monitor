from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RawPacket:
    data: bytes
    timestamp: datetime

    def hex(self) -> str:
        return " ".join(f"{byte:02X}" for byte in self.data)


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
        # Nur die unteren 6 Bit des MSB enthalten den Wert
        return ((self.data_msb & 0x3F) << 8) | self.data_lsb

    @property
    def sensor_fault(self) -> bool:
        # Bit 6 signalisiert Sensorfehler
        return bool(self.data_msb & 0x40)