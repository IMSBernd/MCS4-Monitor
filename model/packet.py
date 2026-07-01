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
        # Vorläufige Extraktion. Wird nach finaler PDF-Auswertung angepasst.
        return self.header & 0x0F

    @property
    def raw_value(self) -> int:
        return ((self.data_msb & 0x7F) << 8) | self.data_lsb

    @property
    def sensor_fault(self) -> bool:
        # Vorläufig: Bit 6 im Daten-MSB. Wird später gegen PDF final geprüft.
        return bool(self.data_msb & 0x40)
