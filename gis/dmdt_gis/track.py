"""Build track-segment geometries from ordered station waypoints.

A "track segment" in this twin is the running rail between two consecutive
stations on a direction of travel. Each segment carries:

* an explicit ``LineString`` of ``(lon,lat)`` waypoints — straight-aligned by
  default, with inserted intermediate vertices where the corridor curves (so
  curvature radius at each vertex is well defined);
* ``length_m`` from UTM planar integration;
* ``max_curve_radius_m`` (tightest radius on the segment) and the derived
  ``speed_limit_kmh`` — DMRC's curve-speed rule of thumb: comfortable
  cant-balance limit sets ~v = sqrt(127 * R * cant_balance); for Delhi broad
  gauge with cant deficiency ≈ 100mm the practically-observed line speed on
  curves is sqrt(127 * R * 0.085), capped at the line's design speed.
* ``gradient_pct`` (0.0 at-grade unless the dataset overrides for ramps).

The two directions of travel (up/down) share the same centreline geometry but
get their own rows so signalling and timetable logic can address them
independently.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Sequence

from .geometry import (
    Curvature,
    bearing_deg,
    max_curvature_segment,
    polyline_length_m,
)


# Approximate DMRC operating speed envelopes (km/h). These are network-wide
# defaults; per-segment overrides live in the dataset.
_LINE_DESIGN_SPEED_KMH: dict[str, float] = {
    "RD": 80.0,  # Red — surface/elevated, broad-gauge
    "YL": 80.0,
    "BL": 80.0,  # Blue — underground section ~80 peak
    "BR": 80.0,
    "GR": 75.0,  # Green — standard gauge, lighter corridor
    "GB": 75.0,
    "VL": 80.0,
    "PK": 80.0,
    "MG": 80.0,
    "GY": 80.0,  # Grey — elevated spur
    "OR": 120.0,  # Airport Express — premium high-speed (Alstom, design 135/operational 120)
    "RM": 80.0,  # Rapid Metro Gurugram
}


def design_speed_kmh(line_code: str) -> float:
    return _LINE_DESIGN_SPEED_KMH.get(line_code, 80.0)


@dataclass(frozen=True, slots=True)
class TrackSegmentGeometry:
    from_station: str
    to_station: str
    direction: str  # "up" | "down"
    waypoints_lonlat: tuple[tuple[float, float], ...]
    length_m: float
    heading_in_deg: float
    heading_out_deg: float
    max_curve_radius_m: float
    speed_limit_kmh: float
    gradient_pct: float
    is_curve: bool

    @property
    def coords(self) -> list[tuple[float, float]]:
        return list(self.waypoints_lonlat)


def _curve_speed_kmh(radius_m: float, line_speed_kmh: float) -> float:
    """Per-segment speed limit from osculating-circle radius.

    Uses the Delhi-network cant-balance approximation: a tight 150 m radius
    caps speed near 40 km/h; a gentle 1500 m curve is effectively the line
    speed; anything above ~3000 m is treated as "straight" at line speed.
    """
    if math.isinf(radius_m) or radius_m >= 3000.0:
        return line_speed_kmh
    # v = sqrt(127 * R * e) with e = 0.085 (8.5% cant/deficiency blend, broad & std gauge)
    v = math.sqrt(127.0 * radius_m * 0.085) * 3.6
    return min(v, line_speed_kmh)


@dataclass
class TrackBuilder:
    """Accumulates a corridor's track segments from an ordered station list."""

    line_code: str
    line_speed_kmh: float = field(default=0.0)
    segments: list[TrackSegmentGeometry] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.line_speed_kmh == 0.0:
            self.line_speed_kmh = design_speed_kmh(self.line_code)

    def add_segment(
        self,
        from_station: str,
        to_station: str,
        direction: str,
        waypoints: Sequence[tuple[float, float]],
        *,
        gradient_pct: float = 0.0,
        override_speed_kmh: float | None = None,
        max_curve_radius_m: float | None = None,
    ) -> TrackSegmentGeometry:
        if len(waypoints) < 2:
            raise ValueError(
                f"segment {from_station}->{to_station} needs >=2 waypoints"
            )
        wps = tuple(waypoints)
        length = polyline_length_m(list(wps))
        h_in = bearing_deg(wps[0], wps[1])
        h_out = bearing_deg(wps[-2], wps[-1])
        curve: Curvature = (
            Curvature(max_curve_radius_m, 0.0)
            if max_curve_radius_m is not None
            else max_curvature_segment(list(wps))
        )
        base_speed = (
            override_speed_kmh
            if override_speed_kmh is not None
            else self.line_speed_kmh
        )
        limit = _curve_speed_kmh(curve.radius_m, base_speed)
        seg = TrackSegmentGeometry(
            from_station=from_station,
            to_station=to_station,
            direction=direction,
            waypoints_lonlat=wps,
            length_m=length,
            heading_in_deg=h_in,
            heading_out_deg=h_out,
            max_curve_radius_m=curve.radius_m,
            speed_limit_kmh=limit,
            gradient_pct=gradient_pct,
            is_curve=not curve.is_straight,
        )
        self.segments.append(seg)
        return seg

    def build_corridor(
        self,
        stations_lonlat: Sequence[tuple[str, tuple[float, float]]],
        direction: str = "up",
        *,
        override_speeds: dict[tuple[str, str], float] | None = None,
        gradients: dict[tuple[str, str], float] | None = None,
        insert_curve_vertex_at: dict[tuple[str, str], list[tuple[float, float]]]
        | None = None,
    ) -> list[TrackSegmentGeometry]:
        """Build all segments of a corridor from an ordered (name,(lon,lat)) list.

        ``insert_curve_vertex_at`` lets the dataset inject intermediate
        waypoints on a known curve so the osculating-circle radius is real
        rather than inferred from two terminal stations. This is how corridors
        like the Yellow Line's airport loop get their curvature captured
        without needing a dense surveyed polyline of every rail joint.
        """
        override_speeds = override_speeds or {}
        gradients = gradients or {}
        insert_curve_vertex_at = insert_curve_vertex_at or {}
        built: list[TrackSegmentGeometry] = []
        for i in range(len(stations_lonlat) - 1):
            name_a, (lon_a, lat_a) = stations_lonlat[i]
            name_b, (lon_b, lat_b) = stations_lonlat[i + 1]
            key = (name_a, name_b)
            waypoints: list[tuple[float, float]] = [(lon_a, lat_a)]
            waypoints.extend(insert_curve_vertex_at.get(key, []))
            waypoints.append((lon_b, lat_b))
            seg = self.add_segment(
                name_a,
                name_b,
                direction,
                waypoints,
                gradient_pct=gradients.get(key, 0.0),
                override_speed_kmh=override_speeds.get(key),
            )
            built.append(seg)
        return built
