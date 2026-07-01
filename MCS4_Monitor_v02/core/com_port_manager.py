from __future__ import annotations

from dataclasses import dataclass
from serial.tools import list_ports


@dataclass(frozen=True)
class ComPortInfo:
    device: str
    description: str
    manufacturer: str
    hwid: str
    is_likely_exsys: bool = False

    @property
    def display_name(self) -> str:
        marker = "  [wahrscheinlich Exsys/USB-RS422]" if self.is_likely_exsys else ""
        parts = [self.device]
        if self.description:
            parts.append(self.description)
        if self.manufacturer:
            parts.append(self.manufacturer)
        return " - ".join(parts) + marker


class ComPortManager:
    """Erkennt serielle Windows-COM-Ports und markiert wahrscheinliche USB-RS422-Adapter.

    pySerial liefert je nach Treiber Hersteller, Beschreibung und Hardware-ID.
    Exsys-Adapter erscheinen häufig als FTDI/USB Serial Port oder mit Exsys im Text.
    """

    EXSYS_HINTS = (
        "exsys",
        "ftdi",
        "usb serial",
        "usb-serial",
        "rs422",
        "rs-422",
        "serial converter",
    )

    @classmethod
    def list_ports(cls) -> list[ComPortInfo]:
        ports: list[ComPortInfo] = []
        for port in list_ports.comports():
            text = " ".join(
                str(value or "")
                for value in (port.device, port.description, port.manufacturer, port.hwid)
            ).lower()
            ports.append(
                ComPortInfo(
                    device=port.device or "",
                    description=port.description or "",
                    manufacturer=port.manufacturer or "",
                    hwid=port.hwid or "",
                    is_likely_exsys=any(hint in text for hint in cls.EXSYS_HINTS),
                )
            )
        return sorted(ports, key=lambda p: (not p.is_likely_exsys, p.device))

    @classmethod
    def preferred_port(cls) -> ComPortInfo | None:
        ports = cls.list_ports()
        for port in ports:
            if port.is_likely_exsys:
                return port
        return ports[0] if ports else None
