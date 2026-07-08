from __future__ import annotations

import random
import time
from collections import defaultdict
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from .depot.yard import DepotYard
from .events.bus import EventBus
from .incidents.manager import IncidentManager
from .network.graph import NetworkGraph
from .passengers.flow import PassengerFlowModel
from .passengers.population import PassengerPopulation, get_demand_multiplier
from .perf.metrics import MetricsCollector
from .physics.train import TrainMotionModel, DrivingMode
from .routing.router import DynamicRouter
from .schedule.maintenance import MaintenanceScheduler
from .schedule.timetable import (
    Timetable,
    TimetableGenerator,
    SERVICE_START_S,
    SERVICE_END_S,
    get_headway,
)
from .signalling.block import BlockManager
from .signalling.cbtc import CBTCController
from .types import (
    Direction,
    IncidentType,
    MovementAuthority,
    PassengerState,
    SimulationConfig,
    SimulationSnapshot,
    TrainSpec,
    TrainStatus,
    TripPlan,
)


def ist_seconds() -> float:
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    return now.hour * 3600.0 + now.minute * 60.0 + now.second + now.microsecond / 1_000_000.0


def get_service_period(t_s: float) -> str:
    h = t_s / 3600.0
    if h < 5.0:
        return "pre_service"
    if h < 5.5:
        return "startup"
    if h < 8.0:
        return "early_service"
    if h < 10.0:
        return "morning_peak"
    if h < 17.0:
        return "midday"
    if h < 20.0:
        return "evening_peak"
    if h < 22.0:
        return "late_service"
    if h < 23.5:
        return "wind_down"
    return "post_service"


