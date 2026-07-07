from __future__ import annotations

from dmdt_sim.schedule.timetable import Timetable, TimetableGenerator
from dmdt_sim.types import Direction, SimulationConfig


def test_timetable_generation():
    config = SimulationConfig(
        dt_s=1.0,
        seed=42,
        duration_s=3600.0,
        n_passengers=100,
        headway_target_s=300.0,
    )
    gen = TimetableGenerator(config)
    stations = [
        {"id": "s1", "code": "STA", "name": "Station A", "sequence": 1},
        {"id": "s2", "code": "STB", "name": "Station B", "sequence": 2},
        {"id": "s3", "code": "STC", "name": "Station C", "sequence": 3},
    ]
    entries, plans = gen.generate("LINE1", stations, Direction.UP)
    assert len(entries) > 0
    assert len(plans) > 0
    for plan in plans:
        assert plan.line_code == "LINE1"
        assert plan.direction == Direction.UP
    first_trip = plans[0]
    assert len(first_trip.stops) == 3


def test_timetable_lookup():
    config = SimulationConfig(dt_s=1.0, seed=42, duration_s=3600.0)
    tt = Timetable(config)
    from dmdt_sim.types import TimetableEntry

    entry = TimetableEntry(
        train_id="tr1",
        line_code="RED",
        direction=Direction.UP,
        departure_time=100.0,
        from_station_code="A",
        to_station_code="B",
    )
    tt.add_entry(entry)
    found = tt.next_departure("RED", Direction.UP, 50.0)
    assert found is not None
    assert found.train_id == "tr1"
    none_found = tt.next_departure("RED", Direction.DOWN, 50.0)
    assert none_found is None
