from __future__ import annotations

from sqlalchemy import select

from ..models import Depot
from .base import BaseRepository


class DepotRepository(BaseRepository[Depot]):
    def __init__(self, session):
        super().__init__(session, Depot)

    def list_by_line(self, line_code: str) -> list[Depot]:
        stmt = select(Depot).where(Depot.line_code == line_code)
        return list(self.session.execute(stmt).scalars().all())

    def get_by_name(self, name: str) -> Depot | None:
        stmt = select(Depot).where(Depot.name == name)
        return self.session.execute(stmt).scalar_one_or_none()
