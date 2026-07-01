from __future__ import annotations
from datetime import datetime
from pathlib import Path

class TelegramRecorder:
    def __init__(self, directory: str = "recordings") -> None:
        self.directory = Path(directory)
        self.directory.mkdir(exist_ok=True)
        self.file = None
        self.path: Path | None = None

    @property
    def active(self) -> bool:
        return self.file is not None

    def start(self) -> Path:
        self.stop()
        self.path = self.directory / f"mcs4_{datetime.now():%Y%m%d_%H%M%S}.mcslog"
        self.file = self.path.open("a", encoding="utf-8")
        return self.path

    def write(self, data: bytes) -> None:
        if not self.file:
            return
        self.file.write(f"{datetime.now().isoformat()} {data.hex().upper()}\n")
        self.file.flush()

    def stop(self) -> None:
        if self.file:
            self.file.close()
            self.file = None
