from __future__ import annotations

import pytest

from app.db import get_recent_chat_messages, save_chat_message


def test_save_chat_message_user(initialized_db):
    msg = save_chat_message("user", "What's my portfolio worth?")
    assert msg["role"] == "user"
    assert msg["content"] == "What's my portfolio worth?"
    assert msg["actions"] is None


def test_save_chat_message_assistant_with_actions(initialized_db):
    actions = {"trades": [{"ticker": "AAPL", "side": "buy", "quantity": 10}]}
    msg = save_chat_message("assistant", "Bought 10 AAPL.", actions=actions)
    assert msg["actions"] == actions


def test_save_chat_message_rejects_invalid_role(initialized_db):
    with pytest.raises(ValueError):
        save_chat_message("system", "nope")


def test_get_recent_chat_messages_oldest_first(initialized_db):
    save_chat_message("user", "first")
    save_chat_message("assistant", "second")
    save_chat_message("user", "third")
    messages = get_recent_chat_messages()
    assert [m["content"] for m in messages] == ["first", "second", "third"]


def test_get_recent_chat_messages_respects_limit(initialized_db):
    for i in range(10):
        save_chat_message("user", f"message {i}")
    messages = get_recent_chat_messages(limit=3)
    assert len(messages) == 3
    assert [m["content"] for m in messages] == ["message 7", "message 8", "message 9"]


def test_get_recent_chat_messages_roundtrips_actions_json(initialized_db):
    actions = {"watchlist_changes": [{"ticker": "PYPL", "action": "add"}]}
    save_chat_message("assistant", "Added PYPL.", actions=actions)
    messages = get_recent_chat_messages()
    assert messages[-1]["actions"] == actions


def test_chat_messages_scoped_per_user(initialized_db):
    save_chat_message("user", "hello", user_id="someone-else")
    assert get_recent_chat_messages() == []
    assert len(get_recent_chat_messages(user_id="someone-else")) == 1
