from __future__ import annotations

import os
from dataclasses import dataclass
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
        return (
            f"postgresql+psycopg2://{self.user}@{self.host}:{self.port}/{self.database}"
        )

    def to_sa_params(self) -> dict[str, Any]:
        return {
            "url": self.url_psycopg2,
            "echo": self.echo,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
        }


def _parse_database_url(url: str) -> dict[str, str | int]:
    """Parse a postgresql:// or postgresql+asyncpg:// URL into component parts."""
    parts = url.split("://", 1)[1] if "://" in url else url
    creds, rest = parts.split("@", 1) if "@" in parts else ("", parts)
    user = creds.split(":", 1)[0] if ":" in creds else creds
    password = creds.split(":", 1)[1] if ":" in creds else ""
    host_port, database = rest.split("/", 1) if "/" in rest else (rest, "dmdt")
    host = host_port.split(":")[0] if ":" in host_port else host_port
    port = int(host_port.split(":")[1]) if ":" in host_port else 5432
    return {"host": host, "port": port, "database": database, "user": user, "password": password}


def _load_from_env() -> DatabaseConfig:
    database_url = os.environ.get("DATABASE_URL", "")
    if database_url:
        parsed = _parse_database_url(database_url)
        return DatabaseConfig(
            host=str(parsed["host"]),
            port=int(parsed["port"]),
            database=str(parsed["database"]),
            user=str(parsed["user"]),
            password=str(parsed["password"]),
            echo=os.environ.get("DMDT_DB_ECHO", "0") == "1",
            pool_size=int(os.environ.get("DMDT_DB_POOL_SIZE", "5")),
            max_overflow=int(os.environ.get("DMDT_DB_MAX_OVERFLOW", "10")),
        )
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
