"""Repository functions for portfolio_snapshots (P&L chart data)."""

from __future__ import annotations

import datetime
import uuid

from .connection import connect
from .schema import DEFAULT_USER_ID


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def record_snapshot(total_value: float, user_id: str = DEFAULT_USER_ID) -> dict:
    """Append a portfolio value snapshot."""
    snap = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "total_value": total_value,
        "recorded_at": _now(),
    }
    with connect() as conn:
        conn.execute(
            "INSERT INTO portfolio_snapshots (id, user_id, total_value, recorded_at) "
            "VALUES (:id, :user_id, :total_value, :recorded_at)",
            snap,
        )
    return snap


def get_snapshots(user_id: str = DEFAULT_USER_ID, since: str | None = None) -> list[dict]:
    """Return snapshots for the user in chronological order, optionally filtered by ISO timestamp."""
    query = (
        "SELECT id, user_id, total_value, recorded_at FROM portfolio_snapshots WHERE user_id = ?"
    )
    params: tuple = (user_id,)
    if since is not None:
        query += " AND recorded_at >= ?"
        params = (user_id, since)
    query += " ORDER BY recorded_at ASC"
    with connect() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
