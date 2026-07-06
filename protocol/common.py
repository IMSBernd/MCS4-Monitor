from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

SYNC_BYTE = 0xFF
WORD_LENGTHS = {0: 8, 1: 8, 2: 5, 3: 5, 4: 5, 5: 5, 6: 8, 7: 8}

WORD_TYPE_NAMES = {
    0: "Data Value",
    1: "Limit Value",
    2: "Alarm Message",
    3: "Control Command",
    4: "Binary Signal",
    5: "Key Identification",
    6: "Status Message",
    7: "Curve Transfer",
}


def hex_string(data: bytes) -> str:
    return " ".join(f"{b:02X}" for b in data)


def byte_bits(value: int) -> str:
    return f"{int(value) & 0xFF:08b}"


def decode_word_type(header: int) -> int:
    """PDF: Byte 2, bits D3..D0 define the word type."""
    return int(header) & 0x0F


def decode_word_flags(header: int) -> int:
    """PDF: Byte 2, bits D7..D4 are word-specific extensions."""
    return (int(header) >> 4) & 0x0F


def decode_page_line(byte6: int) -> tuple[int, int]:
    """PDF Appendix 1/2: Byte 6 D7..D3 = page, D2..D0 = line."""
    return (int(byte6) >> 3) & 0x1F, int(byte6) & 0x07


def decode_12bit_value(byte7: int, byte8: int) -> tuple[int, bool, bool]:
    """PDF Appendix 2: byte7 D6=fault, D5=sign, D4..D0 high bits; byte8 D6..D0 low bits."""
    sensor_fault = bool(byte7 & 0x40)
    negative = bool(byte7 & 0x20)
    raw = ((byte7 & 0x1F) << 7) | (byte8 & 0x7F)
    if negative:
        raw = -raw
    return raw, negative, sensor_fault


@dataclass(slots=True)
class DecodedFrame:
    raw: bytes
    word_type: int
    word_type_name: str
    flags: int
    length: int
    expected_length: int | None
    target: int | None = None
    source: int | None = None
    number: int | None = None
    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    fields: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def hex(self) -> str:
        return hex_string(self.raw)

    @property
    def is_data_value(self) -> bool:
        return self.word_type == 0 and self.is_valid
