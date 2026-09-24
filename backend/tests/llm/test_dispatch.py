"""Tests for get_chat_response's LLM_MOCK dispatch behavior."""

from __future__ import annotations

from app.llm import ChatResponse, get_chat_response

PORTFOLIO = {"cash_balance": 100.0, "total_value": 100.0, "positions": [], "watchlist": []}


def test_llm_mock_true_uses_deterministic_mock(monkeypatch):
    monkeypatch.setenv("LLM_MOCK", "true")
    result = get_chat_response("buy 1 AAPL", PORTFOLIO, [])
    assert isinstance(result, ChatResponse)
    assert result.trades is not None
    assert result.trades[0].ticker == "AAPL"


def test_llm_mock_case_and_value_variants(monkeypatch):
    for value in ("True", "1", "yes", "YES"):
        monkeypatch.setenv("LLM_MOCK", value)
        result = get_chat_response("hello", PORTFOLIO, [])
        assert isinstance(result, ChatResponse)


def test_llm_mock_false_calls_real_client(monkeypatch):
    monkeypatch.setenv("LLM_MOCK", "false")
    monkeypatch.setattr(
        "app.llm.client.call_llm",
        lambda *a, **kw: ChatResponse(message="real client was called"),
    )
    result = get_chat_response("hello", PORTFOLIO, [])
    assert result.message == "real client was called"


def test_llm_mock_unset_defaults_to_real_client(monkeypatch):
    monkeypatch.delenv("LLM_MOCK", raising=False)
    monkeypatch.setattr(
        "app.llm.client.call_llm",
        lambda *a, **kw: ChatResponse(message="real client was called"),
    )
    result = get_chat_response("hello", PORTFOLIO, [])
    assert result.message == "real client was called"
