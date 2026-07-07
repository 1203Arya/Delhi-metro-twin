"""GeoJSON emitters for the Delhi Metro network layers.

Every emitter returns a plain GeoJSON ``FeatureCollection`` dict (RFC 7946),
WGS84 coordinates in ``(lon, lat)`` order — ready to be written to
``gis/layers/*.geojson`` for the tile pipeline or shipped to MapLibre directly.

Layers produced:

* ``lines``       — one Feature per line: a centreline LineString joining the
                    stations, plus line metadata (colour, length, signalling).
* ``stations``    — one Feature per (line, station): Point with interchange +
                    terminus flags and a confidence marker.
* ``track_segments`` — one Feature per direction-of-travel segment: LineString
                    waypoints + length + curve radius + speed limit.
* ``platforms``   — one Feature per platform: aligned rectangle Polygon.
* ``depots``      — one Feature per depot: Point + capacity.
* ``crossovers``  — one Feature per crossover near a junction: short LineString
                    joining up/down centrelines.
* ``junctions``   — one Feature per track-level junction (turnout) Point.
* ``switches``    — one Feature per switch Point, offset slightly from its
                    junction so the map can render the blade orientation.

The emitters are pure and deterministic: feeding them the same
:class:`Network` always yields byte-identical output, so the generated layer
files are reproducible and diff cleanly in git.
"""

from __future__ import annotations

import json
from typing import Any, Iterable

from shapely.geometry import LineString, Point, mapping

from .dataset import DepotSpec, LineSpec, Network, StationSpec
from .geometry import (
    bearing_deg,
    platform_polygon_m,
    station_polygon_m,
)
from .track import TrackBuilder, TrackSegmentGeometry


# ───────────────────────── helpers ─────────────────────────


def _feature(geometry: Any, properties: dict[str, Any]) -> dict[str, Any]:
    return {"type": "Feature", "geometry": mapping(geometry), "properties": properties}


def _collection(features: Iterable[dict[str, Any]]) -> dict[str, Any]:
    return {"type": "FeatureCollection", "features": list(features)}


def _jsonable(o: Any) -> Any:
    """Coerce non-JSON-native types (tuple, frozenset, inf) for serialisation."""
    if isinstance(o, tuple):
        return list(o)
    if isinstance(o, float):
        if o != o:  # NaN
            return None
        if o == float("inf"):
            return None
        return o
    return o


def write_geojson(path_or_buffer, collection: dict[str, Any]) -> None:
    """Write a FeatureCollection as pretty-printed UTF-8 JSON."""
    payload = json.dumps(collection, ensure_ascii=False, indent=2, default=_jsonable)
    if hasattr(path_or_buffer, "write"):
        path_or_buffer.write(payload)
    else:
        from pathlib import Path

        Path(path_or_buffer).write_text(payload, encoding="utf-8")


# ───────────────────────── line centrelines + tracks ─────────────────────────


def _line_centreline(line: LineSpec) -> LineString:
    pts = [(s.longitude, s.latitude) for s in line.stations]
    return LineString(pts)


def emit_lines(network: Network) -> dict[str, Any]:
    """One Feature per line: its station-to-station centreline + metadata."""
    feats: list[dict[str, Any]] = []
    for ln in network.lines:
        line_geom = _line_centreline(ln)
        feats.append(
            _feature(
                line_geom,
                {
                    "line_code": ln.code,
                    "line_name": ln.name,
                    "line_number": ln.number,
                    "color": ln.color_hex,
                    "corridor": ln.corridor,
                    "operator": ln.operator,
                    "gauge_mm": ln.gauge_mm,
                    "electrification": ln.electrification,
                    "signalling": ln.signalling_system,
                    "opened_year": ln.opened_year,
                    "total_length_km": ln.total_length_km,
                    "station_count": ln.total_stations,
                    "is_branch": ln.is_branch,
                },
            )
        )
    return _collection(feats)


