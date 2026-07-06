from __future__ import annotations

from .common import SYNC_BYTE, WORD_LENGTHS, decode_word_flags


def validate_common(packet: bytes, word_type: int) -> list[str]:
    errors: list[str] = []
    if not packet:
        return ["empty telegram"]
    if packet[0] != SYNC_BYTE:
        errors.append(f"sync byte is 0x{packet[0]:02X}, expected 0xFF")
    expected = WORD_LENGTHS.get(word_type)
    if expected is None:
        errors.append(f"WordType {word_type} is reserved/undefined in the PDF")
    elif len(packet) != expected:
        errors.append(f"length {len(packet)} instead of {expected}")
    if len(packet) >= 3 and packet[2] > 127:
        errors.append(f"target address >127 ({packet[2]})")
    if len(packet) >= 4 and packet[3] > 63:
        errors.append(f"source address >63 ({packet[3]})")
    if len(packet) >= 5 and packet[4] == 255:
        errors.append("number 255 is not permitted")
    if len(packet) == 8:
        if packet[6] & 0x80:
            errors.append("byte 7 D7 set; PDF data fields reserve this bit as 0")
        if packet[7] & 0x80:
            errors.append("byte 8 D7 set; PDF data fields reserve this bit as 0")
    if word_type == 0 and len(packet) >= 2 and decode_word_flags(packet[1]) != 0:
        errors.append("Data Value has non-zero Byte 2 flags; Appendix 2 expects 0000 0000")
    if word_type == 0 and len(packet) >= 5 and packet[4] > 159:
        errors.append(f"Data Value measuring point outside 0..159 ({packet[4]})")
    return errors
