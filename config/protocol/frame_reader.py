from __future__ import annotations

from protocol.common import SYNC_BYTE, WORD_LENGTHS, decode_word_type


class FrameReader:
    """PDF-oriented stream reader for mixed 5-byte and 8-byte MCS-4 words."""

    def __init__(self):
        self.buffer = bytearray()
        self.invalid_words = 0

    def feed(self, data: bytes) -> list[bytes]:
        self.buffer.extend(data)
        frames: list[bytes] = []
        while True:
            if SYNC_BYTE not in self.buffer:
                self.buffer.clear()
                return frames
            sync_index = self.buffer.index(SYNC_BYTE)
            if sync_index:
                del self.buffer[:sync_index]
            if len(self.buffer) < 2:
                return frames
            wt = decode_word_type(self.buffer[1])
            length = WORD_LENGTHS.get(wt)
            if length is None:
                self.invalid_words += 1
                del self.buffer[0]
                continue
            if len(self.buffer) < length:
                return frames
            frames.append(bytes(self.buffer[:length]))
            del self.buffer[:length]
