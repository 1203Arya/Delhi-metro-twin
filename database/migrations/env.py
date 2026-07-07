from __future__ import annotations

import sys
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dmdt_db.base import Base
from dmdt_db.config import db_config
from dmdt_db.models import (  # noqa: F401
    Crossover,
    Depot,
    Junction,
    Line,
    Platform,
    Siding,
    Station,
    Switch,
    TrackSegment,
    TrainClass,
)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = db_config.url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    cfg = context.config
    cfg.set_main_option("sqlalchemy.url", db_config.url_psycopg2)
    connectable = engine_from_config(
        cfg.get_section(cfg.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
