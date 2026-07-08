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
    depot_trains: int = 0
    passengers: int
    completed_passengers: int
    active_incidents: int
    service_period: str = ""
    ist_time: str = ""
    service_start: str = ""
    service_end: str = ""


class SimulationMetrics(BaseModel):
    avg_headway_s: float = 0.0
    avg_dwell_s: float = 0.0
    avg_journey_time_s: float = 0.0
    avg_speed_mps: float = 0.0
    total_energy_wh: float = 0.0


class TrainPosition(BaseModel):
    train_id: str
    line_code: str
    line_name: str = ""
    direction: str
    direction_destination: str = ""
    status: str
    speed_kmh: float
    speed_mps: float
    position_m: float
    current_station: str  # station code; use current_station_name for display
    current_station_name: str = ""
    next_station: str  # station code; use next_station_name for display
    next_station_name: str = ""
    occupancy: int
    doors_open: bool
    block_id: str


class DisruptRequest(BaseModel):
    station_code: str
    line_code: str = ""
    incident_type: str = "emergency_brake"
    duration_s: float = 300.0


class ApproachInfo(BaseModel):
    bearing: float
    line_code: str
    direction: str


class StationApproachData(BaseModel):
    id: str
    code: str
    name: str
    line_code: str
    latitude: float
    longitude: float
    platforms: int
    has_junction: bool


class ApproachingTrainsResponse(BaseModel):
    station_code: str
    station: StationApproachData
    trains: list[TrainPosition]
    approaches: list[ApproachInfo]
