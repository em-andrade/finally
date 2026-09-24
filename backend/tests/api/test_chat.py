"""API-level tests for /api/chat.

app.llm.get_chat_response is now implemented (see app/llm/) -- these tests
run with LLM_MOCK=true (deterministic, no network call) and verify both the
route's plumbing and its auto-execution of the LLM's returned actions. See
app/llm/mock.py's docstring for the exact deterministic trigger phrases.
"""

from __future__ import annotations

import pytest

from app import db


@pytest.fixture(autouse=True)
def _llm_mock(monkeypatch):
    monkeypatch.setenv("LLM_MOCK", "true")


def test_chat_generic_message_returns_portfolio_analysis(client):
    response = client.post("/api/chat", json={"message": "What's my portfolio worth?"})
    assert response.status_code == 200
    body = response.json()
    assert "$10,000.00" in body["message"]  # default seeded cash balance
    assert body["trades"] == []
    assert body["watchlist_changes"] == []


def test_chat_buy_message_auto_executes_trade(client):
    response = client.post("/api/chat", json={"message": "buy 1 AAPL"})
    assert response.status_code == 200
    body = response.json()
    assert len(body["trades"]) == 1
    trade = body["trades"][0]
    assert {k: trade[k] for k in ("ticker", "side", "quantity", "status", "error")} == {
        "ticker": "AAPL",
        "side": "buy",
        "quantity": 1,
        "status": "executed",
        "error": None,
    }
    assert isinstance(trade["price"], (int, float)) and trade["price"] > 0

    portfolio = client.get("/api/portfolio").json()
    tickers = [p["ticker"] for p in portfolio["positions"]]
    assert "AAPL" in tickers


def test_chat_watchlist_change_auto_executes(client):
    # PYPL isn't on the default watchlist.
    response = client.post("/api/chat", json={"message": "add PYPL"})
    assert response.status_code == 200
    body = response.json()
    assert body["watchlist_changes"] == [
        {"ticker": "PYPL", "action": "add", "status": "executed", "error": None}
    ]

    watchlist = client.get("/api/watchlist").json()
    tickers = [w["ticker"] for w in watchlist]
    assert "PYPL" in tickers


def test_chat_persists_user_and_assistant_messages(client):
    client.post("/api/chat", json={"message": "Hello"})

    messages = db.get_recent_chat_messages()
    assert [m["role"] for m in messages] == ["user", "assistant"]
    assert messages[0]["content"] == "Hello"
