from __future__ import annotations

from typing import TYPE_CHECKING, Any

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, Timestamps, UUIDPK

if TYPE_CHECKING:
    from .station import Station


class Junction(Base, UUIDPK, Timestamps):
    __tablename__ = "junctions"

    station_id = mapped_column(
        "station_id", None, ForeignKey("stations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    location: Mapped[Any] = mapped_column(
        Geometry("POINT", srid=4326, ), nullable=False
    )
    is_interchange: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_turnout: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    lines: Mapped[str] = mapped_column(String(200), nullable=False, default="")

    station: Mapped[Station] = relationship("Station", back_populates="junctions")

    def __repr__(self) -> str:
        return f"<Junction {self.name}>"
