"""Tests for app/llm/prompts.py message assembly."""

from __future__ import annotations

from app.llm.prompts import HISTORY_LIMIT, build_messages

PORTFOLIO = {
    "cash_balance": 1000.0,
    "total_value": 2000.0,
    "positions": [
        {
            "ticker": "AAPL",
            "quantity": 5.0,
            "avg_cost": 150.0,
            "current_price": 160.0,
            "unrealized_pl": 50.0,
            "unrealized_pl_percent": 6.67,
        }
    ],
    "watchlist": [{"ticker": "AAPL", "price": 160.0}, {"ticker": "PYPL", "price": None}],
}


def test_system_messages_include_portfolio_data():
    messages = build_messages("hello", PORTFOLIO, [])
    assert messages[0]["role"] == "system"
    context_text = messages[1]["content"]
    assert "AAPL" in context_text
    assert "$1,000.00" in context_text  # cash
    assert "$2,000.00" in context_text  # total value
    assert "PYPL" in context_text
    assert "no live price" in context_text


def test_appends_user_message_when_not_in_history():
    messages = build_messages("what's my P&L?", PORTFOLIO, [])
    assert messages[-1] == {"role": "user", "content": "what's my P&L?"}


def test_does_not_duplicate_user_message_already_in_history():
    # Mirrors app/routes/chat.py: db.save_chat_message("user", ...) happens
    # before db.get_recent_chat_messages(), so history already ends with the
    # current turn.
    history = [
        {"role": "user", "content": "earlier question"},
        {"role": "assistant", "content": "earlier answer"},
        {"role": "user", "content": "current question"},
    ]
    messages = build_messages("current question", PORTFOLIO, history)
    user_message_count = sum(
        1 for m in messages if m["role"] == "user" and m["content"] == "current question"
    )
    assert user_message_count == 1
    assert messages[-1] == {"role": "user", "content": "current question"}


def test_history_is_trimmed_to_limit():
    history = [{"role": "user", "content": f"msg-{i}"} for i in range(HISTORY_LIMIT + 10)]
    messages = build_messages("new message", PORTFOLIO, history)
    # 2 system messages + trimmed history + the new user message
    assert len(messages) <= 2 + HISTORY_LIMIT + 1


def test_empty_positions_and_watchlist():
    empty_portfolio = {"cash_balance": 0.0, "total_value": 0.0, "positions": [], "watchlist": []}
    messages = build_messages("hi", empty_portfolio, [])
    context_text = messages[1]["content"]
    assert "Positions: none" in context_text
    assert "Watchlist: empty" in context_text
