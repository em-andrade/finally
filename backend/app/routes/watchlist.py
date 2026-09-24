"""Watchlist management routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import db, services
from app.market import MarketDataSource, PriceCache


class WatchlistAddRequest(BaseModel):
    ticker: str


def create_watchlist_router(price_cache: PriceCache, market_source: MarketDataSource) -> APIRouter:
    router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])

    @router.get("")
    async def get_watchlist() -> list[dict]:
        entries = db.get_watchlist()
        result = []
        for entry in entries:
            ticker = entry["ticker"]
            update = price_cache.get(ticker)
            result.append(
                {
                    "ticker": ticker,
                    "added_at": entry["added_at"],
                    "price": update.price if update else None,
                    "previous_price": update.previous_price if update else None,
                    "change": update.change if update else None,
                    "change_percent": update.change_percent if update else None,
                    "direction": update.direction if update else "flat",
                }
            )
        return result

    @router.post("")
    async def add_ticker(body: WatchlistAddRequest) -> dict:
        return await services.add_watchlist_ticker_live(body.ticker, market_source)

    @router.delete("/{ticker}")
    async def remove_ticker(ticker: str) -> dict:
        removed = await services.remove_watchlist_ticker_live(ticker, market_source)
        if not removed:
            raise HTTPException(status_code=404, detail=f"{ticker!r} not on watchlist")
        return {"removed": True, "ticker": ticker.upper().strip()}

    return router
