from __future__ import annotations


class PacketReader:
    """Bildet aus einem Byte-Strom feste MCS-4-Rohtelegramme.

    Aktueller Basisstand: 8 Byte, erstes Byte 0xFF.
    Spätere Protokolldetails werden hier erweitert.
    """

    def __init__(self, sync_byte: int = 0xFF, packet_len: int = 8) -> None:
        self.sync_byte = sync_byte
        self.packet_len = packet_len
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[bytes]:
        packets: list[bytes] = []
        for b in data:
            if not self._buffer:
                if b == self.sync_byte:
                    self._buffer.append(b)
                continue

            if len(self._buffer) == 0 and b != self.sync_byte:
                continue

            self._buffer.append(b)

            if len(self._buffer) == self.packet_len:
                packets.append(bytes(self._buffer))
                self._buffer.clear()

        return packets
