from pathlib import Path


class TelegramPlayer:
    def __init__(self):
        self.packets: list[bytes] = []
        self.index = 0

    def load_latest(self, folder: str = "recordings") -> str | None:
        files = sorted(Path(folder).glob("*.mcslog"))
        if not files:
            return None
        return self.load(files[-1])

    def load(self, path) -> str:
        self.packets.clear()
        self.index = 0
        path = Path(path)
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    _, hex_part = line.split(";", 1)
                    data = bytes(int(x, 16) for x in hex_part.split())
                    if data:
                        self.packets.append(data)
                except Exception:
                    continue
        return str(path)

    def next_packet(self) -> bytes | None:
        if not self.packets:
            return None
        packet = self.packets[self.index]
        self.index = (self.index + 1) % len(self.packets)
        return packet
