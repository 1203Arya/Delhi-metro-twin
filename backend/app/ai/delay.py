from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from .base import BasePredictor


class DelayPredictor(BasePredictor[GradientBoostingRegressor]):
    def __init__(self, model_dir: str = "") -> None:
        super().__init__(model_dir)
        self._feature_names = [
            "hour",
            "day_of_week",
            "month",
            "is_peak_hour",
            "is_weekend",
            "line_code_encoded",
            "station_sequence",
            "num_stations_remaining",
            "prev_delay_minutes",
            "headway_s",
            "dwell_time_s",
            "train_occupancy_pct",
            "is_terminus",
            "has_junction",
            "num_platforms",
            "track_length_km",
            "speed_limit_kmh",
            "is_curve",
        ]

    def _build_model(self) -> GradientBoostingRegressor:
        return GradientBoostingRegressor(
            n_estimators=300,
            max_depth=5,
            learning_rate=0.08,
            subsample=0.8,
            min_samples_leaf=5,
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
                float(abs(hash(row.get("line_code", ""))) % 100),
                float(row.get("station_sequence", 0)),
                float(row.get("num_stations_remaining", 0)),
                float(row.get("prev_delay_minutes", 0.0)),
                float(row.get("headway_s", 120.0)),
                float(row.get("dwell_time_s", 20.0)),
                float(row.get("train_occupancy_pct", 0.5)),
                float(row.get("is_terminus", 0)),
                float(row.get("has_junction", 0)),
                float(row.get("num_platforms", 2)),
                float(row.get("track_length_km", 1.0)),
                float(row.get("speed_limit_kmh", 80.0)),
                float(row.get("is_curve", 0)),
            ]
            rows.append(features)
        return np.array(rows, dtype=np.float64)

    def _predict_impl(self, data: list[dict[str, Any]] | np.ndarray) -> np.ndarray:
        if isinstance(data, np.ndarray):
            return self.model.predict(data)
        X = self._prepare_features(data)
        return self.model.predict(X)

    def train(self, data: list[dict[str, Any]], target_col: str = "delay_minutes") -> dict[str, float]:
        X = self._prepare_features(data)
        y = np.array([row.get(target_col, 0.0) for row in data], dtype=np.float64)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        self.model = self._build_model()
        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)
        self._metrics = {
            "mae": float(mean_absolute_error(y_test, y_pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_test, y_pred))),
            "r2": float(r2_score(y_test, y_pred)),
            "train_samples": int(len(X_train)),
            "test_samples": int(len(X_test)),
        }
        self._is_trained = True
        return self._metrics

    def generate_synthetic_data(self, n_samples: int = 1000) -> list[dict[str, Any]]:
        rng = np.random.default_rng(42)
        data: list[dict[str, Any]] = []
        lines = ["RD", "YL", "BL", "GR", "OR", "PK", "MG", "GY", "BR", "VL", "GB", "RM"]
        for _ in range(n_samples):
            hour = int(rng.integers(5, 24))
            day = int(rng.integers(0, 7))
            month = int(rng.integers(1, 13))
            is_peak = 1 if (7 <= hour <= 10) or (17 <= hour <= 20) else 0
            is_weekend = 1 if day >= 5 else 0
            line = rng.choice(lines)
            seq = int(rng.integers(1, 30))
            remaining = int(rng.integers(0, 30 - seq))
            prev_delay = max(0, rng.normal(1.5, 3.0))
            headway = rng.uniform(90, 300)
            dwell = rng.uniform(15, 45)
            occupancy = rng.uniform(0.1, 1.2)
            is_term = 1 if seq == 1 or remaining == 0 else 0
            has_junc = int(rng.random() < 0.15)
            n_plat = int(rng.integers(2, 6))
            track_km = rng.uniform(0.5, 3.0)
            speed_limit = rng.uniform(40, 100)
            is_curve = int(rng.random() < 0.2)
            base_delay = prev_delay * 0.3 + (1 - occupancy) * 2.0 + dwell * 0.05
            if is_peak:
                base_delay += 2.0
            if is_weekend:
                base_delay *= 0.7
            noise = rng.normal(0, 1.5)
            delay = max(0, base_delay + noise)
            data.append({
                "hour": hour,
                "day_of_week": day,
                "month": month,
                "is_peak_hour": is_peak,
                "is_weekend": is_weekend,
                "line_code": line,
                "station_sequence": seq,
                "num_stations_remaining": remaining,
                "prev_delay_minutes": round(prev_delay, 2),
                "headway_s": round(headway, 1),
                "dwell_time_s": round(dwell, 1),
                "train_occupancy_pct": round(occupancy, 3),
                "is_terminus": is_term,
                "has_junction": has_junc,
                "num_platforms": n_plat,
                "track_length_km": round(track_km, 3),
                "speed_limit_kmh": speed_limit,
                "is_curve": is_curve,
                "delay_minutes": round(delay, 2),
            })
        return data


DelayPredictor._prepare_features.__annotations__["return"] = np.ndarray
delay_predictor = DelayPredictor()
