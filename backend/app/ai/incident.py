from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

from .base import BasePredictor


class IncidentPredictor(BasePredictor[GradientBoostingClassifier]):
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
            "num_trains_active",
            "avg_headway_s",
            "avg_speed_kmh",
            "avg_occupancy_pct",
            "is_terminus",
            "has_junction",
            "num_platforms",
            "track_length_km",
            "speed_limit_kmh",
            "is_curve",
            "max_gradient_pct",
            "days_since_last_incident",
            "prev_incidents_24h",
        ]

    def _build_model(self) -> GradientBoostingClassifier:
        return GradientBoostingClassifier(
            n_estimators=300,
            max_depth=4,
            learning_rate=0.08,
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
                float(abs(hash(row.get("line_code", ""))) % 100),
                float(row.get("station_sequence", 0)),
                float(row.get("num_trains_active", 10)),
                float(row.get("avg_headway_s", 120.0)),
                float(row.get("avg_speed_kmh", 45.0)),
                float(row.get("avg_occupancy_pct", 50.0)),
                float(row.get("is_terminus", 0)),
                float(row.get("has_junction", 0)),
                float(row.get("num_platforms", 2)),
                float(row.get("track_length_km", 1.0)),
                float(row.get("speed_limit_kmh", 80.0)),
                float(row.get("is_curve", 0)),
                float(row.get("max_gradient_pct", 0.0)),
                float(row.get("days_since_last_incident", 30.0)),
                float(row.get("prev_incidents_24h", 0)),
            ]
            rows.append(features)
        return np.array(rows, dtype=np.float64)

    def _predict_impl(self, data: list[dict[str, Any]] | np.ndarray) -> np.ndarray:
        if isinstance(data, np.ndarray):
            return self.model.predict(data)
        X = self._prepare_features(data)
        return self.model.predict(X)

    def predict_proba(self, data: list[dict[str, Any]]) -> np.ndarray:
        if not self.is_trained:
            raise RuntimeError("Model not trained. Call train() first.")
        X = self._prepare_features(data)
        return self.model.predict_proba(X)

    def train(self, data: list[dict[str, Any]], target_col: str = "incident_occurred") -> dict[str, float]:
        X = self._prepare_features(data)
        y = np.array([int(row.get(target_col, 0)) for row in data], dtype=np.int32)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        self.model = self._build_model()
        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)
        y_proba = self.model.predict_proba(X_test)[:, 1]
        self._metrics = {
            "accuracy": float(accuracy_score(y_test, y_pred)),
            "precision": float(precision_score(y_test, y_pred, zero_division=0)),
            "recall": float(recall_score(y_test, y_pred, zero_division=0)),
            "f1": float(f1_score(y_test, y_pred, zero_division=0)),
            "roc_auc": float(roc_auc_score(y_test, y_proba) if len(np.unique(y_test)) > 1 else 0.0),
            "train_samples": int(len(X_train)),
            "test_samples": int(len(X_test)),
        }
        self._is_trained = True
        return self._metrics

    def predict_risk(
        self,
        line_code: str,
        station_sequence: int = 5,
        hour: int = 12,
        day_of_week: int = 0,
    ) -> dict[str, Any]:
        is_peak = 1 if (7 <= hour <= 10) or (17 <= hour <= 20) else 0
        is_weekend = 1 if day_of_week >= 5 else 0
        row = {
            "hour": hour,
            "day_of_week": day_of_week,
            "month": 1,
            "is_peak_hour": is_peak,
            "is_weekend": is_weekend,
            "line_code": line_code,
            "station_sequence": station_sequence,
            "num_trains_active": 15,
            "avg_headway_s": 120.0,
            "avg_speed_kmh": 45.0,
            "avg_occupancy_pct": 60.0,
            "is_terminus": 1 if station_sequence <= 2 else 0,
            "has_junction": 1,
            "num_platforms": 2,
            "track_length_km": 1.5,
            "speed_limit_kmh": 80.0,
            "is_curve": 0,
            "max_gradient_pct": 1.0,
            "days_since_last_incident": 30.0,
            "prev_incidents_24h": 0,
        }
        proba = self.predict_proba([row])[0]
        risk_pct = float(proba[1] * 100)
        level = "low"
        if risk_pct >= 30:
            level = "medium"
        if risk_pct >= 60:
            level = "high"
        return {
            "risk_probability_pct": round(risk_pct, 2),
            "risk_level": level,
            "line_code": line_code,
            "hour": hour,
        }

    def generate_synthetic_data(self, n_samples: int = 2000) -> list[dict[str, Any]]:
        rng = np.random.default_rng(42)
        data: list[dict[str, Any]] = []
        lines = ["RD", "YL", "BL", "GR", "OR", "PK", "MG"]
        for _ in range(n_samples):
            hour = int(rng.integers(5, 24))
            day = int(rng.integers(0, 7))
            month = int(rng.integers(1, 13))
            is_peak = 1 if (7 <= hour <= 10) or (17 <= hour <= 20) else 0
            is_weekend = 1 if day >= 5 else 0
            seq = int(rng.integers(1, 30))
            n_trains = int(rng.integers(5, 30))
            headway = rng.uniform(90, 300)
            speed = rng.uniform(20, 70)
            occupancy = rng.uniform(20, 95)
            days_since = rng.uniform(0, 60)
            prev_24h = int(rng.integers(0, 5))
            base_risk = 0.02
            if is_peak:
                base_risk += 0.08
            if occupancy > 80:
                base_risk += 0.05
            if headway < 100:
                base_risk += 0.03
            if days_since < 7:
                base_risk += 0.04
            if prev_24h > 0:
                base_risk += prev_24h * 0.02
            if speed > 60:
                base_risk += 0.02
            risk = float(np.clip(base_risk + rng.normal(0, 0.03), 0, 1))
            incident = 1 if rng.random() < risk else 0
            data.append({
                "hour": hour,
                "day_of_week": day,
                "month": month,
                "is_peak_hour": is_peak,
                "is_weekend": is_weekend,
                "line_code": rng.choice(lines),
                "station_sequence": seq,
                "num_trains_active": n_trains,
                "avg_headway_s": round(headway, 1),
                "avg_speed_kmh": round(speed, 1),
                "avg_occupancy_pct": round(occupancy, 1),
                "is_terminus": 1 if seq <= 2 or seq >= 28 else 0,
                "has_junction": int(rng.random() < 0.15),
                "num_platforms": int(rng.integers(2, 6)),
                "track_length_km": round(rng.uniform(0.5, 3.0), 3),
                "speed_limit_kmh": rng.uniform(40, 100),
                "is_curve": int(rng.random() < 0.2),
                "max_gradient_pct": round(rng.uniform(0, 3), 2),
                "days_since_last_incident": round(days_since, 1),
                "prev_incidents_24h": prev_24h,
                "incident_occurred": incident,
            })
        return data


incident_predictor = IncidentPredictor()
