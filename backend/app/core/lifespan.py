from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ..db.session import async_session_factory
from ..messaging.rabbitmq import connect as mq_connect, disconnect as mq_disconnect
from ..simulation_bridge import get_bridge
from .config import settings

logger = logging.getLogger(__name__)


async def _try_start_simulation() -> None:
    try:
        from ..api.v1.simulation import _build_network_data

        async with async_session_factory() as db:
            network_data = await _build_network_data(db)

        bridge = get_bridge()
        await bridge.send_command("start", {"network": network_data})
        logger.info(
            "Simulation auto-started with %d lines", len(network_data.get("lines", []))
        )
    except Exception:
        logger.warning(
            "Failed to auto-start simulation — will be unavailable until manually started"
        )


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting %s — environment=%s", _app.title, settings.ENVIRONMENT)
    if settings.RABBITMQ_URL:
        await mq_connect()
    await _try_start_simulation()
    yield
    if settings.RABBITMQ_URL:
        await mq_disconnect()
    logger.info("Shutting down %s", _app.title)
