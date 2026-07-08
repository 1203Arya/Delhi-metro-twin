from __future__ import annotations

from collections import defaultdict
from typing import Any

from ..types import Direction, ScheduledStop, SimulationConfig, TimetableEntry, TripPlan


def get_headway(time_s: float) -> float:
    hour = time_s / 3600.0
    if 8.0 <= hour <= 10.0 or 17.0 <= hour <= 20.0:
        return 300.0
    return 600.0


def get_demand_multiplier(time_s: float) -> float:
    hour = time_s / 3600.0
    if hour < 5.5 or hour >= 22.5:
        return 0.0
    if 8.0 <= hour <= 10.0 or 17.0 <= hour <= 20.0:
        return 3.0
    if 5.5 <= hour < 8.0 or 20.0 <= hour < 22.5:
        return 1.0
    return 0.6


SERVICE_START_S = 5.5 * 3600
SERVICE_END_S = 22.5 * 3600


class Timetable:
    def __init__(self, config: SimulationConfig) -> None:
        self.config = config
        self.entries: list[TimetableEntry] = []
        self.trip_plans: dict[str, TripPlan] = {}
        self._line_entries: dict[str, list[TimetableEntry]] = defaultdict(list)
        self._dispatched_entry_ids: set[int] = set()

    def add_entry(self, entry: TimetableEntry) -> None:
        self.entries.append(entry)
        self._line_entries[entry.line_code].append(entry)

    def add_trip_plan(self, train_id: str, plan: TripPlan) -> None:
        self.trip_plans[train_id] = plan

    def entries_for_line(self, line_code: str) -> list[TimetableEntry]:
        return sorted(
            self._line_entries.get(line_code, []), key=lambda e: e.departure_time
        )

    def entries_for_train(self, train_id: str) -> list[TimetableEntry]:
        return [e for e in self.entries if e.train_id == train_id]

    def next_departure(
        self, line_code: str, direction: Direction, after_time: float
    ) -> TimetableEntry | None:
        candidates = [
            e
            for e in self._line_entries.get(line_code, [])
            if e.direction == direction and e.departure_time > after_time
        ]
        return min(candidates, key=lambda e: e.departure_time) if candidates else None

    def get_trip_plan(self, train_id: str) -> TripPlan | None:
        return self.trip_plans.get(train_id)

    def dispatch_trains(
        self,
        current_time: float,
        line_code: str,
        direction: Direction,
        available_trains: list[str],
    ) -> list[tuple[str, TimetableEntry]]:
        dispatched: list[tuple[str, TimetableEntry]] = []
        for idx, entry in enumerate(self._line_entries.get(line_code, [])):
            if idx in self._dispatched_entry_ids:
                continue
            if (
                entry.direction == direction
                and entry.departure_time <= current_time
                and entry.is_depot_dispatch
                and available_trains
            ):
                train_id = available_trains.pop(0)
                dispatched.append((train_id, entry))
                self._dispatched_entry_ids.add(idx)
        return dispatched


class TimetableGenerator:
    def __init__(self, config: SimulationConfig) -> None:
        self.config = config

    def generate(
        self,
        line_code: str,
        stations: list[dict[str, Any]],
        direction: Direction,
    ) -> tuple[list[TimetableEntry], list[TripPlan]]:
        entries: list[TimetableEntry] = []
        plans: list[TripPlan] = []
        sorted_stations = sorted(stations, key=lambda s: s.get("sequence", 0))
        if direction == Direction.DOWN:
            sorted_stations = list(reversed(sorted_stations))
        travel_time_between_stops = 90.0
        station_ids = [s["code"] for s in sorted_stations]
        if not station_ids:
            return entries, plans

        t = SERVICE_START_S
        train_idx = 0
        while t < SERVICE_END_S:
            hw = get_headway(t)
            train_id = f"SCHED_{line_code}_{direction.value}_{train_idx:04d}"
            stops: list[ScheduledStop] = []
            dwell = self.config.dwell_time_base_s
            arrival_t = t
            for seq, station in enumerate(sorted_stations):
                is_last = seq == len(sorted_stations) - 1
                st = ScheduledStop(
                    station_id=station.get("id", station["code"]),
                    station_code=station["code"],
                    station_name=station.get("name", ""),
                    line_code=line_code,
                    sequence=seq,
                    arrival_time=arrival_t,
                    departure_time=arrival_t + (dwell if not is_last else 0.0),
                    min_stop_dwell_s=dwell,
                )
                stops.append(st)
                if not is_last:
                    arrival_t = st.departure_time + travel_time_between_stops
            plan = TripPlan(
                train_id=train_id,
                line_code=line_code,
                direction=direction,
                stops=stops,
                start_time=t,
                end_time=arrival_t,
            )
            plans.append(plan)
            for seq, st in enumerate(stops):
                entry = TimetableEntry(
                    train_id=train_id,
                    line_code=line_code,
                    direction=direction,
                    departure_time=st.departure_time,
                    from_station_code=st.station_code,
                    to_station_code=station_ids[seq + 1]
                    if seq + 1 < len(station_ids)
                    else st.station_code,
                    is_depot_dispatch=(seq == 0),
                    is_turnback=(seq == len(stops) - 1),
                )
                entries.append(entry)
            t += hw
            train_idx += 1
        return entries, plans
