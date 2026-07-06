from __future__ import annotations

from protocol.common import DecodedFrame, WORD_LENGTHS, WORD_TYPE_NAMES, decode_word_flags, decode_word_type
from protocol.decoders.generic import GenericWordDecoder
from protocol.decoders.wordtype0 import DataValueDecoder
from protocol.validators import validate_common

_DECODERS = {
    0: DataValueDecoder(),
    1: GenericWordDecoder(1),
    2: GenericWordDecoder(2),
    3: GenericWordDecoder(3),
    4: GenericWordDecoder(4),
    5: GenericWordDecoder(5),
    6: GenericWordDecoder(6),
    7: GenericWordDecoder(7),
}


def decode_frame(packet: bytes) -> DecodedFrame:
    header = packet[1] if len(packet) > 1 else 0
    wt = decode_word_type(header)
    decoder = _DECODERS.get(wt)
    if decoder:
        return decoder.decode(packet)
    frame = DecodedFrame(
        raw=packet,
        word_type=wt,
        word_type_name=WORD_TYPE_NAMES.get(wt, "Reserved/Undefined"),
        flags=decode_word_flags(header),
        length=len(packet),
        expected_length=WORD_LENGTHS.get(wt),
        target=packet[2] if len(packet) > 2 else None,
        source=packet[3] if len(packet) > 3 else None,
        number=packet[4] if len(packet) > 4 else None,
    )
    frame.errors.extend(validate_common(packet, wt))
    frame.is_valid = not frame.errors
    return frame
