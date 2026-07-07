from __future__ import annotations

from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from ..core.config import settings

limiter = Limiter(key_func=get_remote_address)


def setup_rate_limiting(app: FastAPI) -> None:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)


def rate_limit_key() -> str:
    return f"{settings.RATE_LIMIT_PER_MINUTE}/minute"
