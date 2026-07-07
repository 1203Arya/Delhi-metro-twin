from __future__ import annotations

from sqlalchemy import select

from ..models import Switch
from .base import BaseRepository


class SwitchRepository(BaseRepository[Switch]):
    def __init__(self, session):
        super().__init__(session, Switch)

    def list_by_line(self, line_code: str) -> list[Switch]:
        stmt = select(Switch).where(Switch.line_code == line_code)
        return list(self.session.execute(stmt).scalars().all())

    def list_by_junction(self, junction_id) -> list[Switch]:
        stmt = select(Switch).where(Switch.junction_id == junction_id)
        return list(self.session.execute(stmt).scalars().all())
