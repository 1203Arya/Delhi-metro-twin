from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.deps import get_db, get_pagination, Pagination
from ...schemas import PaginatedResponse, TrackSegmentDetail, TrackSegmentList
from ...services import TrackService

router = APIRouter(prefix="/tracks", tags=["tracks"])


@router.get("", response_model=PaginatedResponse[TrackSegmentList])
async def list_tracks(
    line_code: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    pagination: Pagination = Depends(get_pagination),
):
    svc = TrackService(db)
    tracks = await svc.list_tracks(line_code, pagination.skip, pagination.limit)
    items = [
        TrackSegmentList(
            id=str(t.id),
            line_code=t.line_code,
            from_station_id=str(t.from_station_id),
            to_station_id=str(t.to_station_id),
            direction=t.direction,
            segment_index=t.segment_index,
            length_m=t.length_m,
            heading_in_deg=t.heading_in_deg,
            heading_out_deg=t.heading_out_deg,
            max_curve_radius_m=t.max_curve_radius_m,
            speed_limit_kmh=t.speed_limit_kmh,
            gradient_pct=t.gradient_pct,
            is_curve=t.is_curve,
        )
        for t in tracks
    ]
    return PaginatedResponse(
        items=items, total=len(tracks), skip=pagination.skip, limit=pagination.limit
    )


@router.get("/{track_id}", response_model=TrackSegmentDetail)
async def get_track(track_id: str, db: AsyncSession = Depends(get_db)):
    svc = TrackService(db)
    t = await svc.get_track(track_id)
    if not t:
        from ...core.exceptions import NotFoundError

        raise NotFoundError(f"Track segment {track_id} not found")
    return TrackSegmentDetail(
        id=str(t.id),
        line_code=t.line_code,
        from_station_id=str(t.from_station_id),
        to_station_id=str(t.to_station_id),
        direction=t.direction,
        segment_index=t.segment_index,
        length_m=t.length_m,
        heading_in_deg=t.heading_in_deg,
        heading_out_deg=t.heading_out_deg,
        max_curve_radius_m=t.max_curve_radius_m,
        speed_limit_kmh=t.speed_limit_kmh,
        gradient_pct=t.gradient_pct,
        is_curve=t.is_curve,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )
