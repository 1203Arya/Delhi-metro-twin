from __future__ import annotations

from sqlalchemy import select

from ..models import Line
from .base import BaseRepository


class LineRepository(BaseRepository[Line]):
    def __init__(self, session):
        super().__init__(session, Line)

    def get_by_code(self, code: str) -> Line | None:
        stmt = select(Line).where(Line.code == code)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_all(self) -> list[Line]:
        stmt = select(Line).order_by(Line.number)
        return list(self.session.execute(stmt).scalars().all())
