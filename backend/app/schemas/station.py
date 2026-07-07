from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class StationBrief(BaseModel):
    id: str
    code: str
    name: str
    line_code: str
    sequence: int
    latitude: float
    longitude: float
    is_terminus: bool = False
    has_junction: bool = False
    structure: str = "elevated"

    model_config = {"from_attributes": True}


class StationList(StationBrief):
    platforms: int = 2
    opened_year: int = 0

    model_config = {"from_attributes": True}


class StationDetail(StationList):
    created_at: datetime
    updated_at: datetime
    coordinate_confidence: str = "high"

    model_config = {"from_attributes": True}
