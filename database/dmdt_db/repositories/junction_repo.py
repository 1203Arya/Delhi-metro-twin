from __future__ import annotations

from sqlalchemy import select

from ..models import Junction
from .base import BaseRepository


class JunctionRepository(BaseRepository[Junction]):
    def __init__(self, session):
        super().__init__(session, Junction)

    def list_interchanges(self) -> list[Junction]:
        stmt = select(Junction).where(Junction.is_interchange == True)  # noqa: E712
        return list(self.session.execute(stmt).scalars().all())

    def list_turnouts(self) -> list[Junction]:
        stmt = select(Junction).where(Junction.is_turnout == True)  # noqa: E712
        return list(self.session.execute(stmt).scalars().all())
