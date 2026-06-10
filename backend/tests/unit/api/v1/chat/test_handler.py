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
    # Sprint 57.98 A1: builders return the wired AgentLoopImpl alone (the verifier
    # registry is injected into the loop ctor). echo_demo never verifies → None.
    loop = build_echo_demo_handler(message="hello")
    assert isinstance(loop, AgentLoopImpl)
    assert loop._verifier_registry is None  # type: ignore[attr-defined]


def test_build_echo_demo_scripts_message_into_tool_call() -> None:
    """Scripted MockChatClient response should carry user's message as echo_tool arg."""
    loop = build_echo_demo_handler(message="zebra")
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
    # Sprint 57.98 A1: build_handler returns the wired AgentLoopImpl alone
    # (the verifier registry is injected into the loop ctor, not returned).
    loop = build_handler("echo_demo", "x")
    assert isinstance(loop, AgentLoopImpl)


def test_build_handler_invalid_mode_raises() -> None:
    with pytest.raises(ValueError, match="Unsupported mode"):
        build_handler("bogus", "x")  # type: ignore[arg-type]


# --- Sprint 57.97: multi-model profile (verifier on the cheap tier) ----------


def _set_azure_env(monkeypatch: pytest.MonkeyPatch, *, strong: str) -> None:
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://placeholder.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "placeholder-key")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT_NAME", strong)


def _force_verification_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin the handler's settings to verification-enabled so the verifier registry is built."""
    from types import SimpleNamespace

    monkeypatch.setattr(
        "api.v1.chat.handler.get_settings",
        lambda: SimpleNamespace(
            chat_verification_mode="enabled",
            chat_verification_judge_template="output_quality",
        ),
    )


def test_build_real_llm_routes_cheap_to_verifier_action_to_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sprint 57.97: the loop runs on the strong (action) deployment; the verifier on the cheap."""
    _set_azure_env(monkeypatch, strong="strong-deploy")
    monkeypatch.setenv("AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME", "cheap-deploy")
    monkeypatch.delenv("AZURE_OPENAI_CHEAP_MODEL_NAME", raising=False)
    _force_verification_enabled(monkeypatch)

    loop = build_real_llm_handler()
    verifier_registry = loop._verifier_registry  # type: ignore[attr-defined]

    # The user-facing action turn runs on the STRONG deployment (unchanged).
    assert loop._chat_client.config.deployment_name == "strong-deploy"  # type: ignore[attr-defined]
    # The verification (llm_judge) call runs on the CHEAP deployment.
    assert verifier_registry is not None
    verifier = verifier_registry.get_all()[0]
    assert verifier._chat.config.deployment_name == "cheap-deploy"  # type: ignore[attr-defined]


def test_build_real_llm_cheap_unset_verifier_shares_action_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cheap unset → the verifier shares the SAME client as the loop (byte-identical fallback)."""
    _set_azure_env(monkeypatch, strong="strong-deploy")
    monkeypatch.delenv("AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME", raising=False)
    _force_verification_enabled(monkeypatch)

    loop = build_real_llm_handler()
    verifier_registry = loop._verifier_registry  # type: ignore[attr-defined]

    assert verifier_registry is not None
    verifier = verifier_registry.get_all()[0]
    # cheap is the strong client → verifier._chat IS loop._chat_client.
    assert verifier._chat is loop._chat_client  # type: ignore[attr-defined]
