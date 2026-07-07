from __future__ import annotations

from typing import TYPE_CHECKING, Any

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, Timestamps, UUIDPK
from ..enums import CoordinateConfidence, StructureType

if TYPE_CHECKING:
    from .line import Line
    from .platform import Platform
    from .junction import Junction
    from .crossover import Crossover
    from .track_segment import TrackSegment


class Station(Base, UUIDPK, Timestamps):
    __tablename__ = "stations"

    line_code: Mapped[str] = mapped_column(
        String(5), ForeignKey("lines.code", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[Any] = mapped_column(
        Geometry("POINT", srid=4326), nullable=False
    )
    structure: Mapped[str] = mapped_column(String(20), nullable=False, default="elevated")
    platforms: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    opened_year: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_terminus: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_junction: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    coordinate_confidence: Mapped[str] = mapped_column(
        String(10), nullable=False, default="high"
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)

    line: Mapped[Line] = relationship("Line", back_populates="stations")
    platforms_rel: Mapped[list[Platform]] = relationship(
        "Platform",
        back_populates="station",
        cascade="all, delete-orphan",
    )
    junctions: Mapped[list[Junction]] = relationship(
        "Junction",
        back_populates="station",
        cascade="all, delete-orphan",
    )
    crossovers: Mapped[list[Crossover]] = relationship(
        "Crossover",
        back_populates="station",
        cascade="all, delete-orphan",
    )
    track_segments_from: Mapped[list[TrackSegment]] = relationship(
        "TrackSegment",
        foreign_keys="TrackSegment.from_station_id",
        back_populates="from_station",
        cascade="all, delete-orphan",
    )
    track_segments_to: Mapped[list[TrackSegment]] = relationship(
        "TrackSegment",
        foreign_keys="TrackSegment.to_station_id",
        back_populates="to_station",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        {"extend_existing": True},
    )

    def __repr__(self) -> str:
        return f"<Station {self.code}: {self.name}>"
