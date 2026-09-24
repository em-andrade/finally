"""Fixtures giving each test an isolated, initialized SQLite database."""

from __future__ import annotations

import pytest


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    """Point FINALLY_DB_PATH at a fresh temp file for this test."""
    path = tmp_path / "test.db"
    monkeypatch.setenv("FINALLY_DB_PATH", str(path))
    return path


@pytest.fixture
def initialized_db(db_path):
    """A db_path with schema created and default data seeded."""
    from app.db import init_db

    init_db()
    return db_path
