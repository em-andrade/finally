"""Lazy database initialization: creates the schema and seeds default data if needed."""

from __future__ import annotations

import datetime
import sqlite3
import uuid
from pathlib import Path

from .connection import connect
from .schema import DEFAULT_CASH_BALANCE, DEFAULT_USER_ID, DEFAULT_WATCHLIST_TICKERS, SCHEMA


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def init_db(db_path: Path | str | None = None) -> None:
    """Create tables if missing and seed default data if the profile doesn't exist yet.

    Idempotent and safe to call on every startup.
    """
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)
        row = conn.execute(
            "SELECT id FROM users_profile WHERE id = ?", (DEFAULT_USER_ID,)
        ).fetchone()
        if row is None:
            _seed(conn)


def _seed(conn: sqlite3.Connection) -> None:
    now = _now()
    conn.execute(
        "INSERT INTO users_profile (id, cash_balance, created_at) VALUES (?, ?, ?)",
        (DEFAULT_USER_ID, DEFAULT_CASH_BALANCE, now),
    )
    for ticker in DEFAULT_WATCHLIST_TICKERS:
        conn.execute(
            "INSERT INTO watchlist (id, user_id, ticker, added_at) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), DEFAULT_USER_ID, ticker, now),
        )
