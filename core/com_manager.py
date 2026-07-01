from __future__ import annotations
from dataclasses import dataclass
from typing import List

try:
    from serial.tools import list_ports
except Exception:  # pyserial may be missing
    list_ports = None


@dataclass
class ComPortInfo:
    device: str
    description: str
    manufacturer: str
    hwid: str

    @property
    def display_name(self) -> str:
        text = f"{self.device} - {self.description}"
        if self.manufacturer:
            text += f" ({self.manufacturer})"
        return text

    @property
    def is_likely_exsys(self) -> bool:
        haystack = f"{self.description} {self.manufacturer} {self.hwid}".lower()
        return any(token in haystack for token in ["exsys", "ftdi", "usb serial", "rs422", "serial port"])


class ComManager:
    def list_ports(self) -> List[ComPortInfo]:
        if list_ports is None:
            return []
        ports: List[ComPortInfo] = []
        for p in list_ports.comports():
            ports.append(ComPortInfo(
                device=p.device or "",
                description=p.description or "",
                manufacturer=p.manufacturer or "",
                hwid=p.hwid or "",
            ))
        return ports
