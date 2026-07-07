from __future__ import annotations

from typing import TYPE_CHECKING, Any

from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, Timestamps, UUIDPK

if TYPE_CHECKING:
    from .line import Line
    from .siding import Siding


class Depot(Base, UUIDPK, Timestamps):
    __tablename__ = "depots"

    line_code: Mapped[str] = mapped_column(
        String(5), ForeignKey("lines.code", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[Any] = mapped_column(
        Geometry("POINT", srid=4326, ), nullable=False
    )
    latitude: Mapped[float] = mapped_column(nullable=False)
    longitude: Mapped[float] = mapped_column(nullable=False)
    area_m2: Mapped[float] = mapped_column(nullable=False, default=0.0)
    capacity_stabling: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    coordinate_confidence: Mapped[str] = mapped_column(String(10), nullable=False, default="medium")

    line: Mapped[Line] = relationship("Line", back_populates="depots")
    sidings: Mapped[list[Siding]] = relationship(
        "Siding",
        back_populates="depot",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Depot {self.name}>"
