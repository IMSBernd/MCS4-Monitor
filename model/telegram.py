from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Telegram:
    raw: bytes
    timestamp: datetime
    source: str = "SIM"

    @property
    def hex_string(self) -> str:
        return " ".join(f"{b:02X}" for b in self.raw)
