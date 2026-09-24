"""API-level tests for /api/portfolio*."""

from __future__ import annotations


def test_get_portfolio_shape(client):
    response = client.get("/api/portfolio")
    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"cash_balance", "positions", "total_value"}
    assert body["cash_balance"] == 10000.0
    assert body["positions"] == []
    assert body["total_value"] == 10000.0


def test_trade_buy_success(client):
    response = client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1, "side": "buy"})
    assert response.status_code == 200
    body = response.json()
    assert body["cash_balance"] < 10000.0
    assert len(body["positions"]) == 1
    assert body["positions"][0]["ticker"] == "AAPL"


def test_trade_buy_insufficient_cash_returns_400(client):
    response = client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1_000_000, "side": "buy"}
    )
    assert response.status_code == 400
    assert "Insufficient cash" in response.json()["detail"]


def test_trade_sell_without_position_returns_400(client):
    response = client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1, "side": "sell"})
    assert response.status_code == 400
    assert "Insufficient shares" in response.json()["detail"]


def test_trade_invalid_side_returns_422(client):
    response = client.post(
        "/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1, "side": "hold"}
    )
    assert response.status_code == 422  # pydantic Literal validation


def test_trade_unknown_ticker_returns_400(client):
    response = client.post("/api/portfolio/trade", json={"ticker": "ZZZZ", "quantity": 1, "side": "buy"})
    assert response.status_code == 400


def test_portfolio_history_starts_empty_then_grows_after_trade(client):
    assert client.get("/api/portfolio/history").json() == []

    client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1, "side": "buy"})

    history = client.get("/api/portfolio/history").json()
    assert len(history) == 1
    assert "total_value" in history[0]
