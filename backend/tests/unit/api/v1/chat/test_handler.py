"""
File: backend/tests/unit/api/v1/chat/test_handler.py
Purpose: Unit tests for build_handler dispatcher + per-mode builders.
Category: tests
Scope: Phase 50 / Sprint 50.2 (Day 1.4)

Created: 2026-04-30
"""

from __future__ import annotations

import pytest

from agent_harness.orchestrator_loop import AgentLoopImpl
from api.v1.chat.handler import (
    build_echo_demo_handler,
    build_handler,
    build_real_llm_handler,
)


def test_build_echo_demo_returns_agent_loop() -> None:
    # Sprint 57.63 (Cat 10, approach A): builders return (loop, verifier_registry).
    loop, registry = build_echo_demo_handler(message="hello")
    assert isinstance(loop, AgentLoopImpl)
    assert registry is None  # echo_demo never verifies


def test_build_echo_demo_scripts_message_into_tool_call() -> None:
    """Scripted MockChatClient response should carry user's message as echo_tool arg."""
    loop, _ = build_echo_demo_handler(message="zebra")
    # peek at scripted responses via MockChatClient internals
    client = loop._chat_client  # type: ignore[attr-defined]
    first_response = client._responses[0]  # type: ignore[attr-defined]
    assert first_response.tool_calls is not None
    assert first_response.tool_calls[0].name == "echo_tool"
    assert first_response.tool_calls[0].arguments == {"text": "zebra"}


def test_build_real_llm_missing_env_raises_runtime_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT_NAME", raising=False)
    with pytest.raises(RuntimeError, match="missing env vars"):
        build_real_llm_handler()


def test_build_handler_dispatches_echo_demo() -> None:
    loop, registry = build_handler("echo_demo", "x")
    assert isinstance(loop, AgentLoopImpl)
    assert registry is None


def test_build_handler_invalid_mode_raises() -> None:
    with pytest.raises(ValueError, match="Unsupported mode"):
        build_handler("bogus", "x")  # type: ignore[arg-type]
