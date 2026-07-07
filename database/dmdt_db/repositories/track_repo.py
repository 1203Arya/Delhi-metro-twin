from __future__ import annotations

from sqlalchemy import select

from ..models import TrackSegment
from .base import BaseRepository


class TrackSegmentRepository(BaseRepository[TrackSegment]):
    def __init__(self, session):
        super().__init__(session, TrackSegment)

    def list_by_line(self, line_code: str) -> list[TrackSegment]:
        stmt = (
            select(TrackSegment)
            .where(TrackSegment.line_code == line_code)
            .order_by(TrackSegment.segment_index)
        )
        return list(self.session.execute(stmt).scalars().all())

    def list_curves(self, line_code: str | None = None) -> list[TrackSegment]:
        stmt = select(TrackSegment).where(TrackSegment.is_curve == True)  # noqa: E712
        if line_code:
            stmt = stmt.where(TrackSegment.line_code == line_code)
        return list(self.session.execute(stmt).scalars().all())
