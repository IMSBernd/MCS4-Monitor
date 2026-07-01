from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from model.sensor import Sensor


class HistoryDatabase:
    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sensor_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    sensor_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT NOT NULL,
                    online INTEGER NOT NULL,
                    alarm INTEGER NOT NULL
                )
                """
            )

    def insert_sensor(self, sensor: Sensor) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                INSERT INTO sensor_history
                (timestamp, sensor_id, name, value, unit, online, alarm)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(timespec="seconds"),
                    sensor.sensor_id,
                    sensor.name,
                    sensor.value,
                    sensor.unit,
                    int(sensor.online),
                    int(sensor.alarm),
                ),
            )
