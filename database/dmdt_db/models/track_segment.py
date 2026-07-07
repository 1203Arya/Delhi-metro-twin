from __future__ import annotations

from typing import TYPE_CHECKING, Any

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, Timestamps, UUIDPK

if TYPE_CHECKING:
    from .line import Line
    from .station import Station


class TrackSegment(Base, UUIDPK, Timestamps):
    __tablename__ = "track_segments"

    line_code: Mapped[str] = mapped_column(
        String(5),
        ForeignKey("lines.code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_station_id = mapped_column(
        "from_station_id",
        None,
        ForeignKey("stations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    to_station_id = mapped_column(
        "to_station_id",
        None,
        ForeignKey("stations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    direction: Mapped[str] = mapped_column(String(10), nullable=False)
    segment_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    geometry: Mapped[Any] = mapped_column(
        Geometry(
            "LINESTRING",
            srid=4326,
        ),
        nullable=False,
    )
    length_m: Mapped[float] = mapped_column(nullable=False)
    heading_in_deg: Mapped[float] = mapped_column(nullable=False, default=0.0)
    heading_out_deg: Mapped[float] = mapped_column(nullable=False, default=0.0)
    max_curve_radius_m: Mapped[float | None] = mapped_column(nullable=True)
    speed_limit_kmh: Mapped[float] = mapped_column(nullable=False)
    gradient_pct: Mapped[float | None] = mapped_column(nullable=True)
    is_curve: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    line: Mapped[Line] = relationship("Line", back_populates="track_segments")
    from_station: Mapped[Station] = relationship(
        "Station", foreign_keys=[from_station_id], back_populates="track_segments_from"
    )
    to_station: Mapped[Station] = relationship(
        "Station", foreign_keys=[to_station_id], back_populates="track_segments_to"
    )

    def __repr__(self) -> str:
        return f"<TrackSegment {self.line_code} {self.from_station_id}->{self.to_station_id} {self.direction}>"
