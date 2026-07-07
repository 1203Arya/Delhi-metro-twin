from __future__ import annotations

from typing import Any

from ..types import Direction, PassengerAgent, SimulationConfig


class PassengerFlowModel:
    def __init__(self, config: SimulationConfig) -> None:
        self.config = config
        self._waiting_times: dict[int, float] = {}
        self._crowding_penalty_factor: float = 0.001

    def calc_dwell_time(self, boarding: int, alighting: int, base_dwell: float | None = None) -> float:
        base = base_dwell if base_dwell is not None else self.config.dwell_time_base_s
        total_movements = boarding + alighting
        return base + total_movements * self.config.dwell_time_per_passenger_s

    def calc_walk_time(self, from_platform: str, to_platform: str, station_data: dict[str, Any]) -> float:
        return 60.0

    def calc_transfer_time(self, from_line: str, to_line: str, station_code: str) -> float:
        return 120.0

    def calc_crowding_penalty(self, occupancy: int, capacity: int) -> float:
        if capacity <= 0:
            return 0.0
        ratio = occupancy / capacity
        if ratio <= 0.7:
            return 0.0
        return (ratio - 0.7) * self._crowding_penalty_factor * 1000.0

    def should_reroute_due_to_crowding(self, occupancy: int, capacity: int, threshold: float = 0.9) -> bool:
        if capacity <= 0:
            return False
        return (occupancy / capacity) >= threshold
