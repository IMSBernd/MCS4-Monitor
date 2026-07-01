from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SerialConfig:
    port: str = ""
    baudrate: int = 38400
    bytesize: int = 8
    parity: str = "O"
    stopbits: int = 1
    timeout: float = 0.1


@dataclass
class PacketConfig:
    sync_byte: int = 0xFF
    length: int = 8


@dataclass
class AlarmConfig:
    sensor_timeout_seconds: float = 3.0


@dataclass
class DatabaseConfig:
    path: str = "mcs4_history.sqlite"


@dataclass
class AppConfig:
    app_name: str = "MCS-4 Monitor"
    mode: str = "simulator"
    serial: SerialConfig = None
    packet: PacketConfig = None
    alarm: AlarmConfig = None
    database: DatabaseConfig = None

    def __post_init__(self) -> None:
        self.serial = self.serial or SerialConfig()
        self.packet = self.packet or PacketConfig()
        self.alarm = self.alarm or AlarmConfig()
        self.database = self.database or DatabaseConfig()


def load_config(path: str | Path = "config.json") -> AppConfig:
    path = Path(path)
    if not path.exists():
        return AppConfig()

    data = json.loads(path.read_text(encoding="utf-8"))
    return AppConfig(
        app_name=data.get("app_name", "MCS-4 Monitor"),
        mode=data.get("mode", "simulator"),
        serial=SerialConfig(**data.get("serial", {})),
        packet=PacketConfig(**data.get("packet", {})),
        alarm=AlarmConfig(**data.get("alarm", {})),
        database=DatabaseConfig(**data.get("database", {})),
    )
