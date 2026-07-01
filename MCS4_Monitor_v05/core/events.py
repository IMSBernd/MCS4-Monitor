from __future__ import annotations
from PySide6.QtCore import QObject, Signal
from model.sensor import Sensor
from model.telegram import Telegram


class AppEvents(QObject):
    sensor_updated = Signal(object)      # Sensor
    telegram_received = Signal(object)   # Telegram
    status_changed = Signal(str)
    diagnostics_changed = Signal(dict)
