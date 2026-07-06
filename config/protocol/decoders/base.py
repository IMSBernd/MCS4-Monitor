from __future__ import annotations

from abc import ABC, abstractmethod

from protocol.common import DecodedFrame, WORD_TYPE_NAMES, decode_word_flags, decode_word_type
from protocol.validators import validate_common


class WordDecoder(ABC):
    word_type: int

    def base_frame(self, packet: bytes) -> DecodedFrame:
        header = packet[1] if len(packet) > 1 else 0
        wt = decode_word_type(header)
        frame = DecodedFrame(
            raw=packet,
            word_type=wt,
            word_type_name=WORD_TYPE_NAMES.get(wt, "Reserved/Undefined"),
            flags=decode_word_flags(header),
            length=len(packet),
            expected_length=None,
            target=packet[2] if len(packet) > 2 else None,
            source=packet[3] if len(packet) > 3 else None,
            number=packet[4] if len(packet) > 4 else None,
        )
        from protocol.common import WORD_LENGTHS
        frame.expected_length = WORD_LENGTHS.get(wt)
        frame.errors.extend(validate_common(packet, wt))
        frame.is_valid = not frame.errors
        return frame

    @abstractmethod
    def decode(self, packet: bytes) -> DecodedFrame:
        raise NotImplementedError
