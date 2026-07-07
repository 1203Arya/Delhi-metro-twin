from __future__ import annotations

from typing import TYPE_CHECKING, Any

from geoalchemy2 import Geometry
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base, Timestamps, UUIDPK

if TYPE_CHECKING:
    from .line import Line


class Switch(Base, UUIDPK, Timestamps):
    __tablename__ = "switches"

    line_code: Mapped[str] = mapped_column(
        String(5),
        ForeignKey("lines.code", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    junction_id = mapped_column(
        "junction_id",
        None,
        ForeignKey("junctions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    location: Mapped[Any] = mapped_column(
        Geometry(
            "POINT",
            srid=4326,
        ),
        nullable=False,
    )
    switch_label: Mapped[str] = mapped_column(String(20), nullable=False)
    heading_deg: Mapped[float] = mapped_column(nullable=False, default=0.0)

    line: Mapped[Line] = relationship("Line", back_populates="switches")

    def __repr__(self) -> str:
        return f"<Switch {self.switch_label} junction={self.junction_id}>"
