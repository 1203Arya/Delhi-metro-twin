from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dmdt_db import Station


class StationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_stations(
        self, line_code: str | None = None, skip: int = 0, limit: int = 100
    ) -> list[Station]:
        stmt = select(Station).order_by(Station.line_code, Station.sequence)
        if line_code:
            stmt = stmt.where(Station.line_code == line_code)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_station(self, station_id: str) -> Station | None:
        stmt = select(Station).where(Station.id == uuid.UUID(station_id))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def count_stations(self, line_code: str | None = None) -> int:
        from sqlalchemy import func, select

        stmt = select(func.count(Station.id))
        if line_code:
            stmt = stmt.where(Station.line_code == line_code)
        result = await self.db.execute(stmt)
        return result.scalar() or 0
