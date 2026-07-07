from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any


class Direction(str, Enum):
    UP = "up"
    DOWN = "down"

    def opposite(self) -> Direction:
        return Direction.DOWN if self == Direction.UP else Direction.UP


class TrainStatus(str, Enum):
    IN_DEPOT = "in_depot"
    DEPARTING = "departing"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    DOOR_OPEN = "door_open"
    DOOR_CLOSE = "door_close"
    TURNBACK = "turnback"
    MAINTENANCE = "maintenance"
    EMERGENCY_BRAKE = "emergency_brake"
    INCIDENT_HALT = "incident_halt"


class MovementAuthority(str, Enum):
    MOVEMENT = "movement"
    RESTRICTED = "restricted"
    STOP = "stop"


class IncidentType(str, Enum):
    EMERGENCY_BRAKE = "emergency_brake"
    TRACK_CLOSURE = "track_closure"
    PLATFORM_CLOSURE = "platform_closure"
    SIGNAL_FAILURE = "signal_failure"
    TRAIN_FAILURE = "train_failure"


class PassengerState(str, Enum):
    WAITING_ORIGIN = "waiting_origin"
    WALKING_TO_PLATFORM = "walking_to_platform"
    QUEUING = "queuing"
    BOARDING = "boarding"
    ON_TRAIN = "on_train"
    ALIGHTING = "alighting"
    TRANSFERRING = "transferring"
    COMPLETED = "completed"


@dataclass
class Position:
    track_segment_id: str = ""
    distance_from_start_m: float = 0.0
    latitude: float = 0.0
    longitude: float = 0.0


@dataclass
class MotionState:
    speed_mps: float = 0.0
    acceleration_mps2: float = 0.0
    position_m: float = 0.0
    distance_travelled_m: float = 0.0
    cumulative_energy_wh: float = 0.0


@dataclass
class TrainSpec:
    train_class_id: str
    name: str
    max_speed_kmh: float
    acceleration_ms2: float
    deceleration_ms2: float
    length_m: float
    capacity_seated: int
    capacity_standing: int
    max_power_kw: float = 3000.0
    mass_tonnes: float = 320.0
    rotational_inertia_factor: float = 1.08
    drag_coefficient: float = 0.5
    frontal_area_m2: float = 10.0
    air_density_kgm3: float = 1.225
    rolling_resistance_N: float = 8000.0
    auxiliary_power_kw: float = 100.0
    regen_efficiency: float = 0.85
    jerk_limit_mps3: float = 0.8
    door_open_time_s: float = 20.0
    door_close_time_s: float = 5.0
    min_standby_time_s: float = 15.0

    @property
    def max_capacity(self) -> int:
        return self.capacity_seated + self.capacity_standing


@dataclass
class ScheduledStop:
    station_id: str
    station_code: str
    station_name: str
    line_code: str
    sequence: int
    arrival_time: float
    departure_time: float
    min_stop_dwell_s: float = 20.0
    platform_side: str = "left"


@dataclass
class TripPlan:
    train_id: str
    line_code: str
    direction: Direction
    stops: list[ScheduledStop] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0
    depot_origin: str | None = None
    depot_return: str | None = None

    @property
    def total_stops(self) -> int:
        return len(self.stops)


@dataclass
class PassengerAgent:
    id: int
    origin_station_code: str
    destination_station_code: str
    origin_line_code: str
    destination_line_code: str
    start_time: float
    state: PassengerState = PassengerState.WAITING_ORIGIN
    path_stations: list[str] = field(default_factory=list)
    path_lines: list[str] = field(default_factory=list)
    current_station_idx: int = 0
    current_line_idx: int = 0
    board_time: float = 0.0
    alight_time: float = 0.0
    total_walk_time: float = 0.0
    total_wait_time: float = 0.0
    total_ride_time: float = 0.0
    is_transfer: bool = False

    @property
    def completed(self) -> bool:
        return self.state == PassengerState.COMPLETED

    @property
    def needs_transfer(self) -> bool:
        return len(self.path_lines) > 1


@dataclass
class PlatformQueue:
    station_code: str
    line_code: str
    direction: Direction
    passengers: list[PassengerAgent] = field(default_factory=list)
    occupancy: int = 0

    def add_passenger(self, p: PassengerAgent) -> None:
        self.passengers.append(p)
        self.occupancy = len(self.passengers)

    def pop_boarding(self, capacity_available: int) -> list[PassengerAgent]:
        boarding = self.passengers[:capacity_available]
        self.passengers = self.passengers[capacity_available:]
        self.occupancy = len(self.passengers)
        return boarding


@dataclass
class TrackOccupation:
    train_id: str
    track_segment_id: str
    entry_time: float
    direction: Direction
    head_position_m: float = 0.0
    tail_position_m: float = 0.0


@dataclass
class SignalBlock:
    block_id: str
    line_code: str
    direction: Direction
    from_station_id: str
    to_station_id: str
    length_m: float
    is_occupied: bool = False
    occupying_train_id: str | None = None
    speed_limit_kmh: float = 80.0
    authority: MovementAuthority = MovementAuthority.MOVEMENT


@dataclass
class Incident:
    incident_id: str = ""
    incident_type: IncidentType = IncidentType.EMERGENCY_BRAKE
    line_code: str = ""
    station_code: str = ""
    track_segment_id: str = ""
    start_time: float = 0.0
    duration_s: float = 60.0
    affected_trains: list[str] = field(default_factory=list)
    resolved: bool = False
    description: str = ""


@dataclass
class TimetableEntry:
    train_id: str
    line_code: str
    direction: Direction
    departure_time: float
    from_station_code: str
    to_station_code: str
    is_turnback: bool = False
    is_depot_dispatch: bool = False
    is_maintenance: bool = False


@dataclass
class MaintenanceSlot:
    train_id: str
    start_time: float
    end_time: float
    depot_name: str
    description: str = "routine inspection"


@dataclass
class SimulationConfig:
    dt_s: float = 1.0
    seed: int = 42
    duration_s: float = 3600.0
    n_passengers: int = 50000
    headway_target_s: float = 120.0
    min_headway_s: float = 90.0
    max_trains_per_line: int = 30
    dwell_time_base_s: float = 20.0
    dwell_time_per_passenger_s: float = 0.003
    turnback_time_s: float = 60.0
    depot_dispatch_interval_s: float = 300.0
    maintenance_interval_s: float = 7200.0
    incident_check_interval_s: float = 10.0
    reroute_check_interval_s: float = 30.0


@dataclass
class SimulationSnapshot:
    time_s: float
    trains: list[dict[str, Any]] = field(default_factory=list)
    passengers: list[dict[str, Any]] = field(default_factory=list)
    incidents: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)
