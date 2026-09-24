"""Fixtures for full-app API tests, isolated per test (fresh app + fresh DB)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(initialized_db, monkeypatch):
    """A TestClient wrapping a freshly-built app (own PriceCache/market source).

    Built per-test via create_app() rather than importing the module-level
    `app` singleton, since MarketDataSource.start() may only be called once
    per instance -- reusing the singleton across tests would violate that.
    """
    monkeypatch.delenv("MASSIVE_API_KEY", raising=False)  # force the simulator, not Massive

    from app.main import create_app

    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
