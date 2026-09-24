"""Real LLM call: LiteLLM -> OpenRouter, Cerebras inference provider, structured outputs.

Uses the cerebras-inference skill's pattern: `openrouter/openai/gpt-oss-120b`
via litellm.completion(), forcing the Cerebras provider via extra_body, and
Structured Outputs (response_format=<pydantic model>) to get JSON matching
our schema directly.
"""

from __future__ import annotations

import logging
from typing import Any, Literal

from litellm import completion
from pydantic import BaseModel

from . import ChatResponse, TradeIntent, WatchlistIntent
from .prompts import build_messages

logger = logging.getLogger(__name__)

MODEL = "openrouter/openai/gpt-oss-120b"
EXTRA_BODY = {"provider": {"order": ["cerebras"]}}


class _TradeSchema(BaseModel):
    ticker: str
    side: Literal["buy", "sell"]
    quantity: float


class _WatchlistChangeSchema(BaseModel):
    ticker: str
    action: Literal["add", "remove"]


class _ChatResponseSchema(BaseModel):
    """The JSON schema the LLM is asked to produce (PLAN.md section 9)."""

    message: str
    trades: list[_TradeSchema] = []
    watchlist_changes: list[_WatchlistChangeSchema] = []


def call_llm(
    user_message: str,
    portfolio_context: dict[str, Any],
    history: list[dict[str, Any]],
) -> ChatResponse:
    """Call OpenRouter/Cerebras with structured outputs and return a ChatResponse.

    Never raises for LLM/network/parsing failures -- returns a ChatResponse
    with an apologetic message instead, so app/routes/chat.py never needs to
    handle anything beyond the NotImplementedError case it already catches.
    Only genuine programmer errors (e.g. a bad import) should escape this.
    """
    messages = build_messages(user_message, portfolio_context, history)

    try:
        response = completion(
            model=MODEL,
            messages=messages,
            response_format=_ChatResponseSchema,
            reasoning_effort="low",
            extra_body=EXTRA_BODY,
        )
        raw = response.choices[0].message.content
        parsed = _ChatResponseSchema.model_validate_json(raw)
    except Exception:
        logger.exception("LLM call failed or returned an unparseable response")
        return ChatResponse(
            message=(
                "Sorry, I ran into a problem processing that request. "
                "Please try again in a moment."
            )
        )

    return ChatResponse(
        message=parsed.message,
        trades=[TradeIntent(ticker=t.ticker, side=t.side, quantity=t.quantity) for t in parsed.trades]
        or None,
        watchlist_changes=[
            WatchlistIntent(ticker=w.ticker, action=w.action) for w in parsed.watchlist_changes
        ]
        or None,
    )
