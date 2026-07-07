from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dmdt_db import Depot


class DepotService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_depots(
        self, line_code: str | None = None, skip: int = 0, limit: int = 100
    ) -> list[Depot]:
        stmt = select(Depot).order_by(Depot.line_code, Depot.name)
        if line_code:
            stmt = stmt.where(Depot.line_code == line_code)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_depot(self, depot_id: str) -> Depot | None:
        stmt = select(Depot).where(Depot.id == uuid.UUID(depot_id))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
