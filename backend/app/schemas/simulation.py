from __future__ import annotations

from pydantic import BaseModel


class SimulationConfigSchema(BaseModel):
    duration_s: float = 3600.0
    dt_s: float = 1.0
    seed: int = 42
    n_passengers: int = 50000
    headway_target_s: float = 120.0
    snapshot_interval_s: float = 30.0


class SimulationState(BaseModel):
    running: bool
    paused: bool = False
    time_s: float
    trains: int
    active_trains: int
    passengers: int
    completed_passengers: int
    active_incidents: int


class SimulationMetrics(BaseModel):
    avg_headway_s: float = 0.0
    avg_dwell_s: float = 0.0
    avg_journey_time_s: float = 0.0
    avg_speed_mps: float = 0.0
    total_energy_wh: float = 0.0


class TrainPosition(BaseModel):
    train_id: str
    line_code: str
    direction: str
    status: str
    speed_kmh: float
    speed_mps: float
    position_m: float
    current_station: str
    next_station: str
    occupancy: int
    doors_open: bool
    block_id: str
