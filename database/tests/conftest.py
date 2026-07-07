from __future__ import annotations

import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "gis"))

from dmdt_db import Base
from dmdt_db.config import db_config


@pytest.fixture(scope="session")
def engine():
    e = create_engine(db_config.url_psycopg2, echo=False)
    Base.metadata.drop_all(e)
    Base.metadata.create_all(e)
    yield e
    Base.metadata.drop_all(e)


@pytest.fixture(autouse=True)
def transaction(engine):
    """Run each test in a transaction that gets rolled back."""
    conn = engine.connect()
    trans = conn.begin()
    session = Session(bind=conn)
    yield session
    session.close()
    trans.rollback()
    conn.close()
