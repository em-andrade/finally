# Backend — Developer Guide

## Project Setup

```bash
cd backend
uv sync --extra dev   # Install all dependencies including test/lint tools
```

## Market Data API

The market data subsystem lives in `app/market/`. Use these imports:

```python
from app.market import PriceCache, PriceUpdate, MarketDataSource, create_market_data_source
```

### Core Types

- **`PriceUpdate`** — Immutable dataclass: `ticker`, `price`, `previous_price`, `timestamp`, plus properties `change`, `change_percent`, `direction` ("up"/"down"/"flat"), and `to_dict()` for JSON serialization.

- **`PriceCache`** — Thread-safe in-memory store. Key methods:
  - `update(ticker, price, timestamp=None) -> PriceUpdate`
  - `get(ticker) -> PriceUpdate | None`
  - `get_price(ticker) -> float | None`
  - `get_all() -> dict[str, PriceUpdate]`
  - `remove(ticker)`
  - `version` property — monotonic counter, increments on every update (for SSE change detection)

- **`MarketDataSource`** — Abstract interface implemented by `SimulatorDataSource` and `MassiveDataSource`. Lifecycle: `start(tickers)` -> `add_ticker()` / `remove_ticker()` -> `stop()`.

- **`create_market_data_source(cache)`** — Factory. Returns `MassiveDataSource` if `MASSIVE_API_KEY` is set, otherwise `SimulatorDataSource`.

### SSE Streaming

```python
from app.market import create_stream_router

router = create_stream_router(price_cache)  # Returns FastAPI APIRouter
# Endpoint: GET /api/stream/prices (text/event-stream)
```

### Seed Data

Default tickers: AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA, META, JPM, V, NFLX. Seed prices and per-ticker volatility/drift params are in `app/market/seed_prices.py`.

## Database (SQLite)

The persistence layer lives at `app/db/` (not top-level `backend/db/` as PLAN.md's
directory sketch shows — it's a Python package, so it needs to sit under `app/` next
to `market/` for `from app.db import ...` to work; `backend/db/` was never a real
directory, just documentation of the runtime layout). Callers should **never** write
raw SQL — go through the exported functions:

```python
from app.db import (
    init_db,                                             # lazy schema create + seed, idempotent
    get_profile, update_cash_balance,                    # users_profile
    get_watchlist, add_watchlist_ticker, remove_watchlist_ticker,
    get_positions, get_position, upsert_position,
    record_trade, get_trades,                            # append-only log
    record_snapshot, get_snapshots,                      # for the P&L chart
    save_chat_message, get_recent_chat_messages,
)
```

- Every function takes an optional `user_id: str = "default"` per the single-user model.
- `init_db()` should be called once at FastAPI startup (or lazily on first request); it
  creates all six tables from `planning/PLAN.md` section 7 and seeds the default profile
  ($10,000 cash) + 10-ticker watchlist only if `users_profile` is empty — safe to call
  repeatedly.
- DB file location: `db/finally.db` at the project root by default (the Docker volume
  mount point). Override with `FINALLY_DB_PATH` — tests use this to point at a temp file
  per test (see `tests/db/conftest.py`).
- `upsert_position(ticker, quantity, avg_cost)` takes the final resulting values (callers
  compute the new quantity/avg_cost after a buy/sell); passing `quantity <= 0` deletes the
  position row.
- `save_chat_message(role, content, actions=None)` JSON-encodes `actions`;
  `get_recent_chat_messages(limit)` returns oldest-first, ready to feed into an LLM prompt.

## API Application (`app/main.py`)

FastAPI app factory: `from app.main import app` (module-level singleton, used by
uvicorn/Docker) or `create_app()` (fresh instance per call — tests use this
since `MarketDataSource.start()` may only be called once per instance).
`create_app()` builds one `PriceCache` + one market data source, wires all
routers around them, and mounts `static/` (frontend build output) at `/` if
present (absent in local dev — that's fine, only `/api/*` routes work).
`lifespan` calls `db.init_db()`, starts the market source with the DB
watchlist's tickers, and runs a 30s-interval task recording portfolio
snapshots via `app.services.compute_total_value`.

Routes (all under `/api`, see `planning/PLAN.md` section 8 for the contract):
`GET /health`, `GET /stream/prices` (SSE, from `app.market`), `GET|POST
/portfolio`, `POST /portfolio/trade`, `GET /portfolio/history`, `GET|POST
/watchlist`, `DELETE /watchlist/{ticker}`, `POST /chat`.

### `app/services.py` — trade & watchlist business logic

Route handlers call these; so does the chat auto-execution flow. Never
duplicate this logic elsewhere:

```python
from app.services import (
    get_portfolio_state,        # (price_cache) -> {cash_balance, positions, total_value}
    compute_total_value,         # (price_cache) -> float, used by the snapshot task
    execute_trade,                # (ticker, quantity, side, price_cache) -> portfolio state; raises TradeError
    add_watchlist_ticker_live,    # async (ticker, market_source) -> dict
    remove_watchlist_ticker_live, # async (ticker, market_source) -> bool
    TradeError, WatchlistError,
)
```

`execute_trade` validates cash/shares, updates cash + position (weighted
avg_cost on buys, unchanged on sells), records the trade and a fresh
snapshot — all atomically from the caller's point of view. Raises
`TradeError` with a user-facing message on any failure (insufficient
cash/shares, unknown ticker with no cached price, non-positive quantity).

### `app/llm/` — chat integration seam (LLM Engineer implements this)

`POST /api/chat` (`app/routes/chat.py`) already does everything except the
actual model call: persists the user message, builds `portfolio_context`
(portfolio state + watchlist prices), loads recent history via
`db.get_recent_chat_messages()`, calls `llm.get_chat_response(...)`, and for
each returned trade/watchlist-change calls the `services` functions above
(per-item try/except so one bad instruction doesn't fail the whole
response), persists the assistant reply + executed actions, and returns
them. It currently catches `NotImplementedError` and returns a placeholder
message — implement `app.llm.get_chat_response` (full contract and dataclass
shapes documented in `app/llm/__init__.py`'s module docstring) to replace
that. Use the `cerebras-inference` skill for the actual LiteLLM/OpenRouter
call per `planning/PLAN.md` section 9, and honor `LLM_MOCK=true` for
deterministic test responses.

## Running Tests

```bash
uv run --extra dev pytest -v              # All tests
uv run --extra dev pytest --cov=app       # With coverage
uv run --extra dev ruff check app/ tests/ # Lint
```

## Demo

```bash
uv run market_data_demo.py   # Live terminal dashboard with simulated prices
```
