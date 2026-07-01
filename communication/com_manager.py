try:
    import serial
    from serial.tools import list_ports
except Exception:
    serial = None
    list_ports = None


class ComManager:
    @staticmethod
    def available_ports():
        if list_ports is None:
            return []
        return [(p.device, p.description) for p in list_ports.comports()]

    def __init__(self):
        self.port = None

    def open(self, port_name: str):
        if serial is None:
            raise RuntimeError("pyserial ist nicht verfügbar")
        self.port = serial.Serial(
            port=port_name,
            baudrate=38400,
            bytesize=8,
            parity=serial.PARITY_ODD,
            stopbits=1,
            timeout=0,
        )

    def close(self):
        if self.port is not None:
            self.port.close()
            self.port = None

    def read_available(self) -> bytes:
        if self.port is None:
            return b""
        waiting = self.port.in_waiting
        if waiting <= 0:
            return b""
        return self.port.read(waiting)

    @property
    def is_open(self) -> bool:
        return self.port is not None
