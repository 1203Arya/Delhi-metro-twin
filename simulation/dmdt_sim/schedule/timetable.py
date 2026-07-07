from __future__ import annotations

from collections import defaultdict
from typing import Any

from ..types import Direction, ScheduledStop, SimulationConfig, TimetableEntry, TripPlan


class Timetable:
    def __init__(self, config: SimulationConfig) -> None:
        self.config = config
        self.entries: list[TimetableEntry] = []
        self.trip_plans: dict[str, TripPlan] = {}
        self._line_entries: dict[str, list[TimetableEntry]] = defaultdict(list)

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
        for entry in self._line_entries.get(line_code, []):
            if (
                entry.direction == direction
                and abs(entry.departure_time - current_time) < self.config.dt_s
            ):
                if available_trains and entry.is_depot_dispatch:
                    # check if entry.departure_time <= current_time <= entry.departure_time + self.config.dt_s
                    pass
        for entry in self._line_entries.get(line_code, []):
            if (
                entry.direction == direction
                and entry.departure_time
                <= current_time
                <= entry.departure_time + self.config.dt_s
            ):
                if entry.is_depot_dispatch and available_trains:
                    train_id = available_trains.pop(0)
                    dispatched.append((train_id, entry))
        return dispatched


class TimetableGenerator:
    def __init__(self, config: SimulationConfig) -> None:
        self.config = config

    def generate(
        self,
        line_code: str,
        stations: list[dict[str, Any]],
        direction: Direction,
        start_time: float = 0.0,
        total_duration_s: float | None = None,
        headway_s: float | None = None,
    ) -> tuple[list[TimetableEntry], list[TripPlan]]:
        duration = (
            total_duration_s if total_duration_s is not None else self.config.duration_s
        )
        hw = headway_s if headway_s is not None else self.config.headway_target_s
        entries: list[TimetableEntry] = []
        plans: list[TripPlan] = []
        sorted_stations = sorted(stations, key=lambda s: s.get("sequence", 0))
        if direction == Direction.DOWN:
            sorted_stations = list(reversed(sorted_stations))
        travel_time_between_stops = 90.0
        station_ids = [s["code"] for s in sorted_stations]
        if not station_ids:
            return entries, plans
        t = start_time
        train_idx = 0
        while t < duration:
            train_id = f"{line_code}_{direction.value}_{train_idx:04d}"
            stops: list[ScheduledStop] = []
            arrival_t = t
            for seq, station in enumerate(sorted_stations):
                st = ScheduledStop(
                    station_id=station.get("id", station["code"]),
                    station_code=station["code"],
                    station_name=station.get("name", ""),
                    line_code=line_code,
                    sequence=seq,
                    arrival_time=arrival_t,
                    departure_time=arrival_t + self.config.dwell_time_base_s,
                    min_stop_dwell_s=self.config.dwell_time_base_s,
                )
                stops.append(st)
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
                    is_depot_dispatch=(seq == 0 and train_idx % 3 == 0),
                    is_turnback=(seq == len(stops) - 1),
                )
                entries.append(entry)
            t += hw
            train_idx += 1
        return entries, plans
