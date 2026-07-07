from __future__ import annotations

from sqlalchemy import select

from ..models import Crossover
from .base import BaseRepository


class CrossoverRepository(BaseRepository[Crossover]):
    def __init__(self, session):
        super().__init__(session, Crossover)

    def list_by_line(self, line_code: str) -> list[Crossover]:
        stmt = select(Crossover).where(Crossover.line_code == line_code)
        return list(self.session.execute(stmt).scalars().all())

    def list_by_station(self, station_id) -> list[Crossover]:
        stmt = select(Crossover).where(Crossover.station_id == station_id)
        return list(self.session.execute(stmt).scalars().all())
