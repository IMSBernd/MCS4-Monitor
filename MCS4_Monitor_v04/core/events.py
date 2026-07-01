from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable


class EventBus:
    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[..., None]]] = defaultdict(list)

    def subscribe(self, event_name: str, callback: Callable[..., None]) -> None:
        self._listeners[event_name].append(callback)

    def publish(self, event_name: str, *args: Any, **kwargs: Any) -> None:
        for callback in list(self._listeners.get(event_name, [])):
            callback(*args, **kwargs)


EVENT_LOG = "log"
EVENT_PACKET = "packet_received"
EVENT_SENSOR = "sensor_updated"
EVENT_ALARM = "alarm_changed"
EVENT_DIAG = "diagnostics_updated"
EVENT_CONNECTION = "connection_changed"
