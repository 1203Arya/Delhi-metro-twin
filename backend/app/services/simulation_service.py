from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from dmdt_sim.engine import SimulationEngine
from dmdt_sim.types import SimulationConfig

logger = logging.getLogger(__name__)


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
        while (
            self._running and self.engine.current_time < self._config.duration_s
            if self._config
            else 3600
        ):
            if self._paused:
                await asyncio.sleep(0.1)
                continue
            snapshot = self.engine.step()
            self._snapshots.append(snapshot.__dict__)
            await asyncio.sleep(0)
        self._running = False

    async def stream_positions(
        self, line_code: str | None = None, interval: float = 2.0
    ) -> AsyncIterator[str]:
        tick = 0
        while True:
            if self.engine and self._running:
                data = {
                    "type": "position_update",
                    "tick": tick,
                    "time_s": self.engine.current_time,
                    "trains": self._get_train_positions(line_code),
                    "metrics": self._get_metrics(),
                }
            else:
                data = {
                    "type": "position_update",
                    "tick": tick,
                    "time_s": 0.0,
                    "trains": [],
                    "metrics": {},
                }
            yield json.dumps(data)
            tick += 1
            await asyncio.sleep(interval)

    def _get_train_positions(self, line_code: str | None) -> list[dict[str, Any]]:
        if not self.engine:
            return []
        trains = []
        for train in self.engine.trains.values():
            if line_code and train.line_code != line_code:
                continue
            trains.append(train.to_dict())
        return trains

    def _get_metrics(self) -> dict[str, float]:
        if not self.engine:
            return {}
        return self.engine.get_state().get("metrics", {})

    def get_state(self) -> dict[str, Any]:
        if not self.engine:
            return {
                "running": False,
                "time_s": 0.0,
                "trains": 0,
                "active_trains": 0,
                "passengers": 0,
                "completed_passengers": 0,
                "active_incidents": 0,
            }
        state = self.engine.get_state()
        return {
            "running": self._running,
            "paused": self._paused,
            "time_s": state["time"],
            "trains": state["trains"],
            "active_trains": state["active_trains"],
            "passengers": state["passengers"],
            "completed_passengers": state["completed_passengers"],
            "active_incidents": state["active_incidents"],
        }

    def get_snapshots(self) -> list[dict[str, Any]]:
        return list(self._snapshots)
