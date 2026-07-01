from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class RawTelegram:
    data: bytes
    timestamp: datetime

    def hex(self) -> str:
        return " ".join(f"{b:02X}" for b in self.data)

class TelegramBuffer:
    def __init__(self, sync_byte: int = 0xFF, length: int = 8) -> None:
        self.sync_byte = sync_byte
        self.length = length
        self._buffer = bytearray()

    def clear(self) -> None:
        self._buffer.clear()

    def feed(self, data: bytes) -> list[RawTelegram]:
        self._buffer.extend(data)
        result: list[RawTelegram] = []

        while True:
            try:
                sync_index = self._buffer.index(self.sync_byte)
            except ValueError:
                self._buffer.clear()
                break

            if sync_index > 0:
                del self._buffer[:sync_index]

            if len(self._buffer) < self.length:
                break

            telegram = bytes(self._buffer[:self.length])
            del self._buffer[:self.length]
            result.append(RawTelegram(telegram, datetime.now()))

        return result
