from __future__ import annotations

from sqlalchemy import select

from ..models import Platform
from .base import BaseRepository


class PlatformRepository(BaseRepository[Platform]):
    def __init__(self, session):
        super().__init__(session, Platform)

    def list_by_station(self, station_id) -> list[Platform]:
        stmt = (
            select(Platform)
            .where(Platform.station_id == station_id)
            .order_by(Platform.platform_number)
        )
        return list(self.session.execute(stmt).scalars().all())
