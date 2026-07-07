from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..base import Base

M = TypeVar("M", bound=Base)


class BaseRepository(Generic[M]):
    def __init__(self, session: Session, model_cls: type[M]) -> None:
        self.session = session
        self.model_cls = model_cls

    def get(self, id: Any) -> M | None:
        return self.session.get(self.model_cls, id)

    def list(self, **filters: Any) -> list[M]:
        stmt = select(self.model_cls)
        for col, val in filters.items():
            if hasattr(self.model_cls, col):
                stmt = stmt.where(getattr(self.model_cls, col) == val)
        return list(self.session.execute(stmt).scalars().all())

    def add(self, instance: M) -> M:
        self.session.add(instance)
        self.session.flush()
        return instance

    def add_all(self, instances: list[M]) -> list[M]:
        self.session.add_all(instances)
        self.session.flush()
        return instances

    def delete(self, instance: M) -> None:
        self.session.delete(instance)
        self.session.flush()

    def count(self, **filters: Any) -> int:
        stmt = select(self.model_cls)
        for col, val in filters.items():
            if hasattr(self.model_cls, col):
                stmt = stmt.where(getattr(self.model_cls, col) == val)
        return self.session.execute(stmt).scalar_one_or_none() or 0

    def exists(self, **filters: Any) -> bool:
        return self.count(**filters) > 0
