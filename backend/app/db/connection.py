"""SQLite connection management.

The database file lives at ``<project root>/db/finally.db`` by default (the
Docker volume mount point per planning/PLAN.md section 11). Set
``FINALLY_DB_PATH`` to point elsewhere (used by tests to isolate each run to
a temp file).
"""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

# backend/app/db/connection.py -> parents[3] == project root
_DEFAULT_DB_PATH = Path(__file__).resolve().parents[3] / "db" / "finally.db"


def get_db_path() -> Path:
    """Resolve the active database file path, honoring FINALLY_DB_PATH."""
    override = os.environ.get("FINALLY_DB_PATH", "").strip()
    if override:
        return Path(override)
    return _DEFAULT_DB_PATH


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    """Open a new connection, creating the parent directory if needed."""
    path = Path(db_path) if db_path is not None else get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def connect(db_path: Path | str | None = None) -> Iterator[sqlite3.Connection]:
    """Context manager yielding a connection; commits on success, rolls back on error."""
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
