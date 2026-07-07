from __future__ import annotations

from collections import defaultdict
from typing import Any

from ..incidents.manager import IncidentManager
from ..network.graph import NetworkGraph
from ..schedule.timetable import Timetable
from ..types import Direction, Incident, TripPlan


class DynamicRouter:
    def __init__(
        self,
        network_graph: NetworkGraph,
        incident_manager: IncidentManager | None = None,
        timetable: Timetable | None = None,
    ) -> None:
        self.network = network_graph
        self.incident_manager = incident_manager
        self.timetable = timetable
        self._rerouted_trains: dict[str, TripPlan] = {}
        self._reroute_log: list[dict[str, Any]] = []
        self._line_blockages: dict[str, dict[str, bool]] = defaultdict(
            lambda: defaultdict(bool)
        )

    def check_incidents_affecting_line(
        self, line_code: str, current_time: float
    ) -> list[Incident]:
        if not self.incident_manager:
            return []
        active = self.incident_manager.get_active_incidents(current_time)
        return [inc for inc in active if inc.line_code == line_code]

    def is_track_blocked(self, line_code: str, station_code: str) -> bool:
        return self._line_blockages[line_code].get(station_code, False)

    def block_track(self, line_code: str, station_code: str) -> None:
        self._line_blockages[line_code][station_code] = True

    def unblock_track(self, line_code: str, station_code: str) -> None:
        self._line_blockages[line_code][station_code] = False

    def find_alternative_route(
        self,
        from_station: str,
        to_station: str,
        line_code: str,
        direction: Direction,
    ) -> list[tuple[str, str, str]]:
        alt_path = self.network.find_path(from_station, to_station, direction)
        if not alt_path:
            alt_path = self.network.find_transfer_path(from_station, to_station)
        return alt_path

    def reroute_train(
        self,
        train_id: str,
        original_plan: TripPlan,
        current_station: str,
        current_time: float,
    ) -> TripPlan | None:
        line_code = original_plan.line_code
        altitude = self.check_incidents_affecting_line(line_code, current_time)
        if not altitude:
            return None
        alt_path = self.find_alternative_route(
            current_station,
            original_plan.stops[-1].station_code,
            line_code,
            original_plan.direction,
        )
        if not alt_path:
            return None
        new_plan = TripPlan(
            train_id=train_id,
            line_code=line_code,
            direction=original_plan.direction,
            start_time=current_time,
            end_time=original_plan.end_time,
        )
        new_plan.stops = list(original_plan.stops)
        self._rerouted_trains[train_id] = new_plan
        self._reroute_log.append(
            {
                "time": current_time,
                "train_id": train_id,
                "from": current_station,
                "reason": f"incident on {line_code}",
            }
        )
        return new_plan

    def get_reroute_history(self) -> list[dict[str, Any]]:
        return list(self._reroute_log)
