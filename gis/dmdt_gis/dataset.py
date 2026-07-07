"""Typed access to the canonical Delhi Metro network dataset.

The on-disk canonical source is ``gis/data/network.json``. This module parses it
into frozen dataclasses so callers (the seed loader, the GeoJSON emitter, the
simulation network builder) get a single, validated, hashable view of the
network.

Schema of ``network.json``::

    {
      "lines": [ { "code": "RD", "name": "Red Line", ...,
                   "corridor": "Rithala - Shaheed Sthal",
                   "depots": [ {...} ],
                   "stations": [ {station...} ],
                   "speed_overrides": {"Rithala-Rohini West": 60},     # optional
                   "curve_vertices": {"Rohini West-Pitampura": [[28.7,77.1]]}, # optional
                   "gradients": {"Welcome-Shahdara": 1.0}              # optional
                 },
                 ...
               ]
    }

A ``station`` is::

    {
      "name": "Rajiv Chowk",
      "code": "RC",
      "latitude": 28.6314,
      "longitude": 77.2196,
      "structure": "underground",
      "interchange_with": ["YL", "BL"],
      "platforms": 4,
      "opened_year": 2005,
      "is_terminus": true,
      "has_junction": true,         # track-level junction (crossovers / turnouts)
      "coordinate_confidence": "high"
    }

The dataset is deliberately human-readable and editable — corrections to
coordinates are applied by editing ``network.json`` and re-running the seed
loader, never by hand-editing the database.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "network.json"


# ───────────────────────── value types ─────────────────────────


@dataclass(frozen=True, slots=True)
class DepotSpec:
    name: str
    latitude: float
    longitude: float
    area_m2: float
    capacity_stabling: int
    coordinate_confidence: str = "high"


@dataclass(frozen=True, slots=True)
class StationSpec:
    name: str
    code: str
    latitude: float
    longitude: float
    structure: str               # elevated | underground | at-grade
    interchange_with: tuple[str, ...]
    platforms: int
    opened_year: int
    is_terminus: bool = False
    has_junction: bool = False
    coordinate_confidence: str = "high"

    @property
    def lonlat(self) -> tuple[float, float]:
        return (self.longitude, self.latitude)


@dataclass(frozen=True, slots=True)
class LineSpec:
    code: str
    name: str
    number: int
    color_hex: str
    corridor: str
    opened_year: int
    operator: str
    gauge_mm: int
    electrification: str
    signalling_system: str
    total_length_km: float
    stations: tuple[StationSpec, ...]
    depots: tuple[DepotSpec, ...] = ()
    interchanges: tuple[tuple[str, str, str], ...] = ()  # (this_station, that_line_code, that_station)
    speed_overrides: dict[tuple[str, str], float] = field(default_factory=dict)
    curve_vertices: dict[tuple[str, str], list[tuple[float, float]]] = field(default_factory=dict)
    gradients: dict[tuple[str, str], float] = field(default_factory=dict)

    @property
    def total_stations(self) -> int:
        return len(self.stations)

    @property
    def is_branch(self) -> bool:
        return "branch" in self.name.lower()


@dataclass(frozen=True, slots=True)
class Network:
    lines: tuple[LineSpec, ...]

    def line(self, code: str) -> LineSpec:
        for ln in self.lines:
            if ln.code == code:
                return ln
        raise KeyError(code)

    def station(self, line_code: str, station_code: str) -> StationSpec:
        for s in self.line(line_code).stations:
            if s.code == station_code:
                return s
        raise KeyError(f"{line_code}/{station_code}")

    def find_station_by_code(self, code: str) -> list[tuple[str, StationSpec]]:
        out: list[tuple[str, StationSpec]] = []
        for ln in self.lines:
            for s in ln.stations:
                if s.code == code:
                    out.append((ln.code, s))
        return out

    def find_station_by_name(self, name: str) -> list[tuple[str, StationSpec]]:
        wanted = name.strip().lower()
        out: list[tuple[str, StationSpec]] = []
        for ln in self.lines:
            for s in ln.stations:
                if s.name.strip().lower() == wanted:
                    out.append((ln.code, s))
        return out

    @property
    def all_stations(self) -> Iterable[tuple[str, StationSpec]]:
        for ln in self.lines:
            for s in ln.stations:
                yield ln.code, s

    @property
    def station_count(self) -> int:
        # de-duplicated by station code (a shared intermodal station may appear on two lines)
        return len({s.code for _, s in self.all_stations})


# ───────────────────────── parsing ─────────────────────────


def _station(raw: dict) -> StationSpec:
    return StationSpec(
        name=raw["name"],
        code=raw["code"],
        latitude=float(raw["latitude"]),
        longitude=float(raw["longitude"]),
        structure=raw.get("structure", "elevated"),
        interchange_with=tuple(raw.get("interchange_with", [])),
        platforms=int(raw.get("platforms", 2)),
        opened_year=int(raw.get("opened_year", 0)),
        is_terminus=bool(raw.get("is_terminus", False)),
        has_junction=bool(raw.get("has_junction", False)),
        coordinate_confidence=raw.get("coordinate_confidence", "high"),
    )


def _depot(raw: dict) -> DepotSpec:
    return DepotSpec(
        name=raw["name"],
        latitude=float(raw["latitude"]),
        longitude=float(raw["longitude"]),
        area_m2=float(raw.get("area_m2", 0.0)),
        capacity_stabling=int(raw.get("capacity_stabling", 0)),
        coordinate_confidence=raw.get("coordinate_confidence", "high"),
    )


def _kv_pairs(raw: dict, valueconv):
    out: dict[tuple[str, str], object] = {}
    for k, v in raw.items():
        if "-" not in k:
            continue
        a, b = k.split("-", 1)
        out[(a.strip(), b.strip())] = valueconv(v)
    return out


def _line(raw: dict) -> LineSpec:
    stations = tuple(_station(s) for s in raw["stations"])
    depots = tuple(_depot(d) for d in raw.get("depots", []))
    interchanges = tuple(
        (i["station"], i["line"], i["with_station"]) for i in raw.get("interchanges", [])
    )
    speed_overrides: dict[tuple[str, str], float] = {}
    for k, v in raw.get("speed_overrides", {}).items():
        a, b = k.split("-", 1)
        speed_overrides[(a.strip(), b.strip())] = float(v)
    curve_vertices: dict[tuple[str, str], list[tuple[float, float]]] = {}
    for k, verts in raw.get("curve_vertices", {}).items():
        a, b = k.split("-", 1)
        curve_vertices[(a.strip(), b.strip())] = [
            (float(lon), float(lat)) for lon, lat in verts
        ]
    gradients: dict[tuple[str, str], float] = {}
    for k, v in raw.get("gradients", {}).items():
        a, b = k.split("-", 1)
        gradients[(a.strip(), b.strip())] = float(v)

    return LineSpec(
        code=raw["code"],
        name=raw["name"],
        number=int(raw["number"]),
        color_hex=raw["color_hex"],
        corridor=raw["corridor"],
        opened_year=int(raw["opened_year"]),
        operator=raw.get("operator", "DMRC"),
        gauge_mm=int(raw["gauge_mm"]),
        electrification=raw.get("electrification", "25 kV AC OHE"),
        signalling_system=raw.get("signalling_system", "ATP"),
        total_length_km=float(raw["total_length_km"]),
        stations=stations,
        depots=depots,
        interchanges=interchanges,
        speed_overrides=speed_overrides,
        curve_vertices=curve_vertices,
        gradients=gradients,
    )


def load_network(path: Path | str | None = None) -> Network:
    """Parse the canonical ``network.json`` into a :class:`Network`.

    A path may be passed for tests; production callers omit it.
    """
    p = Path(path) if path else DATA_FILE
    raw = json.loads(p.read_text(encoding="utf-8"))
    lines = tuple(_line(ln) for ln in raw["lines"])
    _validate(lines)
    return Network(lines=lines)


def _validate(lines: Sequence[LineSpec]) -> None:
    """Cross-line integrity checks executed at load time.

    Catches typos in the hand-authored dataset before the seed loader ever sees
    them — duplicate station codes inside a line, an interchange that names a
    line that isn't in the dataset, a missing terminus, etc.
    """
    codes = {ln.code for ln in lines}
    for ln in lines:
        seen: set[str] = set()
        for s in ln.stations:
            if s.code in seen:
                raise ValueError(f"{ln.code}: duplicate station code {s.code!r}")
            seen.add(s.code)
        # at least one terminus must be flagged
        if not any(s.is_terminus for s in ln.stations):
            raise ValueError(f"{ln.code}: no terminal station flagged")
        for station_code, that_line, _that_station in ln.interchanges:
            if that_line not in codes:
                raise ValueError(
                    f"{ln.code}: interchange at {station_code} references unknown line {that_line!r}"
                )
