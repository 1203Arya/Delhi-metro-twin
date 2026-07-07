from __future__ import annotations

from typing import TYPE_CHECKING, Any

from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, Timestamps, UUIDPK

if TYPE_CHECKING:
    from .depot import Depot


class Siding(Base, UUIDPK, Timestamps):
    __tablename__ = "sidings"

    depot_id = mapped_column(
        "depot_id",
        None,
        ForeignKey("depots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    geometry: Mapped[Any] = mapped_column(
        Geometry(
            "LINESTRING",
            srid=4326,
        ),
        nullable=False,
    )
    length_m: Mapped[float] = mapped_column(nullable=False)
    capacity_trains: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    depot: Mapped[Depot] = relationship("Depot", back_populates="sidings")

    def __repr__(self) -> str:
        return f"<Siding {self.name} ({self.length_m:.0f}m)>"
