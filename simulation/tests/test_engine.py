from __future__ import annotations

from dmdt_sim.engine import SimulationEngine
from dmdt_sim.types import SimulationConfig


def test_engine_initialize():
    config = SimulationConfig(
        dt_s=1.0,
        seed=42,
        duration_s=100.0,
        n_passengers=100,
    )
    engine = SimulationEngine(config)
    network_data = {
        "lines": [{"code": "RED", "name": "Red Line", "color": "#FF0000"}],
        "stations": [
            {
                "id": "s1",
                "code": "STA",
                "name": "Station A",
                "line_code": "RED",
                "sequence": 1,
            },
            {
                "id": "s2",
                "code": "STB",
                "name": "Station B",
                "line_code": "RED",
                "sequence": 2,
            },
            {
                "id": "s3",
                "code": "STC",
                "name": "Station C",
                "line_code": "RED",
                "sequence": 3,
            },
        ],
        "track_segments": [
            {
                "block_id": "blk_0",
                "line_code": "RED",
                "direction": "up",
                "from_station_id": "s1",
                "to_station_id": "s2",
                "from_station_code": "STA",
                "to_station_code": "STB",
                "length_m": 1000.0,
                "sequence": 0,
                "speed_limit_kmh": 80.0,
            },
            {
                "block_id": "blk_1",
                "line_code": "RED",
                "direction": "up",
                "from_station_id": "s2",
                "to_station_id": "s3",
                "from_station_code": "STB",
                "to_station_code": "STC",
                "length_m": 1000.0,
                "sequence": 1,
                "speed_limit_kmh": 80.0,
            },
        ],
        "depots": [{"name": "depot_RED", "code": "depot_RED", "line_code": "RED"}],
        "train_classes": [
            {
                "train_class_id": "std",
                "max_speed_kmh": 80.0,
                "acceleration_ms2": 0.8,
                "deceleration_ms2": 0.9,
            },
        ],
    }
    engine.load_network(network_data)
    engine.initialize()
    assert len(engine.trains) > 0
    state = engine.get_state()
    assert state["trains"] > 0


def test_engine_step():
    config = SimulationConfig(
        dt_s=1.0,
        seed=42,
        duration_s=500.0,
        n_passengers=100,
    )
    engine = SimulationEngine(config)
    network_data = {
        "lines": [{"code": "RED", "name": "Red Line", "color": "#FF0000"}],
        "stations": [
            {
                "id": "s1",
                "code": "STA",
                "name": "Station A",
                "line_code": "RED",
                "sequence": 1,
            },
            {
                "id": "s2",
                "code": "STB",
                "name": "Station B",
                "line_code": "RED",
                "sequence": 2,
            },
        ],
        "track_segments": [
            {
                "block_id": "blk_0",
                "line_code": "RED",
                "direction": "up",
                "from_station_id": "s1",
                "to_station_id": "s2",
                "from_station_code": "STA",
                "to_station_code": "STB",
                "length_m": 1000.0,
                "sequence": 0,
                "speed_limit_kmh": 80.0,
            },
        ],
        "depots": [{"name": "depot_RED", "code": "depot_RED", "line_code": "RED"}],
        "train_classes": [],
    }
    engine.load_network(network_data)
    engine.initialize()
    snapshots = engine.run(50.0)
    assert len(snapshots) >= 1


def test_deterministic():
    config = SimulationConfig(dt_s=1.0, seed=42, duration_s=200.0, n_passengers=50)
    engine1 = SimulationEngine(config)
    engine2 = SimulationEngine(config)
    network_data = {
        "lines": [{"code": "RED", "name": "Red Line", "color": "#FF0000"}],
        "stations": [
            {
                "id": "s1",
                "code": "STA",
                "name": "Station A",
                "line_code": "RED",
                "sequence": 1,
            },
            {
                "id": "s2",
                "code": "STB",
                "name": "Station B",
                "line_code": "RED",
                "sequence": 2,
            },
        ],
        "track_segments": [
            {
                "block_id": "blk_0",
                "line_code": "RED",
                "direction": "up",
                "from_station_id": "s1",
                "to_station_id": "s2",
                "from_station_code": "STA",
                "to_station_code": "STB",
                "length_m": 1000.0,
                "sequence": 0,
                "speed_limit_kmh": 80.0,
            },
        ],
        "depots": [{"name": "depot_RED", "code": "depot_RED", "line_code": "RED"}],
        "train_classes": [],
    }
    engine1.load_network(network_data)
    engine2.load_network(network_data)
    s1 = engine1.run(200.0)
    s2 = engine2.run(200.0)
    assert len(s1) == len(s2)
