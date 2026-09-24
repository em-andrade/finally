"""Unit tests for app.services.execute_trade and portfolio valuation."""

from __future__ import annotations

import pytest

from app import db
from app.market import PriceCache
from app.services import TradeError, execute_trade, get_portfolio_state


@pytest.fixture
def price_cache() -> PriceCache:
    cache = PriceCache()
    cache.update("AAPL", 100.0)
    cache.update("TSLA", 200.0)
    return cache


def test_buy_deducts_cash_and_creates_position(initialized_db, price_cache):
    profile_before = db.get_profile()
    state = execute_trade("AAPL", 10, "buy", price_cache)

    assert state["cash_balance"] == pytest.approx(profile_before["cash_balance"] - 1000.0)
    position = next(p for p in state["positions"] if p["ticker"] == "AAPL")
    assert position["quantity"] == 10
    assert position["avg_cost"] == pytest.approx(100.0)


def test_buy_insufficient_cash_raises(initialized_db, price_cache):
    with pytest.raises(TradeError, match="Insufficient cash"):
        execute_trade("AAPL", 1_000_000, "buy", price_cache)

    # Nothing should have changed.
    assert db.get_position("AAPL") is None


def test_sell_insufficient_shares_raises(initialized_db, price_cache):
    with pytest.raises(TradeError, match="Insufficient shares"):
        execute_trade("AAPL", 5, "sell", price_cache)


def test_buy_recomputes_weighted_avg_cost(initialized_db, price_cache):
    execute_trade("AAPL", 10, "buy", price_cache)  # 10 @ 100 -> avg 100
    price_cache.update("AAPL", 200.0)
    execute_trade("AAPL", 10, "buy", price_cache)  # +10 @ 200 -> avg (1000+2000)/20 = 150

    position = db.get_position("AAPL")
    assert position["quantity"] == 20
    assert position["avg_cost"] == pytest.approx(150.0)


def test_sell_does_not_change_avg_cost(initialized_db, price_cache):
    execute_trade("AAPL", 10, "buy", price_cache)
    price_cache.update("AAPL", 50.0)
    state = execute_trade("AAPL", 4, "sell", price_cache)

    position = next(p for p in state["positions"] if p["ticker"] == "AAPL")
    assert position["quantity"] == 6
    assert position["avg_cost"] == pytest.approx(100.0)  # unchanged despite lower sell price


def test_sell_at_a_loss_reports_negative_pl(initialized_db, price_cache):
    execute_trade("AAPL", 10, "buy", price_cache)  # avg_cost 100
    price_cache.update("AAPL", 60.0)  # price drops
    state = get_portfolio_state(price_cache)

    position = next(p for p in state["positions"] if p["ticker"] == "AAPL")
    assert position["unrealized_pl"] == pytest.approx((60.0 - 100.0) * 10)
    assert position["unrealized_pl_percent"] < 0


def test_full_sell_removes_position(initialized_db, price_cache):
    execute_trade("AAPL", 10, "buy", price_cache)
    execute_trade("AAPL", 10, "sell", price_cache)

    assert db.get_position("AAPL") is None


def test_unknown_ticker_raises(initialized_db, price_cache):
    with pytest.raises(TradeError, match="No live price"):
        execute_trade("ZZZZ", 1, "buy", price_cache)


def test_trade_records_history_and_snapshot(initialized_db, price_cache):
    execute_trade("AAPL", 10, "buy", price_cache)

    trades = db.get_trades()
    assert len(trades) == 1
    assert trades[0]["ticker"] == "AAPL"
    assert trades[0]["side"] == "buy"

    snapshots = db.get_snapshots()
    assert len(snapshots) == 1


def test_invalid_side_raises(initialized_db, price_cache):
    with pytest.raises(TradeError):
        execute_trade("AAPL", 1, "hold", price_cache)  # type: ignore[arg-type]


def test_zero_or_negative_quantity_raises(initialized_db, price_cache):
    with pytest.raises(TradeError):
        execute_trade("AAPL", 0, "buy", price_cache)
    with pytest.raises(TradeError):
        execute_trade("AAPL", -5, "buy", price_cache)


def test_get_portfolio_state_total_value(initialized_db, price_cache):
    profile = db.get_profile()
    state = get_portfolio_state(price_cache)

    assert state["total_value"] == pytest.approx(profile["cash_balance"])
    assert state["positions"] == []
