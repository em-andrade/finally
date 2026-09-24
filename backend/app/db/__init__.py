"""SQLite persistence layer for FinAlly.

Lazily initialized, single SQLite file (see connection.get_db_path). Callers
must never write raw SQL directly against the database — go through the
functions exported here.

Public API:
    init_db()                                    - Create schema + seed if missing (idempotent)
    get_profile() / update_cash_balance()         - users_profile
    get_watchlist() / add_watchlist_ticker() /
        remove_watchlist_ticker()                 - watchlist
    get_positions() / get_position() /
        upsert_position()                         - positions
    record_trade() / get_trades()                 - trades (append-only)
    record_snapshot() / get_snapshots()            - portfolio_snapshots
    save_chat_message() / get_recent_chat_messages() - chat_messages
"""

from .chat import get_recent_chat_messages, save_chat_message
from .init import init_db
from .positions import get_position, get_positions, upsert_position
from .profile import get_profile, update_cash_balance
from .schema import DEFAULT_CASH_BALANCE, DEFAULT_USER_ID, DEFAULT_WATCHLIST_TICKERS
from .snapshots import get_snapshots, record_snapshot
from .trades import get_trades, record_trade
from .watchlist import add_watchlist_ticker, get_watchlist, remove_watchlist_ticker

__all__ = [
    "init_db",
    "get_profile",
    "update_cash_balance",
    "get_watchlist",
    "add_watchlist_ticker",
    "remove_watchlist_ticker",
    "get_positions",
    "get_position",
    "upsert_position",
    "record_trade",
    "get_trades",
    "record_snapshot",
    "get_snapshots",
    "get_recent_chat_messages",
    "save_chat_message",
    "DEFAULT_USER_ID",
    "DEFAULT_CASH_BALANCE",
    "DEFAULT_WATCHLIST_TICKERS",
]
