from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Sequence

from shapely.geometry import LineString, MultiLineString, Point, Polygon, mapping
from shapely import is_valid_reason

from .crs import lonlat_to_utm, utm_to_lonlat
from .dataset import DepotSpec, LineSpec, Network, StationSpec
from .geometry import (
    bearing_deg,
    curvature_radius_m,
    haversine_m,
    offset_linestring_m,
    planar_distance_m,
    platform_polygon_m,
    polyline_length_m,
    station_polygon_m,
)
from .track import TrackBuilder, TrackSegmentGeometry, design_speed_kmh
from .validation import (
    validate_coordinate,
    validate_depot,
    validate_platform_polygon,
    validate_station,
    validate_station_polygon,
    validate_track_segment,
)


@dataclass(frozen=True)
class StationGeometry:
    station: StationSpec
    point: Point
    polygon: Polygon
    utm_easting: float
    utm_northing: float

    @classmethod
    def build(cls, station: StationSpec, heading_deg: float = 0.0) -> StationGeometry:
        vs = validate_station(station)
        vs.raise_if_invalid()
        pt = Point((station.longitude, station.latitude))
        if not pt.is_valid:
            raise ValueError(f"station {station.code}: invalid point geometry")
        poly = station_polygon_m(
            (station.longitude, station.latitude),
            length_m=200.0,
            width_m=30.0,
            heading_deg=heading_deg,
        )
        if not poly.is_valid:
            raise ValueError(f"station {station.code}: polygon invalid ({is_valid_reason(poly)})")
        easting, northing = lonlat_to_utm(station.longitude, station.latitude)
        return cls(
            station=station,
            point=pt,
            polygon=poly,
            utm_easting=round(easting, 3),
            utm_northing=round(northing, 3),
        )


