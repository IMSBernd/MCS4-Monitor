from __future__ import annotations

from dataclasses import dataclass

try:
    from serial.tools import list_ports
except Exception:  # pragma: no cover
    list_ports = None


@dataclass(frozen=True)
class ComPortInfo:
    device: str
    description: str
    manufacturer: str
    hwid: str

    @property
    def display_name(self) -> str:
        parts = [self.device]
        if self.description:
            parts.append(self.description)
        if self.manufacturer:
            parts.append(self.manufacturer)
        return " - ".join(parts)


def list_com_ports() -> list[ComPortInfo]:
    if list_ports is None:
        return []
    ports: list[ComPortInfo] = []
    for port in list_ports.comports():
        ports.append(
            ComPortInfo(
                device=port.device or "",
                description=port.description or "",
                manufacturer=port.manufacturer or "",
                hwid=port.hwid or "",
            )
        )
    return ports
