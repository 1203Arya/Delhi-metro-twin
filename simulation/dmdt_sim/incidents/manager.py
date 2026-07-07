from __future__ import annotations

import uuid
from collections import defaultdict
from typing import Any, Callable

from ..types import Incident, IncidentType, SimulationConfig


class IncidentManager:
    def __init__(self, config: SimulationConfig) -> None:
        self.config = config
        self.incidents: list[Incident] = []
        self._active: dict[str, Incident] = {}
        self._resolved: list[Incident] = []
        self._line_incidents: dict[str, list[str]] = defaultdict(list)
        self._listeners: dict[str, list[Callable]] = defaultdict(list)

    def on(self, event: str, callback: Callable) -> None:
        self._listeners[event].append(callback)

    def trigger(self, event: str, data: dict[str, Any]) -> None:
        for cb in self._listeners.get(event, []):
            cb(data)

    def create_incident(
        self,
        incident_type: IncidentType,
        line_code: str = "",
        station_code: str = "",
        track_segment_id: str = "",
        start_time: float = 0.0,
        duration_s: float = 60.0,
        description: str = "",
    ) -> Incident:
        inc = Incident(
            incident_id=str(uuid.uuid4()),
            incident_type=incident_type,
            line_code=line_code,
            station_code=station_code,
            track_segment_id=track_segment_id,
            start_time=start_time,
            duration_s=duration_s,
            description=description,
        )
        self.incidents.append(inc)
        self._active[inc.incident_id] = inc
        self._line_incidents[line_code].append(inc.incident_id)
        self.trigger(
            "incident_created",
            {
                "incident_id": inc.incident_id,
                "type": incident_type.value,
                "line_code": line_code,
                "time": start_time,
            },
        )
        return inc

    def resolve_incident(self, incident_id: str, current_time: float) -> None:
        inc = self._active.pop(incident_id, None)
        if inc:
            inc.resolved = True
            self._resolved.append(inc)
            self.trigger(
                "incident_resolved",
                {
                    "incident_id": incident_id,
                    "time": current_time,
                },
            )

    def get_active_incidents(self, current_time: float) -> list[Incident]:
        active: list[Incident] = []
        expired: list[str] = []
        for inc in self._active.values():
            if current_time >= inc.start_time + inc.duration_s:
                expired.append(inc.incident_id)
            elif current_time >= inc.start_time:
                active.append(inc)
        for eid in expired:
            self.resolve_incident(eid, current_time)
        return active

    def get_incidents_for_line(
        self, line_code: str, current_time: float
    ) -> list[Incident]:
        inc_ids = self._line_incidents.get(line_code, [])
        return [
            self.incidents[i]
            for i, _ in enumerate(self.incidents)
            if self.incidents[i].incident_id in inc_ids
            and not self.incidents[i].resolved
            and current_time >= self.incidents[i].start_time
            and current_time
            <= self.incidents[i].start_time + self.incidents[i].duration_s
        ]

    def is_line_affected(self, line_code: str, current_time: float) -> bool:
        return len(self.get_incidents_for_line(line_code, current_time)) > 0

    def get_stats(self) -> dict[str, Any]:
        return {
            "total": len(self.incidents),
            "active": len(self._active),
            "resolved": len(self._resolved),
            "by_type": {
                t.value: sum(1 for i in self.incidents if i.incident_type == t)
                for t in IncidentType
            },
        }
