from __future__ import annotations

import logging
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from dmdt_db import Depot, Line, Station, TrackSegment, TrainClass

from ...core.deps import get_db
from dmdt_sim.types import IncidentType

from ...schemas import (
    ApproachingTrainsResponse,
    DisruptRequest,
    LineStationSummary,
    LineTrainGroup,
    SimulationConfigSchema,
    SimulationState,
    SuccessResponse,
    TrainDebugPosition,
    TrainPositionsResponse,
)
from ...simulation_bridge import get_bridge

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/simulation", tags=["simulation"])


async def _build_network_data(db: AsyncSession) -> dict[str, Any]:
    lines_result = await db.execute(select(Line))
    lines = lines_result.scalars().all()

    stations_result = await db.execute(select(Station))
    stations = stations_result.scalars().all()
    station_id_to_code: dict[Any, str] = {s.id: s.code for s in stations}

    tracks_result = await db.execute(select(TrackSegment))
    tracks = tracks_result.scalars().all()

    depots_result = await db.execute(select(Depot))
    depots = depots_result.scalars().all()

    classes_result = await db.execute(select(TrainClass))
    train_classes = classes_result.scalars().all()

    return {
        "lines": [
            {
                "code": line.code,
                "name": line.name,
                "color_hex": line.color_hex,
                "total_length_km": line.total_length_km,
            }
            for line in lines
        ],
        "stations": [
            {
                "id": str(s.id),
                "code": s.code,
                "name": s.name,
                "line_code": s.line_code,
                "sequence": s.sequence,
                "latitude": s.latitude,
                "longitude": s.longitude,
                "is_terminus": s.is_terminus,
                "has_junction": s.has_junction,
                "platforms": s.platforms,
            }
            for s in stations
        ],
        "track_segments": [
            {
                "line_code": t.line_code,
                "from_station_code": station_id_to_code.get(t.from_station_id, ""),
                "to_station_code": station_id_to_code.get(t.to_station_id, ""),
                "direction": t.direction,
                "segment_index": t.segment_index,
                "length_m": t.length_m,
                "speed_limit_kmh": t.speed_limit_kmh,
                "is_curve": t.is_curve,
                "gradient_pct": t.gradient_pct,
            }
            for t in tracks
        ],
        "depots": [
            {
                "line_code": d.line_code,
                "name": f"depot_{d.line_code}",
                "latitude": d.latitude,
                "longitude": d.longitude,
                "capacity_stabling": d.capacity_stabling,
            }
            for d in depots
        ],
        "train_classes": [
            {
                "name": tc.name,
                "max_speed_kmh": tc.max_speed_kmh,
                "acceleration_ms2": tc.acceleration_ms2,
                "deceleration_ms2": tc.deceleration_ms2,
                "length_m": tc.length_m,
                "capacity_seated": tc.capacity_seated,
                "capacity_standing": tc.capacity_standing,
            }
            for tc in train_classes
        ],
    }


