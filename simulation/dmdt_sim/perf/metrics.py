from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import datetime
from typing import Any


class MetricsCollector:
    def __init__(self) -> None:
        self._snapshots: list[dict[str, float]] = []
        self._train_metrics: dict[str, list[dict[str, float]]] = defaultdict(list)
        self._line_metrics: dict[str, list[dict[str, float]]] = defaultdict(list)
        self._passenger_metrics: dict[str, float] = {}
        self._headway_samples: list[float] = []
        self._dwell_samples: list[float] = []
        self._journey_times: list[float] = []
        self._energy_samples: list[float] = []
        self._speed_samples: list[float] = []

    def record_snapshot(self, data: dict[str, float]) -> None:
        self._snapshots.append(data)

    def record_train_metric(self, train_id: str, data: dict[str, float]) -> None:
        self._train_metrics[train_id].append(data)

    def record_line_metric(self, line_code: str, data: dict[str, float]) -> None:
        self._line_metrics[line_code].append(data)

    def record_headway(self, headway_s: float) -> None:
        self._headway_samples.append(headway_s)

    def record_dwell(self, dwell_s: float) -> None:
        self._dwell_samples.append(dwell_s)

    def record_journey_time(self, time_s: float) -> None:
        self._journey_times.append(time_s)

    def record_energy(self, energy_wh: float) -> None:
        self._energy_samples.append(energy_wh)

    def record_speed(self, speed_mps: float) -> None:
        self._speed_samples.append(speed_mps)

    def get_snapshots(self) -> list[dict[str, float]]:
        return list(self._snapshots)

    def get_train_summary(self, train_id: str) -> dict[str, float]:
        data = self._train_metrics.get(train_id, [])
        if not data:
            return {}
        avg_speed = statistics.mean([d.get("speed_mps", 0) for d in data]) if data else 0.0
        max_speed = max(d.get("speed_mps", 0) for d in data) if data else 0.0
        total_energy = sum(d.get("energy_wh", 0) for d in data)
        total_distance = sum(d.get("distance_m", 0) for d in data)
        return {
            "avg_speed_mps": avg_speed,
            "max_speed_mps": max_speed,
            "total_energy_wh": total_energy,
            "total_distance_m": total_distance,
        }

    def get_line_summary(self, line_code: str) -> dict[str, float]:
        data = self._line_metrics.get(line_code, [])
        if not data:
            return {}
        total_trains = data[-1].get("active_trains", 0) if data else 0
        throughput = sum(d.get("passengers_ boarded", 0) for d in data)
        return {"total_trains": float(total_trains), "total_throughput": float(throughput)}

    def get_summary(self) -> dict[str, Any]:
        avg_headway = statistics.mean(self._headway_samples) if self._headway_samples else 0.0
        avg_dwell = statistics.mean(self._dwell_samples) if self._dwell_samples else 0.0
        avg_journey = statistics.mean(self._journey_times) if self._journey_times else 0.0
        avg_energy = statistics.mean(self._energy_samples) if self._energy_samples else 0.0
        avg_speed = statistics.mean(self._speed_samples) if self._speed_samples else 0.0
        p95_speed = sorted(self._speed_samples)[int(len(self._speed_samples) * 0.95)] if len(self._speed_samples) > 20 else avg_speed
        return {
            "avg_headway_s": avg_headway,
            "avg_dwell_s": avg_dwell,
            "avg_journey_time_s": avg_journey,
            "avg_energy_wh": avg_energy,
            "avg_speed_mps": avg_speed,
            "p95_speed_mps": p95_speed,
            "total_snapshots": len(self._snapshots),
            "total_headway_samples": len(self._headway_samples),
            "total_dwell_samples": len(self._dwell_samples),
            "total_journey_times": len(self._journey_times),
        }
