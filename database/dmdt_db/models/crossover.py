from __future__ import annotations

from typing import TYPE_CHECKING, Any

from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, Timestamps, UUIDPK

if TYPE_CHECKING:
    from .line import Line
    from .station import Station


class Crossover(Base, UUIDPK, Timestamps):
    __tablename__ = "crossovers"

    line_code: Mapped[str] = mapped_column(
        String(5), ForeignKey("lines.code", ondelete="CASCADE"), nullable=False, index=True
    )
    station_id = mapped_column(
        "station_id", None, ForeignKey("stations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    geometry: Mapped[Any] = mapped_column(
        Geometry("LINESTRING", srid=4326, ), nullable=False
    )
    heading_deg: Mapped[float] = mapped_column(nullable=False, default=0.0)

    line: Mapped[Line] = relationship("Line", back_populates="crossovers")
    station: Mapped[Station] = relationship("Station", back_populates="crossovers")

    def __repr__(self) -> str:
        return f"<Crossover {self.line_code} station={self.station_id}>"
