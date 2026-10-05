"""Shared pytest fixtures.

The database backend is chosen by environment variable:

- `TEST_DATABASE_URL` set  -> use that real database (CI proves row-locking)
- unset                    -> fall back to in-memory SQLite (fast local runs)

SQLite ignores `SELECT ... FOR UPDATE`, so SQLite alone cannot prove
concurrency safety. That is why CI runs this suite against PostgreSQL.
See ADR-007.
"""

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.base import Base


def _build_engine():
    url = os.environ.get("TEST_DATABASE_URL")

    if not url:
        # Fast, isolated, zero-infrastructure default for local development.
        return create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )

    # Real database: needed to prove locking and transaction behaviour.
    return create_engine(url, pool_pre_ping=True)


@pytest.fixture
def db_session():
    """A clean schema on every test, rolled back afterwards."""
    engine = _build_engine()
    Base.metadata.create_all(engine)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session: Session = TestingSessionLocal()

    yield session

    session.close()
    # SQLite in-memory dies with the engine. A real Postgres DB keeps its
    # tables, so drop them or the next test run collides on existing rows.
    if os.environ.get("TEST_DATABASE_URL"):
        Base.metadata.drop_all(engine)
    engine.dispose()
