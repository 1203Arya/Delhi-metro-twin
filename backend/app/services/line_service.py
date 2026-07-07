from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dmdt_db import Line, Station


class LineService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_lines(self) -> list[Line]:
        stmt = select(Line).order_by(Line.number)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_line(self, code: str) -> Line | None:
        stmt = select(Line).where(Line.code == code)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_line_with_stations(self, code: str) -> Line | None:
        stmt = select(Line).where(Line.code == code)
        result = await self.db.execute(stmt)
        line = result.scalar_one_or_none()
        if line:
            s = (
                select(Station)
                .where(Station.line_code == code)
                .order_by(Station.sequence)
            )
            r = await self.db.execute(s)
            line._stations_cache = list(r.scalars().all())
        return line

    async def get_station_count(self, line_code: str) -> int:
        stmt = select(func.count(Station.id)).where(Station.line_code == line_code)
        result = await self.db.execute(stmt)
        return result.scalar() or 0
