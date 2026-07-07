from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.deps import get_db, get_pagination, Pagination
from ...schemas import DepotDetail, DepotList, PaginatedResponse
from ...services import DepotService

router = APIRouter(prefix="/depots", tags=["depots"])


@router.get("", response_model=PaginatedResponse[DepotList])
async def list_depots(
    line_code: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    pagination: Pagination = Depends(get_pagination),
):
    svc = DepotService(db)
    depots = await svc.list_depots(line_code, pagination.skip, pagination.limit)
    items = [
        DepotList(
            id=str(d.id),
            line_code=d.line_code,
            name=d.name,
            latitude=d.latitude,
            longitude=d.longitude,
            area_m2=d.area_m2,
            capacity_stabling=d.capacity_stabling,
            coordinate_confidence=d.coordinate_confidence,
        )
        for d in depots
    ]
    return PaginatedResponse(items=items, total=len(depots), skip=pagination.skip, limit=pagination.limit)


@router.get("/{depot_id}", response_model=DepotDetail)
async def get_depot(depot_id: str, db: AsyncSession = Depends(get_db)):
    svc = DepotService(db)
    d = await svc.get_depot(depot_id)
    if not d:
        from ...core.exceptions import NotFoundError
        raise NotFoundError(f"Depot {depot_id} not found")
    return DepotDetail(
        id=str(d.id),
        line_code=d.line_code,
        name=d.name,
        latitude=d.latitude,
        longitude=d.longitude,
        area_m2=d.area_m2,
        capacity_stabling=d.capacity_stabling,
        coordinate_confidence=d.coordinate_confidence,
        created_at=d.created_at,
        updated_at=d.updated_at,
    )
