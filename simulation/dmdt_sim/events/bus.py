from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, dict[str, Callable]] = defaultdict(dict)
        self._history: list[dict[str, Any]] = []
        self._max_history: int = 10000

    def subscribe(self, event_type: str, callback: Callable, subscriber_id: str | None = None) -> str:
        sid = subscriber_id or str(uuid.uuid4())
        self._subscribers[event_type][sid] = callback
        return sid

    def unsubscribe(self, event_type: str, subscriber_id: str) -> None:
        self._subscribers[event_type].pop(subscriber_id, None)

    def publish(self, event_type: str, data: dict[str, Any]) -> None:
        entry = {
            "type": event_type,
            "data": dict(data),
            "timestamp": datetime.now().isoformat(),
        }
        self._history.append(entry)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        for callback in list(self._subscribers.get(event_type, {}).values()):
            callback(data)

    def get_history(self, event_type: str | None = None) -> list[dict[str, Any]]:
        if event_type:
            return [e for e in self._history if e["type"] == event_type]
        return list(self._history)

    def clear_history(self) -> None:
        self._history.clear()
