from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from ...schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(timestamp=datetime.now(timezone.utc))
