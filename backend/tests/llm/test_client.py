"""Tests for app/llm/client.py — the real LLM call path, with litellm.completion stubbed out
(no network access) per PLAN.md section 12: "structured output parsing handles all valid
schemas, graceful handling of malformed responses"."""

from __future__ import annotations

import json

import pytest

from app.llm import ChatResponse
from app.llm.client import call_llm

PORTFOLIO = {"cash_balance": 1000.0, "total_value": 1000.0, "positions": [], "watchlist": []}


class _FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeChoice:
    def __init__(self, content: str) -> None:
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self.choices = [_FakeChoice(content)]


def _stub_completion(content: str):
    def _fn(**kwargs):
        return _FakeResponse(content)

    return _fn


def test_valid_structured_response_with_trade(monkeypatch):
    payload = {
        "message": "Buying 10 AAPL as requested.",
        "trades": [{"ticker": "AAPL", "side": "buy", "quantity": 10}],
        "watchlist_changes": [],
    }
    monkeypatch.setattr("app.llm.client.completion", _stub_completion(json.dumps(payload)))

    result = call_llm("buy 10 AAPL", PORTFOLIO, [])

    assert isinstance(result, ChatResponse)
    assert result.message == "Buying 10 AAPL as requested."
    assert result.trades is not None
    assert result.trades[0].ticker == "AAPL"
    assert result.trades[0].side == "buy"
    assert result.trades[0].quantity == 10
    assert result.watchlist_changes is None  # empty list normalized to None


def test_valid_response_with_no_actions(monkeypatch):
    payload = {"message": "Your portfolio looks balanced.", "trades": [], "watchlist_changes": []}
    monkeypatch.setattr("app.llm.client.completion", _stub_completion(json.dumps(payload)))

    result = call_llm("how am I doing?", PORTFOLIO, [])

    assert result.message == "Your portfolio looks balanced."
    assert result.trades is None
    assert result.watchlist_changes is None


def test_valid_response_with_watchlist_change(monkeypatch):
    payload = {
        "message": "Added PYPL.",
        "trades": [],
        "watchlist_changes": [{"ticker": "PYPL", "action": "add"}],
    }
    monkeypatch.setattr("app.llm.client.completion", _stub_completion(json.dumps(payload)))

    result = call_llm("add PYPL", PORTFOLIO, [])

    assert result.watchlist_changes is not None
    assert result.watchlist_changes[0].ticker == "PYPL"
    assert result.watchlist_changes[0].action == "add"


def test_malformed_json_returns_graceful_error(monkeypatch):
    monkeypatch.setattr("app.llm.client.completion", _stub_completion("not valid json"))

    result = call_llm("hello", PORTFOLIO, [])

    assert isinstance(result, ChatResponse)
    assert result.trades is None
    assert result.watchlist_changes is None
    assert result.message  # some apologetic message, not an exception


def test_schema_violation_returns_graceful_error(monkeypatch):
    # Missing required "message" field.
    monkeypatch.setattr(
        "app.llm.client.completion",
        _stub_completion(json.dumps({"trades": [], "watchlist_changes": []})),
    )

    result = call_llm("hello", PORTFOLIO, [])

    assert isinstance(result, ChatResponse)
    assert result.message


def test_network_exception_returns_graceful_error(monkeypatch):
    def _raise(**kwargs):
        raise ConnectionError("network unreachable")

    monkeypatch.setattr("app.llm.client.completion", _raise)

    result = call_llm("hello", PORTFOLIO, [])

    assert isinstance(result, ChatResponse)
    assert result.message
    assert result.trades is None
    assert result.watchlist_changes is None


def test_call_llm_never_raises_for_llm_failures(monkeypatch):
    def _raise(**kwargs):
        raise RuntimeError("some litellm internal failure")

    monkeypatch.setattr("app.llm.client.completion", _raise)

    try:
        call_llm("hello", PORTFOLIO, [])
    except Exception as exc:  # pragma: no cover - this is the failure condition
        pytest.fail(f"call_llm raised instead of returning a graceful ChatResponse: {exc}")
