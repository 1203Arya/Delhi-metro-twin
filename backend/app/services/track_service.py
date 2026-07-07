from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dmdt_db import TrackSegment


class TrackService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_tracks(
        self, line_code: str | None = None, skip: int = 0, limit: int = 100
    ) -> list[TrackSegment]:
        stmt = select(TrackSegment).order_by(
            TrackSegment.line_code, TrackSegment.segment_index
        )
        if line_code:
            stmt = stmt.where(TrackSegment.line_code == line_code)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_track(self, track_id: str) -> TrackSegment | None:
        stmt = select(TrackSegment).where(TrackSegment.id == uuid.UUID(track_id))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
