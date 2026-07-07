from __future__ import annotations

from sqlalchemy import select

from ..models import Siding
from .base import BaseRepository


class SidingRepository(BaseRepository[Siding]):
    def __init__(self, session):
        super().__init__(session, Siding)

    def list_by_depot(self, depot_id) -> list[Siding]:
        stmt = select(Siding).where(Siding.depot_id == depot_id)
        return list(self.session.execute(stmt).scalars().all())
