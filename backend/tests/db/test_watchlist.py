from __future__ import annotations

from app.db import add_watchlist_ticker, get_watchlist, remove_watchlist_ticker
from app.db.schema import DEFAULT_WATCHLIST_TICKERS


def test_get_watchlist_returns_seeded_tickers(initialized_db):
    tickers = {row["ticker"] for row in get_watchlist()}
    assert tickers == set(DEFAULT_WATCHLIST_TICKERS)


def test_add_watchlist_ticker(initialized_db):
    row = add_watchlist_ticker("PYPL")
    assert row["ticker"] == "PYPL"
    assert row["user_id"] == "default"
    assert "PYPL" in {r["ticker"] for r in get_watchlist()}


def test_add_watchlist_ticker_normalizes_case_and_whitespace(initialized_db):
    row = add_watchlist_ticker(" pypl ")
    assert row["ticker"] == "PYPL"


def test_add_watchlist_ticker_is_idempotent(initialized_db):
    add_watchlist_ticker("PYPL")
    add_watchlist_ticker("PYPL")
    tickers = [r["ticker"] for r in get_watchlist() if r["ticker"] == "PYPL"]
    assert len(tickers) == 1


def test_remove_watchlist_ticker(initialized_db):
    removed = remove_watchlist_ticker("AAPL")
    assert removed is True
    assert "AAPL" not in {r["ticker"] for r in get_watchlist()}


def test_remove_watchlist_ticker_not_present_returns_false(initialized_db):
    assert remove_watchlist_ticker("NOPE") is False


def test_watchlist_scoped_per_user(initialized_db):
    add_watchlist_ticker("PYPL", user_id="someone-else")
    assert "PYPL" not in {r["ticker"] for r in get_watchlist()}
    assert "PYPL" in {r["ticker"] for r in get_watchlist(user_id="someone-else")}
