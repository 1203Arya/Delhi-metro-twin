from __future__ import annotations

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ...simulation_bridge.bridge import SimulationBridge

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websockets"])

_bridge = SimulationBridge()


@router.websocket("/ws/simulation")
async def simulation_ws(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connected: simulation")
    svc = _bridge.service
    try:
        async for msg in svc.stream_positions(interval=2.0):
            await websocket.send_text(msg)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: simulation")


@router.websocket("/ws/simulation/{line_code}")
async def simulation_line_ws(websocket: WebSocket, line_code: str):
    await websocket.accept()
    logger.info("WebSocket connected: simulation/%s", line_code)
    svc = _bridge.service
    try:
        async for msg in svc.stream_positions(line_code=line_code, interval=2.0):
            await websocket.send_text(msg)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected: simulation/%s", line_code)
