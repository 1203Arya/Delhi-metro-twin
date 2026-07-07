from __future__ import annotations

from collections import defaultdict
from typing import Any

from ..types import Direction, MovementAuthority, SignalBlock, TrackOccupation


class BlockManager:
    def __init__(self) -> None:
        self.blocks: dict[str, SignalBlock] = {}
        self.occupations: list[TrackOccupation] = []
        self._line_blocks: dict[str, dict[str, list[SignalBlock]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self._station_blocks: dict[str, list[str]] = defaultdict(list)

    def build_from_network(self, network_data: dict[str, Any]) -> None:
        raw_segments = network_data.get("track_segments", {})
        if isinstance(raw_segments, list):
            segments_by_line: dict[str, list[dict]] = {}
            for seg in raw_segments:
                lc = seg.get("line_code", "")
                segments_by_line.setdefault(lc, []).append(seg)
            raw_segments = segments_by_line
        for line_code, segments in raw_segments.items():
            segments_sorted = sorted(segments, key=lambda s: s.get("sequence", 0))
            for i, seg in enumerate(segments_sorted):
                block_id = seg.get("block_id", f"blk_{line_code}_{i}")
                direction = Direction(seg.get("direction", "up"))
                block = SignalBlock(
                    block_id=block_id,
                    line_code=line_code,
                    direction=direction,
                    from_station_id=seg.get("from_station_id", ""),
                    to_station_id=seg.get("to_station_id", ""),
                    length_m=seg.get("length_m", 500.0),
                    speed_limit_kmh=seg.get("speed_limit_kmh", 80.0),
                )
                self.blocks[block_id] = block
                self._line_blocks[line_code][direction.value].append(block)
                self._station_blocks.setdefault(
                    seg.get("from_station_code", ""), []
                ).append(block_id)
                self._station_blocks.setdefault(
                    seg.get("to_station_code", ""), []
                ).append(block_id)

    def occupy_block(
        self,
        block_id: str,
        train_id: str,
        train_length_m: float,
        head_position_m: float,
        direction: Direction,
        time_s: float,
    ) -> bool:
        block = self.blocks.get(block_id)
        if not block:
            return False
        if block.is_occupied and block.occupying_train_id != train_id:
            return False
        block.is_occupied = True
        block.occupying_train_id = train_id
        block.authority = MovementAuthority.MOVEMENT
        occ = TrackOccupation(
            train_id=train_id,
            track_segment_id=block_id,
            entry_time=time_s,
            direction=direction,
            head_position_m=head_position_m,
            tail_position_m=head_position_m - train_length_m,
        )
        self.occupations.append(occ)
        return True

    def release_block(self, block_id: str, train_id: str) -> None:
        block = self.blocks.get(block_id)
        if block and block.occupying_train_id == train_id:
            block.is_occupied = False
            block.occupying_train_id = None
            block.authority = MovementAuthority.MOVEMENT

    def get_leading_train(
        self,
        line_code: str,
        direction: Direction,
        current_position_m: float,
        train_length_m: float,
    ) -> tuple[str | None, float]:
        blocks_in_dir = self._line_blocks.get(line_code, {}).get(direction.value, [])
        for block in blocks_in_dir:
            if block.is_occupied and block.occupying_train_id:
                relevant_occs = [
                    o
                    for o in self.occupations
                    if o.train_id == block.occupying_train_id
                ]
                if relevant_occs:
                    occ = relevant_occs[-1]
                    if occ.head_position_m > current_position_m:
                        gap = occ.tail_position_m - current_position_m
                        return block.occupying_train_id, max(0, gap)
        return None, float("inf")

    def check_headway(
        self,
        line_code: str,
        direction: Direction,
        rear_position_m: float,
        train_length_m: float,
    ) -> tuple[float, bool]:
        lead_id, gap = self.get_leading_train(
            line_code, direction, rear_position_m, train_length_m
        )
        if lead_id is None:
            return float("inf"), True
        safe_gap = 50.0
        return gap, gap >= safe_gap

    def get_authority(self, block_id: str) -> MovementAuthority:
        block = self.blocks.get(block_id)
        return block.authority if block else MovementAuthority.STOP

    def set_authority(self, block_id: str, authority: MovementAuthority) -> None:
        block = self.blocks.get(block_id)
        if block:
            block.authority = authority

    def get_occupied_blocks(self) -> list[SignalBlock]:
        return [b for b in self.blocks.values() if b.is_occupied]

    def get_line_occupancy(self, line_code: str) -> dict[str, list[SignalBlock]]:
        result: dict[str, list[SignalBlock]] = {}
        for direction in (Direction.UP, Direction.DOWN):
            blocks = self._line_blocks.get(line_code, {}).get(direction.value, [])
            result[direction.value] = [b for b in blocks if b.is_occupied]
        return result

    def find_route_blocks(
        self,
        from_station_code: str,
        to_station_code: str,
        line_code: str,
        direction: Direction,
    ) -> list[str]:
        blocks = self._line_blocks.get(line_code, {}).get(direction.value, [])
        in_route = False
        route_blocks: list[str] = []
        for block in blocks:
            if (
                block.from_station_id == from_station_code
                or block.to_station_id == from_station_code
            ):
                in_route = True
            if in_route:
                route_blocks.append(block.block_id)
            if (
                block.from_station_id == to_station_code
                or block.to_station_id == to_station_code
            ):
                break
        return route_blocks
