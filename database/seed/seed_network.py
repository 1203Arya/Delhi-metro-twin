#!/usr/bin/env python3
"""Seed the database from the canonical Delhi Metro network dataset.

Usage:
    python -m database.seed.seed_network

Loads ``gis/data/network.json`` via :func:`dmdt_gis.load_network`, builds all
spatial geometries, and inserts the full network into PostgreSQL via SQLAlchemy.
"""

from __future__ import annotations

import sys
from pathlib import Path

import geoalchemy2

GIS_ROOT = Path(__file__).resolve().parent.parent.parent / "gis"
sys.path.insert(0, str(GIS_ROOT))

import dmdt_gis  # noqa: E402
from dmdt_db import (  # noqa: E402
    Crossover,
    Depot,
    Junction,
    Line,
    Platform,
    Siding,
    Station,
    Switch,
    TrackSegment,
    TrainClass,
    get_session_factory,
)
from dmdt_db.repositories import (  # noqa: E402
    CrossoverRepository,
    DepotRepository,
    JunctionRepository,
    LineRepository,
    PlatformRepository,
    StationRepository,
    SwitchRepository,
    TrackSegmentRepository,
)


def _to_geom_wkb(shapely_geom):
    return geoalchemy2.WKBElement(shapely_geom.wkb, srid=4326)


def seed_network(session) -> dict[str, int]:
    counts: dict[str, int] = {}
    network = dmdt_gis.load_network()
    line_repo = LineRepository(session)
    station_repo = StationRepository(session)
    platform_repo = PlatformRepository(session)
    track_repo = TrackSegmentRepository(session)
    depot_repo = DepotRepository(session)
    crossover_repo = CrossoverRepository(session)
    junction_repo = JunctionRepository(session)
    switch_repo = SwitchRepository(session)

    station_geoms = dmdt_gis.build_all_station_geometries(network)
    platform_geoms = dmdt_gis.build_all_platform_geometries(network)
    track_geoms = dmdt_gis.build_all_track_geometries(network)
    depot_geoms = dmdt_gis.build_all_depot_geometries(network)
    junction_geoms = dmdt_gis.build_all_junction_geometries(network)
    crossover_geoms = dmdt_gis.build_all_crossover_geometries(network)
    _ = junction_geoms

    for line_spec in network.lines:
        line = Line(
            code=line_spec.code,
            name=line_spec.name,
            number=line_spec.number,
            color_hex=line_spec.color_hex,
            corridor=line_spec.corridor,
            opened_year=line_spec.opened_year,
            operator=line_spec.operator,
            gauge_mm=line_spec.gauge_mm,
            electrification=line_spec.electrification,
            signalling_system=line_spec.signalling_system,
            total_length_km=line_spec.total_length_km,
        )
        line_repo.add(line)
        counts["lines"] = counts.get("lines", 0) + 1

        for sg in station_geoms.get(line_spec.code, []):
            station = Station(
                line_code=line_spec.code,
                code=sg.station.code,
                name=sg.station.name,
                location=_to_geom_wkb(sg.point),
                structure=sg.station.structure,
                platforms=sg.station.platforms,
                opened_year=sg.station.opened_year,
                is_terminus=sg.station.is_terminus,
                has_junction=sg.station.has_junction,
                coordinate_confidence=sg.station.coordinate_confidence,
                sequence=line_spec.stations.index(sg.station),
                latitude=sg.station.latitude,
                longitude=sg.station.longitude,
            )
            station_repo.add(station)
            counts["stations"] = counts.get("stations", 0) + 1

        for pg in platform_geoms.get(line_spec.code, []):
            host_stations = station_repo.get_by_code(pg.station.code)
            host = next(
                (s for s in host_stations if s.line_code == line_spec.code), None
            )
            if host is None:
                continue
            platform = Platform(
                station_id=host.id,
                platform_number=pg.platform_number,
                geometry=_to_geom_wkb(pg.polygon),
                heading_deg=pg.heading_deg,
                length_m=pg.length_m,
                width_m=pg.width_m,
                is_edge_platform=pg.is_edge_platform,
            )
            platform_repo.add(platform)
            counts["platforms"] = counts.get("platforms", 0) + 1

        for tg in track_geoms.get(line_spec.code, []):
            from_stations = station_repo.list_by_line(line_spec.code)
            to_stations = station_repo.list_by_line(line_spec.code)
            from_s = next(
                (s for s in from_stations if s.name == tg.segment.from_station), None
            )
            to_s = next(
                (s for s in to_stations if s.name == tg.segment.to_station), None
            )
            if from_s is None or to_s is None:
                continue
            track = TrackSegment(
                line_code=line_spec.code,
                from_station_id=from_s.id,
                to_station_id=to_s.id,
                direction=tg.segment.direction,
                segment_index=0,
                geometry=_to_geom_wkb(tg.linestring),
                length_m=tg.total_length_m,
                heading_in_deg=tg.segment.heading_in_deg,
                heading_out_deg=tg.segment.heading_out_deg,
                max_curve_radius_m=tg.segment.max_curve_radius_m,
                speed_limit_kmh=tg.segment.speed_limit_kmh,
                gradient_pct=tg.segment.gradient_pct,
                is_curve=tg.segment.is_curve,
            )
            track_repo.add(track)
            counts["track_segments"] = counts.get("track_segments", 0) + 1

        for dg in depot_geoms.get(line_spec.code, []):
            depot = Depot(
                line_code=line_spec.code,
                name=dg.depot.name,
                location=_to_geom_wkb(dg.point),
                latitude=dg.depot.latitude,
                longitude=dg.depot.longitude,
                area_m2=dg.depot.area_m2,
                capacity_stabling=dg.depot.capacity_stabling,
                coordinate_confidence=dg.depot.coordinate_confidence,
            )
            depot_repo.add(depot)
            counts["depots"] = counts.get("depots", 0) + 1

            for sname, siding_geom in _generate_sidings(dg):
                siding = Siding(
                    depot_id=depot.id,
                    name=sname,
                    geometry=_to_geom_wkb(siding_geom.linestring),
                    length_m=siding_geom.length_m,
                    capacity_trains=siding_geom.capacity_trains,
                )
                session.add(siding)
                counts["sidings"] = counts.get("sidings", 0) + 1

        for st in line_spec.stations:
            if not (st.has_junction or st.interchange_with):
                continue
            host_stations = station_repo.get_by_code(st.code)
            host = next(
                (s for s in host_stations if s.line_code == line_spec.code), None
            )
            if host is None:
                continue
            all_lines = list(st.interchange_with) + [line_spec.code]
            junction = Junction(
                station_id=host.id,
                name=st.name,
                location=_to_geom_wkb(
                    __import__("shapely.geometry", fromlist=["Point"]).Point(
                        (st.longitude, st.latitude)
                    )
                ),
                is_interchange=len(all_lines) > 1,
                is_turnout=st.has_junction,
                lines=",".join(sorted(set(all_lines))),
            )
            junction_repo.add(junction)
            counts["junctions"] = counts.get("junctions", 0) + 1

            for label in ("entry", "exit"):
                sw = Switch(
                    line_code=line_spec.code,
                    junction_id=junction.id,
                    location=_to_geom_wkb(
                        __import__("shapely.geometry", fromlist=["Point"]).Point(
                            (st.longitude, st.latitude)
                        )
                    ),
                    switch_label=label,
                    heading_deg=0.0,
                )
                switch_repo.add(sw)
                counts["switches"] = counts.get("switches", 0) + 1

        for cg in crossover_geoms.get(line_spec.code, []):
            host_stations = station_repo.get_by_code(cg.station.code)
            host = next(
                (s for s in host_stations if s.line_code == line_spec.code), None
            )
            if host is None:
                continue
            crossover = Crossover(
                line_code=line_spec.code,
                station_id=host.id,
                geometry=_to_geom_wkb(cg.linestring),
                heading_deg=cg.heading_deg,
            )
            crossover_repo.add(crossover)
            counts["crossovers"] = counts.get("crossovers", 0) + 1

    _seed_train_classes(session)
    counts["train_classes"] = 4

    session.commit()
    return counts


