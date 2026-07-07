from __future__ import annotations

from sqlalchemy import select

from ..models import TrainClass
from .base import BaseRepository


class TrainClassRepository(BaseRepository[TrainClass]):
    def __init__(self, session):
        super().__init__(session, TrainClass)

    def get_by_name(self, name: str) -> TrainClass | None:
        stmt = select(TrainClass).where(TrainClass.name == name)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_all(self) -> list[TrainClass]:
        stmt = select(TrainClass).order_by(TrainClass.max_speed_kmh)
        return list(self.session.execute(stmt).scalars().all())
