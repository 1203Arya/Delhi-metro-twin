from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ..messaging.rabbitmq import connect as mq_connect, disconnect as mq_disconnect
from .config import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting %s — environment=%s", _app.title, settings.ENVIRONMENT)
    if settings.RABBITMQ_URL:
        await mq_connect()
    yield
    if settings.RABBITMQ_URL:
        await mq_disconnect()
    logger.info("Shutting down %s", _app.title)