def emit_track_segments(network: Network) -> dict[str, Any]:
    """Two Features per inter-station link (up + down) with geometry + physics metadata."""
    feats: list[dict[str, Any]] = []
    for ln in network.lines:
        builder = TrackBuilder(line_code=ln.code)
        stations_lonlat = [(s.name, (s.longitude, s.latitude)) for s in ln.stations]
        for direction in ("up", "down"):
            segs = builder.build_corridor(
                stations_lonlat,
                direction=direction,
                override_speeds=ln.speed_overrides,
                gradients=ln.gradients,
                insert_curve_vertex_at=ln.curve_vertices,
            )
            for idx, seg in enumerate(segs):
                line_geom = LineString(seg.coords)
                feats.append(
                    _feature(
                        line_geom,
                        {
                            "line_code": ln.code,
                            "segment_index": idx,
                            "direction": seg.direction,
                            "from_station": seg.from_station,
                            "to_station": seg.to_station,
                            "length_m": round(seg.length_m, 2),
                            "heading_in_deg": round(seg.heading_in_deg, 2),
                            "heading_out_deg": round(seg.heading_out_deg, 2),
                            "max_curve_radius_m": (
                                round(seg.max_curve_radius_m, 2)
                                if seg.max_curve_radius_m != float("inf")
                                else None
                            ),
                            "speed_limit_kmh": round(seg.speed_limit_kmh, 2),
                            "gradient_pct": round(seg.gradient_pct, 3),
                            "is_curve": seg.is_curve,
                        },
                    )
                )
    return _collection(feats)


# ───────────────────────── stations + platforms ─────────────────────────


def emit_stations(network: Network) -> dict[str, Any]:
    feats: list[dict[str, Any]] = []
    for ln in network.lines:
        order = 0
        for s in ln.stations:
            feats.append(
                _feature(
                    Point((s.longitude, s.latitude)),
                    {
                        "line_code": ln.code,
                        "station_name": s.name,
                        "station_code": s.code,
                        "sequence": order,
                        "structure": s.structure,
                        "interchange_with": list(s.interchange_with),
                        "platforms": s.platforms,
                        "opened_year": s.opened_year,
                        "is_terminus": s.is_terminus,
                        "has_junction": s.has_junction,
                        "coordinate_confidence": s.coordinate_confidence,
                    },
                )
            )
            order += 1
    return _collection(feats)


