from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from ...schemas import (
    SimulationConfigSchema,
    SimulationState,
    SuccessResponse,
)
from ...simulation_bridge.bridge import SimulationBridge

router = APIRouter(prefix="/simulation", tags=["simulation"])

_bridge = SimulationBridge()


@router.post("/start", response_model=SuccessResponse)
async def start_simulation(
    config: SimulationConfigSchema | None = None,
) -> dict[str, str]:
    payload: dict[str, Any] = {}
    if config:
        payload["config"] = config.model_dump()
    await _bridge.send_command("start", payload)
    return {"message": "Simulation started"}


@router.post("/stop", response_model=SuccessResponse)
async def stop_simulation() -> dict[str, str]:
    await _bridge.send_command("stop", {})
    return {"message": "Simulation stopped"}


@router.post("/pause", response_model=SuccessResponse)
async def pause_simulation() -> dict[str, str]:
    await _bridge.send_command("pause", {})
    return {"message": "Simulation paused"}


@router.post("/resume", response_model=SuccessResponse)
async def resume_simulation() -> dict[str, str]:
    await _bridge.send_command("resume", {})
    return {"message": "Simulation resumed"}


@router.get("/state", response_model=SimulationState)
async def get_simulation_state() -> dict[str, Any]:
    return _bridge.get_state()


@router.get("/snapshots")
async def get_snapshots() -> list[dict[str, Any]]:
    return _bridge.service.get_snapshots()
