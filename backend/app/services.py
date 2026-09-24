"""Business logic for trades and watchlist management.

Extracted from route handlers so the LLM chat flow can auto-execute the exact
same validated logic that the manual REST endpoints use, without going
through HTTP. Route handlers in app/routes/*.py and app/llm/* should call
these instead of touching app.db or app.state directly.
"""

from __future__ import annotations

from app import db
from app.market import MarketDataSource, PriceCache


class TradeError(Exception):
    """Raised when a trade fails validation (insufficient cash/shares, unknown ticker)."""


class WatchlistError(Exception):
    """Raised when a watchlist operation is invalid."""


def get_portfolio_state(price_cache: PriceCache) -> dict:
    """Assemble the current portfolio: cash, positions (with live P&L), total value."""
    profile = db.get_profile()
    cash_balance = profile["cash_balance"] if profile else 0.0

    positions = []
    positions_value = 0.0
    for pos in db.get_positions():
        ticker = pos["ticker"]
        current_price = price_cache.get_price(ticker) or pos["avg_cost"]
        quantity = pos["quantity"]
        market_value = quantity * current_price
        cost_basis = quantity * pos["avg_cost"]
        unrealized_pl = market_value - cost_basis
        pl_percent = (unrealized_pl / cost_basis * 100) if cost_basis else 0.0
        positions_value += market_value
        positions.append(
            {
                "ticker": ticker,
                "quantity": quantity,
                "avg_cost": pos["avg_cost"],
                "current_price": current_price,
                "market_value": market_value,
                "unrealized_pl": round(unrealized_pl, 2),
                "unrealized_pl_percent": round(pl_percent, 4),
            }
        )

    total_value = cash_balance + positions_value
    return {
        "cash_balance": cash_balance,
        "positions": positions,
        "total_value": round(total_value, 2),
    }


def compute_total_value(price_cache: PriceCache) -> float:
    """Cash + sum(position market values). Used by the periodic snapshot task."""
    profile = db.get_profile()
    cash_balance = profile["cash_balance"] if profile else 0.0
    positions_value = 0.0
    for pos in db.get_positions():
        current_price = price_cache.get_price(pos["ticker"]) or pos["avg_cost"]
        positions_value += pos["quantity"] * current_price
    return round(cash_balance + positions_value, 2)


def execute_trade(ticker: str, quantity: float, side: str, price_cache: PriceCache) -> dict:
    """Validate and execute a market order at the current cached price.

    Raises TradeError with a human-readable message on any validation failure
    (unknown ticker, insufficient cash, insufficient shares). On success,
    updates cash balance, upserts the position (weighted avg_cost on buys,
    unchanged avg_cost on sells), records the trade and a fresh portfolio
    snapshot, and returns the updated portfolio state (see get_portfolio_state).
    """
    ticker = ticker.upper().strip()
    if side not in ("buy", "sell"):
        raise TradeError(f"side must be 'buy' or 'sell', got {side!r}")
    if quantity <= 0:
        raise TradeError("quantity must be positive")

    price = price_cache.get_price(ticker)
    if price is None:
        raise TradeError(f"No live price available for {ticker!r}; is it on the watchlist?")

    if side == "buy":
        profile = db.get_profile()
        cash_balance = profile["cash_balance"] if profile else 0.0
        cost = quantity * price
        if cost > cash_balance:
            raise TradeError(
                f"Insufficient cash: need ${cost:,.2f} to buy {quantity} {ticker}, "
                f"have ${cash_balance:,.2f}"
            )
        existing = db.get_position(ticker)
        if existing:
            new_quantity = existing["quantity"] + quantity
            new_avg_cost = (
                existing["quantity"] * existing["avg_cost"] + quantity * price
            ) / new_quantity
        else:
            new_quantity = quantity
            new_avg_cost = price
        db.update_cash_balance(-cost)
        db.upsert_position(ticker, new_quantity, new_avg_cost)
    else:  # sell
        existing = db.get_position(ticker)
        held = existing["quantity"] if existing else 0.0
        if quantity > held:
            raise TradeError(
                f"Insufficient shares: trying to sell {quantity} {ticker}, only hold {held}"
            )
        proceeds = quantity * price
        new_quantity = held - quantity
        avg_cost = existing["avg_cost"] if existing else price
        db.update_cash_balance(proceeds)
        db.upsert_position(ticker, new_quantity, avg_cost)

    db.record_trade(ticker, side, quantity, price)
    state = get_portfolio_state(price_cache)
    db.record_snapshot(state["total_value"])
    return state


async def add_watchlist_ticker_live(ticker: str, market_source: MarketDataSource) -> dict:
    """Add a ticker to the DB watchlist and the running market data source."""
    ticker = ticker.upper().strip()
    row = db.add_watchlist_ticker(ticker)
    await market_source.add_ticker(ticker)
    return row


async def remove_watchlist_ticker_live(ticker: str, market_source: MarketDataSource) -> bool:
    """Remove a ticker from the DB watchlist and the running market data source."""
    ticker = ticker.upper().strip()
    removed = db.remove_watchlist_ticker(ticker)
    await market_source.remove_ticker(ticker)
    return removed
