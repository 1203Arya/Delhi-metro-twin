from __future__ import annotations

from dmdt_sim.signalling.block import BlockManager
from dmdt_sim.signalling.cbtc import CBTCController
from dmdt_sim.types import Direction, SignalBlock, TrainSpec


def test_block_occupancy():
    bm = BlockManager()
    block = SignalBlock(
        block_id="b1",
        line_code="RED",
        direction=Direction.UP,
        from_station_id="A",
        to_station_id="B",
        length_m=500.0,
    )
    bm.blocks["b1"] = block
    bm._line_blocks["RED"][Direction.UP.value].append(block)
    occupied = bm.occupy_block("b1", "tr1", 200.0, 100.0, Direction.UP, 0.0)
    assert occupied
    assert bm.blocks["b1"].is_occupied
    assert bm.blocks["b1"].occupying_train_id == "tr1"
    bm.release_block("b1", "tr1")
    assert not bm.blocks["b1"].is_occupied


def test_headway_check():
    bm = BlockManager()
    block1 = SignalBlock("b1", "RED", Direction.UP, "A", "B", 500.0)
    block2 = SignalBlock("b2", "RED", Direction.UP, "B", "C", 500.0)
    bm.blocks["b1"] = block1
    bm.blocks["b2"] = block2
    bm._line_blocks["RED"][Direction.UP.value] = [block1, block2]
    bm.occupy_block("b1", "tr1", 200.0, 100.0, Direction.UP, 0.0)
    bm.occupy_block("b2", "tr2", 200.0, 400.0, Direction.UP, 0.0)
    gap, safe = bm.check_headway("RED", Direction.UP, 100.0, 200.0)
    assert safe


def test_cbtc_movement_authority():
    bm = BlockManager()
    block = SignalBlock("b1", "RED", Direction.UP, "A", "B", 500.0)
    bm.blocks["b1"] = block
    bm._line_blocks["RED"][Direction.UP.value] = [block]
    cbtc = CBTCController(bm, min_headway_m=50.0)
    spec = TrainSpec(
        train_class_id="test",
        name="test",
        max_speed_kmh=80.0,
        acceleration_ms2=0.8,
        deceleration_ms2=0.9,
        length_m=200.0,
        capacity_seated=350,
        capacity_standing=650,
    )
    bm.occupy_block("b1", "tr1", 200.0, 100.0, Direction.UP, 0.0)
    expected = cbtc.compute_movement_authority(
        "tr2", "RED", Direction.UP, 10.0, 5.0, spec
    )
    assert expected is not None
