from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class TrackSegmentBase(BaseModel):
    line_code: str
    from_station_id: str
    to_station_id: str
    direction: str
    segment_index: int
    length_m: float
    heading_in_deg: float = 0.0
    heading_out_deg: float = 0.0
    max_curve_radius_m: float | None = None
    speed_limit_kmh: float
    gradient_pct: float | None = None
    is_curve: bool = False


class TrackSegmentList(TrackSegmentBase):
    id: str

    model_config = {"from_attributes": True}


class TrackSegmentDetail(TrackSegmentList):
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
