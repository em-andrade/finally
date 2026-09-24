"""Repository functions for positions."""

from __future__ import annotations

import datetime
import uuid

from .connection import connect
from .schema import DEFAULT_USER_ID


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def get_positions(user_id: str = DEFAULT_USER_ID) -> list[dict]:
    """Return all positions for the user, ordered by ticker."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, user_id, ticker, quantity, avg_cost, updated_at FROM positions "
            "WHERE user_id = ? ORDER BY ticker",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_position(ticker: str, user_id: str = DEFAULT_USER_ID) -> dict | None:
    """Return a single position by ticker, or None if the user holds none."""
    ticker = ticker.upper().strip()
    with connect() as conn:
        row = conn.execute(
            "SELECT id, user_id, ticker, quantity, avg_cost, updated_at FROM positions "
            "WHERE user_id = ? AND ticker = ?",
            (user_id, ticker),
        ).fetchone()
        return dict(row) if row else None


def upsert_position(
    ticker: str, quantity: float, avg_cost: float, user_id: str = DEFAULT_USER_ID
) -> dict | None:
    """Set a position's quantity/avg_cost (creating it if needed).

    Callers compute the resulting quantity/avg_cost themselves (e.g. after a buy/sell
    fill) and pass the final values here. If quantity <= 0 the position row is deleted
    (fully closed out) and None is returned; otherwise the resulting row is returned.
    """
    ticker = ticker.upper().strip()
    now = _now()
    with connect() as conn:
        if quantity <= 0:
            conn.execute(
                "DELETE FROM positions WHERE user_id = ? AND ticker = ?", (user_id, ticker)
            )
            return None

        existing = conn.execute(
            "SELECT id FROM positions WHERE user_id = ? AND ticker = ?", (user_id, ticker)
        ).fetchone()
        if existing:
            pos_id = existing["id"]
            conn.execute(
                "UPDATE positions SET quantity = ?, avg_cost = ?, updated_at = ? WHERE id = ?",
                (quantity, avg_cost, now, pos_id),
            )
        else:
            pos_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO positions (id, user_id, ticker, quantity, avg_cost, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (pos_id, user_id, ticker, quantity, avg_cost, now),
            )
        row = conn.execute(
            "SELECT id, user_id, ticker, quantity, avg_cost, updated_at FROM positions "
            "WHERE id = ?",
            (pos_id,),
        ).fetchone()
        return dict(row)
