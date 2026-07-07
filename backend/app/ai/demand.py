from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from .base import BasePredictor


class DemandPredictor(BasePredictor[GradientBoostingRegressor]):
    def __init__(self, model_dir: str = "") -> None:
        super().__init__(model_dir)
        self._od_pairs: dict[str, float] = {}
        self._feature_names = [
            "hour",
            "day_of_week",
            "month",
            "is_peak_hour",
            "is_weekend",
            "origin_line_encoded",
            "dest_line_encoded",
            "origin_sequence",
            "dest_sequence",
            "station_distance_km",
            "num_interchanges",
            "num_stations_between",
            "is_same_line",
            "is_reverse_direction",
            "origin_nearby_offices",
            "dest_nearby_offices",
            "origin_nearby_residential",
            "dest_nearby_residential",
            "temperature_c",
            "is_holiday",
        ]

    def _build_model(self) -> GradientBoostingRegressor:
        return GradientBoostingRegressor(
            n_estimators=400,
            max_depth=5,
            learning_rate=0.06,
            subsample=0.8,
            min_samples_leaf=10,
            random_state=42,
        )

    def _prepare_features(self, data: list[dict[str, Any]]) -> np.ndarray:
        rows = []
        for row in data:
            features = [
                float(row.get("hour", 12)),
                float(row.get("day_of_week", 0)),
                float(row.get("month", 1)),
                float(row.get("is_peak_hour", 0)),
                float(row.get("is_weekend", 0)),
                float(abs(hash(row.get("origin_line", ""))) % 100),
                float(abs(hash(row.get("dest_line", ""))) % 100),
                float(row.get("origin_sequence", 0)),
                float(row.get("dest_sequence", 0)),
                float(row.get("station_distance_km", 5.0)),
                float(row.get("num_interchanges", 0)),
                float(row.get("num_stations_between", 0)),
                float(row.get("is_same_line", 1)),
                float(row.get("is_reverse_direction", 0)),
                float(row.get("origin_nearby_offices", 0)),
                float(row.get("dest_nearby_offices", 0)),
                float(row.get("origin_nearby_residential", 0)),
                float(row.get("dest_nearby_residential", 0)),
                float(row.get("temperature_c", 25.0)),
                float(row.get("is_holiday", 0)),
            ]
            rows.append(features)
        return np.array(rows, dtype=np.float64)

    def _predict_impl(self, data: list[dict[str, Any]] | np.ndarray) -> np.ndarray:
        if isinstance(data, np.ndarray):
            return self.model.predict(data)
        X = self._prepare_features(data)
        return self.model.predict(X)

    def train(self, data: list[dict[str, Any]], target_col: str = "passenger_count") -> dict[str, float]:
        X = self._prepare_features(data)
        y = np.array([row.get(target_col, 0.0) for row in data], dtype=np.float64)
        y = np.maximum(y, 0)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        self.model = self._build_model()
        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)
        y_pred = np.maximum(y_pred, 0)
        self._metrics = {
            "mae": float(mean_absolute_error(y_test, y_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
            "r2": float(r2_score(y_test, y_pred)),
            "train_samples": int(len(X_train)),
            "test_samples": int(len(X_test)),
        }
        for i, row in enumerate(data):
            key = f"{row.get('origin_station','')}->{row.get('dest_station','')}"
            self._od_pairs[key] = float(y[i])
        self._is_trained = True
        return self._metrics

    def predict_od(
        self,
        origin_station: str,
        dest_station: str,
        origin_line: str = "",
        dest_line: str = "",
        hour: int = 12,
        day_of_week: int = 0,
    ) -> float:
        is_peak = 1 if (7 <= hour <= 10) or (17 <= hour <= 20) else 0
        is_weekend = 1 if day_of_week >= 5 else 0
        same_line = 1 if origin_line == dest_line else 0
        row = {
            "hour": hour,
            "day_of_week": day_of_week,
            "month": 1,
            "is_peak_hour": is_peak,
            "is_weekend": is_weekend,
            "origin_line": origin_line,
            "dest_line": dest_line,
            "origin_sequence": 1,
            "dest_sequence": 10,
            "station_distance_km": 10.0,
            "num_interchanges": 0 if same_line else 1,
            "num_stations_between": 9,
            "is_same_line": same_line,
            "is_reverse_direction": 0,
            "origin_nearby_offices": 5,
            "dest_nearby_offices": 5,
            "origin_nearby_residential": 3,
            "dest_nearby_residential": 3,
            "temperature_c": 25.0,
            "is_holiday": 0,
        }
        result = self.predict([row])
        return float(max(0, result[0]))

    def get_top_od_pairs(self, n: int = 10) -> list[dict[str, Any]]:
        sorted_pairs = sorted(self._od_pairs.items(), key=lambda x: x[1], reverse=True)
        return [
            {"origin_dest": k, "passenger_count": round(v, 1)}
            for k, v in sorted_pairs[:n]
        ]

    def generate_synthetic_data(self, n_samples: int = 1000) -> list[dict[str, Any]]:
        rng = np.random.default_rng(42)
        data: list[dict[str, Any]] = []
        station_list = [
            ("STA", "RD", 1), ("STB", "RD", 2), ("STC", "RD", 3), ("STD", "RD", 4),
            ("ST1", "YL", 1), ("ST2", "YL", 2), ("ST3", "YL", 3),
            ("S4A", "BL", 1), ("S4B", "BL", 2), ("S4C", "BL", 3), ("S4D", "BL", 4),
        ]
        for _ in range(n_samples):
            orig_idx = int(rng.integers(0, len(station_list)))
            dest_idx = int(rng.integers(0, len(station_list)))
            while dest_idx == orig_idx:
                dest_idx = int(rng.integers(0, len(station_list)))
            orig = station_list[orig_idx]
            dest = station_list[dest_idx]
            hour = int(rng.integers(5, 24))
            day = int(rng.integers(0, 7))
            is_peak = 1 if (7 <= hour <= 10) or (17 <= hour <= 20) else 0
            is_weekend = 1 if day >= 5 else 0
            dist = abs(orig[2] - dest[2]) * 1.5 + float(rng.uniform(0, 2))
            n_inter = 0 if orig[1] == dest[1] else int(rng.integers(1, 3))
            n_stations = abs(orig[2] - dest[2])
            same = 1 if orig[1] == dest[1] else 0
            base = 50.0 if is_peak else 20.0
            if is_weekend:
                base *= 0.6
            base += rng.poisson(30)
            count = max(0, int(base + rng.normal(0, 10)))
            data.append({
                "hour": hour,
                "day_of_week": day,
                "month": int(rng.integers(1, 13)),
                "is_peak_hour": is_peak,
                "is_weekend": is_weekend,
                "origin_station": orig[0],
                "dest_station": dest[0],
                "origin_line": orig[1],
                "dest_line": dest[1],
                "origin_sequence": orig[2],
                "dest_sequence": dest[2],
                "station_distance_km": round(dist, 2),
                "num_interchanges": n_inter,
                "num_stations_between": int(n_stations),
                "is_same_line": same,
                "is_reverse_direction": int(orig[2] > dest[2] and same),
                "origin_nearby_offices": int(rng.integers(0, 20)),
                "dest_nearby_offices": int(rng.integers(0, 20)),
                "origin_nearby_residential": int(rng.integers(0, 30)),
                "dest_nearby_residential": int(rng.integers(0, 30)),
                "temperature_c": round(rng.uniform(10, 45), 1),
                "is_holiday": int(rng.random() < 0.05),
                "passenger_count": count,
            })
        return data


demand_predictor = DemandPredictor()
