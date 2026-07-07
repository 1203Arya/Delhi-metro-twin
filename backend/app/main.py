from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI

from .api.v1.router import api_router
from .core.config import settings
from .core.lifespan import lifespan
from .core.logging import setup_logging
from .middleware.cors import setup_cors
from .middleware.logging_mw import setup_request_logging
from .middleware.metrics import setup_metrics
from .middleware.rate_limit import setup_rate_limiting

setup_logging()
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Delhi Metro Digital Twin API",
        description="Backend API for the Delhi Metro Digital Twin platform",
        version="0.1.0",
        lifespan=lifespan,
    )

    setup_cors(app)
    setup_metrics(app)
    setup_rate_limiting(app)
    setup_request_logging(app)

    app.include_router(api_router, prefix=settings.API_PREFIX)

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.is_development,
    )
