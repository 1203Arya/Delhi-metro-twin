from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class LineBase(BaseModel):
    code: str
    name: str
    number: int
    color_hex: str
    corridor: str
    opened_year: int
    operator: str = "DMRC"
    gauge_mm: int
    electrification: str
    signalling_system: str
    total_length_km: float


class LineList(LineBase):
    id: str
    station_count: int = 0

    model_config = {"from_attributes": True}


class LineDetail(LineBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LineWithStations(LineDetail):
    stations: list[StationBrief] = []


from .station import StationBrief  # noqa: E402

LineWithStations.model_rebuild()
