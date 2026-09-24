"""Repository functions for watchlist."""

from __future__ import annotations

import datetime
import sqlite3
import uuid

from .connection import connect
from .schema import DEFAULT_USER_ID


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def get_watchlist(user_id: str = DEFAULT_USER_ID) -> list[dict]:
    """Return all watchlist entries for the user, oldest first."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, user_id, ticker, added_at FROM watchlist "
            "WHERE user_id = ? ORDER BY added_at",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def add_watchlist_ticker(ticker: str, user_id: str = DEFAULT_USER_ID) -> dict:
    """Add a ticker to the watchlist. Idempotent — returns the existing row if already present."""
    ticker = ticker.upper().strip()
    with connect() as conn:
        try:
            conn.execute(
                "INSERT INTO watchlist (id, user_id, ticker, added_at) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), user_id, ticker, _now()),
            )
        except sqlite3.IntegrityError:
            pass  # already on the watchlist
        row = conn.execute(
            "SELECT id, user_id, ticker, added_at FROM watchlist WHERE user_id = ? AND ticker = ?",
            (user_id, ticker),
        ).fetchone()
        return dict(row)


def remove_watchlist_ticker(ticker: str, user_id: str = DEFAULT_USER_ID) -> bool:
    """Remove a ticker from the watchlist. Returns True if a row was removed."""
    ticker = ticker.upper().strip()
    with connect() as conn:
        cur = conn.execute(
            "DELETE FROM watchlist WHERE user_id = ? AND ticker = ?", (user_id, ticker)
        )
        return cur.rowcount > 0
