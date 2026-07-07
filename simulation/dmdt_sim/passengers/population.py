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

    def generate(
        self,
        stations: dict[str, dict[str, Any]],
        lines: dict[str, dict[str, Any]],
        interchange_stations: dict[str, list[str]] | None = None,
        n_passengers: int | None = None,
    ) -> None:
        count = n_passengers if n_passengers is not None else self.config.n_passengers
        station_codes = list(stations.keys())
        if not station_codes:
            return
        interchange = interchange_stations or {}
        for i in range(count):
            origin = self._rng.choice(station_codes)
            dest = self._rng.choice([s for s in station_codes if s != origin])
            orig_stn = stations[origin]
            dest_stn = stations[dest]
            origin_line = orig_stn.get("line_code", "")
            dest_line = dest_stn.get("line_code", "")
            path_stations = [origin, dest]
            path_lines = [origin_line, dest_line]
            if (
                origin_line != dest_line
                and origin in interchange
                and any(lc in interchange[origin] for lc in [dest_line])
            ):
                path_lines = [origin_line, dest_line]
            start_time = self._rng.uniform(0, self.config.duration_s * 0.8)
            agent = PassengerAgent(
                id=i,
                origin_station_code=origin,
                destination_station_code=dest,
                origin_line_code=origin_line,
                destination_line_code=dest_line,
                start_time=start_time,
                path_stations=path_stations,
                path_lines=path_lines,
            )
            self.agents.append(agent)
        self._stats["total_passengers"] = float(len(self.agents))

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
