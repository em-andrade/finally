"""AI chat route: persists conversation, calls the LLM seam, auto-executes actions."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app import db, llm, services
from app.market import MarketDataSource, PriceCache


class ChatRequest(BaseModel):
    message: str


class ExecutedTrade(BaseModel):
    ticker: str
    side: Literal["buy", "sell"]
    quantity: float
    price: float | None = None
    status: Literal["executed", "failed"]
    error: str | None = None


class ExecutedWatchlistChange(BaseModel):
    ticker: str
    action: Literal["add", "remove"]
    status: Literal["executed", "failed"]
    error: str | None = None


class ChatApiResponse(BaseModel):
    message: str
    trades: list[ExecutedTrade] = []
    watchlist_changes: list[ExecutedWatchlistChange] = []


def _build_portfolio_context(price_cache: PriceCache) -> dict:
    state = services.get_portfolio_state(price_cache)
    watchlist = db.get_watchlist()
    state["watchlist"] = [
        {"ticker": w["ticker"], "price": price_cache.get_price(w["ticker"])} for w in watchlist
    ]
    return state


def create_chat_router(price_cache: PriceCache, market_source: MarketDataSource) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["chat"])

    @router.post("/chat")
    async def chat(body: ChatRequest) -> ChatApiResponse:
        db.save_chat_message("user", body.message)

        history = [
            {"role": m["role"], "content": m["content"]} for m in db.get_recent_chat_messages()
        ]
        portfolio_context = _build_portfolio_context(price_cache)

        try:
            response = llm.get_chat_response(body.message, portfolio_context, history)
        except NotImplementedError:
            reply = ChatApiResponse(message="LLM integration pending.")
            db.save_chat_message("assistant", reply.message, actions=None)
            return reply

        executed_trades: list[ExecutedTrade] = []
        for intent in response.trades or []:
            try:
                services.execute_trade(intent.ticker, intent.quantity, intent.side, price_cache)
                fill_price = price_cache.get_price(intent.ticker.upper().strip())
                executed_trades.append(
                    ExecutedTrade(
                        ticker=intent.ticker,
                        side=intent.side,
                        quantity=intent.quantity,
                        price=fill_price,
                        status="executed",
                    )
                )
            except services.TradeError as exc:
                executed_trades.append(
                    ExecutedTrade(
                        ticker=intent.ticker,
                        side=intent.side,
                        quantity=intent.quantity,
                        status="failed",
                        error=str(exc),
                    )
                )

        executed_watchlist: list[ExecutedWatchlistChange] = []
        for change in response.watchlist_changes or []:
            try:
                if change.action == "add":
                    await services.add_watchlist_ticker_live(change.ticker, market_source)
                else:
                    await services.remove_watchlist_ticker_live(change.ticker, market_source)
                executed_watchlist.append(
                    ExecutedWatchlistChange(
                        ticker=change.ticker, action=change.action, status="executed"
                    )
                )
            except services.WatchlistError as exc:
                executed_watchlist.append(
                    ExecutedWatchlistChange(
                        ticker=change.ticker,
                        action=change.action,
                        status="failed",
                        error=str(exc),
                    )
                )

        reply = ChatApiResponse(
            message=response.message, trades=executed_trades, watchlist_changes=executed_watchlist
        )
        actions = {
            "trades": [t.model_dump() for t in executed_trades],
            "watchlist_changes": [w.model_dump() for w in executed_watchlist],
        }
        db.save_chat_message("assistant", reply.message, actions=actions)
        return reply

    return router
