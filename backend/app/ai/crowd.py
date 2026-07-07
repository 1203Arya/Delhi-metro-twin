from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from .base import BasePredictor


class CrowdPredictor(BasePredictor[GradientBoostingRegressor]):
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
            "is_terminus",
            "has_junction",
            "is_interchange",
            "num_platforms",
            "num_lines_at_station",
            "nearby_offices",
            "nearby_residential",
            "temperature_c",
            "is_holiday",
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
                float(row.get("month", 1)),
                float(row.get("is_peak_hour", 0)),
                float(row.get("is_weekend", 0)),
                float(abs(hash(row.get("line_code", ""))) % 100),
                float(row.get("station_sequence", 0)),
                float(row.get("is_terminus", 0)),
                float(row.get("has_junction", 0)),
                float(row.get("is_interchange", 0)),
                float(row.get("num_platforms", 2)),
                float(row.get("num_lines_at_station", 1)),
                float(row.get("nearby_offices", 0)),
                float(row.get("nearby_residential", 0)),
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

    def train(
        self, data: list[dict[str, Any]], target_col: str = "crowding_pct"
    ) -> dict[str, float]:
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

    def predict_station(
        self,
        station_code: str,
        line_code: str,
        hour: int,
        day_of_week: int = 0,
        month: int = 1,
    ) -> float:
        is_peak = 1 if (7 <= hour <= 10) or (17 <= hour <= 20) else 0
        is_weekend = 1 if day_of_week >= 5 else 0
        row = {
            "hour": hour,
            "day_of_week": day_of_week,
            "month": month,
            "is_peak_hour": is_peak,
            "is_weekend": is_weekend,
            "line_code": line_code,
            "station_sequence": 15,
            "is_terminus": 0,
            "has_junction": 0,
            "is_interchange": 1,
            "num_platforms": 2,
            "num_lines_at_station": 2,
            "nearby_offices": 5,
            "nearby_residential": 3,
            "temperature_c": 25.0,
            "is_holiday": 0,
        }
        result = self.predict([row])
        return float(result[0])

    def generate_synthetic_data(self, n_samples: int = 1000) -> list[dict[str, Any]]:
        rng = np.random.default_rng(42)
        data: list[dict[str, Any]] = []
        lines = ["RD", "YL", "BL", "GR", "OR", "PK"]
        for _ in range(n_samples):
            hour = int(rng.integers(5, 24))
            day = int(rng.integers(0, 7))
            month = int(rng.integers(1, 13))
            is_peak = 1 if (7 <= hour <= 10) or (17 <= hour <= 20) else 0
            is_weekend = 1 if day >= 5 else 0
            seq = int(rng.integers(1, 30))
            is_term = 1 if seq <= 2 or seq >= 28 else 0
            base_crowding = 30.0
            if is_peak:
                base_crowding += 40.0
            if is_weekend:
                base_crowding -= 15.0
            if is_term:
                base_crowding += 10.0
            base_crowding += rng.normal(0, 8)
            crowding = float(np.clip(base_crowding, 5, 100))
            data.append(
                {
                    "hour": hour,
                    "day_of_week": day,
                    "month": month,
                    "is_peak_hour": is_peak,
                    "is_weekend": is_weekend,
                    "line_code": rng.choice(lines),
                    "station_sequence": seq,
                    "is_terminus": is_term,
                    "has_junction": int(rng.random() < 0.15),
                    "is_interchange": int(rng.random() < 0.2),
                    "num_platforms": int(rng.integers(2, 6)),
                    "num_lines_at_station": int(rng.integers(1, 4)),
                    "nearby_offices": int(rng.integers(0, 20)),
                    "nearby_residential": int(rng.integers(0, 30)),
                    "temperature_c": round(rng.uniform(10, 45), 1),
                    "is_holiday": int(rng.random() < 0.05),
                    "crowding_pct": round(crowding, 1),
                }
            )
        return data


crowd_predictor = CrowdPredictor()
