from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    database: str = "dmdt"
    user: str = "aryamansharma"
    password: str = ""
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10

    @property
    def url(self) -> str:
        if self.password:
            return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        return f"postgresql://{self.user}@{self.host}:{self.port}/{self.database}"

    @property
    def url_psycopg2(self) -> str:
        if self.password:
            return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        return f"postgresql+psycopg2://{self.user}@{self.host}:{self.port}/{self.database}"

    def to_sa_params(self) -> dict[str, Any]:
        return {
            "url": self.url_psycopg2,
            "echo": self.echo,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
        }


def _load_from_env() -> DatabaseConfig:
    return DatabaseConfig(
        host=os.environ.get("DMDT_DB_HOST", "localhost"),
        port=int(os.environ.get("DMDT_DB_PORT", "5432")),
        database=os.environ.get("DMDT_DB_NAME", "dmdt"),
        user=os.environ.get("DMDT_DB_USER", "aryamansharma"),
        password=os.environ.get("DMDT_DB_PASSWORD", ""),
        echo=os.environ.get("DMDT_DB_ECHO", "0") == "1",
        pool_size=int(os.environ.get("DMDT_DB_POOL_SIZE", "5")),
        max_overflow=int(os.environ.get("DMDT_DB_MAX_OVERFLOW", "10")),
    )


db_config = _load_from_env()

_engine = None
_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(**db_config.to_sa_params())
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine())
    return _session_factory
