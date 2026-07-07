from __future__ import annotations

from collections import defaultdict
from typing import Any

from ..types import TrainSpec


class DepotYard:
    def __init__(self) -> None:
        self.depots: dict[str, dict[str, Any]] = {}
        self._yard_trains: dict[str, list[str]] = defaultdict(list)
        self._train_specs: dict[str, TrainSpec] = {}
        self._train_depot: dict[str, str] = {}

    def add_depot(self, depot_data: dict[str, Any]) -> None:
        name = depot_data.get("name", depot_data.get("code", ""))
        self.depots[name] = depot_data

    def register_train(self, train_id: str, spec: TrainSpec, depot_name: str) -> None:
        self._train_specs[train_id] = spec
        self._train_depot[train_id] = depot_name
        self._yard_trains[depot_name].append(train_id)

    def store_train(self, train_id: str, depot_name: str) -> None:
        if train_id not in self._train_specs:
            return
        self._train_depot[train_id] = depot_name
        self._yard_trains[depot_name].append(train_id)

    def dispatch_train(self, depot_name: str) -> str | None:
        yard = self._yard_trains.get(depot_name, [])
        if not yard:
            return None
        train_id = yard.pop(0)
        self._train_depot[train_id] = ""
        return train_id

    def return_to_depot(self, train_id: str, depot_name: str) -> None:
        self._yard_trains[depot_name].append(train_id)
        self._train_depot[train_id] = depot_name

    def get_available_trains(self, depot_name: str) -> list[str]:
        return list(self._yard_trains.get(depot_name, []))

    def get_train_count(self, depot_name: str) -> int:
        return len(self._yard_trains.get(depot_name, []))

    def get_train_spec(self, train_id: str) -> TrainSpec | None:
        return self._train_specs.get(train_id)

    def is_in_depot(self, train_id: str) -> bool:
        depot = self._train_depot.get(train_id, "")
        return bool(depot)
