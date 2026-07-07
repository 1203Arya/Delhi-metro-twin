from __future__ import annotations

from typing import Any

from .crowd import crowd_predictor
from .delay import delay_predictor
from .demand import demand_predictor
from .eta import eta_predictor
from .incident import incident_predictor


class InferenceEngine:
    def __init__(self) -> None:
        self.predictors = {
            "delay": delay_predictor,
            "crowd": crowd_predictor,
            "demand": demand_predictor,
            "eta": eta_predictor,
            "incident": incident_predictor,
        }

    def load_all(self, model_dir: str = "") -> dict[str, bool]:
        results: dict[str, bool] = {}
        for name, predictor in self.predictors.items():
            try:
                ok = predictor.load(name)
                results[name] = ok
            except Exception:
                results[name] = False
        return results

    def predict(self, model_name: str, data: Any) -> Any:
        predictor = self.predictors.get(model_name)
        if predictor is None:
            raise ValueError(f"Unknown model: {model_name}")
        return predictor.predict(data)

    def predict_delay(self, features: list[dict[str, Any]]) -> list[float]:
        return [float(x) for x in self.predictors["delay"].predict(features)]

    def predict_crowd(self, features: list[dict[str, Any]]) -> list[float]:
        return [float(x) for x in self.predictors["crowd"].predict(features)]

    def predict_demand(self, features: list[dict[str, Any]]) -> list[float]:
        return [float(x) for x in self.predictors["demand"].predict(features)]

    def predict_eta(self, features: list[dict[str, Any]]) -> list[float]:
        return [float(x) for x in self.predictors["eta"].predict(features)]

    def predict_incident(self, features: list[dict[str, Any]]) -> list[int]:
        return [int(x) for x in self.predictors["incident"].predict(features)]

    def predict_incident_proba(self, features: list[dict[str, Any]]) -> list[float]:
        proba = self.predictors["incident"].predict_proba(features)
        return [float(p[1]) for p in proba] if proba.shape[1] > 1 else [0.0] * len(features)

    def is_ready(self) -> dict[str, bool]:
        return {name: p.is_trained for name, p in self.predictors.items()}


inference_engine = InferenceEngine()
