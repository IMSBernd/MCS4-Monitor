def hex_string(data: bytes) -> str:
    return " ".join(f"{b:02X}" for b in data)


def make_packet(channel: int, unit_code: int, value: int) -> bytes:
    value = max(0, min(value, 0x3FFF))
    return bytes([
        0xFF, 0x00, 0x01, 0x02,
        channel & 0xFF,
        unit_code & 0x0F,
        (value >> 8) & 0x3F,
        value & 0xFF,
    ])
