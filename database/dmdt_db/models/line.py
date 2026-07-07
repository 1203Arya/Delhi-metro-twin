from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, Timestamps, UUIDPK

if TYPE_CHECKING:
    from .station import Station
    from .track_segment import TrackSegment
    from .depot import Depot
    from .crossover import Crossover
    from .switch import Switch


class Line(Base, UUIDPK, Timestamps):
    __tablename__ = "lines"

    code: Mapped[str] = mapped_column(
        String(5), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    color_hex: Mapped[str] = mapped_column(String(7), nullable=False)
    corridor: Mapped[str] = mapped_column(String(300), nullable=False)
    opened_year: Mapped[int] = mapped_column(Integer, nullable=False)
    operator: Mapped[str] = mapped_column(String(100), nullable=False, default="DMRC")
    gauge_mm: Mapped[int] = mapped_column(Integer, nullable=False)
    electrification: Mapped[str] = mapped_column(String(100), nullable=False)
    signalling_system: Mapped[str] = mapped_column(String(50), nullable=False)
    total_length_km: Mapped[float] = mapped_column(nullable=False)

    stations: Mapped[list[Station]] = relationship(
        "Station",
        back_populates="line",
        order_by="Station.sequence",
        cascade="all, delete-orphan",
    )
    track_segments: Mapped[list[TrackSegment]] = relationship(
        "TrackSegment",
        back_populates="line",
        cascade="all, delete-orphan",
    )
    depots: Mapped[list[Depot]] = relationship(
        "Depot",
        back_populates="line",
        cascade="all, delete-orphan",
    )
    crossovers: Mapped[list[Crossover]] = relationship(
        "Crossover",
        back_populates="line",
        cascade="all, delete-orphan",
    )
    switches: Mapped[list[Switch]] = relationship(
        "Switch",
        back_populates="line",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Line {self.code}: {self.name}>"
