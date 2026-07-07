from __future__ import annotations

import logging
import time

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("dmdt.http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.monotonic()
        response: Response = await call_next(request)
        elapsed = time.monotonic() - start
        logger.info(
            "%s %s → %s (%.3fs)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        return response


def setup_request_logging(app: FastAPI) -> None:
    app.add_middleware(RequestLoggingMiddleware)
