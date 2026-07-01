class TelegramBuffer:
    def __init__(self, sync_byte: int = 0xFF, packet_length: int = 8):
        self.sync_byte = sync_byte
        self.packet_length = packet_length
        self.buffer = bytearray()

    def clear(self):
        self.buffer.clear()

    def feed(self, data: bytes) -> list[bytes]:
        self.buffer.extend(data)
        packets = []
        while True:
            if self.sync_byte not in self.buffer:
                self.buffer.clear()
                return packets
            sync_index = self.buffer.index(self.sync_byte)
            if sync_index > 0:
                del self.buffer[:sync_index]
            if len(self.buffer) < self.packet_length:
                return packets
            packet = bytes(self.buffer[:self.packet_length])
            del self.buffer[:self.packet_length]
            packets.append(packet)