@router.post("/start", response_model=SuccessResponse)
async def start_simulation(
    config: SimulationConfigSchema | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    bridge = get_bridge()
    payload: dict[str, Any] = {}
    if config:
        payload["config"] = config.model_dump()
    network_data = await _build_network_data(db)
    await bridge.send_command("start", {"network": network_data, **payload})
    return {"message": "Simulation started"}


@router.post("/stop", response_model=SuccessResponse)
async def stop_simulation() -> dict[str, str]:
    await get_bridge().send_command("stop", {})
    return {"message": "Simulation stopped"}


@router.post("/disrupt", response_model=SuccessResponse)
async def disrupt_station(body: DisruptRequest) -> dict[str, str]:
    bridge = get_bridge()
    engine = bridge.service.engine
    if not engine:
        return {"message": "Simulation not running — cannot create incident"}
    incident_type = IncidentType(body.incident_type)
    station_code = body.station_code
    line_code = body.line_code or ""
    engine.incident_manager.create_incident(
        incident_type=incident_type,
        line_code=line_code,
        station_code=station_code,
        start_time=engine.current_time,
        duration_s=body.duration_s,
        description=f"Manual disrupt at {station_code}",
    )
    logger.info(
        "Disrupt incident created at %s (type=%s, duration=%.0fs)",
        station_code,
        body.incident_type,
        body.duration_s,
    )
    return {"message": f"Disrupt created at {station_code}"}


@router.get("/station/{code}/approaching", response_model=ApproachingTrainsResponse)
async def get_approaching_trains(
    code: str, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    stmt = await db.execute(select(Station).where(Station.code == code))
    station = stmt.scalars().first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    bridge = get_bridge()

    trains_list: list[dict[str, Any]] = []
    engine = bridge.service.engine
    if engine:
        for t in engine.trains.values():
            d = t.to_dict()
            if d.get("next_station") == code:
                trains_list.append(d)

    segments = await db.execute(
        select(TrackSegment).where(
            or_(
                TrackSegment.from_station_id == station.id,
                TrackSegment.to_station_id == station.id,
            )
        )
    )
    approaches_list: list[dict[str, Any]] = []
    for seg in segments.scalars().all():
        if seg.to_station_id == station.id:
            approaches_list.append(
                {
                    "bearing": float(seg.heading_in_deg or 0),
                    "line_code": seg.line_code,
                    "direction": seg.direction,
                }
            )
        if seg.from_station_id == station.id:
            approaches_list.append(
                {
                    "bearing": float(
                        (seg.heading_out_deg + 180) % 360 if seg.heading_out_deg else 0
                    ),
                    "line_code": seg.line_code,
                    "direction": f"reverse_{seg.direction}" if seg.direction else "",
                }
            )

    return {
        "station_code": code,
        "station": {
            "id": str(station.id),
            "code": station.code,
            "name": station.name,
            "line_code": station.line_code,
            "latitude": station.latitude,
            "longitude": station.longitude,
            "platforms": station.platforms,
            "has_junction": station.has_junction,
        },
        "trains": trains_list,
        "approaches": approaches_list,
    }


@router.post("/pause", response_model=SuccessResponse)
async def pause_simulation() -> dict[str, str]:
    await get_bridge().send_command("pause", {})
    return {"message": "Simulation paused"}


@router.post("/resume", response_model=SuccessResponse)
async def resume_simulation() -> dict[str, str]:
    await get_bridge().send_command("resume", {})
    return {"message": "Simulation resumed"}


@router.get("/state", response_model=SimulationState)
async def get_simulation_state() -> dict[str, Any]:
    return get_bridge().get_state()


@router.get("/snapshots")
async def get_snapshots() -> list[dict[str, Any]]:
    return get_bridge().service.get_snapshots()


def _station_name(code: str, stations: list[dict[str, Any]]) -> str:
    for s in stations:
        if s.get("code") == code:
            return s.get("name", code)
    return code


def _build_line_name_map(network) -> dict[str, str]:
    names: dict[str, str] = {}
    for lc, ls in network.lines.items():
        names[lc] = ls.get("name", lc) if isinstance(ls, dict) else lc
    return names


def _terminal_name(
    line_code: str,
    direction: str,
    stations_map: dict[str, str],
    line_stations: list[dict[str, Any]],
) -> str:
    if not line_stations:
        return line_code
    if direction == "up":
        first = line_stations[0]
        return stations_map.get(first["code"], first["code"])
    else:
        last = line_stations[-1]
        return stations_map.get(last["code"], last["code"])


@router.get("/trains/positions", response_model=TrainPositionsResponse)
async def get_train_positions() -> TrainPositionsResponse:
    bridge = get_bridge()
    engine = bridge.service.engine
    if not engine or not engine.trains:
        return TrainPositionsResponse(
            generated_at_s=0.0,
            ist_time="",
            service_period="",
            lines=[],
            total_trains=0,
            total_active=0,
        )

    line_names = _build_line_name_map(engine.network)
    lines_data: dict[str, dict[str, Any]] = {}

    for train in engine.trains.values():
        lc = train.line_code
        if lc not in lines_data:
            lines_data[lc] = {"line_code": lc, "trains": []}
        lines_data[lc]["trains"].append(train)

    result_lines: list[dict[str, Any]] = []

    for lc in sorted(lines_data.keys()):
        raw_trains = lines_data[lc]["trains"]
        line_stations = engine.network.get_stations_on_line(lc)
        n_stations = len(line_stations)
        stations_map = {s["code"]: s.get("name", s["code"]) for s in line_stations}
        station_seq = {s["code"]: i for i, s in enumerate(line_stations)}
        line_name = line_names.get(lc, lc)

        # Terminal names for direction display
        up_terminal_code = line_stations[0]["code"] if line_stations else ""
        down_terminal_code = line_stations[-1]["code"] if line_stations else ""
        up_terminal = stations_map.get(up_terminal_code, up_terminal_code)
        down_terminal = stations_map.get(down_terminal_code, down_terminal_code)

        positions: list[TrainDebugPosition] = []
        for t in raw_trains:
            if t.status.value in ("in_depot", "maintenance"):
                continue

            status_str = t.status.value
            speed = t.speed_kmh
            dist = t.distance_to_next_station_m
            eta = dist / max(t.speed_mps, 0.1) if t.speed_mps > 0.1 else 999.0
            is_at = t.is_at_platform or t.status.value in (
                "stopped",
                "door_open",
                "door_close",
            )
            direction = t.direction.value
            dest = up_terminal if direction == "up" else down_terminal

            cur_code = t.current_station_code
            nxt_code = t.next_station_code

            positions.append(
                TrainDebugPosition(
                    train_id=t.train_id,
                    line_code=lc,
                    line_name=line_name,
                    direction=direction,
                    direction_destination=f"towards {dest}",
                    status=status_str,
                    speed_kmh=round(speed, 1),
                    occupancy=t.occupancy,
                    current_station=stations_map.get(cur_code, cur_code),
                    current_station_code=cur_code,
                    next_station=stations_map.get(nxt_code, nxt_code),
                    next_station_code=nxt_code,
                    distance_to_next_m=round(dist, 1),
                    eta_s=round(eta, 1),
                    is_at_platform=is_at,
                    doors_open=t.doors_open,
                )
            )

        def _sort_key(p: TrainDebugPosition) -> tuple:
            idx = station_seq.get(p.current_station_code, 999)
            if p.direction == "down":
                idx = (n_stations - 1 - idx) if idx < n_stations else idx + 10000
            return (0 if p.direction == "up" else 1, idx)

        positions.sort(key=_sort_key)

        station_summary: list[LineStationSummary] = []
        at_station_counts: dict[str, int] = {}
        approaching_counts: dict[str, int] = {}
        for p in positions:
            cs = p.current_station_code
            if p.is_at_platform:
                at_station_counts[cs] = at_station_counts.get(cs, 0) + 1
            else:
                approaching_counts[cs] = approaching_counts.get(cs, 0) + 1
            ns = p.next_station_code
            if ns:
                approaching_counts[ns] = approaching_counts.get(ns, 0) + 1

        for s in line_stations:
            code = s["code"]
            station_summary.append(
                LineStationSummary(
                    station_name=s.get("name", code),
                    station_code=code,
                    at_platform=at_station_counts.get(code, 0),
                    approaching=approaching_counts.get(code, 0),
                )
            )

        result_lines.append(
            LineTrainGroup(
                line_code=lc,
                line_name=line_name,
                terminal_up=up_terminal,
                terminal_down=down_terminal,
                total_trains=len(raw_trains),
                active_trains=positions,
                station_summary=station_summary,
            )
        )

    now_ist = datetime.now(ZoneInfo("Asia/Kolkata"))
    total_active = sum(len(grp.active_trains) for grp in result_lines)
    return TrainPositionsResponse(
        generated_at_s=engine.current_time,
        ist_time=now_ist.strftime("%H:%M:%S"),
        service_period=engine.service_period,
        lines=result_lines,
        total_trains=len(engine.trains),
        total_active=total_active,
    )
