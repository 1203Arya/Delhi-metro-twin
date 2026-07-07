from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.deps import get_db, get_pagination, Pagination
from ...schemas import LineDetail, LineList, LineWithStations
from ...services import LineService

router = APIRouter(prefix="/lines", tags=["lines"])


@router.get("", response_model=list[LineList])
async def list_lines(
    db: AsyncSession = Depends(get_db),
    pagination: Pagination = Depends(get_pagination),
):
    svc = LineService(db)
    lines = await svc.list_lines()
    result = []
    for line in lines:
        count = await svc.get_station_count(line.code)
        result.append(
            LineList(
                id=str(line.id),
                code=line.code,
                name=line.name,
                number=line.number,
                color_hex=line.color_hex,
                corridor=line.corridor,
                opened_year=line.opened_year,
                operator=line.operator,
                gauge_mm=line.gauge_mm,
                electrification=line.electrification,
                signalling_system=line.signalling_system,
                total_length_km=line.total_length_km,
                station_count=count,
            )
        )
    return result


@router.get("/{code}", response_model=LineDetail)
async def get_line(code: str, db: AsyncSession = Depends(get_db)):
    svc = LineService(db)
    line = await svc.get_line(code)
    if not line:
        from ...core.exceptions import NotFoundError
        raise NotFoundError(f"Line {code} not found")
    return LineDetail(
        id=str(line.id),
        code=line.code,
        name=line.name,
        number=line.number,
        color_hex=line.color_hex,
        corridor=line.corridor,
        opened_year=line.opened_year,
        operator=line.operator,
        gauge_mm=line.gauge_mm,
        electrification=line.electrification,
        signalling_system=line.signalling_system,
        total_length_km=line.total_length_km,
        created_at=line.created_at,
        updated_at=line.updated_at,
    )


@router.get("/{code}/stations", response_model=LineWithStations)
async def get_line_with_stations(code: str, db: AsyncSession = Depends(get_db)):
    svc = LineService(db)
    line = await svc.get_line_with_stations(code)
    if not line:
        from ...core.exceptions import NotFoundError
        raise NotFoundError(f"Line {code} not found")
    stations = []
    for s in line._stations_cache:
        stations.append(
            {
                "id": str(s.id),
                "code": s.code,
                "name": s.name,
                "line_code": s.line_code,
                "sequence": s.sequence,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "is_terminus": s.is_terminus,
                "has_junction": s.has_junction,
                "structure": s.structure,
            }
        )
    return LineWithStations(
        id=str(line.id),
        code=line.code,
        name=line.name,
        number=line.number,
        color_hex=line.color_hex,
        corridor=line.corridor,
        opened_year=line.opened_year,
        operator=line.operator,
        gauge_mm=line.gauge_mm,
        electrification=line.electrification,
        signalling_system=line.signalling_system,
        total_length_km=line.total_length_km,
        created_at=line.created_at,
        updated_at=line.updated_at,
        stations=stations,
    )
