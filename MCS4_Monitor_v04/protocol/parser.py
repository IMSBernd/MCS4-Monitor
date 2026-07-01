from __future__ import annotations

from datetime import datetime

from model.packet import MCSPacket, RawPacket


class PacketParseError(ValueError):
    pass


class PacketParser:
    def __init__(self, sync_byte: int = 0xFF, packet_length: int = 8) -> None:
        self.sync_byte = sync_byte
        self.packet_length = packet_length

    def parse(self, raw: RawPacket) -> MCSPacket:
        data = raw.data
        if len(data) != self.packet_length:
            raise PacketParseError(f"Ungültige Telegrammlänge: {len(data)}")
        if data[0] != self.sync_byte:
            raise PacketParseError(f"Sync-Byte fehlt: {data[0]:02X}")
        return MCSPacket(
            sync=data[0],
            header=data[1],
            destination=data[2],
            source=data[3],
            channel=data[4],
            info=data[5],
            data_msb=data[6],
            data_lsb=data[7],
            timestamp=raw.timestamp or datetime.now(),
            raw=data,
        )
