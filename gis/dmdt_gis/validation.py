from __future__ import annotations

from dataclasses import dataclass

from shapely import is_valid_reason

from .dataset import (
    DepotSpec,
    LineSpec,
    Network,
    StationSpec,
    load_network,
)
from .geometry import (
    curvature_radius_m,
    haversine_m,
    platform_polygon_m,
    station_polygon_m,
)
from .track import TrackBuilder, TrackSegmentGeometry

DELHI_LAT_MIN = 28.38
DELHI_LAT_MAX = 28.80
DELHI_LON_MIN = 76.80
DELHI_LON_MAX = 77.45

MAX_STATION_SPACING_KM = 5.0
MIN_STATION_SPACING_M = 300.0
MAX_DEPOT_AREA_M2 = 500_000
MAX_PLATFORM_LENGTH_M = 320
MAX_PLATFORM_WIDTH_M = 20
MAX_CURVATURE_DEG_PER_100M = 15.0
MAX_TRACK_GRADIENT_PCT = 4.0


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def __bool__(self) -> bool:
        return self.valid

    def raise_if_invalid(self) -> None:
        if not self.valid:
            raise ValueError("; ".join(self.errors))


def _in_delhi(lat: float, lon: float) -> bool:
    return (
        DELHI_LAT_MIN <= lat <= DELHI_LAT_MAX and DELHI_LON_MIN <= lon <= DELHI_LON_MAX
    )


def validate_coordinate(lat: float, lon: float, label: str = "") -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    if not (-90 <= lat <= 90):
        errors.append(f"{label}: latitude {lat} out of range [-90, 90]")
    if not (-180 <= lon <= 180):
        errors.append(f"{label}: longitude {lon} out of range [-180, 180]")
    if not _in_delhi(lat, lon):
        warnings.append(f"{label}: ({lat}, {lon}) outside Delhi NCR bounding box")
    return ValidationResult(
        valid=not errors, errors=tuple(errors), warnings=tuple(warnings)
    )


def validate_station(station: StationSpec) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    cv = validate_coordinate(
        station.latitude, station.longitude, f"station {station.code}"
    )
    errors.extend(cv.errors)
    warnings.extend(cv.warnings)
    if station.structure not in ("elevated", "underground", "at-grade"):
        errors.append(
            f"station {station.code}: invalid structure {station.structure!r}"
        )
    if station.platforms < 1:
        errors.append(f"station {station.code}: platforms must be >= 1")
    if station.platforms > 8:
        warnings.append(
            f"station {station.code}: unusually high platform count ({station.platforms})"
        )
    if station.opened_year < 2000:
        warnings.append(
            f"station {station.code}: opened_year {station.opened_year} seems early"
        )
    if station.opened_year > 2030:
        warnings.append(
            f"station {station.code}: opened_year {station.opened_year} in the future"
        )
    return ValidationResult(
        valid=not errors, errors=tuple(errors), warnings=tuple(warnings)
    )


def validate_depot(depot: DepotSpec) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    cv = validate_coordinate(depot.latitude, depot.longitude, f"depot {depot.name}")
    errors.extend(cv.errors)
    warnings.extend(cv.warnings)
    if depot.area_m2 < 100:
        warnings.append(f"depot {depot.name}: area_m2 {depot.area_m2} seems small")
    if depot.area_m2 > MAX_DEPOT_AREA_M2:
        warnings.append(f"depot {depot.name}: area_m2 {depot.area_m2} unusually large")
    if depot.capacity_stabling < 1:
        errors.append(f"depot {depot.name}: capacity_stabling must be >= 1")
    return ValidationResult(
        valid=not errors, errors=tuple(errors), warnings=tuple(warnings)
    )