class SimulatedTrain:
    def __init__(
        self,
        train_id: str,
        spec: TrainSpec,
        line_code: str,
        direction: Direction,
        config: SimulationConfig,
    ) -> None:
        self.train_id = train_id
        self.spec = spec
        self.line_code = line_code
        self.direction = direction
        self.config = config
        self.status = TrainStatus.IN_DEPOT
        self.motion = TrainMotionModel(spec)
        self.current_station_index: int = 0
        self.current_station_code: str = ""
        self.next_station_code: str = ""
        self.distance_to_next_station_m: float = 0.0
        self.position_m: float = 0.0
        self.block_id: str = ""
        self.passengers_on_board: list[Any] = []
        self.occupancy: int = 0
        self.dwell_timer: float = 0.0
        self.is_at_platform: bool = False
        self.doors_open: bool = False
        self.doors_timer: float = 0.0
        self.turnback_timer: float = 0.0
        self.emergency_brake_active: bool = False
        self.incident_hold: bool = False
        self.arrival_time_at_station: float = 0.0
        self.total_distance_m: float = 0.0
        self.total_energy_wh: float = 0.0
        self.speed_samples: list[float] = []
        self._just_turned_back: bool = False
        self._arrivals_at_terminus: int = 0
        self._should_return_to_depot: bool = False
        self.max_trips: int = 8
        self._rng = random.Random(config.seed + hash(train_id) % 10000)

    @property
    def speed_mps(self) -> float:
        return self.motion.state.speed_mps

    @property
    def speed_kmh(self) -> float:
        return self.motion.speed_kmh

    @property
    def at_destination(self) -> bool:
        return self.status in (TrainStatus.TURNBACK, TrainStatus.MAINTENANCE)

    def update(
        self, dt: float, gradient_pct: float = 0.0, speed_limit_mps: float = 80.0
    ) -> None:
        if self.status == TrainStatus.RUNNING:
            if self.emergency_brake_active:
                self.motion.emergency_brake(dt, gradient_pct)
                if self.motion.state.speed_mps < 0.01:
                    self.status = TrainStatus.EMERGENCY_BRAKE
            elif self.incident_hold:
                self.motion.brake(dt, gradient_pct)
                if self.motion.state.speed_mps < 0.01:
                    self.status = TrainStatus.INCIDENT_HALT
            elif (
                self.motion.mode == DrivingMode.BRAKING
                and self.motion.state.speed_mps < 0.01
            ):
                self.motion.state.speed_mps = 0.0
                self.status = TrainStatus.STOPPED
            else:
                target = min(speed_limit_mps, self.motion.max_speed_mps)
                if self.distance_to_next_station_m > 0:
                    brake_dist = self.motion.brake_distance()
                    if self.distance_to_next_station_m <= brake_dist:
                        self.motion.brake_to_stop(
                            dt, self.distance_to_next_station_m, gradient_pct
                        )
                    else:
                        self.motion.accelerate(dt, gradient_pct, target)
                else:
                    self.motion.accelerate(dt, gradient_pct, target)
                self.position_m += self.motion.state.speed_mps * dt
                self.total_distance_m += self.motion.state.speed_mps * dt
                self.total_energy_wh += self.motion.state.cumulative_energy_wh
                self.speed_samples.append(self.motion.state.speed_mps)
                self.distance_to_next_station_m -= self.motion.state.speed_mps * dt
        elif self.status == TrainStatus.STOPPED and self.is_at_platform:
            self._handle_dwell(dt)
        elif self.status == TrainStatus.DOOR_OPEN:
            self._handle_doors(dt)
        elif self.status == TrainStatus.TURNBACK:
            self.turnback_timer -= dt
            if self.turnback_timer <= 0:
                self.direction = self.direction.opposite()
                self.status = TrainStatus.RUNNING
                self._just_turned_back = True
                self.is_at_platform = False
        elif self.status == TrainStatus.EMERGENCY_BRAKE:
            if not self.emergency_brake_active:
                self.status = TrainStatus.STOPPED
        elif self.status == TrainStatus.INCIDENT_HALT:
            if not self.incident_hold:
                self.status = TrainStatus.RUNNING

    def _handle_dwell(self, dt: float) -> None:
        self.dwell_timer -= dt
        if self.dwell_timer <= 0:
            self.status = TrainStatus.DOOR_OPEN
            self.doors_open = True
            self.doors_timer = self.spec.door_open_time_s

    def _handle_doors(self, dt: float) -> None:
        self.doors_timer -= dt
        if self.doors_timer <= 0:
            self.doors_open = False
            self.is_at_platform = False
            self.status = TrainStatus.RUNNING

    def arrive_at_station(self, station_code: str, dwell_time_s: float) -> None:
        self.current_station_code = station_code
        self.is_at_platform = True
        self.status = TrainStatus.STOPPED
        self.dwell_timer = dwell_time_s
        self.arrival_time_at_station = 0.0
        self.distance_to_next_station_m = 0.0
        self.motion.state.speed_mps = 0.0
        self.motion.state.acceleration_mps2 = 0.0
        self.motion.mode = DrivingMode.STOPPED

    def depart(self) -> None:
        self.status = TrainStatus.RUNNING
        self.is_at_platform = False
        self.doors_open = False

    def start_emergency_brake(self) -> None:
        self.emergency_brake_active = True

    def release_emergency_brake(self) -> None:
        self.emergency_brake_active = False
        self.status = TrainStatus.RUNNING

    def to_dict(self) -> dict[str, Any]:
        if self.status == TrainStatus.RUNNING and self.speed_mps > 0:
            eta_s = self.distance_to_next_station_m / self.speed_mps
        elif self.status == TrainStatus.STOPPED and self.is_at_platform:
            eta_s = max(0.0, self.dwell_timer + (self.spec.door_open_time_s if not self.doors_open else self.doors_timer))
        elif self.status == TrainStatus.DOOR_OPEN:
            eta_s = max(0.0, self.doors_timer)
        elif self.status == TrainStatus.TURNBACK:
            eta_s = max(0.0, self.turnback_timer)
        else:
            eta_s = 0.0
        return {
            "train_id": self.train_id,
            "line_code": self.line_code,
            "direction": self.direction.value,
            "status": self.status.value,
            "speed_mps": self.speed_mps,
            "speed_kmh": self.speed_kmh,
            "position_m": self.position_m,
            "current_station": self.current_station_code,
            "next_station": self.next_station_code,
            "distance_to_next_m": self.distance_to_next_station_m,
            "eta_s": round(eta_s, 1),
            "is_at_platform": self.is_at_platform,
            "occupancy": self.occupancy,
            "doors_open": self.doors_open,
            "mode": self.motion.mode.name.lower(),
            "block_id": self.block_id,
            "total_distance_m": self.total_distance_m,
            "total_energy_wh": self.total_energy_wh,
            "trips_completed": self._arrivals_at_terminus,
            "max_trips": self.max_trips,
        }


