"""Repository functions for chat_messages."""

from __future__ import annotations

import datetime
import json
import uuid
from typing import Any

from .connection import connect
from .schema import DEFAULT_USER_ID


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save_chat_message(
    role: str,
    content: str,
    actions: dict[str, Any] | list[Any] | None = None,
    user_id: str = DEFAULT_USER_ID,
) -> dict:
    """Persist a chat message. `actions` (trades/watchlist changes executed) is JSON-encoded."""
    if role not in ("user", "assistant"):
        raise ValueError(f"role must be 'user' or 'assistant', got {role!r}")
    row = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "role": role,
        "content": content,
        "actions": json.dumps(actions) if actions is not None else None,
        "created_at": _now(),
    }
    with connect() as conn:
        conn.execute(
            "INSERT INTO chat_messages (id, user_id, role, content, actions, created_at) "
            "VALUES (:id, :user_id, :role, :content, :actions, :created_at)",
            row,
        )
    return {**row, "actions": actions}


def get_recent_chat_messages(limit: int = 20, user_id: str = DEFAULT_USER_ID) -> list[dict]:
    """Return the most recent `limit` messages, oldest first (ready to feed an LLM prompt)."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, user_id, role, content, actions, created_at FROM chat_messages "
            "WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    messages = [dict(r) for r in rows]
    for m in messages:
        m["actions"] = json.loads(m["actions"]) if m["actions"] else None
    messages.reverse()
    return messages