def emit_platforms(network: Network, *, default_length_m: float = 180.0, default_width_m: float = 6.0) -> dict[str, Any]:
    """One Feature per physical platform, layout-aligned to the running track.

    For an N-platform station we lay them out symmetrically about the
    centreline, alternating sides. The heading is taken from the first segment
    leaving the station (or the last segment arriving, for terminal stations).
    """
    feats: list[dict[str, Any]] = []
    for ln in network.lines:
        for idx, s in enumerate(ln.stations):
            heading = _heading_for_station(ln, idx)
            for plat_no in range(1, s.platforms + 1):
                # Alternate sides of the centreline, spacing platforms ~5m apart.
                side = 1 if plat_no % 2 == 1 else -1
                offset_m = side * (2.5 + 5.0 * ((plat_no - 1) // 2))
                poly = platform_polygon_m(
                    (s.longitude, s.latitude),
                    length_m=default_length_m,
                    width_m=default_width_m,
                    heading_deg=heading,
                    offset_left_m=offset_m,
                )
                feats.append(
                    _feature(
                        poly,
                        {
                            "line_code": ln.code,
                            "station_code": s.code,
                            "station_name": s.name,
                            "platform_number": plat_no,
                            "heading_deg": round(heading, 2),
                            "is_edge_platform": plat_no in (1, s.platforms),
                        },
                    )
                )
    return _collection(feats)


def _heading_for_station(line: LineSpec, idx: int) -> float:
    """Best compass heading through a station — from the adjacent segment(s)."""
    n = len(line.stations)
    if idx < n - 1:
        here = line.stations[idx]
        nxt = line.stations[idx + 1]
        return bearing_deg(here.lonlat, nxt.lonlat)
    if idx > 0:
        prev = line.stations[idx - 1]
        here = line.stations[idx]
        return bearing_deg(prev.lonlat, here.lonlat)
    return 0.0


# ───────────────────────── depots ─────────────────────────


def emit_depots(network: Network) -> dict[str, Any]:
    feats: list[dict[str, Any]] = []
    for ln in network.lines:
        for d in ln.depots:
            feats.append(
                _feature(
                    Point((d.longitude, d.latitude)),
                    {
                        "line_code": ln.code,
                        "depot_name": d.name,
                        "area_m2": d.area_m2,
                        "capacity_stabling": d.capacity_stabling,
                        "coordinate_confidence": d.coordinate_confidence,
                    },
                )
            )
    return _collection(feats)


# ───────────────────────── crossovers / junctions / switches ─────────────────────────


def emit_crossovers(network: Network, *, offset_m: float = 8.0) -> dict[str, Any]:
    """One short cross-over Feature per station that sits on a junction.

    These are nominal links between the up and down centrelines at every
    station — enough for the simulation's signalling engine and the map to
    represent train reversals and short-turns. With surveyed turnout positions
    the curve_vertices dataset can refine them.
    """
    feats: list[dict[str, Any]] = []
    for ln in network.lines:
        for idx, s in enumerate(ln.stations):
            heading = _heading_for_station(ln, idx)
            # Project the perpendicular to the heading by ±offset_m around the station.
            import math

            th = math.radians(heading + 90.0)
            # The two endpoints sit on the up/down centrelines, offset across the station.
            ahead = _offset_point(s, heading, offset_m * 3.0)
            cross_up = _offset_point(s, heading + 90.0, offset_m)
            cross_down = _offset_point(s, heading - 90.0, offset_m)
            line_geom = LineString([cross_up, ahead, cross_down])
            feats.append(
                _feature(
                    line_geom,
                    {
                        "line_code": ln.code,
                        "station_code": s.code,
                        "station_name": s.name,
                        "heading_deg": round(heading, 2),
                        "kind": "crossover",
                    },
                )
            )
            # unused but documents intent
            _ = th
    return _collection(feats)


def _offset_point(station: StationSpec, heading_deg: float, distance_m: float) -> tuple[float, float]:
    """Move a station point along a compass heading by ``distance_m`` metres (WGS84 out)."""
    import math

    # Use a metre-per-degree approximation at Delhi's latitude; precise enough
    # for the small offsets used here (<100 m). The geometry module's UTM path
    # is the authoritative one for larger offsets.
    lat_rad = math.radians(station.latitude)
    dlat = (distance_m * math.cos(math.radians(heading_deg))) / 111_320.0
    dlon = (distance_m * math.sin(math.radians(heading_deg))) / (111_320.0 * math.cos(lat_rad))
    return (station.longitude + dlon, station.latitude + dlat)


def emit_junctions(network: Network) -> dict[str, Any]:
    """One Feature per track-level junction (interchange + flagged turnouts)."""
    feats: list[dict[str, Any]] = []
    seen: set[str] = set()
    for ln in network.lines:
        for s in ln.stations:
            is_interchange = bool(s.interchange_with)
            if not (s.has_junction or is_interchange):
                continue
            key = f"{s.code}"
            if key in seen:
                feats_by_key = {f["properties"]["junction_code"]: f for f in feats}
                # Merge: record additional line ownership.
                existing = feats_by_key.get(key)
                if existing is not None:
                    existing["properties"]["lines"].append(ln.code)
                    continue
            seen.add(key)
            feats.append(
                _feature(
                    Point((s.longitude, s.latitude)),
                    {
                        "junction_code": s.code,
                        "junction_name": s.name,
                        "lines": [ln.code],
                        "is_interchange": is_interchange,
                        "is_turnout": s.has_junction,
                    },
                )
            )
    return _collection(feats)


def emit_switches(network: Network) -> dict[str, Any]:
    """One Feature per railway switch (point blade), offset from its junction."""
    feats: list[dict[str, Any]] = []
    for ln in network.lines:
        for idx, s in enumerate(ln.stations):
            if not (s.has_junction or s.interchange_with):
                continue
            heading = _heading_for_station(ln, idx)
            # A junction typically presents two facing switches ~30 m apart.
            for side, label in ((-1, "entry"), (1, "exit")):
                pos = _offset_point(s, heading, side * 30.0)
                feats.append(
                    _feature(
                        Point(pos),
                        {
                            "line_code": ln.code,
                            "junction_code": s.code,
                            "switch_label": label,
                            "heading_deg": round(heading, 2),
                        },
                    )
                )
    return _collection(feats)


# ───────────────────────── all-in-one ─────────────────────────


def emit_all(network: Network) -> dict[str, str]:
    """Return every layer as a dict keyed by layer name (``stations`` → FeatureCollection)."""
    return {
        "lines": emit_lines(network),
        "stations": emit_stations(network),
        "track_segments": emit_track_segments(network),
        "platforms": emit_platforms(network),
        "depots": emit_depots(network),
        "crossovers": emit_crossovers(network),
        "junctions": emit_junctions(network),
        "switches": emit_switches(network),
    }
