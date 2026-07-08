from __future__ import annotations

import random
from collections import defaultdict
from typing import Any

from ..types import (
    Direction,
    PassengerAgent,
    PassengerState,
    PlatformQueue,
    SimulationConfig,
)


def get_demand_multiplier(time_s: float) -> float:
    hour = time_s / 3600.0
    if hour < 5.5 or hour >= 22.5:
        return 0.0
    if 8.0 <= hour <= 10.0 or 17.0 <= hour <= 20.0:
        return 3.0
    if 5.5 <= hour < 8.0 or 20.0 <= hour < 22.5:
        return 1.0
    return 0.6


class PassengerPopulation:
    def __init__(self, config: SimulationConfig) -> None:
        self.config = config
        self.agents: list[PassengerAgent] = []
        self.platform_queues: dict[str, dict[str, dict[str, PlatformQueue]]] = (
            defaultdict(lambda: defaultdict(lambda: defaultdict(PlatformQueue)))
        )
        self._rng = random.Random(config.seed)
        self._stats: dict[str, float] = {
            "total_passengers": 0.0,
            "completed": 0.0,
            "avg_wait_time": 0.0,
            "avg_ride_time": 0.0,
            "avg_journey_time": 0.0,
        }
        self._agent_counter: int = 0
        self._interchange_stations: set[str] = set()
        self._stations_list: list[str] = []
        self._station_data: dict[str, dict[str, Any]] = {}

    def setup_stations(
        self,
        stations: dict[str, dict[str, Any]],
        interchange_stations: dict[str, list[str]] | None = None,
    ) -> None:
        self._stations_list = list(stations.keys())
        self._station_data = stations
        if interchange_stations:
            self._interchange_stations = set(interchange_stations.keys())

    def generate(
        self,
        stations: dict[str, dict[str, Any]],
        lines: dict[str, dict[str, Any]],
        interchange_stations: dict[str, list[str]] | None = None,
        n_passengers: int | None = None,
    ) -> None:
        self.setup_stations(stations, interchange_stations)
        self.agents.clear()
        self._agent_counter = 0
        total_passengers = (
            n_passengers if n_passengers is not None else self.config.n_passengers
        )
        if total_passengers <= 0 or len(self._stations_list) < 2:
            self._stats["total_passengers"] = float(total_passengers)
            return

        station_codes = list(self._stations_list)
        for idx in range(total_passengers):
            origin = station_codes[idx % len(station_codes)]
            origin_stn = self._station_data.get(origin, {})
            origin_line = origin_stn.get("line_code", "")
            if not origin_line and lines:
                origin_line = next(iter(lines.keys()))
            destination_choices = [code for code in station_codes if code != origin]
            if not destination_choices:
                continue
            dest = destination_choices[self._rng.randrange(len(destination_choices))]
            dest_stn = self._station_data.get(dest, {})
            dest_line = dest_stn.get("line_code", "")
            if not dest_line and lines:
                dest_line = next(iter(lines.keys()))
            agent = PassengerAgent(
                id=self._agent_counter,
                origin_station_code=origin,
                destination_station_code=dest,
                origin_line_code=origin_line,
                destination_line_code=dest_line,
                start_time=0.0,
                path_stations=[origin, dest],
                path_lines=[origin_line, dest_line],
            )
            self._agent_counter += 1
            self.agents.append(agent)
        self._stats["total_passengers"] = float(len(self.agents))

    def generate_tick(self, current_time: float, dt: float) -> None:
        mult = get_demand_multiplier(current_time)
        if mult <= 0.0:
            return
        base_rate = self.config.n_passengers / 64800.0
        n_new = int(base_rate * mult * dt * len(self._stations_list) / 10.0)
        n_new = max(0, min(n_new, 200))
        if n_new == 0:
            return
        for _ in range(n_new):
            origin = self._rng.choice(self._stations_list)
            dest = self._rng.choice([s for s in self._stations_list if s != origin])
            orig_stn = self._station_data.get(origin, {})
            dest_stn = self._station_data.get(dest, {})
            origin_line = orig_stn.get("line_code", "")
            dest_line = dest_stn.get("line_code", "")
            if not origin_line or not dest_line:
                continue
            weight = 1.0
            if origin in self._interchange_stations:
                weight = 2.0
            if self._rng.random() * weight > 0.5 / max(mult, 0.1):
                continue
            path_stations = [origin, dest]
            path_lines = [origin_line, dest_line]
            agent = PassengerAgent(
                id=self._agent_counter,
                origin_station_code=origin,
                destination_station_code=dest,
                origin_line_code=origin_line,
                destination_line_code=dest_line,
                start_time=current_time,
                path_stations=path_stations,
                path_lines=path_lines,
            )
            self._agent_counter += 1
            self.agents.append(agent)

    def add_agent_to_queue(
        self, agent: PassengerAgent, line_code: str, direction: Direction
    ) -> None:
        station_q = self.platform_queues[agent.origin_station_code]
        if line_code not in station_q:
            station_q[line_code] = {}
        if direction.value not in station_q[line_code]:
            station_q[line_code][direction.value] = PlatformQueue(
                station_code=agent.origin_station_code,
                line_code=line_code,
                direction=direction,
            )
        station_q[line_code][direction.value].add_passenger(agent)
        agent.state = PassengerState.QUEUING

    def process_boarding(
        self,
        station_code: str,
        line_code: str,
        direction: Direction,
        capacity_available: int,
        current_time: float,
    ) -> list[PassengerAgent]:
        q = (
            self.platform_queues.get(station_code, {})
            .get(line_code, {})
            .get(direction.value)
        )
        if not q or not q.passengers:
            return []
        boarding = q.pop_boarding(capacity_available)
        for p in boarding:
            p.state = PassengerState.BOARDING
            p.board_time = current_time
        return boarding

    def process_alighting(
        self,
        train_passengers: list[PassengerAgent],
        station_code: str,
        current_time: float,
    ) -> tuple[list[PassengerAgent], list[PassengerAgent]]:
        alighting: list[PassengerAgent] = []
        remaining: list[PassengerAgent] = []
        for p in train_passengers:
            if p.destination_station_code == station_code:
                p.state = PassengerState.ALIGHTING
                p.alight_time = current_time
                p.total_ride_time += current_time - p.board_time
                p.state = PassengerState.COMPLETED
                self._stats["completed"] += 1.0
                alighting.append(p)
            else:
                remaining.append(p)
        return alighting, remaining

    def get_completed_count(self) -> int:
        return sum(1 for a in self.agents if a.completed)

    def get_queue_length(
        self, station_code: str, line_code: str, direction: Direction
    ) -> int:
        q = (
            self.platform_queues.get(station_code, {})
            .get(line_code, {})
            .get(direction.value)
        )
        return q.occupancy if q else 0

    def get_stats(self) -> dict[str, float]:
        completed = [a for a in self.agents if a.completed]
        if completed:
            waits = [c.total_wait_time for c in completed]
            rides = [c.total_ride_time for c in completed]
            journeys = [w + r for w, r in zip(waits, rides)]
            self._stats["avg_wait_time"] = sum(waits) / len(waits) if waits else 0.0
            self._stats["avg_ride_time"] = sum(rides) / len(rides) if rides else 0.0
            self._stats["avg_journey_time"] = (
                sum(journeys) / len(journeys) if journeys else 0.0
            )
        return dict(self._stats)
