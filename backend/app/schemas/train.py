from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TrainClassBase(BaseModel):
    name: str
    max_speed_kmh: float
    acceleration_ms2: float
    deceleration_ms2: float
    length_m: float
    capacity_seated: int
    capacity_standing: int


class TrainClassList(TrainClassBase):
    id: str

    model_config = {"from_attributes": True}


class TrainClassDetail(TrainClassList):
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