def _generate_sidings(depot_geom):
    from dmdt_gis.spatial import SidingGeometry

    depot = depot_geom.depot
    results = []
    for i in range(max(1, depot.capacity_stabling // 16)):
        offset = (i + 1) * 20.0
        from_lonlat = (
            depot.longitude + 0.0005,
            depot.latitude + 0.0005 + offset * 1e-5,
        )
        to_lonlat = (depot.longitude + 0.0020, depot.latitude + 0.0005 + offset * 1e-5)
        sg = SidingGeometry.build(
            name=f"{depot.name} Siding {i + 1}",
            depot=depot,
            from_lonlat=from_lonlat,
            to_lonlat=to_lonlat,
            capacity_trains=2,
        )
        results.append((sg.name, sg))
    return results


def _seed_train_classes(session):
    classes = [
        TrainClass(
            name="Standard",
            max_speed_kmh=80.0,
            acceleration_ms2=0.9,
            deceleration_ms2=1.1,
            length_m=208.0,
            capacity_seated=328,
            capacity_standing=1200,
        ),
        TrainClass(
            name="Airport Express",
            max_speed_kmh=120.0,
            acceleration_ms2=0.8,
            deceleration_ms2=1.0,
            length_m=150.0,
            capacity_seated=208,
            capacity_standing=600,
        ),
        TrainClass(
            name="Rapid Metro",
            max_speed_kmh=80.0,
            acceleration_ms2=1.0,
            deceleration_ms2=1.2,
            length_m=60.0,
            capacity_seated=108,
            capacity_standing=300,
        ),
        TrainClass(
            name="Standard-8Car",
            max_speed_kmh=85.0,
            acceleration_ms2=0.85,
            deceleration_ms2=1.05,
            length_m=278.0,
            capacity_seated=440,
            capacity_standing=1600,
        ),
    ]
    for tc in classes:
        session.add(tc)


def main() -> int:
    session_factory = get_session_factory()
    with session_factory() as session:
        counts = seed_network(session)
        print("Seed complete:")
        for k, v in sorted(counts.items()):
            print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
