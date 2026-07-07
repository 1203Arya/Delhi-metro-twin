from __future__ import annotations

from typing import TYPE_CHECKING, Any

from geoalchemy2 import Geometry
from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, Timestamps, UUIDPK

if TYPE_CHECKING:
    from .station import Station


class Platform(Base, UUIDPK, Timestamps):
    __tablename__ = "platforms"

    station_id = mapped_column(
        "station_id",
        None,
        ForeignKey("stations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform_number: Mapped[int] = mapped_column(Integer, nullable=False)
    geometry: Mapped[Any] = mapped_column(
        Geometry(
            "POLYGON",
            srid=4326,
        ),
        nullable=False,
    )
    heading_deg: Mapped[float] = mapped_column(nullable=False, default=0.0)
    length_m: Mapped[float] = mapped_column(nullable=False, default=180.0)
    width_m: Mapped[float] = mapped_column(nullable=False, default=6.0)
    is_edge_platform: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    station: Mapped[Station] = relationship("Station", back_populates="platforms_rel")

    def __repr__(self) -> str:
        return f"<Platform station={self.station_id} platform={self.platform_number}>"
