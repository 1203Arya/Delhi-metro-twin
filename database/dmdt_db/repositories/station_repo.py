from __future__ import annotations

from sqlalchemy import select

from ..models import Station
from .base import BaseRepository


class StationRepository(BaseRepository[Station]):
    def __init__(self, session):
        super().__init__(session, Station)

    def get_by_code(self, code: str) -> list[Station]:
        stmt = select(Station).where(Station.code == code).order_by(Station.sequence)
        return list(self.session.execute(stmt).scalars().all())

    def list_by_line(self, line_code: str) -> list[Station]:
        stmt = (
            select(Station)
            .where(Station.line_code == line_code)
            .order_by(Station.sequence)
        )
        return list(self.session.execute(stmt).scalars().all())

    def list_terminals(self) -> list[Station]:
        stmt = select(Station).where(Station.is_terminus == True)  # noqa: E712
        return list(self.session.execute(stmt).scalars().all())

    def list_junctions(self) -> list[Station]:
        stmt = select(Station).where(Station.has_junction == True)  # noqa: E712
        return list(self.session.execute(stmt).scalars().all())
