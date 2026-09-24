from __future__ import annotations

from app.db import get_position, get_positions, upsert_position


def test_get_positions_empty_initially(initialized_db):
    assert get_positions() == []


def test_upsert_position_creates(initialized_db):
    row = upsert_position("AAPL", 10, 150.0)
    assert row["ticker"] == "AAPL"
    assert row["quantity"] == 10
    assert row["avg_cost"] == 150.0


def test_upsert_position_updates_existing(initialized_db):
    upsert_position("AAPL", 10, 150.0)
    row = upsert_position("AAPL", 20, 160.0)
    assert row["quantity"] == 20
    assert row["avg_cost"] == 160.0
    assert len(get_positions()) == 1


def test_upsert_position_zero_quantity_deletes(initialized_db):
    upsert_position("AAPL", 10, 150.0)
    result = upsert_position("AAPL", 0, 0)
    assert result is None
    assert get_position("AAPL") is None


def test_upsert_position_negative_quantity_deletes(initialized_db):
    upsert_position("AAPL", 10, 150.0)
    result = upsert_position("AAPL", -5, 150.0)
    assert result is None
    assert get_position("AAPL") is None


def test_get_position_normalizes_ticker(initialized_db):
    upsert_position("aapl", 10, 150.0)
    assert get_position("AAPL")["quantity"] == 10


def test_get_positions_ordered_by_ticker(initialized_db):
    upsert_position("TSLA", 1, 200.0)
    upsert_position("AAPL", 1, 150.0)
    upsert_position("MSFT", 1, 300.0)
    tickers = [r["ticker"] for r in get_positions()]
    assert tickers == sorted(tickers)


def test_positions_scoped_per_user(initialized_db):
    upsert_position("AAPL", 10, 150.0, user_id="someone-else")
    assert get_positions() == []
    assert len(get_positions(user_id="someone-else")) == 1
