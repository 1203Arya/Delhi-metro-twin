from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
    timestamp: datetime


class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None


class SuccessResponse(BaseModel):
    message: str = "Success"


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    skip: int = 0
    limit: int = 100


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    geometry: dict[str, Any]
    properties: dict[str, Any]


class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: list[GeoJSONFeature]
