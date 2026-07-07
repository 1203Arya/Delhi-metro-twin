from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base, Timestamps, UUIDPK


class TrainClass(Base, UUIDPK, Timestamps):
    __tablename__ = "train_classes"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    max_speed_kmh: Mapped[float] = mapped_column(nullable=False)
    acceleration_ms2: Mapped[float] = mapped_column(nullable=False)
    deceleration_ms2: Mapped[float] = mapped_column(nullable=False)
    length_m: Mapped[float] = mapped_column(nullable=False)
    capacity_seated: Mapped[int] = mapped_column(Integer, nullable=False)
    capacity_standing: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self) -> str:
        return f"<TrainClass {self.name} ({self.max_speed_kmh} km/h)>"
