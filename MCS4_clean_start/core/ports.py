from __future__ import annotations


def list_serial_ports() -> list[tuple[str, str]]:
    try:
        from serial.tools import list_ports
    except Exception:
        return []
    result: list[tuple[str, str]] = []
    for port in list_ports.comports():
        desc = port.description or "Serieller Anschluss"
        if port.manufacturer:
            desc += f" ({port.manufacturer})"
        result.append((port.device, desc))
    return result
