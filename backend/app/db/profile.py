"""Repository functions for users_profile."""

from __future__ import annotations

from .connection import connect
from .schema import DEFAULT_USER_ID


def get_profile(user_id: str = DEFAULT_USER_ID) -> dict | None:
    """Return the user's profile (id, cash_balance, created_at), or None if not found."""
    with connect() as conn:
        row = conn.execute(
            "SELECT id, cash_balance, created_at FROM users_profile WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None


def update_cash_balance(delta: float, user_id: str = DEFAULT_USER_ID) -> float:
    """Apply delta (positive or negative) to the cash balance. Returns the new balance."""
    with connect() as conn:
        conn.execute(
            "UPDATE users_profile SET cash_balance = cash_balance + ? WHERE id = ?",
            (delta, user_id),
        )
        row = conn.execute(
            "SELECT cash_balance FROM users_profile WHERE id = ?", (user_id,)
        ).fetchone()
        return row["cash_balance"]
