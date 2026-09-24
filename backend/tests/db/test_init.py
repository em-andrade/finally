"""Tests for lazy schema creation and seeding."""

from __future__ import annotations

import sqlite3

from app.db import init_db
from app.db.connection import get_db_path
from app.db.schema import DEFAULT_CASH_BALANCE, DEFAULT_USER_ID, DEFAULT_WATCHLIST_TICKERS


def test_init_creates_db_file(db_path):
    assert not db_path.exists()
    init_db()
    assert db_path.exists()


def test_init_creates_all_tables(initialized_db):
    conn = sqlite3.connect(get_db_path())
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    conn.close()
    expected = {
        "users_profile",
        "watchlist",
        "positions",
        "trades",
        "portfolio_snapshots",
        "chat_messages",
    }
    assert expected.issubset(tables)


def test_init_seeds_default_profile(initialized_db):
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT id, cash_balance FROM users_profile WHERE id = ?", (DEFAULT_USER_ID,)
    ).fetchone()
    conn.close()
    assert row is not None
    assert row["cash_balance"] == DEFAULT_CASH_BALANCE


def test_init_seeds_default_watchlist(initialized_db):
    conn = sqlite3.connect(get_db_path())
    tickers = {
        row[0]
        for row in conn.execute(
            "SELECT ticker FROM watchlist WHERE user_id = ?", (DEFAULT_USER_ID,)
        ).fetchall()
    }
    conn.close()
    assert tickers == set(DEFAULT_WATCHLIST_TICKERS)


def test_init_is_idempotent(db_path):
    init_db()
    init_db()
    init_db()
    conn = sqlite3.connect(get_db_path())
    profile_count = conn.execute("SELECT COUNT(*) FROM users_profile").fetchone()[0]
    watchlist_count = conn.execute("SELECT COUNT(*) FROM watchlist").fetchone()[0]
    conn.close()
    assert profile_count == 1
    assert watchlist_count == len(DEFAULT_WATCHLIST_TICKERS)


def test_init_does_not_reseed_after_manual_changes(initialized_db):
    """Re-running init_db after the user has modified their data must not reset it."""
    from app.db import remove_watchlist_ticker, update_cash_balance

    update_cash_balance(-500.0)
    remove_watchlist_ticker("AAPL")

    init_db()

    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    balance = conn.execute(
        "SELECT cash_balance FROM users_profile WHERE id = ?", (DEFAULT_USER_ID,)
    ).fetchone()["cash_balance"]
    tickers = {
        row[0] for row in conn.execute("SELECT ticker FROM watchlist").fetchall()
    }
    conn.close()
    assert balance == DEFAULT_CASH_BALANCE - 500.0
    assert "AAPL" not in tickers