def validate_line(line: LineSpec) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    if not line.stations:
        errors.append(f"line {line.code}: no stations")
    if line.total_length_km <= 0:
        errors.append(f"line {line.code}: total_length_km must be positive")
    seen_codes: set[str] = set()
    for idx, station in enumerate(line.stations):
        sv = validate_station(station)
        errors.extend(sv.errors)
        warnings.extend(sv.warnings)
        if station.code in seen_codes:
            errors.append(f"line {line.code}: duplicate station code {station.code!r}")
        seen_codes.add(station.code)
        if idx > 0:
            prev = line.stations[idx - 1]
            dist_m = haversine_m(
                (prev.latitude, prev.longitude), (station.latitude, station.longitude)
            )
            if dist_m < MIN_STATION_SPACING_M:
                warnings.append(
                    f"line {line.code}: {prev.code} -> {station.code} spacing {dist_m:.0f}m < {MIN_STATION_SPACING_M}m"
                )
            if dist_m > MAX_STATION_SPACING_KM * 1000:
                warnings.append(
                    f"line {line.code}: {prev.code} -> {station.code} spacing {dist_m:.0f}m > {MAX_STATION_SPACING_KM * 1000:.0f}m"
                )
    if not any(s.is_terminus for s in line.stations):
        errors.append(f"line {line.code}: no terminus flagged")
    for depot in line.depots:
        dv = validate_depot(depot)
        errors.extend(dv.errors)
        warnings.extend(dv.warnings)
    return ValidationResult(
        valid=not errors, errors=tuple(errors), warnings=tuple(warnings)
    )


def validate_network(network: Network) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    line_codes = {ln.code for ln in network.lines}
    for line in network.lines:
        lv = validate_line(line)
        errors.extend(lv.errors)
        warnings.extend(lv.warnings)
        for ic_station, ic_line, _ic_with in line.interchanges:
            if ic_line not in line_codes:
                errors.append(
                    f"line {line.code}: interchange references unknown line {ic_line!r}"
                )
            if ic_line == line.code:
                warnings.append(
                    f"line {line.code}: self-referencing interchange at {ic_station}"
                )
    station_coords: dict[str, list[tuple[str, float, float]]] = {}
    for ln in network.lines:
        for s in ln.stations:
            station_coords.setdefault(s.code, []).append(
                (ln.code, s.latitude, s.longitude)
            )
    for code, entries in station_coords.items():
        if len(entries) < 2:
            continue
        lat_set = {e[1] for e in entries}
        lon_set = {e[2] for e in entries}
        if len(lat_set) > 1 or len(lon_set) > 1:
            reprs = ", ".join(f"{ln}({lat},{lon})" for ln, lat, lon in entries)
            warnings.append(
                f"station {code} has inconsistent coordinates across lines: {reprs}"
            )
    return ValidationResult(
        valid=not errors, errors=tuple(errors), warnings=tuple(warnings)
    )


def validate_station_polygon(
    station: StationSpec, length_m: float = 200.0, width_m: float = 30.0
) -> ValidationResult:
    errors: list[str] = []
    poly = station_polygon_m(
        (station.longitude, station.latitude),
        length_m=length_m,
        width_m=width_m,
        heading_deg=0.0,
    )
    if not poly.is_valid:
        errors.append(
            f"station {station.code}: polygon invalid ({is_valid_reason(poly)})"
        )
    if poly.area <= 0:
        errors.append(f"station {station.code}: polygon has zero area")
    return ValidationResult(valid=not errors, errors=tuple(errors))


