"""Deterministic mock chat responses, used when LLM_MOCK=true (no network call).

This is the contract the Integration Tester's Playwright E2E suite asserts
against, so the rules below are intentionally simple, regex-based, and fixed
-- not real NLU. Do not change matching behavior without updating E2E tests.

Rules (checked in this order; first match wins; matching is case-insensitive):

1. BUY:  r"\\bbuy\\s+(\\d+(?:\\.\\d+)?)\\s+(?:shares?\\s+of\\s+)?([A-Za-z]{1,5})\\b"
         e.g. "buy 10 AAPL" or "Buy 5 shares of TSLA"
         -> trades=[{"ticker": <TICKER>, "side": "buy", "quantity": <qty>}]
         -> message = "Buying {qty:g} shares of {TICKER}."

2. SELL: r"\\bsell\\s+(\\d+(?:\\.\\d+)?)\\s+(?:shares?\\s+of\\s+)?([A-Za-z]{1,5})\\b"
         e.g. "sell 3 NVDA"
         -> trades=[{"ticker": <TICKER>, "side": "sell", "quantity": <qty>}]
         -> message = "Selling {qty:g} shares of {TICKER}."

3. ADD:  r"\\badd\\s+([A-Za-z]{1,5})\\b(?:\\s+to\\s+(?:the\\s+)?watchlist)?"
         e.g. "add PYPL" or "add PYPL to the watchlist"
         -> watchlist_changes=[{"ticker": <TICKER>, "action": "add"}]
         -> message = "Adding {TICKER} to your watchlist."

4. REMOVE/DELETE: r"\\b(?:remove|delete)\\s+([A-Za-z]{1,5})\\b(?:\\s+from\\s+(?:the\\s+)?watchlist)?"
         e.g. "remove PYPL" or "delete PYPL from watchlist"
         -> watchlist_changes=[{"ticker": <TICKER>, "action": "remove"}]
         -> message = "Removing {TICKER} from your watchlist."

5. DEFAULT (no match): a canned analysis message referencing the live
   portfolio context's total value and cash balance:
         message = "Your portfolio is currently worth ${total_value:,.2f}, "
                    "including ${cash_balance:,.2f} in cash. Ask me to buy, "
                    "sell, or manage your watchlist and I'll take care of it."
   -> no trades, no watchlist_changes.
"""

from __future__ import annotations

import re
from typing import Any

from . import ChatResponse, TradeIntent, WatchlistIntent

_BUY_RE = re.compile(r"\bbuy\s+(\d+(?:\.\d+)?)\s+(?:shares?\s+of\s+)?([A-Za-z]{1,5})\b", re.IGNORECASE)
_SELL_RE = re.compile(r"\bsell\s+(\d+(?:\.\d+)?)\s+(?:shares?\s+of\s+)?([A-Za-z]{1,5})\b", re.IGNORECASE)
_ADD_RE = re.compile(r"\badd\s+([A-Za-z]{1,5})\b", re.IGNORECASE)
_REMOVE_RE = re.compile(r"\b(?:remove|delete)\s+([A-Za-z]{1,5})\b", re.IGNORECASE)


def mock_chat_response(user_message: str, portfolio_context: dict[str, Any]) -> ChatResponse:
    """Rule-based, deterministic stand-in for the real LLM call. See module docstring."""
    if match := _BUY_RE.search(user_message):
        quantity, ticker = float(match.group(1)), match.group(2).upper()
        return ChatResponse(
            message=f"Buying {quantity:g} shares of {ticker}.",
            trades=[TradeIntent(ticker=ticker, side="buy", quantity=quantity)],
        )

    if match := _SELL_RE.search(user_message):
        quantity, ticker = float(match.group(1)), match.group(2).upper()
        return ChatResponse(
            message=f"Selling {quantity:g} shares of {ticker}.",
            trades=[TradeIntent(ticker=ticker, side="sell", quantity=quantity)],
        )

    if match := _ADD_RE.search(user_message):
        ticker = match.group(1).upper()
        return ChatResponse(
            message=f"Adding {ticker} to your watchlist.",
            watchlist_changes=[WatchlistIntent(ticker=ticker, action="add")],
        )

    if match := _REMOVE_RE.search(user_message):
        ticker = match.group(1).upper()
        return ChatResponse(
            message=f"Removing {ticker} from your watchlist.",
            watchlist_changes=[WatchlistIntent(ticker=ticker, action="remove")],
        )

    total_value = portfolio_context.get("total_value", 0.0)
    cash_balance = portfolio_context.get("cash_balance", 0.0)
    return ChatResponse(
        message=(
            f"Your portfolio is currently worth ${total_value:,.2f}, including "
            f"${cash_balance:,.2f} in cash. Ask me to buy, sell, or manage your "
            "watchlist and I'll take care of it."
        )
    )
