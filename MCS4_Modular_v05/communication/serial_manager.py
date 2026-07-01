from __future__ import annotations

try:
    import serial
    from serial.tools import list_ports
except Exception:  # pragma: no cover
    serial = None
    list_ports = None

class SerialManager:
    @staticmethod
    def available_ports() -> list[tuple[str, str]]:
        if list_ports is None:
            return []
        return [(p.device, p.description) for p in list_ports.comports()]

    def __init__(self) -> None:
        self._port = None

    @property
    def is_open(self) -> bool:
        return self._port is not None and self._port.is_open

    def open(self, port: str, baudrate: int = 38400) -> None:
        if serial is None:
            raise RuntimeError("pyserial ist nicht installiert")
        self.close()
        self._port = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=8,
            parity=serial.PARITY_ODD,
            stopbits=1,
            timeout=0,
        )

    def read_available(self) -> bytes:
        if not self.is_open:
            return b""
        waiting = self._port.in_waiting
        if waiting <= 0:
            return b""
        return self._port.read(waiting)

    def close(self) -> None:
        if self._port is not None:
            try:
                self._port.close()
            finally:
                self._port = None
