"""Portfolio and trade execution routes."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app import db, services
from app.market import PriceCache


class TradeRequest(BaseModel):
    ticker: str
    quantity: float = Field(gt=0)
    side: Literal["buy", "sell"]


def create_portfolio_router(price_cache: PriceCache) -> APIRouter:
    """Factory so the router can read live prices without a global (mirrors app.market's pattern)."""
    router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])

    @router.get("")
    async def get_portfolio() -> dict:
        return services.get_portfolio_state(price_cache)

    @router.post("/trade")
    async def trade(body: TradeRequest) -> dict:
        try:
            return services.execute_trade(body.ticker, body.quantity, body.side, price_cache)
        except services.TradeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @router.get("/history")
    async def history() -> list[dict]:
        return db.get_snapshots()

    return router
