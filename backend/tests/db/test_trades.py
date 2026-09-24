from __future__ import annotations

import pytest

from app.db import get_trades, record_trade


def test_record_trade_returns_row(initialized_db):
    trade = record_trade("AAPL", "buy", 10, 150.0)
    assert trade["ticker"] == "AAPL"
    assert trade["side"] == "buy"
    assert trade["quantity"] == 10
    assert trade["price"] == 150.0
    assert trade["id"]
    assert trade["executed_at"]


def test_record_trade_rejects_invalid_side(initialized_db):
    with pytest.raises(ValueError):
        record_trade("AAPL", "hold", 10, 150.0)


def test_get_trades_is_append_only_log(initialized_db):
    record_trade("AAPL", "buy", 10, 150.0)
    record_trade("AAPL", "sell", 5, 155.0)
    trades = get_trades()
    assert len(trades) == 2


def test_get_trades_most_recent_first(initialized_db):
    first = record_trade("AAPL", "buy", 10, 150.0)
    second = record_trade("MSFT", "buy", 5, 300.0)
    trades = get_trades()
    assert trades[0]["id"] == second["id"]
    assert trades[1]["id"] == first["id"]


def test_get_trades_respects_limit(initialized_db):
    for _ in range(5):
        record_trade("AAPL", "buy", 1, 150.0)
    assert len(get_trades(limit=2)) == 2


def test_trades_scoped_per_user(initialized_db):
    record_trade("AAPL", "buy", 10, 150.0, user_id="someone-else")
    assert get_trades() == []
    assert len(get_trades(user_id="someone-else")) == 1