@dataclass(frozen=True)
class PlatformGeometry:
    station: StationSpec
    platform_number: int
    polygon: Polygon
    heading_deg: float
    length_m: float
    width_m: float
    offset_left_m: float
    is_edge_platform: bool

    @classmethod
    def build(
        cls,
        station: StationSpec,
        platform_number: int,
        heading_deg: float,
        length_m: float = 180.0,
        width_m: float = 6.0,
    ) -> PlatformGeometry:
        vs = validate_station(station)
        vs.raise_if_invalid()
        side = 1 if platform_number % 2 == 1 else -1
        offset_m = side * (2.5 + 5.0 * ((platform_number - 1) // 2))
        vp = validate_platform_polygon(
            station, platform_number, heading_deg, length_m=length_m, width_m=width_m
        )
        vp.raise_if_invalid()
        poly = platform_polygon_m(
            (station.longitude, station.latitude),
            length_m=length_m,
            width_m=width_m,
            heading_deg=heading_deg,
            offset_left_m=offset_m,
        )
        if not poly.is_valid:
            raise ValueError(
                f"platform {station.code}-{platform_number}: polygon invalid ({is_valid_reason(poly)})"
            )
        return cls(
            station=station,
            platform_number=platform_number,
            polygon=poly,
            heading_deg=heading_deg,
            length_m=length_m,
            width_m=width_m,
            offset_left_m=offset_m,
            is_edge_platform=platform_number in (1, station.platforms),
        )


@dataclass(frozen=True)
class TrackGeometry:
    segment: TrackSegmentGeometry
    linestring: LineString
    curvature_at_vertices: tuple[float, ...]
    total_length_m: float

    @classmethod
    def build(cls, segment: TrackSegmentGeometry) -> TrackGeometry:
        vt = validate_track_segment(segment)
        vt.raise_if_invalid()
        coords_lonlat = list(segment.coords)
        ls = LineString(coords_lonlat)
        if not ls.is_valid:
            raise ValueError(
                f"track {segment.from_station}->{segment.to_station}: invalid linestring"
            )
        curvatures: list[float] = []
        for i in range(1, len(coords_lonlat) - 1):
            prev_pt = coords_lonlat[i - 1]
            curr_pt = coords_lonlat[i]
            next_pt = coords_lonlat[i + 1]
            cr = curvature_radius_m(
                (prev_pt[1], prev_pt[0]),
                (curr_pt[1], curr_pt[0]),
                (next_pt[1], next_pt[0]),
            )
            curvatures.append(cr.radius_m if cr.radius_m is not None else float("inf"))
        total_m = polyline_length_m([(c[1], c[0]) for c in coords_lonlat])
        return cls(
            segment=segment,
            linestring=ls,
            curvature_at_vertices=tuple(curvatures),
            total_length_m=total_m,
        )


@dataclass(frozen=True)
class DepotGeometry:
    depot: DepotSpec
    point: Point
    utm_easting: float
    utm_northing: float

    @classmethod
    def build(cls, depot: DepotSpec) -> DepotGeometry:
        vd = validate_depot(depot)
        vd.raise_if_invalid()
        pt = Point((depot.longitude, depot.latitude))
        if not pt.is_valid:
            raise ValueError(f"depot {depot.name}: invalid point geometry")
        easting, northing = lonlat_to_utm(depot.longitude, depot.latitude)
        return cls(
            depot=depot,
            point=pt,
            utm_easting=round(easting, 3),
            utm_northing=round(northing, 3),
        )


@dataclass(frozen=True)
class SidingGeometry:
    name: str
    depot: DepotSpec
    linestring: LineString
    length_m: float
    capacity_trains: int

    @classmethod
    def build(
        cls,
        name: str,
        depot: DepotSpec,
        from_lonlat: tuple[float, float],
        to_lonlat: tuple[float, float],
        capacity_trains: int = 1,
    ) -> SidingGeometry:
        vd = validate_depot(depot)
        vd.raise_if_invalid()
        ls = LineString([from_lonlat, to_lonlat])
        if not ls.is_valid:
            raise ValueError(f"siding {name}: invalid linestring")
        length_m = planar_distance_m(from_lonlat, to_lonlat)
        if length_m < 10:
            raise ValueError(f"siding {name}: too short ({length_m:.0f}m)")
        return cls(
            name=name,
            depot=depot,
            linestring=ls,
            length_m=round(length_m, 2),
            capacity_trains=capacity_trains,
        )


@dataclass(frozen=True)
class JunctionGeometry:
    name: str
    station: StationSpec
    point: Point
    is_interchange: bool
    is_turnout: bool
    lines: tuple[str, ...]

    @classmethod
    def build(
        cls,
        name: str,
        station: StationSpec,
        lines: Sequence[str],
        is_turnout: bool = False,
    ) -> JunctionGeometry:
        vs = validate_station(station)
        vs.raise_if_invalid()
        pt = Point((station.longitude, station.latitude))
        if not pt.is_valid:
            raise ValueError(f"junction {name}: invalid point geometry")
        is_interchange = len(lines) > 1
        return cls(
            name=name,
            station=station,
            point=pt,
            is_interchange=is_interchange,
            is_turnout=is_turnout,
            lines=tuple(lines),
        )


@dataclass(frozen=True)
class CrossoverGeometry:
    name: str
    station: StationSpec
    linestring: LineString
    heading_deg: float

    @classmethod
    def build(
        cls,
        name: str,
        station: StationSpec,
        heading_deg: float,
        offset_m: float = 8.0,
    ) -> CrossoverGeometry:
        vs = validate_station(station)
        vs.raise_if_invalid()
        th = math.radians(heading_deg + 90.0)
        _ = th
        ahead = _offset_point_lonlat(station.longitude, station.latitude, heading_deg, offset_m * 3.0)
        cross_up = _offset_point_lonlat(
            station.longitude, station.latitude, heading_deg + 90.0, offset_m
        )
        cross_down = _offset_point_lonlat(
            station.longitude, station.latitude, heading_deg - 90.0, offset_m
        )
        ls = LineString([cross_up, ahead, cross_down])
        if not ls.is_valid:
            raise ValueError(f"crossover {name}: invalid linestring")
        return cls(name=name, station=station, linestring=ls, heading_deg=heading_deg)


@dataclass(frozen=True)
class SwitchGeometry:
    name: str
    junction: JunctionGeometry
    point: Point
    switch_label: str
    heading_deg: float

    @classmethod
    def build(
        cls,
        name: str,
        junction: JunctionGeometry,
        switch_label: str,
        heading_deg: float,
        offset_m: float = 30.0,
    ) -> SwitchGeometry:
        side = -1 if switch_label == "entry" else 1
        lon, lat = junction.station.longitude, junction.station.latitude
        pos = _offset_point_lonlat(lon, lat, heading_deg, side * offset_m)
        pt = Point(pos)
        if not pt.is_valid:
            raise ValueError(f"switch {name}: invalid point geometry")
        return cls(
            name=name,
            junction=junction,
            point=pt,
            switch_label=switch_label,
            heading_deg=heading_deg,
        )


def _offset_point_lonlat(
    lon: float, lat: float, heading_deg: float, distance_m: float
) -> tuple[float, float]:
    lat_rad = math.radians(lat)
    dlat = (distance_m * math.cos(math.radians(heading_deg))) / 111_320.0
    dlon = (distance_m * math.sin(math.radians(heading_deg))) / (111_320.0 * math.cos(lat_rad))
    return (lon + dlon, lat + dlat)


def build_all_station_geometries(network: Network) -> dict[str, list[StationGeometry]]:
    result: dict[str, list[StationGeometry]] = {}
    for line in network.lines:
        geoms: list[StationGeometry] = []
        for idx, station in enumerate(line.stations):
            heading = _heading_at_station(line, idx)
            geoms.append(StationGeometry.build(station, heading_deg=heading))
        result[line.code] = geoms
    return result


def build_all_platform_geometries(
    network: Network,
    default_length_m: float = 180.0,
    default_width_m: float = 6.0,
) -> dict[str, list[PlatformGeometry]]:
    result: dict[str, list[PlatformGeometry]] = {}
    for line in network.lines:
        geoms: list[PlatformGeometry] = []
        for idx, station in enumerate(line.stations):
            heading = _heading_at_station(line, idx)
            for pn in range(1, station.platforms + 1):
                geoms.append(
                    PlatformGeometry.build(
                        station, pn, heading, length_m=default_length_m, width_m=default_width_m
                    )
                )
        result[line.code] = geoms
    return result


def build_all_track_geometries(network: Network) -> dict[str, list[TrackGeometry]]:
    result: dict[str, list[TrackGeometry]] = {}
    for line in network.lines:
        geoms: list[TrackGeometry] = []
        builder = TrackBuilder(line_code=line.code)
        stations_lonlat = [(s.name, (s.longitude, s.latitude)) for s in line.stations]
        for direction in ("up", "down"):
            segs = builder.build_corridor(
                stations_lonlat,
                direction=direction,
                override_speeds=line.speed_overrides,
                gradients=line.gradients,
                insert_curve_vertex_at=line.curve_vertices,
            )
            for seg in segs:
                geoms.append(TrackGeometry.build(seg))
        result[line.code] = geoms
    return result


def build_all_depot_geometries(network: Network) -> dict[str, list[DepotGeometry]]:
    result: dict[str, list[DepotGeometry]] = {}
    for line in network.lines:
        result[line.code] = [DepotGeometry.build(d) for d in line.depots]
    return result


def build_all_junction_geometries(network: Network) -> dict[str, list[JunctionGeometry]]:
    result: dict[str, list[JunctionGeometry]] = {}
    seen: dict[str, set[str]] = {}
    for line in network.lines:
        geoms: list[JunctionGeometry] = []
        for station in line.stations:
            if not (station.has_junction or station.interchange_with):
                continue
            key = station.code
            if key not in seen:
                seen[key] = set()
            seen[key].add(line.code)
            lines = list(seen[key])
            is_turnout = station.has_junction
            geoms.append(
                JunctionGeometry.build(
                    name=station.name,
                    station=station,
                    lines=lines,
                    is_turnout=is_turnout,
                )
            )
        result[line.code] = geoms
    return result


def build_all_crossover_geometries(network: Network) -> dict[str, list[CrossoverGeometry]]:
    result: dict[str, list[CrossoverGeometry]] = {}
    for line in network.lines:
        geoms: list[CrossoverGeometry] = []
        for idx, station in enumerate(line.stations):
            heading = _heading_at_station(line, idx)
            geoms.append(
                CrossoverGeometry.build(
                    name=f"{line.code}_{station.code}",
                    station=station,
                    heading_deg=heading,
                )
            )
        result[line.code] = geoms
    return result


def _heading_at_station(line: LineSpec, idx: int) -> float:
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