class SimulationEngine:
    def __init__(self, config: SimulationConfig | None = None) -> None:
        self.config = config or SimulationConfig()
        self.network = NetworkGraph()
        self.block_manager = BlockManager()
        self.cbtc = CBTCController(self.block_manager)
        self.depot_yard = DepotYard()
        self.timetable = Timetable(self.config)
        self.timetable_gen = TimetableGenerator(self.config)
        self.maintenance = MaintenanceScheduler(self.config)
        self.passenger_pop = PassengerPopulation(self.config)
        self.passenger_flow = PassengerFlowModel(self.config)
        self.incident_manager = IncidentManager(self.config)
        self.event_bus = EventBus()
        self.metrics = MetricsCollector()
        self.router = DynamicRouter(self.network, self.incident_manager, self.timetable)
        self.trains: dict[str, SimulatedTrain] = {}
        self._line_trains: dict[str, list[str]] = defaultdict(list)
        self._rng = random.Random(self.config.seed)
        self.current_time: float = 0.0
        self.service_period: str = "pre_service"
        self.is_running: bool = False
        self.snapshot_interval_s: float = 30.0
        self._last_snapshot_time: float = 0.0
        self._train_id_counter: int = 0
        self._last_step_wall: float = time.monotonic()
        self._last_incident_spawn: float = 0.0

    def load_network(self, network_data: dict[str, Any]) -> None:
        # Support flat top-level arrays AND nested-per-line formats
        lines = network_data.get("lines", [])
        for line in lines:
            self.network.add_line(line)
        stations = network_data.get("stations", [])
        if not stations:
            for line in lines:
                for stn in line.get("stations", []):
                    stn.setdefault("line_code", line.get("code", ""))
                    stations.append(stn)
        for stn in stations:
            self.network.add_station(stn)
        segments = network_data.get("track_segments", [])
        if not segments:
            for line in lines:
                for seg in line.get("track_segments", []):
                    seg.setdefault("line_code", line.get("code", ""))
                    segments.append(seg)
        for seg in segments:
            self.network.add_track_segment(seg)
        depots = network_data.get("depots", [])
        if not depots:
            for line in lines:
                lc = line.get("code", "")
                for dp in line.get("depots", []):
                    dp.setdefault("line_code", lc)
                    dp.setdefault("display_name", dp.get("name", f"depot_{lc}"))
                    dp["name"] = f"depot_{lc}"
                    depots.append(dp)
        for dp in depots:
            self.network.add_depot(dp)
            self.depot_yard.add_depot(dp)
        for pf in network_data.get("platforms", []):
            self.network.add_platform(pf)
        for jnc in network_data.get("junctions", []):
            self.network.add_junction(jnc)
        for tc in network_data.get("train_classes", []):
            self.network.add_train_class(tc)
        self.network.build_graph()
        self.block_manager.build_from_network(network_data)

    def load_seed_data(self, seed_data: dict[str, Any]) -> None:
        if "train_classes" in seed_data:
            for tc in seed_data["train_classes"]:
                self.network.add_train_class(tc)

    def _get_default_spec(self) -> TrainSpec:
        return TrainSpec(
            train_class_id="std",
            name="Standard",
            max_speed_kmh=80.0,
            acceleration_ms2=0.8,
            deceleration_ms2=0.9,
            length_m=200.0,
            capacity_seated=350,
            capacity_standing=650,
        )

    def _estimate_trains_for_line(self, line_code: str) -> int:
        stations = self.network.get_stations_on_line(line_code)
        if not stations:
            return 0
        n_stations = len(stations)
        trip_duration_s = n_stations * 90.0
        trips_per_train = max(2, int(self.config.duration_s / trip_duration_s / 2.0))
        trips_per_train = min(trips_per_train, 10)
        total_trips_per_dir = (SERVICE_END_S - SERVICE_START_S) / 480.0
        n_trains = max(5, int(total_trips_per_dir / max(trips_per_train, 1)) + 5)
        return min(n_trains, self.config.max_trains_per_line)

    def _get_trips_per_train(self) -> int:
        return 8

    def initialize(self) -> None:
        self.trains.clear()
        self._line_trains.clear()
        self._train_id_counter = 0
        self.current_time = ist_seconds()
        self.service_period = get_service_period(self.current_time)
        self._last_step_wall = time.monotonic()
        self._last_incident_spawn = self.current_time
        self.incident_manager = IncidentManager(self.config)
        self.timetable = Timetable(self.config)
        self.event_bus = EventBus()
        self.router = DynamicRouter(self.network, self.incident_manager, self.timetable)
        self._create_all_trains()
        self._generate_daily_timetable()
        interchange = self.network.get_interchange_stations()
        self.passenger_pop.setup_stations(self.network.stations, interchange)

    def _create_all_trains(self) -> None:
        for line_code in self.network.lines:
            line_stations = self.network.get_stations_on_line(line_code)
            if not line_stations:
                continue
            n_trains = self._estimate_trains_for_line(line_code)
            for i in range(n_trains):
                train_id = f"TRAIN_{line_code}_{self._train_id_counter:04d}"
                spec = self._get_default_spec()
                train = SimulatedTrain(
                    train_id=train_id,
                    spec=spec,
                    line_code=line_code,
                    direction=Direction.UP if i % 2 == 0 else Direction.DOWN,
                    config=self.config,
                )
                depot_key = f"depot_{line_code}"
                if depot_key in self.depot_yard.depots:
                    self.depot_yard.register_train(train_id, spec, depot_key)
                train.status = TrainStatus.IN_DEPOT
                train.max_trips = self._get_trips_per_train()
                self.trains[train_id] = train
                self._line_trains[line_code].append(train_id)
                self.maintenance.register_train(train_id, 0.0)
                self._train_id_counter += 1

    def _generate_daily_timetable(self) -> None:
        for line_code in self.network.lines:
            stations = self.network.get_stations_on_line(line_code)
            if not stations:
                continue
            for direction in (Direction.UP, Direction.DOWN):
                entries, plans = self.timetable_gen.generate(
                    line_code,
                    stations,
                    direction,
                )
                for plan in plans:
                    self.timetable.add_trip_plan(plan.train_id, plan)
                for entry in entries:
                    self.timetable.add_entry(entry)

    def _dispatch_trains(self) -> None:
        sp = self.service_period
        if sp in ("pre_service", "post_service"):
            return
        for line_code in self.network.lines:
            depot_key = f"depot_{line_code}"
            for direction in (Direction.UP, Direction.DOWN):
                available = self.depot_yard.get_available_trains(depot_key)
                if not available:
                    continue
                dispatched = self.timetable.dispatch_trains(
                    self.current_time, line_code, direction, available
                )
                for train_id, entry in dispatched:
                    train = self.trains.get(train_id)
                    if not train:
                        continue
                    stations = self.network.get_stations_on_line(line_code)
                    if not stations:
                        continue
                    self.depot_yard.remove_from_yard(train_id, depot_key)
                    plan = self.timetable.get_trip_plan(entry.train_id)
                    if plan and entry.departure_time < self.current_time:
                        self._position_train_from_schedule(
                            train, plan, stations, line_code, direction
                        )
                    else:
                        train.status = TrainStatus.DEPARTING
                        if direction == Direction.UP:
                            train.current_station_index = 0
                            train.current_station_code = stations[0]["code"]
                            train.next_station_code = stations[1]["code"] if len(stations) > 1 else stations[0]["code"]
                        else:
                            train.current_station_index = len(stations) - 1
                            train.current_station_code = stations[-1]["code"]
                            train.next_station_code = stations[-2]["code"] if len(stations) > 1 else stations[-1]["code"]
                        train.position_m = 0.0
                        train.distance_to_next_station_m = 500.0
                        train.direction = direction
                        train._arrivals_at_terminus = 0
                        train.status = TrainStatus.RUNNING

    def _position_train_from_schedule(
        self,
        train: SimulatedTrain,
        plan: TripPlan,
        stations: list[dict[str, Any]],
        line_code: str,
        direction: Direction,
    ) -> None:
        ts = sorted(stations, key=lambda s: s.get("sequence", 0))
        n = len(ts)
        if n < 2:
            return
        forward_codes = [s["code"] for s in ts]
        reverse_codes = list(reversed(forward_codes))

        trip_dur = plan.end_time - plan.start_time
        turnback = self.config.turnback_time_s
        cycle_dur = trip_dur * 2 + turnback

        elapsed = self.current_time - plan.start_time
        if elapsed < 0:
            elapsed = 0.0
        cycle_t = elapsed % cycle_dur

        fwd = cycle_t < trip_dur
        rev = cycle_t >= trip_dur + turnback
        if fwd:
            codes = forward_codes
            effective_dir = direction
            rel_t = cycle_t
        elif rev:
            codes = reverse_codes
            effective_dir = direction.opposite()
            rel_t = cycle_t - trip_dur - turnback
        else:
            term_code = forward_codes[-1]
            train.current_station_index = n - 1
            train.current_station_code = term_code
            train.next_station_code = term_code
            train.distance_to_next_station_m = 0.0
            train.position_m = 0.0
            train.direction = direction.opposite()
            train._arrivals_at_terminus = 0
            train.is_at_platform = True
            train.motion.state.speed_mps = 0.0
            train.motion.state.acceleration_mps2 = 0.0
            train.motion.mode = DrivingMode.STOPPED
            train.status = TrainStatus.TURNBACK
            train.turnback_timer = turnback - (cycle_t - trip_dur)
            return

        stop_t = 0.0
        seg_dur = 90.0
        dwell_dur = plan.stops[0].min_stop_dwell_s if plan.stops else self.config.dwell_time_base_s
        for i in range(len(codes) - 1):
            seg_start = stop_t + dwell_dur
            seg_end = seg_start + seg_dur
            if seg_start <= rel_t < seg_end:
                progress = (rel_t - seg_start) / seg_dur if seg_dur > 0 else 0.0
                track_len = self._track_distance(line_code, codes[i], codes[i + 1])
                train.current_station_index = i if effective_dir == direction else n - 1 - i
                train.current_station_code = codes[i]
                train.next_station_code = codes[i + 1]
                train.distance_to_next_station_m = track_len * (1.0 - progress)
                train.position_m = track_len * progress
                train.direction = effective_dir
                train._arrivals_at_terminus = i if effective_dir == direction.opposite() else 0
                train.is_at_platform = False
                train.motion.state.speed_mps = 22.0
                train.motion.state.acceleration_mps2 = 0.0
                train.motion.mode = DrivingMode.CRUISING
                train.status = TrainStatus.RUNNING
                return
            if stop_t <= rel_t < seg_start:
                remaining = max(0.0, seg_start - rel_t)
                train.current_station_index = i if effective_dir == direction else n - 1 - i
                train.current_station_code = codes[i]
                train.next_station_code = codes[i + 1]
                train.distance_to_next_station_m = 0.0
                train.position_m = 0.0
                train.direction = effective_dir
                train._arrivals_at_terminus = 0
                train.is_at_platform = True
                train.dwell_timer = remaining
                train.motion.state.speed_mps = 0.0
                train.motion.state.acceleration_mps2 = 0.0
                train.motion.mode = DrivingMode.STOPPED
                train.status = TrainStatus.STOPPED
                return
            stop_t = seg_end + dwell_dur

        last_code = codes[-1]
        train.current_station_index = n - 1 if effective_dir == Direction.UP else 0
        train.current_station_code = last_code
        train.next_station_code = last_code
        train.distance_to_next_station_m = 0.0
        train.position_m = 0.0
        train.direction = effective_dir
        train._arrivals_at_terminus = 0
        train.is_at_platform = True
        train.motion.state.speed_mps = 0.0
        train.motion.state.acceleration_mps2 = 0.0
        train.motion.mode = DrivingMode.STOPPED
        train.status = TrainStatus.STOPPED

    def check_incidents(self) -> None:
        active = self.incident_manager.get_active_incidents(self.current_time)
        for inc in active:
            if inc.incident_type == IncidentType.EMERGENCY_BRAKE:
                for train_id in self._line_trains.get(inc.line_code, []):
                    train = self.trains.get(train_id)
                    if train and train.status == TrainStatus.RUNNING:
                        train.start_emergency_brake()
            elif inc.incident_type in (
                IncidentType.TRACK_CLOSURE,
                IncidentType.PLATFORM_CLOSURE,
            ):
                self.router.block_track(inc.line_code, inc.station_code)
                for train_id in self._line_trains.get(inc.line_code, []):
                    train = self.trains.get(train_id)
                    if train and train.current_station_code == inc.station_code:
                        train.incident_hold = True
                        train.status = TrainStatus.INCIDENT_HALT

    def resolve_incidents(self) -> None:
        for inc in list(self.incident_manager._active.values()):
            if self.current_time >= inc.start_time + inc.duration_s:
                self.incident_manager.resolve_incident(
                    inc.incident_id, self.current_time
                )
                if inc.incident_type == IncidentType.EMERGENCY_BRAKE:
                    for train_id in self._line_trains.get(inc.line_code, []):
                        train = self.trains.get(train_id)
                        if train:
                            train.release_emergency_brake()
                else:
                    self.router.unblock_track(inc.line_code, inc.station_code)
                    for train_id in self._line_trains.get(inc.line_code, []):
                        train = self.trains.get(train_id)
                        if train:
                            train.incident_hold = False
                            if train.status == TrainStatus.INCIDENT_HALT:
                                train.status = TrainStatus.RUNNING

    def process_station_stops(self) -> None:
        for train in self.trains.values():
            if train.status != TrainStatus.RUNNING:
                continue
            if train.distance_to_next_station_m <= 2.0:
                stations = self.network.get_stations_on_line(train.line_code)
                if not stations:
                    continue
                if train.direction == Direction.UP:
                    next_idx = train.current_station_index + 1
                    if next_idx >= len(stations):
                        train.status = TrainStatus.TURNBACK
                        train.turnback_timer = self.config.turnback_time_s
                        train._arrivals_at_terminus += 1
                        train._should_return_to_depot = train._arrivals_at_terminus >= train.max_trips
                        continue
                    station = stations[next_idx]
                    train.current_station_index = next_idx
                else:
                    next_idx = train.current_station_index - 1
                    if next_idx < 0:
                        train.status = TrainStatus.TURNBACK
                        train.turnback_timer = self.config.turnback_time_s
                        train._arrivals_at_terminus += 1
                        train._should_return_to_depot = train._arrivals_at_terminus >= train.max_trips
                        continue
                    station = stations[next_idx]
                    train.current_station_index = next_idx
                station_code = station["code"]
                boarding = self._get_boarding_count(train, station_code)
                alighting = len(
                    [
                        p
                        for p in train.passengers_on_board
                        if p.destination_station_code == station_code
                    ]
                )
                dwell = self.passenger_flow.calc_dwell_time(boarding, alighting)
                train.arrive_at_station(station_code, dwell)
                self._process_boarding_alighting(train, station_code)
                if train.direction == Direction.UP:
                    next_next_idx = train.current_station_index + 1
                    if next_next_idx < len(stations):
                        train.next_station_code = stations[next_next_idx]["code"]
                        train.distance_to_next_station_m = self._track_distance(
                            train.line_code, station_code, stations[next_next_idx]["code"]
                        )
                else:
                    next_next_idx = train.current_station_index - 1
                    if next_next_idx >= 0:
                        train.next_station_code = stations[next_next_idx]["code"]
                        train.distance_to_next_station_m = self._track_distance(
                            train.line_code, station_code, stations[next_next_idx]["code"]
                        )

    def _return_train_to_depot(self, train: SimulatedTrain) -> None:
        depot_key = f"depot_{train.line_code}"
        if depot_key in self.depot_yard.depots:
            self.depot_yard.return_to_depot(train.train_id, depot_key)
        train.status = TrainStatus.IN_DEPOT
        train.current_station_code = ""
        train.next_station_code = ""
        train.position_m = 0.0
        train.distance_to_next_station_m = 0.0
        train.passengers_on_board.clear()
        train.occupancy = 0
        train._arrivals_at_terminus = 0
        train._just_turned_back = False

    def _get_boarding_count(self, train: SimulatedTrain, station_code: str) -> int:
        q = (
            self.passenger_pop.platform_queues.get(station_code, {})
            .get(train.line_code, {})
            .get(train.direction.value)
        )
        return q.occupancy if q else 0

    def _process_boarding_alighting(
        self, train: SimulatedTrain, station_code: str
    ) -> None:
        passengers = train.passengers_on_board
        alighted, remaining = self.passenger_pop.process_alighting(
            passengers, station_code, self.current_time
        )
        train.passengers_on_board = remaining
        capacity_avail = train.spec.max_capacity - len(remaining)
        if capacity_avail > 0:
            boarding = self.passenger_pop.process_boarding(
                station_code,
                train.line_code,
                train.direction,
                capacity_avail,
                self.current_time,
            )
            train.passengers_on_board.extend(boarding)
        train.occupancy = len(train.passengers_on_board)

    def _track_distance(self, line_code: str, from_station: str, to_station: str) -> float:
        segments = self.network.track_segments.get(line_code, [])
        for seg in segments:
            if seg.get("from_station_code") == from_station and seg.get("to_station_code") == to_station:
                return seg.get("length_m", 500.0)
        return 500.0

    def update_signal_blocks(self) -> None:
        for train in self.trains.values():
            if train.status not in (
                TrainStatus.RUNNING,
                TrainStatus.STOPPED,
            ):
                continue
            blocks = self.block_manager._line_blocks.get(train.line_code, {}).get(
                train.direction.value, []
            )
            if not blocks:
                continue
            for block in blocks:
                if (
                    block.from_station_id == train.current_station_code
                    or block.to_station_id == train.current_station_code
                ):
                    if train.block_id != block.block_id:
                        if train.block_id:
                            self.block_manager.release_block(
                                train.block_id, train.train_id
                            )
                        occupied = self.block_manager.occupy_block(
                            block.block_id,
                            train.train_id,
                            train.spec.length_m,
                            train.position_m,
                            train.direction,
                            self.current_time,
                        )
                        if occupied:
                            train.block_id = block.block_id
                    break

    def apply_cbtc(self) -> None:
        for train in self.trains.values():
            if train.status != TrainStatus.RUNNING:
                continue
            mx = self.cbtc.compute_movement_authority(
                train.train_id,
                train.line_code,
                train.direction,
                train.position_m,
                train.speed_mps,
                train.spec,
            )
            if mx == MovementAuthority.STOP:
                train.motion.emergency_brake(self.config.dt_s)
            elif mx == MovementAuthority.RESTRICTED:
                lead_id, gap = self.block_manager.get_leading_train(
                    train.line_code,
                    train.direction,
                    train.position_m,
                    train.spec.length_m,
                )
                target = self.cbtc.compute_target_speed(
                    mx, train.speed_mps, gap, train.spec, train.motion.max_speed_mps
                )
                train.motion.cruise(self.config.dt_s, 0.0, target)

    def spawn_incidents(self) -> None:
        lines = list(self.network.lines.keys())
        if not lines:
            return
        if self.current_time - self._last_incident_spawn < 60.0:
            return
        self._last_incident_spawn = self.current_time
        if self._rng.random() > 0.05:
            return
        line_code = self._rng.choice(lines)
        stations = self.network.get_stations_on_line(line_code)
        if not stations:
            return
        station = self._rng.choice(stations)
        it = self._rng.choice([t for t in IncidentType])
        self.incident_manager.create_incident(
            incident_type=it,
            line_code=line_code,
            station_code=station["code"],
            start_time=self.current_time,
            duration_s=self._rng.uniform(60, 300),
            description=f"random {it.value} at {station['code']}",
        )
        self.event_bus.publish(
            "incident.spawned",
            {
                "type": it.value,
                "line": line_code,
                "station": station["code"],
                "time": self.current_time,
            },
        )

    def reroute_affected_trains(self) -> None:
        for train in list(self.trains.values()):
            if (
                train.status == TrainStatus.INCIDENT_HALT
                or train.emergency_brake_active
            ):
                plan = self.timetable.get_trip_plan(train.train_id)
                if plan:
                    new_plan = self.router.reroute_train(
                        train.train_id,
                        plan,
                        train.current_station_code,
                        self.current_time,
                    )
                    if new_plan:
                        train.incident_hold = False
                        train.status = TrainStatus.RUNNING
                        train.distance_to_next_station_m = 500.0

    def _activate_waiting_passengers(self) -> None:
        for agent in self.passenger_pop.agents:
            if agent.completed or agent.state != PassengerState.WAITING_ORIGIN:
                continue
            if self.current_time >= agent.start_time:
                agent.state = PassengerState.WALKING_TO_PLATFORM
                origin_line = agent.origin_line_code
                line_stations = self.network.get_stations_on_line(origin_line)
                station_codes = [s["code"] for s in line_stations]
                try:
                    orig_idx = station_codes.index(agent.origin_station_code)
                    dest_idx = station_codes.index(agent.destination_station_code)
                    direction = Direction.UP if orig_idx < dest_idx else Direction.DOWN
                except ValueError:
                    direction = Direction.UP
                self.passenger_pop.add_agent_to_queue(agent, origin_line, direction)
                agent.total_walk_time += 60.0

    def collect_metrics(self) -> None:
        active_trains = sum(
            1 for t in self.trains.values() if t.status == TrainStatus.RUNNING
        )
        total_speed = sum(t.speed_mps for t in self.trains.values())
        avg_speed = total_speed / len(self.trains) if self.trains else 0.0
        total_energy = sum(t.total_energy_wh for t in self.trains.values())
        boarded = self.passenger_pop.get_completed_count()
        total_queue = sum(
            q.occupancy
            for station_q in self.passenger_pop.platform_queues.values()
            for line_q in station_q.values()
            for q in line_q.values()
        )
        metric = {
            "time": self.current_time,
            "active_trains": float(active_trains),
            "avg_speed_mps": avg_speed,
            "total_energy_wh": total_energy,
            "passengers_boarded": float(boarded),
            "total_queue_length": float(total_queue),
        }
        self.metrics.record_snapshot(metric)
        for tc in self._line_trains:
            line_trains = [
                self.trains[tid] for tid in self._line_trains[tc] if tid in self.trains
            ]
            if line_trains:
                avg_s = sum(t.speed_mps for t in line_trains) / len(line_trains)
            else:
                avg_s = 0.0
            self.metrics.record_line_metric(
                tc,
                {
                    "time": self.current_time,
                    "active_trains": float(
                        len([t for t in line_trains if t.status == TrainStatus.RUNNING])
                    ),
                    "avg_speed_mps": avg_s,
                },
            )

    def take_snapshot(self) -> SimulationSnapshot:
        running_count = sum(
            1 for t in self.trains.values() if t.status == TrainStatus.RUNNING
        )
        return SimulationSnapshot(
            time_s=self.current_time,
            trains=[t.to_dict() for t in self.trains.values()],
            passengers=[
                {
                    "id": a.id,
                    "state": a.state.value,
                    "origin": a.origin_station_code,
                    "dest": a.destination_station_code,
                }
                for a in self.passenger_pop.agents[:100]
            ],
            incidents=[
                {
                    "id": inc.incident_id,
                    "type": inc.incident_type.value,
                    "line": inc.line_code,
                    "active": not inc.resolved,
                }
                for inc in self.incident_manager.incidents
            ],
            metrics={
                "active_trains": float(running_count),
                "completed_passengers": float(self.passenger_pop.get_completed_count()),
                "avg_speed_mps": (
                    sum(t.speed_mps for t in self.trains.values()) / running_count
                    if running_count > 0
                    else 0.0
                ),
                "total_energy_wh": sum(t.total_energy_wh for t in self.trains.values()),
            },
        )

    def step(self, dt: float | None = None) -> SimulationSnapshot:
        wall_now = time.monotonic()
        step_dt = dt if dt is not None else max(0.0, min(wall_now - self._last_step_wall, 5.0))
        self._last_step_wall = wall_now

        self.current_time = ist_seconds()
        self.service_period = get_service_period(self.current_time)

        if self.service_period in ("pre_service", "post_service"):
            for train in self.trains.values():
                if train.status not in (TrainStatus.IN_DEPOT, TrainStatus.MAINTENANCE, TrainStatus.RETURNING_TO_DEPOT):
                    train.motion.brake(step_dt, 0.0)
                    if train.motion.state.speed_mps < 0.01:
                        self._return_train_to_depot(train)
            return self.take_snapshot()

        sim_dt = self.config.dt_s

        self._dispatch_trains()
        self.spawn_incidents()
        self.resolve_incidents()
        self.check_incidents()

        for train in list(self.trains.values()):
            train.update(sim_dt)

        for train in self.trains.values():
            if train._just_turned_back:
                train._just_turned_back = False
                if train._should_return_to_depot:
                    self._return_train_to_depot(train)
                    continue
                stations = self.network.get_stations_on_line(train.line_code)
                if not stations:
                    continue
                if train.direction == Direction.UP:
                    train.current_station_index = 0
                    train.current_station_code = stations[0]["code"]
                    train.next_station_code = stations[1]["code"] if len(stations) > 1 else stations[0]["code"]
                else:
                    train.current_station_index = len(stations) - 1
                    train.current_station_code = stations[-1]["code"]
                    train.next_station_code = stations[-2]["code"] if len(stations) > 1 else stations[-1]["code"]
                train.distance_to_next_station_m = 500.0

        for train in list(self.trains.values()):
            if train.status == TrainStatus.RETURNING_TO_DEPOT:
                self._return_train_to_depot(train)

        self.update_signal_blocks()
        self.apply_cbtc()
        self.process_station_stops()
        self.passenger_pop.generate_tick(self.current_time, self.config.dt_s)
        self._activate_waiting_passengers()

        if self.current_time - self._last_snapshot_time >= self.snapshot_interval_s:
            self.collect_metrics()
            self._last_snapshot_time = self.current_time

        self.event_bus.publish("sim.step", {"time": self.current_time})
        return self.take_snapshot()

    def run(self, duration_s: float | None = None) -> list[SimulationSnapshot]:
        self.is_running = True
        self.initialize()
        snapshots: list[SimulationSnapshot] = []
        snapshot = self.take_snapshot()
        snapshots.append(snapshot)
        end_time = duration_s if duration_s is not None else self.config.duration_s
        start_wall = time.monotonic()
        while True:
            elapsed = time.monotonic() - start_wall
            if elapsed >= end_time:
                break
            snapshot = self.step()
            if self.current_time - self._last_snapshot_time < 0.001 or True:
                pass
            if self.current_time % self.snapshot_interval_s < self.config.dt_s:
                snapshots.append(snapshot)
        self.is_running = False
        final_snapshot = self.take_snapshot()
        snapshots.append(final_snapshot)
        self.collect_metrics()
        return snapshots

    def get_state(self) -> dict[str, Any]:
        running = sum(1 for t in self.trains.values() if t.status == TrainStatus.RUNNING)
        in_depot = sum(1 for t in self.trains.values() if t.status == TrainStatus.IN_DEPOT)
        returning = sum(1 for t in self.trains.values() if t.status == TrainStatus.RETURNING_TO_DEPOT)
        breaking = sum(1 for t in self.trains.values() if t.status in (TrainStatus.EMERGENCY_BRAKE, TrainStatus.INCIDENT_HALT))
        now_ist = datetime.now(ZoneInfo("Asia/Kolkata"))
        return {
            "time": self.current_time,
            "running": self.is_running,
            "trains": len(self.trains),
            "active_trains": running,
            "depot_trains": in_depot + returning,
            "breaking_trains": breaking,
            "passengers": len(self.passenger_pop.agents),
            "completed_passengers": self.passenger_pop.get_completed_count(),
            "active_incidents": len(self.incident_manager._active),
            "metrics": self.metrics.get_summary(),
            "passenger_stats": self.passenger_pop.get_stats(),
            "service_period": self.service_period,
            "ist_time": now_ist.strftime("%H:%M:%S"),
            "ist_hour": now_ist.hour,
            "ist_minute": now_ist.minute,
            "service_start": "05:30",
            "service_end": "22:30",
        }

    def reset(self) -> None:
        self.trains.clear()
        self._line_trains.clear()
        self.current_time = 0.0
        self.is_running = False
        self._train_id_counter = 0
        self.metrics = MetricsCollector()
        self.incident_manager = IncidentManager(self.config)
        self.event_bus = EventBus()
        self.router = DynamicRouter(self.network, self.incident_manager, self.timetable)
