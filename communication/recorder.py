from datetime import datetime
from pathlib import Path


def hex_string(data: bytes) -> str:
    return " ".join(f"{b:02X}" for b in data)


class TelegramRecorder:
    def __init__(self, folder: str = "recordings"):
        self.folder = Path(folder)
        self.folder.mkdir(exist_ok=True)
        self.file = None
        self.path = None

    @property
    def active(self) -> bool:
        return self.file is not None

    def start(self):
        if self.file:
            return self.path
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.path = self.folder / f"{stamp}.mcslog"
        self.file = self.path.open("w", encoding="utf-8")
        self.file.write("# MCS4 telegram recording\n")
        self.file.write("# timestamp;hex\n")
        self.file.flush()
        return self.path

    def stop(self):
        if self.file:
            self.file.close()
            self.file = None

    def write_packet(self, packet: bytes):
        if not self.file:
            return
        self.file.write(f"{datetime.now().isoformat(timespec='milliseconds')};{hex_string(packet)}\n")
        self.file.flush()
