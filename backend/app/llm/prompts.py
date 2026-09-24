"""Builds the message list sent to the LLM from portfolio context + history."""

from __future__ import annotations

from typing import Any

SYSTEM_PROMPT = """You are FinAlly, an AI trading assistant embedded in a simulated \
trading terminal. You help the user understand and manage their portfolio.

Responsibilities:
- Analyze portfolio composition, risk concentration, and P&L when relevant.
- Suggest trades with clear reasoning grounded in the data you're given.
- When the user asks you to execute a trade, or clearly agrees to one you \
suggested, include it in `trades` so it auto-executes immediately (market \
order, instant fill, no confirmation step -- this is a simulated account).
- Manage the watchlist proactively: add tickers the user asks about or shows \
interest in, remove ones they're done with, via `watchlist_changes`.
- Be concise and data-driven. Reference actual numbers from the context below.
- Always respond with the structured JSON schema you've been given -- never \
prose outside that schema.

Quantities in `trades` are always positive numbers of shares. Tickers are \
upper-case symbols. Only propose trades for tickers with a known current \
price (see the watchlist/positions data below) -- if you don't have a live \
price for a ticker, say so in `message` instead of guessing.
"""

HISTORY_LIMIT = 20


def _format_portfolio_context(portfolio_context: dict[str, Any]) -> str:
    cash = portfolio_context.get("cash_balance", 0.0)
    total_value = portfolio_context.get("total_value", 0.0)
    positions = portfolio_context.get("positions") or []
    watchlist = portfolio_context.get("watchlist") or []

    lines = [
        "Current portfolio state:",
        f"- Cash balance: ${cash:,.2f}",
        f"- Total portfolio value: ${total_value:,.2f}",
    ]

    if positions:
        lines.append("- Positions:")
        for pos in positions:
            lines.append(
                "  - {ticker}: {qty:g} shares @ avg cost ${avg_cost:,.2f}, "
                "current price ${price:,.2f}, unrealized P&L ${pl:,.2f} ({pl_pct:.2f}%)".format(
                    ticker=pos.get("ticker"),
                    qty=pos.get("quantity", 0.0),
                    avg_cost=pos.get("avg_cost", 0.0),
                    price=pos.get("current_price", 0.0),
                    pl=pos.get("unrealized_pl", 0.0),
                    pl_pct=pos.get("unrealized_pl_percent", 0.0),
                )
            )
    else:
        lines.append("- Positions: none")

    if watchlist:
        watch_str = ", ".join(
            f"{w.get('ticker')} (${w['price']:,.2f})" if w.get("price") is not None
            else f"{w.get('ticker')} (no live price)"
            for w in watchlist
        )
        lines.append(f"- Watchlist: {watch_str}")
    else:
        lines.append("- Watchlist: empty")

    return "\n".join(lines)


def build_messages(
    user_message: str,
    portfolio_context: dict[str, Any],
    history: list[dict[str, Any]],
) -> list[dict[str, str]]:
    """Assemble the full chat-completion message list: system + context + history + new turn.

    `history` (as produced by app.db.get_recent_chat_messages, called *after* the
    current user message was already saved by the route) typically already ends
    with the current turn's user message. We detect that and avoid duplicating
    it; if `history` doesn't include it (e.g. a caller passing history that
    predates the current turn, as some unit tests do), we append it ourselves.
    """
    trimmed = list(history[-HISTORY_LIMIT:])

    already_included = bool(trimmed) and (
        trimmed[-1].get("role") == "user" and trimmed[-1].get("content") == user_message
    )

    messages: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": _format_portfolio_context(portfolio_context)},
    ]
    messages.extend({"role": m["role"], "content": m["content"]} for m in trimmed)
    if not already_included:
        messages.append({"role": "user", "content": user_message})

    return messages
