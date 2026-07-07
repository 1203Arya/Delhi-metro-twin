from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class DepotBase(BaseModel):
    line_code: str
    name: str
    latitude: float
    longitude: float
    area_m2: float = 0.0
    capacity_stabling: int = 0
    coordinate_confidence: str = "medium"


class DepotList(DepotBase):
    id: str

    model_config = {"from_attributes": True}


class DepotDetail(DepotList):
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
