"""LLM chat integration seam.

The Backend Engineer built the /api/chat route and its plumbing (persistence,
portfolio context, auto-execution of returned trades/watchlist changes). The
LLM Engineer implements get_chat_response() below: call LiteLLM -> OpenRouter
(Cerebras inference provider, model "openrouter/openai/gpt-oss-120b") using
the cerebras-inference skill, with Structured Outputs matching ChatResponse.

Contract (see planning/PLAN.md section 9 for the authoritative schema):

    get_chat_response(user_message, portfolio_context, history) -> ChatResponse

    - user_message: str, the new message from the user.
    - portfolio_context: dict, shaped like services.get_portfolio_state() plus
      "watchlist" (list of {ticker, price}) -- everything the system prompt
      needs to reason about the user's holdings.
    - history: list[dict], each {"role": "user"|"assistant", "content": str},
      oldest first (this is exactly what db.get_recent_chat_messages returns,
      minus the "actions" field).

    Returns a ChatResponse:
        message: str                                   (required, conversational reply)
        trades: list[TradeIntent] | None                (optional)
            TradeIntent: {"ticker": str, "side": "buy"|"sell", "quantity": float}
        watchlist_changes: list[WatchlistIntent] | None (optional)
            WatchlistIntent: {"ticker": str, "action": "add"|"remove"}

The chat route (app/routes/chat.py) calls this, then for each returned trade
calls app.services.execute_trade(...) and for each watchlist change calls
app.services.add_watchlist_ticker_live/remove_watchlist_ticker_live(...),
catching TradeError/WatchlistError per-item so one bad instruction doesn't
kill the whole response -- the resulting per-item success/error is what gets
persisted as chat_messages.actions and returned to the frontend.

When LLM_MOCK=true, this should return deterministic responses instead of
calling OpenRouter (see PLAN.md section 9, "LLM Mock Mode") -- needed for
fast, free, reproducible E2E tests.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv

# app/llm/__init__.py -> parents[3] == project root (where .env lives). Loaded
# eagerly at import time so `OPENROUTER_API_KEY` is available for local `uv
# run` usage; in Docker the container already gets .env via --env-file, and
# load_dotenv() is a harmless no-op there (override=False, file may not exist).
load_dotenv(Path(__file__).resolve().parents[3] / ".env")


@dataclass(frozen=True, slots=True)
class TradeIntent:
    ticker: str
    side: Literal["buy", "sell"]
    quantity: float


@dataclass(frozen=True, slots=True)
class WatchlistIntent:
    ticker: str
    action: Literal["add", "remove"]


@dataclass(frozen=True, slots=True)
class ChatResponse:
    message: str
    trades: list[TradeIntent] | None = None
    watchlist_changes: list[WatchlistIntent] | None = None


def _llm_mock_enabled() -> bool:
    return os.environ.get("LLM_MOCK", "").strip().lower() in ("true", "1", "yes")


def get_chat_response(
    user_message: str,
    portfolio_context: dict[str, Any],
    history: list[dict[str, Any]],
) -> ChatResponse:
    """Return a structured ChatResponse for the user's message.

    Dispatches to the deterministic mock (see app.llm.mock) when LLM_MOCK is
    truthy, otherwise calls OpenRouter/Cerebras (see app.llm.client). Imports
    are local to keep `litellm` off the import path entirely in mock mode
    (relevant for fast, dependency-light E2E test runs).
    """
    if _llm_mock_enabled():
        from .mock import mock_chat_response

        return mock_chat_response(user_message, portfolio_context)

    from .client import call_llm

    return call_llm(user_message, portfolio_context, history)
