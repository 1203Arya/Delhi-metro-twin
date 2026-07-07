from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dmdt_db import TrainClass


class TrainService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_classes(self) -> list[TrainClass]:
        stmt = select(TrainClass).order_by(TrainClass.max_speed_kmh)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_class(self, class_id: str) -> TrainClass | None:
        stmt = select(TrainClass).where(TrainClass.id == uuid.UUID(class_id))
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
