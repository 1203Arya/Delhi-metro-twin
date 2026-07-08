from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from dmdt_sim.engine import SimulationEngine
from dmdt_sim.types import SimulationConfig
from dmdt_sim.types import TrainStatus

logger = logging.getLogger(__name__)


def _is_service_train(train: Any) -> bool:
    return train.status not in (TrainStatus.IN_DEPOT, TrainStatus.MAINTENANCE)


class SimulationService:
    def __init__(self) -> None:
        self.engine: SimulationEngine | None = None
        self._task: asyncio.Task | None = None
        self._running = False
        self._paused = False
        self._config: SimulationConfig | None = None
        self._snapshots: list[dict[str, Any]] = []

    def configure(self, **kwargs: Any) -> None:
        self._config = SimulationConfig(
            dt_s=kwargs.get("dt_s", 1.0),
            seed=kwargs.get("seed", 42),
            duration_s=kwargs.get("duration_s", 3600.0),
            n_passengers=kwargs.get("n_passengers", 50000),
            headway_target_s=kwargs.get("headway_target_s", 120.0),
        )

    def load_network(self, network_data: dict[str, Any]) -> None:
        if self.engine is None:
            config = self._config or SimulationConfig()
            self.engine = SimulationEngine(config)
        self.engine.load_network(network_data)

    async def start(self) -> None:
        if self._running:
            return
        if self.engine is None:
            config = self._config or SimulationConfig()
            self.engine = SimulationEngine(config)
        self._running = True
        self._paused = False
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Simulation started")

    async def stop(self) -> None:
        self._running = False
        self._paused = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("Simulation stopped")

    async def pause(self) -> None:
        self._paused = True
        logger.info("Simulation paused")

    async def resume(self) -> None:
        self._paused = False
        logger.info("Simulation resumed")

    async def _run_loop(self) -> None:
        if self.engine is None:
            return
        self.engine.initialize()
        self._snapshots.clear()
        snapshot = self.engine.take_snapshot()
        self._snapshots.append(snapshot.__dict__)
        while self._running:
            if self._paused:
                await asyncio.sleep(0.1)
                continue
            snapshot = self.engine.step()
            self._snapshots.append(snapshot.__dict__)
            if len(self._snapshots) > 10000:
                self._snapshots = self._snapshots[-5000:]
            await asyncio.sleep(0)
        self._running = False

    async def stream_positions(
        self, line_code: str | None = None, interval: float = 2.0
    ) -> AsyncIterator[str]:
        tick = 0
        while True:
            running = self._running
            paused = self._paused
            if self.engine and running:
                eng_state = self.engine.get_state()
                data = {
                    "type": "position_update",
                    "tick": tick,
                    "time_s": self.engine.current_time,
                    "ist_time": eng_state.get("ist_time", ""),
                    "service_period": eng_state.get("service_period", ""),
                    "running": running,
                    "paused": paused,
                    "trains": self._get_train_positions(line_code),
                    "metrics": self._get_metrics(),
                    "completed_passengers": eng_state["completed_passengers"],
                    "active_incidents": eng_state["active_incidents"],
                    "passengers": eng_state["passengers"],
                    "depot_trains": eng_state.get("depot_trains", 0),
                    "active_trains": eng_state.get("active_trains", 0),
                    "total_trains": eng_state.get("trains", 0),
                }
            else:
                data = {
                    "type": "position_update",
                    "tick": tick,
                    "time_s": 0.0,
                    "ist_time": "",
                    "service_period": "",
                    "running": False,
                    "paused": False,
                    "trains": [],
                    "metrics": self._get_metrics(),
                    "completed_passengers": 0,
                    "active_incidents": 0,
                    "passengers": 0,
                    "depot_trains": 0,
                    "active_trains": 0,
                }
            yield json.dumps(data)
            tick += 1
            await asyncio.sleep(interval)

    def _get_train_positions(self, line_code: str | None) -> list[dict[str, Any]]:
        if not self.engine:
            return []
        network = self.engine.network
        line_names: dict[str, str] = {}
        for lc, ls in network.lines.items():
            line_names[lc] = ls.get("name", lc) if isinstance(ls, dict) else lc
        trains = []
        for train in self.engine.trains.values():
            if not _is_service_train(train):
                continue
            if line_code and train.line_code != line_code:
                continue
            d = train.to_dict()
            lc = train.line_code
            # Resolve station names
            stn_code = d.get("current_station", "")
            nxt_code = d.get("next_station", "")
            stn = network.stations.get(stn_code, {})
            nxt = network.stations.get(nxt_code, {})
            d["current_station_name"] = stn.get("name", stn_code) if stn else stn_code
            d["next_station_name"] = nxt.get("name", nxt_code) if nxt else nxt_code
            d["line_name"] = line_names.get(lc, lc)
            # Destination-oriented direction: UP→last station, DOWN→first station
            line_stns = network.get_stations_on_line(lc)
            if line_stns:
                term = line_stns[-1] if train.direction.value == "up" else line_stns[0]
                term_name = term.get("name", term.get("code", ""))
                d["direction_destination"] = f"towards {term_name}"
            else:
                d["direction_destination"] = train.direction.value
            trains.append(d)
        return trains

    def _get_metrics(self) -> dict[str, float]:
        if not self.engine:
            return {
                "avg_headway_s": 0.0,
                "avg_dwell_s": 0.0,
                "avg_journey_time_s": 0.0,
                "avg_speed_mps": 0.0,
                "total_energy_wh": 0.0,
            }
        metrics = self.engine.get_state().get("metrics", {})
        return {
            "avg_headway_s": metrics.get("avg_headway_s", 0.0),
            "avg_dwell_s": metrics.get("avg_dwell_s", 0.0),
            "avg_journey_time_s": metrics.get("avg_journey_time_s", 0.0),
            "avg_speed_mps": metrics.get("avg_speed_mps", 0.0),
            "total_energy_wh": metrics.get("total_energy_wh", 0.0),
        }

    def get_state(self) -> dict[str, Any]:
        if not self.engine:
            return {
                "running": False,
                "paused": False,
                "time_s": 0.0,
                "trains": 0,
                "active_trains": 0,
                "depot_trains": 0,
                "passengers": 0,
                "completed_passengers": 0,
                "active_incidents": 0,
                "service_period": "",
                "ist_time": "",
            }
        state = self.engine.get_state()
        return {
            "running": self._running,
            "paused": self._paused,
            "time_s": state["time"],
            "trains": state["trains"],
            "active_trains": state["active_trains"],
            "depot_trains": state["depot_trains"],
            "passengers": state["passengers"],
            "completed_passengers": state["completed_passengers"],
            "active_incidents": state["active_incidents"],
            "service_period": state["service_period"],
            "ist_time": state["ist_time"],
            "service_start": "05:30",
            "service_end": "22:30",
        }

    def get_snapshots(self) -> list[dict[str, Any]]:
        return list(self._snapshots)