def validate_platform_polygon(
    station: StationSpec,
    platform_no: int,
    heading_deg: float,
    length_m: float = 180.0,
    width_m: float = 6.0,
) -> ValidationResult:
    errors: list[str] = []
    if length_m <= 0 or length_m > MAX_PLATFORM_LENGTH_M:
        errors.append(
            f"platform {station.code}-{platform_no}: length {length_m} out of range"
        )
    if width_m <= 0 or width_m > MAX_PLATFORM_WIDTH_M:
        errors.append(
            f"platform {station.code}-{platform_no}: width {width_m} out of range"
        )
    side = 1 if platform_no % 2 == 1 else -1
    offset_m = side * (2.5 + 5.0 * ((platform_no - 1) // 2))
    poly = platform_polygon_m(
        (station.longitude, station.latitude),
        length_m=length_m,
        width_m=width_m,
        heading_deg=heading_deg,
        offset_left_m=offset_m,
    )
    if not poly.is_valid:
        errors.append(
            f"platform {station.code}-{platform_no}: polygon invalid ({is_valid_reason(poly)})"
        )
    if poly.area <= 0:
        errors.append(f"platform {station.code}-{platform_no}: polygon has zero area")
    return ValidationResult(valid=not errors, errors=tuple(errors))


def validate_track_segment(seg: TrackSegmentGeometry) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    if seg.length_m <= 0:
        errors.append(
            f"segment {seg.from_station}->{seg.to_station}: non-positive length"
        )
    if not (0 <= seg.heading_in_deg < 360):
        warnings.append(
            f"segment {seg.from_station}->{seg.to_station}: heading_in {seg.heading_in_deg} out of range"
        )
    if not (0 <= seg.heading_out_deg < 360):
        warnings.append(
            f"segment {seg.from_station}->{seg.to_station}: heading_out {seg.heading_out_deg} out of range"
        )
    if seg.speed_limit_kmh < 5:
        errors.append(
            f"segment {seg.from_station}->{seg.to_station}: speed limit {seg.speed_limit_kmh} too low"
        )
    if seg.speed_limit_kmh > 200:
        errors.append(
            f"segment {seg.from_station}->{seg.to_station}: speed limit {seg.speed_limit_kmh} implausible"
        )
    if seg.gradient_pct is not None and abs(seg.gradient_pct) > MAX_TRACK_GRADIENT_PCT:
        warnings.append(
            f"segment {seg.from_station}->{seg.to_station}: gradient {seg.gradient_pct}% exceeds {MAX_TRACK_GRADIENT_PCT}%"
        )
    if seg.is_curve and (seg.max_curve_radius_m is None or seg.max_curve_radius_m < 50):
        errors.append(
            f"segment {seg.from_station}->{seg.to_station}: curve radius {seg.max_curve_radius_m}m too tight"
        )
    coords = list(seg.coords)
    if len(coords) < 2:
        errors.append(
            f"segment {seg.from_station}->{seg.to_station}: insufficient coordinates"
        )
    if len(coords) > 2:
        for i in range(1, len(coords) - 1):
            prev_pt = coords[i - 1]
            curr_pt = coords[i]
            next_pt = coords[i + 1]
            cr = curvature_radius_m(
                (prev_pt[1], prev_pt[0]),
                (curr_pt[1], curr_pt[0]),
                (next_pt[1], next_pt[0]),
            )
            if cr.radius_m is not None and cr.radius_m < 50:
                errors.append(
                    f"segment {seg.from_station}->{seg.to_station}: tight curve r={cr.radius_m:.0f}m at coord {i}"
                )
    if seg.direction not in ("up", "down"):
        errors.append(
            f"segment {seg.from_station}->{seg.to_station}: invalid direction {seg.direction!r}"
        )
    return ValidationResult(
        valid=not errors, errors=tuple(errors), warnings=tuple(warnings)
    )


def validate_all_track_segments(network: Network) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    for line in network.lines:
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
                sv = validate_track_segment(seg)
                errors.extend(sv.errors)
                warnings.extend(sv.warnings)
    return ValidationResult(
        valid=not errors, errors=tuple(errors), warnings=tuple(warnings)
    )


def validate_geometry_layer(data: dict, layer_name: str) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    features = data.get("features", [])
    if not features:
        warnings.append(f"{layer_name}: empty feature collection")
    for idx, feat in enumerate(features):
        geom = feat.get("geometry")
        if geom is None:
            errors.append(f"{layer_name}[{idx}]: missing geometry")
            continue
        geom_type = geom.get("type")
        if geom_type not in (
            "Point",
            "LineString",
            "Polygon",
            "MultiLineString",
            "MultiPolygon",
        ):
            errors.append(f"{layer_name}[{idx}]: unknown geometry type {geom_type!r}")
        coords = geom.get("coordinates")
        if not coords:
            errors.append(f"{layer_name}[{idx}]: empty coordinates")
    return ValidationResult(
        valid=not errors, errors=tuple(errors), warnings=tuple(warnings)
    )


def validate_full_network() -> ValidationResult:
    network = load_network()
    nv = validate_network(network)
    tv = validate_all_track_segments(network)
    combined_errors = list(nv.errors) + list(tv.errors)
    combined_warnings = list(nv.warnings) + list(tv.warnings)
    return ValidationResult(
        valid=not combined_errors,
        errors=tuple(combined_errors),
        warnings=tuple(combined_warnings),
    )
