"""API-level tests for /api/watchlist*."""

from __future__ import annotations


def test_get_watchlist_has_default_ten_tickers_with_prices(client):
    response = client.get("/api/watchlist")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 10
    for entry in body:
        assert entry["price"] is not None  # simulator seeds prices synchronously on start()


def test_add_ticker(client):
    response = client.post("/api/watchlist", json={"ticker": "pypl"})
    assert response.status_code == 200
    assert response.json()["ticker"] == "PYPL"

    tickers = [e["ticker"] for e in client.get("/api/watchlist").json()]
    assert "PYPL" in tickers


def test_remove_ticker(client):
    client.post("/api/watchlist", json={"ticker": "PYPL"})
    response = client.delete("/api/watchlist/PYPL")
    assert response.status_code == 200
    assert response.json() == {"removed": True, "ticker": "PYPL"}

    tickers = [e["ticker"] for e in client.get("/api/watchlist").json()]
    assert "PYPL" not in tickers


def test_remove_unknown_ticker_returns_404(client):
    response = client.delete("/api/watchlist/ZZZZ")
    assert response.status_code == 404
