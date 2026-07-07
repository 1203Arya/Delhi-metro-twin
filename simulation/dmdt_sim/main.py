from __future__ import annotations

import json
import sys
import time as time_mod
from pathlib import Path

from .engine import SimulationEngine
from .types import SimulationConfig


def load_json(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Delhi Metro Simulation Engine")
    parser.add_argument("--network", type=str, help="Path to network JSON")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed")
    parser.add_argument("--duration", type=float, default=3600.0, help="Simulation duration in seconds")
    parser.add_argument("--dt", type=float, default=1.0, help="Simulation timestep in seconds")
    parser.add_argument("--passengers", type=int, default=50000, help="Number of passenger agents")
    parser.add_argument("--headway", type=float, default=120.0, help="Target headway in seconds")
    parser.add_argument("--output", type=str, default="", help="Path to write output snapshots JSON")
    parser.add_argument("--snapshot-interval", type=float, default=30.0, help="Snapshot interval in seconds")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")

    args = parser.parse_args()

    config = SimulationConfig(
        dt_s=args.dt,
        seed=args.seed,
        duration_s=args.duration,
        n_passengers=args.passengers,
        headway_target_s=args.headway,
    )

    engine = SimulationEngine(config)
    engine.snapshot_interval_s = args.snapshot_interval

    if args.network:
        network_data = load_json(args.network)
        engine.load_network(network_data)

    if not args.quiet:
        print(f"Initializing simulation with {args.passengers} passengers...", file=sys.stderr)

    start_wall = time_mod.time()
    snapshots = engine.run()
    elapsed = time_mod.time() - start_wall

    state = engine.get_state()

    if not args.quiet:
        print(f"\nSimulation completed in {elapsed:.2f}s wall time", file=sys.stderr)
        print(f"Simulated {args.duration:.0f}s of operations", file=sys.stderr)
        print(f"Trains: {state['trains']} ({state['active_trains']} active)", file=sys.stderr)
        print(f"Passengers: {state['passengers']} total, {state['completed_passengers']} completed", file=sys.stderr)
        print(f"Active incidents: {state['active_incidents']}", file=sys.stderr)
        print(f"Snapshots captured: {len(snapshots)}", file=sys.stderr)
        print(f"\nMetrics:", file=sys.stderr)
        for k, v in state["metrics"].items():
            print(f"  {k}: {v}", file=sys.stderr)

    if args.output:
        output_data = {
            "config": {
                "duration_s": args.duration,
                "dt_s": args.dt,
                "seed": args.seed,
                "n_passengers": args.passengers,
                "headway_s": args.headway,
            },
            "summary": state,
            "snapshots": [
                {
                    "time": s.time_s,
                    "train_count": len(s.trains),
                    "active_trains": sum(
                        1 for t in s.trains if t.get("status") == "running"
                    ),
                    "completed_passengers": sum(
                        1 for p in s.passengers if p.get("state") == "completed"
                    ),
                    "active_incidents": len(s.incidents),
                }
                for s in snapshots
            ],
        }
        with open(args.output, "w") as f:
            json.dump(output_data, f, indent=2)
        if not args.quiet:
            print(f"\nOutput written to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
