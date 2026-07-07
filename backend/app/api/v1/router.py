from __future__ import annotations

from fastapi import APIRouter

from .auth import router as auth_router
from .depots import router as depots_router
from .health import router as health_router
from .lines import router as lines_router
from .simulation import router as simulation_router
from .stations import router as stations_router
from .tracks import router as tracks_router
from .trains import router as trains_router
from .websockets import router as ws_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(lines_router)
api_router.include_router(stations_router)
api_router.include_router(tracks_router)
api_router.include_router(trains_router)
api_router.include_router(depots_router)
api_router.include_router(simulation_router)
api_router.include_router(ws_router)
