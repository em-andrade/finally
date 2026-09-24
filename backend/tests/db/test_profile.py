from __future__ import annotations

from app.db import get_profile, update_cash_balance
from app.db.schema import DEFAULT_CASH_BALANCE


def test_get_profile_returns_seeded_default(initialized_db):
    profile = get_profile()
    assert profile["id"] == "default"
    assert profile["cash_balance"] == DEFAULT_CASH_BALANCE
    assert profile["created_at"]


def test_get_profile_unknown_user_returns_none(initialized_db):
    assert get_profile(user_id="nobody") is None


def test_update_cash_balance_applies_positive_delta(initialized_db):
    new_balance = update_cash_balance(250.0)
    assert new_balance == DEFAULT_CASH_BALANCE + 250.0
    assert get_profile()["cash_balance"] == DEFAULT_CASH_BALANCE + 250.0


def test_update_cash_balance_applies_negative_delta(initialized_db):
    new_balance = update_cash_balance(-1000.0)
    assert new_balance == DEFAULT_CASH_BALANCE - 1000.0


def test_update_cash_balance_accumulates(initialized_db):
    update_cash_balance(-100.0)
    update_cash_balance(-50.0)
    final = update_cash_balance(25.0)
    assert final == DEFAULT_CASH_BALANCE - 100.0 - 50.0 + 25.0
