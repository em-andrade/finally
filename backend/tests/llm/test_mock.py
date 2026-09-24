"""Tests for the deterministic LLM_MOCK=true rules (see app/llm/mock.py docstring)."""

from __future__ import annotations

from app.llm import TradeIntent
from app.llm.mock import mock_chat_response

PORTFOLIO = {
    "cash_balance": 5000.0,
    "total_value": 12345.67,
    "positions": [],
    "watchlist": [],
}


def test_buy_simple_form():
    resp = mock_chat_response("buy 10 AAPL", PORTFOLIO)
    assert resp.trades == [TradeIntent(ticker="AAPL", side="buy", quantity=10.0)]
    assert "AAPL" in resp.message
    assert resp.watchlist_changes is None


def test_buy_shares_of_form():
    resp = mock_chat_response("Buy 5 shares of TSLA", PORTFOLIO)
    assert resp.trades is not None
    trade = resp.trades[0]
    assert (trade.ticker, trade.side, trade.quantity) == ("TSLA", "buy", 5.0)


def test_sell_form():
    resp = mock_chat_response("sell 3.5 NVDA", PORTFOLIO)
    assert resp.trades is not None
    trade = resp.trades[0]
    assert (trade.ticker, trade.side, trade.quantity) == ("NVDA", "sell", 3.5)


def test_add_watchlist():
    resp = mock_chat_response("add PYPL", PORTFOLIO)
    assert resp.trades is None
    assert resp.watchlist_changes is not None
    change = resp.watchlist_changes[0]
    assert (change.ticker, change.action) == ("PYPL", "add")


def test_add_watchlist_verbose_form():
    resp = mock_chat_response("please add PYPL to the watchlist", PORTFOLIO)
    change = resp.watchlist_changes[0]
    assert (change.ticker, change.action) == ("PYPL", "add")


def test_remove_watchlist():
    resp = mock_chat_response("remove PYPL", PORTFOLIO)
    change = resp.watchlist_changes[0]
    assert (change.ticker, change.action) == ("PYPL", "remove")


def test_delete_watchlist_verbose_form():
    resp = mock_chat_response("delete PYPL from watchlist", PORTFOLIO)
    change = resp.watchlist_changes[0]
    assert (change.ticker, change.action) == ("PYPL", "remove")


def test_buy_takes_priority_over_add_keyword_collision():
    # "buy" is checked before "add"/"remove"; a message matching multiple
    # patterns resolves to the first rule in the documented order.
    resp = mock_chat_response("buy 1 AAPL and add it too", PORTFOLIO)
    assert resp.trades is not None
    assert resp.watchlist_changes is None


def test_default_analysis_message_uses_live_context():
    resp = mock_chat_response("how am I doing?", PORTFOLIO)
    assert resp.trades is None
    assert resp.watchlist_changes is None
    assert "12,345.67" in resp.message
    assert "5,000.00" in resp.message


def test_case_insensitive_and_ticker_uppercased():
    resp = mock_chat_response("BUY 2 aapl", PORTFOLIO)
    assert resp.trades[0].ticker == "AAPL"
