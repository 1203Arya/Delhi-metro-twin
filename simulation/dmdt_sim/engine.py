from __future__ import annotations

import random
from collections import defaultdict
from typing import Any

from .depot.yard import DepotYard
from .events.bus import EventBus
from .incidents.manager import IncidentManager
from .network.graph import NetworkGraph
from .passengers.flow import PassengerFlowModel
from .passengers.population import PassengerPopulation
from .perf.metrics import MetricsCollector
from .physics.train import TrainMotionModel
from .routing.router import DynamicRouter
from .schedule.maintenance import MaintenanceScheduler
from .schedule.timetable import Timetable, TimetableGenerator
from .signalling.block import BlockManager
from .signalling.cbtc import CBTCController
from .physics.train import DrivingMode
from .types import (
    Direction,
    IncidentType,
    MovementAuthority,
    PassengerState,
    SimulationConfig,
    SimulationSnapshot,
    TrainSpec,
    TrainStatus,
)


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
                self.current_station_index = 0
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
            self.status = TrainStatus.DOOR_CLOSE
            self.is_at_platform = False
            self.status = TrainStatus.RUNNING

    def arrive_at_station(self, station_code: str, dwell_time_s: float) -> None:
        self.current_station_code = station_code
        self.is_at_platform = True
        self.status = TrainStatus.STOPPED
        self.dwell_timer = dwell_time_s
        self.arrival_time_at_station = 0.0
        self.distance_to_next_station_m = 0.0

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
            "occupancy": self.occupancy,
            "doors_open": self.doors_open,
            "mode": self.motion.mode.name.lower(),
            "block_id": self.block_id,
            "total_distance_m": self.total_distance_m,
            "total_energy_wh": self.total_energy_wh,
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
        self.is_running: bool = False
        self.snapshot_interval_s: float = 30.0
        self._last_snapshot_time: float = 0.0
        self._train_id_counter: int = 0

    def load_network(self, network_data: dict[str, Any]) -> None:
        for line in network_data.get("lines", []):
            self.network.add_line(line)
        for stn in network_data.get("stations", []):
            self.network.add_station(stn)
        for seg in network_data.get("track_segments", []):
            self.network.add_track_segment(seg)
        for dp in network_data.get("depots", []):
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

    def initialize(self) -> None:
        self.trains.clear()
        self._line_trains.clear()
        self._train_id_counter = 0
        self.current_time = 0.0
        self._setup_trains()
        self._setup_timetables()
        self._setup_passengers()

    def _setup_trains(self) -> None:
        for line_code in self.network.lines:
            line_stations = self.network.get_stations_on_line(line_code)
            if not line_stations:
                continue
            n_trains = min(
                self.config.max_trains_per_line, max(3, len(line_stations) // 2)
            )
            for i in range(n_trains):
                train_id = f"tr_{line_code}_{self._train_id_counter:04d}"
                spec = TrainSpec(
                    train_class_id="std",
                    name=f"Train {train_id}",
                    max_speed_kmh=80.0,
                    acceleration_ms2=0.8,
                    deceleration_ms2=0.9,
                    length_m=200.0,
                    capacity_seated=350,
                    capacity_standing=650,
                )
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
                self.trains[train_id] = train
                self._line_trains[line_code].append(train_id)
                self.maintenance.register_train(train_id, 0.0)
                self._train_id_counter += 1

    def _setup_timetables(self) -> None:
        for line_code in self.network.lines:
            stations = self.network.get_stations_on_line(line_code)
            if not stations:
                continue
            for direction in (Direction.UP, Direction.DOWN):
                entries, plans = self.timetable_gen.generate(
                    line_code,
                    stations,
                    direction,
                    start_time=self.current_time,
                )
                for plan in plans:
                    self.timetable.add_trip_plan(plan.train_id, plan)
                for entry in entries:
                    self.timetable.add_entry(entry)

    def _setup_passengers(self) -> None:
        interchange = self.network.get_interchange_stations()
        self.passenger_pop.generate(
            self.network.stations,
            self.network.lines,
            interchange_stations=interchange,
        )

    def dispatch_depot_trains(self) -> None:
        for line_code in self.network.lines:
            depot_key = f"depot_{line_code}"
            available = self.depot_yard.get_available_trains(depot_key)
            if not available:
                continue
            dispatched = self.timetable.dispatch_trains(
                self.current_time, line_code, Direction.UP, available
            )
            for train_id, entry in dispatched:
                train = self.trains.get(train_id)
                if train:
                    stations = self.network.get_stations_on_line(line_code)
                    if stations:
                        train.status = TrainStatus.RUNNING
                        train.current_station_code = stations[0]["code"]
                        train.next_station_code = (
                            stations[1]["code"]
                            if len(stations) > 1
                            else stations[0]["code"]
                        )
                        train.position_m = 0.0
                        train.distance_to_next_station_m = 500.0
            dispatched_down = self.timetable.dispatch_trains(
                self.current_time, line_code, Direction.DOWN, available
            )
            for train_id, entry in dispatched_down:
                train = self.trains.get(train_id)
                if train:
                    stations = self.network.get_stations_on_line(line_code)
                    if stations:
                        train.status = TrainStatus.RUNNING
                        train.current_station_code = stations[-1]["code"]
                        train.next_station_code = (
                            stations[-2]["code"]
                            if len(stations) > 1
                            else stations[-1]["code"]
                        )
                        train.position_m = 0.0
                        train.distance_to_next_station_m = 500.0

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
                next_idx = train.current_station_index + 1
                if train.direction == Direction.UP:
                    if next_idx >= len(stations):
                        train.status = TrainStatus.TURNBACK
                        train.turnback_timer = self.config.turnback_time_s
                        continue
                    station = stations[next_idx]
                else:
                    if train.current_station_index <= 0:
                        train.status = TrainStatus.TURNBACK
                        train.turnback_timer = self.config.turnback_time_s
                        continue
                    station = stations[train.current_station_index - 1]
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
                train.current_station_index = next_idx

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

    def update_signal_blocks(self) -> None:
        for train in self.trains.values():
            if train.status not in (
                TrainStatus.RUNNING,
                TrainStatus.STOPPED,
                TrainStatus.STOPPING,
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
        if not lines or self._rng.random() > 0.01:
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
            duration_s=self._rng.uniform(30, 180),
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

    def update_passenger_agents(self) -> None:
        for agent in self.passenger_pop.agents:
            if agent.completed or agent.state != PassengerState.WAITING_ORIGIN:
                continue
            if self.current_time >= agent.start_time:
                agent.state = PassengerState.WALKING_TO_PLATFORM
                origin_line = agent.origin_line_code
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
                "active_trains": float(
                    sum(
                        1
                        for t in self.trains.values()
                        if t.status == TrainStatus.RUNNING
                    )
                ),
                "completed_passengers": float(self.passenger_pop.get_completed_count()),
                "avg_speed_mps": (
                    sum(t.speed_mps for t in self.trains.values()) / len(self.trains)
                    if self.trains
                    else 0.0
                ),
                "total_energy_wh": sum(t.total_energy_wh for t in self.trains.values()),
            },
        )

    def step(self, dt: float | None = None) -> SimulationSnapshot:
        step_dt = dt if dt is not None else self.config.dt_s
        self.current_time += step_dt
        self.dispatch_depot_trains()
        self.spawn_incidents()
        self.resolve_incidents()
        self.check_incidents()
        for train in list(self.trains.values()):
            train.update(step_dt)
        self.update_signal_blocks()
        self.apply_cbtc()
        self.process_station_stops()
        self.update_passenger_agents()
        if self.current_time - self._last_snapshot_time >= self.snapshot_interval_s:
            self.collect_metrics()
            self._last_snapshot_time = self.current_time
        self.event_bus.publish("sim.step", {"time": self.current_time})
        return self.take_snapshot()

    def run(self, duration_s: float | None = None) -> list[SimulationSnapshot]:
        self.is_running = True
        end_time = duration_s if duration_s is not None else self.config.duration_s
        self.initialize()
        snapshots: list[SimulationSnapshot] = []
        snapshot = self.take_snapshot()
        snapshots.append(snapshot)
        while self.current_time < end_time:
            snapshot = self.step()
            if self.current_time - self._last_snapshot_time < 0.001 or True:
                pass
            if self.current_time % self.snapshot_interval_s < self.config.dt_s:
                snapshots.append(snapshot)
            if self.current_time >= end_time:
                break
        self.is_running = False
        final_snapshot = self.take_snapshot()
        snapshots.append(final_snapshot)
        self.collect_metrics()
        return snapshots

    def get_state(self) -> dict[str, Any]:
        return {
            "time": self.current_time,
            "running": self.is_running,
            "trains": len(self.trains),
            "active_trains": sum(
                1 for t in self.trains.values() if t.status == TrainStatus.RUNNING
            ),
            "passengers": len(self.passenger_pop.agents),
            "completed_passengers": self.passenger_pop.get_completed_count(),
            "active_incidents": len(self.incident_manager._active),
            "metrics": self.metrics.get_summary(),
            "passenger_stats": self.passenger_pop.get_stats(),
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
