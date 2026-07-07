"""WKB/WKT <-> Python geometry conversion used by the seed loader.

The seed loader writes geometries via SQLAlchemy as WKB hex (the format
GeoAlchemy2 accepts most cheaply). This module centralises the conversions and
validates them with Shapely so a malformed geometry never reaches the database.
"""

from __future__ import annotations

from typing import Iterable

from shapely import wkb as shp_wkb
from shapely import wkt as shp_wkt
from shapely.geometry.base import BaseGeometry


def to_wkb_hex(geom: BaseGeometry) -> str:
    """Return the little-endian WKB hex of a Shapely geometry.

    GeoAlchemy2's ``ST_GeomFromEWKB`` and the ``Geometry`` type both accept this
    form directly as a bound parameter.
    """
    return geom.wkb_hex


def from_wkb_hex(hexstr: str) -> BaseGeometry:
    return shp_wkb.loads(bytes.fromhex(hexstr))


def to_wkt(geom: BaseGeometry) -> str:
    return geom.wkt


def from_wkt(text: str) -> BaseGeometry:
    return shp_wkt.loads(text)


def ensure_valid(geom: BaseGeometry) -> BaseGeometry:
    """Repair a geometry if PostGIS ``ST_IsValid`` would reject it.

    Offsetting around sharp corners can occasionally self-intersect; this keeps
    the dataset loadable by sending ``buffer(0)`` to unwind the bowties.
    """
    if geom.is_valid:
        return geom
    return geom.buffer(0)


def point_wkt(lon: float, lat: float) -> str:
    return f"POINT({lon} {lat})"


def linestring_wkt(coords: Iterable[tuple[float, float]]) -> str:
    body = ", ".join(f"{lon} {lat}" for lon, lat in coords)
    return f"LINESTRING({body})"


def polygon_wkt(ring: Iterable[tuple[float, float]]) -> str:
    pts = list(ring)
    if pts and pts[0] != pts[-1]:
        pts.append(pts[0])
    body = ", ".join(f"{lon} {lat}" for lon, lat in pts)
    return f"POLYGON(({body}))"
