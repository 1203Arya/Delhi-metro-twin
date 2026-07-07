from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Any


from .crowd import CrowdPredictor
from .delay import DelayPredictor
from .demand import DemandPredictor
from .eta import ETAPredictor
from .incident import IncidentPredictor

logger = logging.getLogger("ai.train")


def train_all(
    model_dir: str | Path = "",
    n_samples: int = 2000,
    verbose: bool = True,
) -> dict[str, dict[str, float]]:
    results: dict[str, dict[str, float]] = {}
    predictors: dict[str, Any] = {
        "delay": (
            DelayPredictor(model_dir),
            DelayPredictor().generate_synthetic_data(n_samples),
            "delay_minutes",
        ),
        "crowd": (
            CrowdPredictor(model_dir),
            CrowdPredictor().generate_synthetic_data(n_samples),
            "crowding_pct",
        ),
        "demand": (
            DemandPredictor(model_dir),
            DemandPredictor().generate_synthetic_data(n_samples),
            "passenger_count",
        ),
        "eta": (
            ETAPredictor(model_dir),
            ETAPredictor().generate_synthetic_data(n_samples),
            "travel_time_s",
        ),
        "incident": (
            IncidentPredictor(model_dir),
            IncidentPredictor().generate_synthetic_data(n_samples),
            "incident_occurred",
        ),
    }
    for name, (predictor, data, target) in predictors.items():
        if verbose:
            logger.info("Training %s predictor on %d samples...", name, len(data))
        t0 = time.time()
        metrics = predictor.train(data, target)
        elapsed = time.time() - t0
        predictor.save(name)
        results[name] = metrics
        if verbose:
            logger.info(
                "  %s trained in %.2fs: %s",
                name,
                elapsed,
                " | ".join(
                    f"{k}={v:.4f}" for k, v in metrics.items() if isinstance(v, float)
                ),
            )
    return results


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(message)s",
        stream=sys.stdout,
    )
    model_dir = Path(__file__).parent / "models"
    results = train_all(str(model_dir), n_samples=3000)
    print("\n=== Training Summary ===")
    for name, metrics in results.items():
        print(f"  {name}:")
        for k, v in metrics.items():
            print(f"    {k}: {v}")
    print(f"\nModels saved to: {model_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
