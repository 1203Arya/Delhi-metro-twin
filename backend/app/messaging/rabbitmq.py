from __future__ import annotations

import json
import logging
from typing import Any

import aio_pika

from ..core.config import settings

logger = logging.getLogger(__name__)

_connection: aio_pika.Connection | None = None
_channel: aio_pika.Channel | None = None


async def connect() -> None:
    global _connection, _channel
    try:
        _connection = await aio_pika.connect(settings.RABBITMQ_URL)
        _channel = await _connection.channel()
        logger.info("Connected to RabbitMQ at %s", settings.RABBITMQ_URL)
    except Exception:
        logger.warning("RabbitMQ unavailable — continuing without messaging")


async def disconnect() -> None:
    global _connection, _channel
    if _channel:
        await _channel.close()
        _channel = None
    if _connection:
        await _connection.close()
        _connection = None


async def publish(queue: str, message: dict[str, Any]) -> None:
    if not _channel:
        logger.warning("RabbitMQ not connected — dropping message to %s", queue)
        return
    await _channel.default_exchange.publish(
        aio_pika.Message(body=json.dumps(message).encode()),
        routing_key=queue,
    )
