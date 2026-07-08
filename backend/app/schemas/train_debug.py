from __future__ import annotations

from pydantic import BaseModel


class TrainDebugPosition(BaseModel):
    train_id: str
    line_code: str
    line_name: str = ""
    direction: str
    direction_destination: str = ""
    status: str
    speed_kmh: float
    occupancy: int
    current_station: str  # Full human-readable name
    current_station_code: str = ""  # Internal code, supplementary only
    next_station: str  # Full human-readable name
    next_station_code: str = ""  # Internal code, supplementary only
    distance_to_next_m: float
    eta_s: float
    is_at_platform: bool
    doors_open: bool


class LineStationSummary(BaseModel):
    station_name: str = ""  # Full human-readable name
    station_code: str = ""  # Internal code, supplementary only
    at_platform: int = 0
    approaching: int = 0


class LineTrainGroup(BaseModel):
    line_code: str
    line_name: str = ""
    terminal_up: str = ""  # Full name of UP terminus
    terminal_down: str = ""  # Full name of DOWN terminus
    total_trains: int
    active_trains: list[TrainDebugPosition]
    station_summary: list[LineStationSummary]


class TrainPositionsResponse(BaseModel):
    generated_at_s: float
    ist_time: str
    service_period: str
    lines: list[LineTrainGroup]
    total_trains: int
    total_active: int
