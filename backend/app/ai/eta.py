from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from .base import BasePredictor


class ETAPredictor(BasePredictor[GradientBoostingRegressor]):
    def __init__(self, model_dir: str = "") -> None:
        super().__init__(model_dir)
        self._feature_names = [
            "hour",
            "day_of_week",
            "is_peak_hour",
            "is_weekend",
            "line_code_encoded",
            "from_sequence",
            "to_sequence",
            "num_stations",
            "total_distance_km",
            "speed_limit_kmh",
            "avg_headway_s",
            "num_curves",
            "max_gradient_pct",
            "is_reverse_peak",
            "num_interchanges",
            "crowding_pct",
        ]

    def _build_model(self) -> GradientBoostingRegressor:
        return GradientBoostingRegressor(
            n_estimators=300,
            max_depth=5,
            learning_rate=0.08,
            subsample=0.8,
            random_state=42,
        )

    def _prepare_features(self, data: list[dict[str, Any]]) -> np.ndarray:
        rows = []
        for row in data:
            features = [
                float(row.get("hour", 12)),
                float(row.get("day_of_week", 0)),
                float(row.get("is_peak_hour", 0)),
                float(row.get("is_weekend", 0)),
                float(abs(hash(row.get("line_code", ""))) % 100),
                float(row.get("from_sequence", 0)),
                float(row.get("to_sequence", 0)),
                float(row.get("num_stations", 1)),
                float(row.get("total_distance_km", 1.0)),
                float(row.get("speed_limit_kmh", 80.0)),
                float(row.get("avg_headway_s", 120.0)),
                float(row.get("num_curves", 0)),
                float(row.get("max_gradient_pct", 0.0)),
                float(row.get("is_reverse_peak", 0)),
                float(row.get("num_interchanges", 0)),
                float(row.get("crowding_pct", 30.0)),
            ]
            rows.append(features)
        return np.array(rows, dtype=np.float64)

    def _predict_impl(self, data: list[dict[str, Any]] | np.ndarray) -> np.ndarray:
        if isinstance(data, np.ndarray):
            return self.model.predict(data)
        X = self._prepare_features(data)
        return self.model.predict(X)

    def train(
        self, data: list[dict[str, Any]], target_col: str = "travel_time_s"
    ) -> dict[str, float]:
        X = self._prepare_features(data)
        y = np.array([row.get(target_col, 0.0) for row in data], dtype=np.float64)
        y = np.maximum(y, 30.0)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        self.model = self._build_model()
        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)
        y_pred = np.maximum(y_pred, 30.0)
        self._metrics = {
            "mae": float(mean_absolute_error(y_test, y_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
            "r2": float(r2_score(y_test, y_pred)),
            "train_samples": int(len(X_train)),
            "test_samples": int(len(X_test)),
        }
        self._is_trained = True
        return self._metrics

    def predict_eta(
        self,
        from_station: str,
        to_station: str,
        line_code: str,
        hour: int = 12,
        day_of_week: int = 0,
    ) -> float:
        is_peak = 1 if (7 <= hour <= 10) or (17 <= hour <= 20) else 0
        is_weekend = 1 if day_of_week >= 5 else 0
        is_rev = 1 if is_peak and (17 <= hour <= 20) else 0
        row = {
            "hour": hour,
            "day_of_week": day_of_week,
            "is_peak_hour": is_peak,
            "is_weekend": is_weekend,
            "line_code": line_code,
            "from_sequence": 1,
            "to_sequence": 5,
            "num_stations": 4,
            "total_distance_km": 6.0,
            "speed_limit_kmh": 80.0,
            "avg_headway_s": 120.0,
            "num_curves": 2,
            "max_gradient_pct": 1.5,
            "is_reverse_peak": is_rev,
            "num_interchanges": 0,
            "crowding_pct": 40.0 if is_peak else 20.0,
        }
        result = self.predict([row])
        return float(max(30.0, result[0]))

    def generate_synthetic_data(self, n_samples: int = 1000) -> list[dict[str, Any]]:
        rng = np.random.default_rng(42)
        data: list[dict[str, Any]] = []
        lines = ["RD", "YL", "BL", "GR", "OR"]
        for _ in range(n_samples):
            hour = int(rng.integers(5, 24))
            day = int(rng.integers(0, 7))
            is_peak = 1 if (7 <= hour <= 10) or (17 <= hour <= 20) else 0
            is_weekend = 1 if day >= 5 else 0
            from_seq = int(rng.integers(1, 25))
            to_seq = int(rng.integers(from_seq + 1, min(from_seq + 10, 30)))
            n_stations = to_seq - from_seq
            dist = n_stations * rng.uniform(1.0, 2.5)
            speed_limit = rng.uniform(50, 100)
            n_curves = int(rng.integers(0, n_stations))
            gradient = rng.uniform(0, 3)
            headway = rng.uniform(90, 300)
            crowding = rng.uniform(10, 90)
            base_time = (dist / speed_limit) * 3600 + n_stations * 25
            if is_peak:
                base_time *= 1.15
            if is_weekend:
                base_time *= 0.9
            base_time += rng.normal(0, 30)
            travel_time = max(30, base_time)
            data.append(
                {
                    "hour": hour,
                    "day_of_week": day,
                    "month": int(rng.integers(1, 13)),
                    "is_peak_hour": is_peak,
                    "is_weekend": is_weekend,
                    "line_code": rng.choice(lines),
                    "from_sequence": from_seq,
                    "to_sequence": to_seq,
                    "num_stations": n_stations,
                    "total_distance_km": round(dist, 2),
                    "speed_limit_kmh": speed_limit,
                    "avg_headway_s": round(headway, 1),
                    "num_curves": n_curves,
                    "max_gradient_pct": round(gradient, 2),
                    "is_reverse_peak": 1 if is_peak and (17 <= hour <= 20) else 0,
                    "num_interchanges": int(rng.integers(0, 3)),
                    "crowding_pct": round(crowding, 1),
                    "travel_time_s": round(travel_time, 1),
                }
            )
        return data


eta_predictor = ETAPredictor()
