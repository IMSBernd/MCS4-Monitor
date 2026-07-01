from __future__ import annotations
import math
import random
import threading
import time
from datetime import datetime
from typing import Callable

from model.sensor import Sensor
from model.telegram import Telegram


class EngineSimulator:
    """Erzeugt plausible Motordaten und Beispieltelegramme für GUI-Tests ohne Hardware."""

    def __init__(self, interval_s: float = 0.1):
        self.interval_s = interval_s
        self._running = False
        self._thread: threading.Thread | None = None
        self._t = 0.0
        self.on_sensor: Callable[[Sensor], None] | None = None
        self.on_telegram: Callable[[Telegram], None] | None = None
        self.on_diagnostics: Callable[[dict], None] | None = None
        self._telegram_count = 0
        self._byte_count = 0
        self._start_time = time.monotonic()

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._start_time = time.monotonic()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def _loop(self) -> None:
        while self._running:
            self._t += self.interval_s
            rpm = 1450 + 260 * math.sin(self._t / 5) + random.uniform(-20, 20)
            oil_temp = 82 + 6 * math.sin(self._t / 11) + (rpm - 1450) / 180 + random.uniform(-0.3, 0.3)
            coolant = 78 + 4 * math.sin(self._t / 13) + (rpm - 1450) / 260 + random.uniform(-0.2, 0.2)
            oil_pressure = 4.8 + (rpm - 1200) / 950 + random.uniform(-0.08, 0.08)
            exhaust = 410 + (rpm - 1200) / 3.2 + random.uniform(-5, 5)

            sensors = [
                Sensor(1, "Öltemperatur", round(oil_temp, 1), "°C", 60, 95, last_update=datetime.now()),
                Sensor(2, "Öldruck", round(oil_pressure, 2), "bar", 3.0, 6.5, last_update=datetime.now()),
                Sensor(3, "Kühlwasser", round(coolant, 1), "°C", 60, 92, last_update=datetime.now()),
                Sensor(4, "Drehzahl", round(rpm, 0), "rpm", 600, 1900, last_update=datetime.now()),
                Sensor(5, "Abgastemperatur", round(exhaust, 0), "°C", 200, 650, last_update=datetime.now()),
            ]

            for sensor in sensors:
                if self.on_sensor:
                    self.on_sensor(sensor)
                raw = self._make_fake_telegram(sensor)
                self._telegram_count += 1
                self._byte_count += len(raw)
                if self.on_telegram:
                    self.on_telegram(Telegram(raw=raw, timestamp=datetime.now(), source="SIM"))

            if self.on_diagnostics:
                elapsed = max(0.001, time.monotonic() - self._start_time)
                self.on_diagnostics({
                    "Quelle": "Simulator",
                    "Telegramme/s": f"{self._telegram_count / elapsed:.1f}",
                    "Telegramme": str(self._telegram_count),
                    "Bytes": str(self._byte_count),
                    "CRC-Fehler": "0",
                    "Timeouts": "0",
                })

            time.sleep(self.interval_s)

    @staticmethod
    def _make_fake_telegram(sensor: Sensor) -> bytes:
        # Platzhaltertelegramm: 8 Byte mit 0xFF Sync. Nicht finales MCS-4-Protokoll.
        value = int(abs(sensor.value) * 10) & 0xFFFF
        b = bytearray(8)
        b[0] = 0xFF
        b[1] = 0x00
        b[2] = 0x01
        b[3] = 0x10
        b[4] = sensor.sensor_id & 0xFF
        b[5] = 0x00
        b[6] = (value >> 8) & 0xFF
        b[7] = value & 0xFF
        return bytes(b)
