from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, TypeVar

import joblib
import numpy as np

T = TypeVar("T")


class ModelPersistence(ABC):
    def __init__(self, model_dir: str | Path = "") -> None:
        self.model_dir = Path(model_dir) if model_dir else Path(__file__).parent / "models"
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def _model_path(self, name: str) -> Path:
        return self.model_dir / f"{name}.joblib"

    def _metadata_path(self, name: str) -> Path:
        return self.model_dir / f"{name}_meta.json"

    def save_model(self, name: str, model: Any, metadata: dict[str, Any] | None = None) -> Path:
        path = self._model_path(name)
        joblib.dump(model, path)
        if metadata:
            mpath = self._metadata_path(name)
            with open(mpath, "w") as f:
                json.dump(metadata, f, indent=2, default=str)
        return path

    def load_model(self, name: str) -> Any:
        path = self._model_path(name)
        if not path.exists():
            return None
        return joblib.load(path)

    def load_metadata(self, name: str) -> dict[str, Any] | None:
        path = self._metadata_path(name)
        if not path.exists():
            return None
        with open(path) as f:
            return json.load(f)

    def model_exists(self, name: str) -> bool:
        return self._model_path(name).exists()


class BasePredictor(ModelPersistence, Generic[T]):
    def __init__(self, model_dir: str | Path = "") -> None:
        super().__init__(model_dir)
        self.model: T | None = None
        self._is_trained = False
        self._feature_names: list[str] = []
        self._metrics: dict[str, float] = {}

    @property
    def is_trained(self) -> bool:
        return self._is_trained or self.model is not None

    @abstractmethod
    def _build_model(self) -> T:
        ...

    @abstractmethod
    def _prepare_features(self, *args: Any, **kwargs: Any) -> np.ndarray:
        ...

    def train(self, *args: Any, **kwargs: Any) -> dict[str, float]:
        self.model = self._build_model()
        self._is_trained = True
        return self._metrics

    def predict(self, *args: Any, **kwargs: Any) -> Any:
        if not self.is_trained:
            raise RuntimeError("Model not trained. Call train() first.")
        return self._predict_impl(*args, **kwargs)

    @abstractmethod
    def _predict_impl(self, *args: Any, **kwargs: Any) -> Any:
        ...

    def save(self, name: str) -> Path:
        meta = {
            "is_trained": self._is_trained,
            "feature_names": self._feature_names,
            "metrics": self._metrics,
        }
        return self.save_model(name, self.model, meta)

    def load(self, name: str) -> bool:
        self.model = self.load_model(name)
        meta = self.load_metadata(name)
        if meta:
            self._is_trained = meta.get("is_trained", False)
            self._feature_names = meta.get("feature_names", [])
            self._metrics = meta.get("metrics", {})
        return self.model is not None

    def get_metrics(self) -> dict[str, float]:
        return dict(self._metrics)
