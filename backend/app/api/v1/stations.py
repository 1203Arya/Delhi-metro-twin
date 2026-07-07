from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.deps import get_db, get_pagination, Pagination
from ...schemas import PaginatedResponse, StationDetail, StationList
from ...services import StationService

router = APIRouter(prefix="/stations", tags=["stations"])


@router.get("", response_model=PaginatedResponse[StationList])
async def list_stations(
    line_code: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    pagination: Pagination = Depends(get_pagination),
):
    svc = StationService(db)
    stations = await svc.list_stations(line_code, pagination.skip, pagination.limit)
    total = await svc.count_stations(line_code)
    items = [
        StationList(
            id=str(s.id),
            code=s.code,
            name=s.name,
            line_code=s.line_code,
            sequence=s.sequence,
            latitude=s.latitude,
            longitude=s.longitude,
            is_terminus=s.is_terminus,
            has_junction=s.has_junction,
            structure=s.structure,
            platforms=s.platforms,
            opened_year=s.opened_year,
        )
        for s in stations
    ]
    return PaginatedResponse(
        items=items, total=total, skip=pagination.skip, limit=pagination.limit
    )


@router.get("/{station_id}", response_model=StationDetail)
async def get_station(station_id: str, db: AsyncSession = Depends(get_db)):
    svc = StationService(db)
    s = await svc.get_station(station_id)
    if not s:
        from ...core.exceptions import NotFoundError

        raise NotFoundError(f"Station {station_id} not found")
    return StationDetail(
        id=str(s.id),
        code=s.code,
        name=s.name,
        line_code=s.line_code,
        sequence=s.sequence,
        latitude=s.latitude,
        longitude=s.longitude,
        is_terminus=s.is_terminus,
        has_junction=s.has_junction,
        structure=s.structure,
        platforms=s.platforms,
        opened_year=s.opened_year,
        created_at=s.created_at,
        updated_at=s.updated_at,
        coordinate_confidence=s.coordinate_confidence,
    )
