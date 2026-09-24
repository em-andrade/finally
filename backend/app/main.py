"""FinAlly FastAPI application entrypoint.

Run locally with: uv run uvicorn app.main:app --reload
Docker runs this as: uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import db, services
from app.market import PriceCache, create_market_data_source, create_stream_router
from app.routes.chat import create_chat_router
from app.routes.health import router as health_router
from app.routes.portfolio import create_portfolio_router
from app.routes.watchlist import create_watchlist_router

logger = logging.getLogger(__name__)

SNAPSHOT_INTERVAL_SECONDS = 30
# app/main.py -> parents[1] == backend/ (where the Docker build places the frontend export)
STATIC_DIR = Path(__file__).resolve().parents[1] / "static"


async def _snapshot_loop(price_cache: PriceCache) -> None:
    """Record a portfolio value snapshot every 30 seconds, forever."""
    while True:
        await asyncio.sleep(SNAPSHOT_INTERVAL_SECONDS)
        try:
            total_value = services.compute_total_value(price_cache)
            db.record_snapshot(total_value)
        except Exception:
            logger.exception("Periodic snapshot failed")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    db.init_db()

    price_cache: PriceCache = app.state.price_cache
    market_source = app.state.market_source
    tickers = [entry["ticker"] for entry in db.get_watchlist()]
    await market_source.start(tickers)

    snapshot_task = asyncio.create_task(_snapshot_loop(price_cache), name="snapshot-loop")

    try:
        yield
    finally:
        snapshot_task.cancel()
        try:
            await snapshot_task
        except asyncio.CancelledError:
            pass
        await market_source.stop()


def create_app() -> FastAPI:
    """Build the FastAPI app with all routers registered up front.

    The PriceCache and market data source are created here (synchronously) so
    routers -- built via factories that close over them, per app.market's
    pattern -- can be included immediately. `lifespan` only starts/stops the
    background market data task and the periodic snapshot task; it doesn't
    register routes, so the app's route table is deterministic regardless of
    whether lifespan has run yet (important for TestClient / import-time use).
    """
    app = FastAPI(title="FinAlly", lifespan=lifespan)

    price_cache = PriceCache()
    market_source = create_market_data_source(price_cache)
    app.state.price_cache = price_cache
    app.state.market_source = market_source

    app.include_router(health_router)
    app.include_router(create_stream_router(price_cache))
    app.include_router(create_portfolio_router(price_cache))
    app.include_router(create_watchlist_router(price_cache, market_source))
    app.include_router(create_chat_router(price_cache, market_source))

    if STATIC_DIR.is_dir():
        app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
    else:
        logger.info("No static/ directory found at %s; frontend not served (local dev)", STATIC_DIR)

    return app


app = create_app()
