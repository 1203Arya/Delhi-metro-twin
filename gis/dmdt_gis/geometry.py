"""Pure geometry primitives for the Delhi Metro twin.

Everything here is a side-effect-free function operating on plain ``(lon, lat)``
tuples or Shapely geometries. Nothing reads files or hits the network, so the
whole module is unit-testable in milliseconds.

All metric computations (distance, length, area, curvature radius, offsetting)
are performed in UTM 43N (EPSG:32643); see :mod:`dmdt_gis.crs`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence

from shapely.geometry import LineString, Polygon, box
from shapely.ops import transform as shp_transform

from .crs import UTM43N, WGS84, transformer

# WGS84 ellipsoid radius of the Earth in metres. Used by the haversine and
# spherical-area helpers so they remain correct even if the dataset ever leaves
# the UTM zone (it currently never does).
_EARTH_R = 6_378_137.0


# ───────────────────────── bearings / distance ─────────────────────────


def bearing_deg(start: tuple[float, float], end: tuple[float, float]) -> float:
    """Initial great-circle bearing from ``start`` to ``end`` in compass degrees.

    Inputs are ``(lon, lat)`` in WGS84 decimal degrees; result is 0..360 with 0°
    = due north, 90° = due east (a standard `ST_Azimuth`-compatible convention).
    """
    lon1, lat1 = math.radians(start[0]), math.radians(start[1])
    lon2, lat2 = math.radians(end[0]), math.radians(end[1])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(
        dlon
    )
    brng = math.degrees(math.atan2(x, y))
    return (brng + 360.0) % 360.0


def turning_deg(
    prev: tuple[float, float], curr: tuple[float, float], nxt: tuple[float, float]
) -> float:
    """Signed turning angle at ``curr`` between segment (prev→curr) and (curr→nxt).

    Returns degrees in (-180, 180]; positive = turn to the right of travel,
    negative = turn to the left. 0.0 means the track is perfectly straight
    through the vertex.
    """
    b1 = bearing_deg(prev, curr)
    b2 = bearing_deg(curr, nxt)
    delta = (b2 - b1 + 540.0) % 360.0 - 180.0
    return delta


def haversine_m(start: tuple[float, float], end: tuple[float, float]) -> float:
    """Great-circle distance in metres between two ``(lon, lat)`` points."""
    lon1, lat1 = math.radians(start[0]), math.radians(start[1])
    lon2, lat2 = math.radians(end[0]), math.radians(end[1])
    dlon, dlat = lon2 - lon1, lat2 - lat1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * _EARTH_R * math.asin(math.sqrt(a))


def planar_distance_m(start: tuple[float, float], end: tuple[float, float]) -> float:
    """Euclidean distance in metres between two ``(lon, lat)`` points via UTM.

    For a local network the haversine and planar methods agree to <0.1m up to a
    few hundred kilometres; we use the planar version where it composes cleanly
    with offsets and area calculations.
    """
    x1, y1 = transformer(WGS84, UTM43N).transform(start[0], start[1])
    x2, y2 = transformer(WGS84, UTM43N).transform(end[0], end[1])
    return math.hypot(x2 - x1, y2 - y1)


def polyline_length_m(points: Sequence[tuple[float, float]]) -> float:
    """Length in metres of a polyline of ``(lon, lat)`` vertices."""
    return sum(
        planar_distance_m(points[i], points[i + 1]) for i in range(len(points) - 1)
    )


# ───────────────────────── curvature ─────────────────────────


@dataclass(frozen=True, slots=True)
class Curvature:
    """Curvature descriptor at a vertex of a polyline.

    ``radius_m`` is the radius of the osculating circle (m); ``"" curves have
    ``math.inf`` radius. ``deflection_deg`` is the unsigned turning angle.
    """

    radius_m: float
    deflection_deg: float

    @property
    def is_straight(self) -> bool:
        return math.isinf(self.radius_m) or self.radius_m > 10_000.0


def curvature_radius_m(
    prev: tuple[float, float], curr: tuple[float, float], nxt: tuple[float, float]
) -> Curvature:
    """Radius of the osculating circle at ``curr`` for the polyline (prev,curr,nxt).

    The three points are projected to UTM and the circumradius of the triangle
    they form is returned. Collinear points yield an infinite radius (straight).
    """
    px, py = transformer(WGS84, UTM43N).transform(prev[0], prev[1])
    cx, cy = transformer(WGS84, UTM43N).transform(curr[0], curr[1])
    nx, ny = transformer(WGS84, UTM43N).transform(nxt[0], nxt[1])

    a = math.hypot(cx - px, cy - py)
    b = math.hypot(nx - cx, ny - cy)
    c = math.hypot(nx - px, ny - py)
    if a == 0 or b == 0 or c == 0:
        return Curvature(math.inf, 0.0)

    # Area of the triangle via the shoelace formula.
    area = 0.5 * abs((px - nx) * (ny - cy) - (cx - nx) * (py - ny))
    if area < 1e-6:
        return Curvature(math.inf, 0.0)

    radius = (a * b * c) / (4.0 * area)
    return Curvature(radius, abs(turning_deg(prev, curr, nxt)))


def max_curvature_segment(points: Sequence[tuple[float, float]]) -> Curvature:
    """Most severe (smallest-radius) curvature across a polyline.

    The radius is dimensionally the same notion DMRC signalling design uses for
    speed limits on curves: tighter radius ⇒ lower permitted speed.
    """
    if len(points) < 3:
        return Curvature(math.inf, 0.0)
    return min(
        (
            curvature_radius_m(points[i - 1], points[i], points[i + 1])
            for i in range(1, len(points) - 1)
        ),
        key=lambda c: c.radius_m,
    )


# ───────────────────────── offsetting / polygons ─────────────────────────


def _to_utm_linestring(points: Sequence[tuple[float, float]]) -> LineString:
    xs, ys = transformer(WGS84, UTM43N).transform(
        [p[0] for p in points], [p[1] for p in points]
    )
    return LineString(zip(xs, ys))


def _from_utm_geom(geom):
    return shp_transform(transformer(UTM43N, WGS84).transform, geom)


def offset_linestring_m(
    pts: Sequence[tuple[float, float]], left_m: float
) -> list[tuple[float, float]]:
    """Offset a polyline laterally by ``left_m`` metres (positive = left of travel).

    Returns a new list of ``(lon, lat)`` waypoints. Used to build the "up" and
    "down" tracks of a corridor from a single centreline, and to lay out
    platform polygons parallel to the track.
    """
    if len(pts) < 2:
        return list(pts)
    line = _to_utm_linestring(pts)
    # Shapely's parallel_offset: right side with negative distance == left side.
    off = line.parallel_offset(
        distance=abs(left_m), side="left" if left_m >= 0 else "right"
    )
    if off.is_empty:
        return list(pts)
    if off.geom_type == "LineString":
        return [(x, y) for x, y in _from_utm_geom(off).coords]
    # parallel_offset can return a MultiLineString around sharp self-intersections;
    # take the longest piece to keep the offset single-valued.
    longest = max(off.geoms, key=lambda g: g.length)
    return [(x, y) for x, y in _from_utm_geom(longest).coords]


def station_polygon_m(
    center: tuple[float, float], *, length_m: float, width_m: float, heading_deg: float
) -> Polygon:
    """Build an aligned station-footprint rectangle centred on ``center``.

    ``heading_deg`` is the compass heading of the track through the station; the
    rectangle's long axis is rotated to match it. The polygon is returned in
    WGS84 so it can be stored directly in a PostGIS ``GEOGRAPHY(POLYGON)`` column.
    """
    hx, hy = transformer(WGS84, UTM43N).transform(center[0], center[1])
    th = math.radians(heading_deg)
    cos_t, sin_t = math.cos(th), math.sin(th)
    half_l, half_w = length_m / 2.0, width_m / 2.0

    def rot(dx: float, dy: float) -> tuple[float, float]:
        return (hx + dx * cos_t - dy * sin_t, hy + dx * sin_t + dy * cos_t)

    corners = [
        rot(-half_l, -half_w),
        rot(half_l, -half_w),
        rot(half_l, half_w),
        rot(-half_l, half_w),
        rot(-half_l, -half_w),
    ]
    xs, ys = transformer(UTM43N, WGS84).transform(
        [c[0] for c in corners], [c[1] for c in corners]
    )
    return Polygon(zip(xs, ys))


def platform_polygon_m(
    center: tuple[float, float],
    *,
    length_m: float,
    width_m: float,
    heading_deg: float,
    offset_left_m: float = 0.0,
) -> Polygon:
    """Build a platform footprint rectangle, offset laterally from the track centreline.

    A metro platform is typically 180 m long and 3–10 m wide, sitting a few
    metres to the side of the running rails. The ``offset_left_m`` argument
    shifts the rectangle perpendicular to the heading.
    """
    if offset_left_m:
        # Shift centre perpendicular to heading before drawing.
        hx, hy = transformer(WGS84, UTM43N).transform(center[0], center[1])
        th = math.radians(heading_deg + 90.0)
        nx = hx + offset_left_m * math.cos(th)
        ny = hy + offset_left_m * math.sin(th)
        wx, wy = transformer(UTM43N, WGS84).transform(nx, ny)
        center = (wx, wy)
    return station_polygon_m(
        center, length_m=length_m, width_m=width_m, heading_deg=heading_deg
    )


def bounding_box(
    lon_min: float, lat_min: float, lon_max: float, lat_max: float
) -> Polygon:
    """WGS84 bounding box, used by the tile emitter and spatial pre-filters."""
    return box(lon_min, lat_min, lon_max, lat_max)


def envelope_of(pts: Iterable[tuple[float, float]]) -> Polygon:
    """WGS84 envelope of a point set, returned as a (possibly rotated) axis box.

    Implemented as the axis-aligned bounding box in UTM, reprojected back to
    WGS84 — this is what the tile pipeline asks for and what PostGIS
    ``ST_Envelope`` would return for the stored geometry.
    """
    xs_utm, ys_utm = [], []
    for lon, lat in pts:
        x, y = transformer(WGS84, UTM43N).transform(lon, lat)
        xs_utm.append(x)
        ys_utm.append(y)
    if not xs_utm:
        raise ValueError("envelope_of: empty point set")
    poly = box(min(xs_utm), min(ys_utm), max(xs_utm), max(ys_utm))
    return _from_utm_geom(poly)
