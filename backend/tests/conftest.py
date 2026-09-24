"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def event_loop_policy():
    """Use the default event loop policy for all async tests."""
    import asyncio

    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    """Point FINALLY_DB_PATH at a fresh temp file for this test.

    Duplicated from tests/db/conftest.py (which shadows this for tests under
    tests/db/) so tests/services and tests/api can use the same pattern
    without importing across sibling test packages.
    """
    path = tmp_path / "test.db"
    monkeypatch.setenv("FINALLY_DB_PATH", str(path))
    return path


@pytest.fixture
def initialized_db(db_path):
    """A db_path with schema created and default data seeded."""
    from app.db import init_db

    init_db()
    return db_path
