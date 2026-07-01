from __future__ import annotations

from datetime import datetime
from typing import Iterable

from model.packet import RawPacket


class PacketReader:
    def __init__(self, sync_byte: int = 0xFF, packet_length: int = 8) -> None:
        self.sync_byte = sync_byte
        self.packet_length = packet_length
        self._buffer = bytearray()
        self._in_packet = False

    def feed(self, data: bytes | Iterable[int]) -> list[RawPacket]:
        packets: list[RawPacket] = []
        for value in data:
            byte = int(value) & 0xFF
            if not self._in_packet:
                if byte == self.sync_byte:
                    self._buffer = bytearray([byte])
                    self._in_packet = True
                continue

            self._buffer.append(byte)
            if len(self._buffer) == self.packet_length:
                packets.append(RawPacket(bytes(self._buffer), datetime.now()))
                self._buffer.clear()
                self._in_packet = False
        return packets
