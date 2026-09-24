"""Repository functions for the trades append-only log."""

from __future__ import annotations

import datetime
import uuid

from .connection import connect
from .schema import DEFAULT_USER_ID


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def record_trade(
    ticker: str, side: str, quantity: float, price: float, user_id: str = DEFAULT_USER_ID
) -> dict:
    """Append a trade to the log. Does not touch cash/positions — callers apply those effects."""
    if side not in ("buy", "sell"):
        raise ValueError(f"side must be 'buy' or 'sell', got {side!r}")
    trade = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "ticker": ticker.upper().strip(),
        "side": side,
        "quantity": quantity,
        "price": price,
        "executed_at": _now(),
    }
    with connect() as conn:
        conn.execute(
            "INSERT INTO trades (id, user_id, ticker, side, quantity, price, executed_at) "
            "VALUES (:id, :user_id, :ticker, :side, :quantity, :price, :executed_at)",
            trade,
        )
    return trade


def get_trades(user_id: str = DEFAULT_USER_ID, limit: int | None = None) -> list[dict]:
    """Return trades for the user, most recent first."""
    query = (
        "SELECT id, user_id, ticker, side, quantity, price, executed_at FROM trades "
        "WHERE user_id = ? ORDER BY executed_at DESC"
    )
    params: tuple = (user_id,)
    if limit is not None:
        query += " LIMIT ?"
        params = (user_id, limit)
    with connect() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
