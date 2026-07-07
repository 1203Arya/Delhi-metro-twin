from __future__ import annotations

import logging
import sys
from pathlib import Path

from .config import settings


def setup_logging(*, log_dir: str | Path | None = None) -> None:
    fmt = (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
    )

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_path / "dmdt.log"))

    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format=fmt,
        handlers=handlers,
    )
