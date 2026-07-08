from __future__ import annotations

from .bridge import SimulationBridge

_bridge: SimulationBridge | None = None


def get_bridge() -> SimulationBridge:
    global _bridge
    if _bridge is None:
        _bridge = SimulationBridge()
    return _bridge
