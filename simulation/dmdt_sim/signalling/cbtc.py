from __future__ import annotations

from typing import Any

from ..types import Direction, MovementAuthority, TrainSpec
from .block import BlockManager


class CBTCController:
    def __init__(
        self, block_manager: BlockManager, min_headway_m: float = 50.0
    ) -> None:
        self.block_manager = block_manager
        self.min_headway_m = min_headway_m
        self.safe_braking_distance_factor: float = 1.2
        self.atp_active: bool = True
        self.ato_active: bool = True

    def compute_movement_authority(
        self,
        train_id: str,
        line_code: str,
        direction: Direction,
        current_position_m: float,
        current_speed_mps: float,
        train_spec: TrainSpec,
    ) -> MovementAuthority:
        if not self.atp_active:
            return MovementAuthority.MOVEMENT
        brake_dist = (current_speed_mps * current_speed_mps) / (
            2 * train_spec.deceleration_ms2
        )
        safe_stop_dist = brake_dist * self.safe_braking_distance_factor
        lead_id, gap = self.block_manager.get_leading_train(
            line_code, direction, current_position_m, train_spec.length_m
        )
        if lead_id is not None and gap < safe_stop_dist + self.min_headway_m:
            if gap < self.min_headway_m:
                return MovementAuthority.STOP
            return MovementAuthority.RESTRICTED
        return MovementAuthority.MOVEMENT

    def compute_target_speed(
        self,
        authority: MovementAuthority,
        current_speed_mps: float,
        distance_to_obstruction_m: float,
        train_spec: TrainSpec,
        speed_limit_mps: float,
    ) -> float:
        if authority == MovementAuthority.STOP:
            return 0.0
        if authority == MovementAuthority.RESTRICTED:
            safe_speed = (
                2 * train_spec.deceleration_ms2 * distance_to_obstruction_m
            ) ** 0.5
            return min(safe_speed, speed_limit_mps * 0.5)
        return speed_limit_mps

    def compute_ato_profile(
        self,
        current_speed_mps: float,
        target_speed_mps: float,
        distance_to_target_m: float,
        train_spec: TrainSpec,
        dt: float,
    ) -> dict[str, Any]:
        if not self.ato_active:
            return {"mode": "coast", "acceleration": 0.0}
        speed_diff = target_speed_mps - current_speed_mps
        if distance_to_target_m < 5.0:
            return {"mode": "brake", "acceleration": -train_spec.deceleration_ms2}
        if speed_diff > 0.5:
            accel = min(speed_diff / dt, train_spec.acceleration_ms2)
            return {"mode": "accelerate", "acceleration": accel}
        elif speed_diff < -0.5:
            decel = max(speed_diff / dt, -train_spec.deceleration_ms2)
            return {"mode": "brake", "acceleration": decel}
        else:
            return {"mode": "cruise", "acceleration": 0.0}

    def check_conflicts(
        self, line_code: str, direction: Direction
    ) -> list[dict[str, Any]]:
        conflicts: list[dict[str, Any]] = []
        blocks = self.block_manager._line_blocks.get(line_code, {}).get(
            direction.value, []
        )
        prev_occupied = False
        for block in blocks:
            if block.is_occupied and prev_occupied:
                conflicts.append(
                    {
                        "type": "adjacent_occupancy",
                        "block_id": block.block_id,
                        "line_code": line_code,
                        "direction": direction.value,
                    }
                )
            prev_occupied = block.is_occupied
        return conflicts
