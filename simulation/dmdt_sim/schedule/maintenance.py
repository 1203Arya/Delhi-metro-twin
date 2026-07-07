from __future__ import annotations

from typing import Any

from ..types import MaintenanceSlot, SimulationConfig


class MaintenanceScheduler:
    def __init__(self, config: SimulationConfig) -> None:
        self.config = config
        self.slots: list[MaintenanceSlot] = []
        self._train_last_service: dict[str, float] = {}

    def register_train(self, train_id: str, start_time: float) -> None:
        self._train_last_service[train_id] = start_time

    def check_due(self, train_id: str, current_time: float) -> bool:
        last = self._train_last_service.get(train_id)
        if last is None:
            return True
        return (current_time - last) >= self.config.maintenance_interval_s

    def schedule(self, train_id: str, current_time: float, depot_name: str, description: str = "routine inspection") -> MaintenanceSlot:
        slot = MaintenanceSlot(
            train_id=train_id,
            start_time=current_time,
            end_time=current_time + 1800.0,
            depot_name=depot_name,
            description=description,
        )
        self.slots.append(slot)
        self._train_last_service[train_id] = current_time
        return slot

    def get_slots_for_train(self, train_id: str) -> list[MaintenanceSlot]:
        return [s for s in self.slots if s.train_id == train_id]

    def get_active_slots(self, current_time: float) -> list[MaintenanceSlot]:
        return [s for s in self.slots if s.start_time <= current_time <= s.end_time]
