from __future__ import annotations

from dmdt_sim.physics.train import DrivingMode, TrainMotionModel
from dmdt_sim.types import TrainSpec


def test_train_accelerates():
    spec = TrainSpec(
        train_class_id="test",
        name="test",
        max_speed_kmh=80.0,
        acceleration_ms2=1.0,
        deceleration_ms2=1.0,
        length_m=200.0,
        capacity_seated=350,
        capacity_standing=650,
    )
    model = TrainMotionModel(spec, seed=42)
    for _ in range(50):
        model.accelerate(1.0)
    assert model.state.speed_mps > 0
    assert model.mode == DrivingMode.ACCELERATING or model.mode == DrivingMode.CRUISING


def test_train_brakes():
    spec = TrainSpec(
        train_class_id="test",
        name="test",
        max_speed_kmh=80.0,
        acceleration_ms2=1.0,
        deceleration_ms2=1.0,
        length_m=200.0,
        capacity_seated=350,
        capacity_standing=650,
    )
    model = TrainMotionModel(spec, seed=42)
    for _ in range(30):
        model.accelerate(1.0)
    v_before = model.state.speed_mps
    for _ in range(60):
        model.brake(1.0)
    assert model.state.speed_mps < v_before
    assert model.state.speed_mps >= 0


def test_brake_distance():
    spec = TrainSpec(
        train_class_id="test",
        name="test",
        max_speed_kmh=80.0,
        acceleration_ms2=1.0,
        deceleration_ms2=1.0,
        length_m=200.0,
        capacity_seated=350,
        capacity_standing=650,
    )
    model = TrainMotionModel(spec, seed=42)
    model.state.speed_mps = 20.0
    dist = model.brake_distance(20.0)
    assert dist > 0
    assert abs(dist - 200.0) < 10


def test_max_speed_respected():
    spec = TrainSpec(
        train_class_id="test",
        name="test",
        max_speed_kmh=36.0,
        acceleration_ms2=2.0,
        deceleration_ms2=2.0,
        length_m=200.0,
        capacity_seated=350,
        capacity_standing=650,
    )
    model = TrainMotionModel(spec, seed=42)
    for _ in range(200):
        model.accelerate(0.5)
    assert model.speed_kmh <= 37.0
