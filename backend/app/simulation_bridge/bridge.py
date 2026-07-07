from __future__ import annotations

import logging
from typing import Any

from ..services.simulation_service import SimulationService

logger = logging.getLogger(__name__)


class SimulationBridge:
    def __init__(self) -> None:
        self.service = SimulationService()
        self.active_trains: dict[str, dict[str, Any]] = {}

    async def send_command(self, command: str, payload: dict[str, Any]) -> None:
        if command == "start":
            config = payload.get("config", {})
            self.service.configure(**config)
            network_data = payload.get("network")
            if network_data:
                self.service.load_network(network_data)
            await self.service.start()
            logger.info("Simulation started via bridge")
        elif command == "stop":
            await self.service.stop()
            logger.info("Simulation stopped via bridge")
        elif command == "pause":
            await self.service.pause()
            logger.info("Simulation paused via bridge")
        elif command == "resume":
            await self.service.resume()
            logger.info("Simulation resumed via bridge")
        elif command == "status":
            pass
        else:
            logger.warning("Unknown command: %s", command)

    async def handle_position_update(self, data: dict[str, Any]) -> None:
        train_id = data.get("train_id", "")
        self.active_trains[train_id] = data

    def get_state(self) -> dict[str, Any]:
        return self.service.get_state()
