"""
File: backend/tests/unit/api/v1/chat/test_handler.py
Purpose: Unit tests for build_handler dispatcher + per-mode builders.
Category: tests
Scope: Phase 50 / Sprint 50.2 (Day 1.4)

Created: 2026-04-30
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from agent_harness._contracts import SubagentBudget
from agent_harness.orchestrator_loop import AgentLoopImpl
from agent_harness.tools.memory_tools import MEMORY_FORMATION_NUDGE
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
            # Sprint 57.99 A2: the MAIN real_llm loop now reads this toggle too;
            # the stub must mirror real Settings (default OFF = A1 byte-identical).
            chat_verification_escalate_on_max=False,
            # Sprint 57.136: the real_llm loop reads the correction-context strategy too;
            # the stub mirrors real Settings (default "keep" = byte-identical).
            chat_verification_correction_strategy="keep",
            # Sprint 57.145: build_real_llm_handler reads knowledge_docs_root to wire
            # the knowledge_search tool; "" → `or None` → None → not registered →
            # byte-identical for these model-routing tests.
            knowledge_docs_root="",
        ),
    )


# --- Sprint 57.148: memory-formation nudge on the system_prompt seam -----------


def test_real_llm_handler_includes_memory_formation_nudge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The nudge rides the proven system_prompt seam when the memory tools are wired."""
    _set_azure_env(monkeypatch, strong="strong-deploy")
    _force_verification_enabled(monkeypatch)

    loop = build_real_llm_handler()

    assert MEMORY_FORMATION_NUDGE in loop._system_prompt  # type: ignore[attr-defined]


def test_echo_demo_handler_omits_memory_formation_nudge() -> None:
    """The no-memory echo path is byte-identical — no formation nudge."""
    loop = build_echo_demo_handler(message="hi")

    assert MEMORY_FORMATION_NUDGE not in loop._system_prompt  # type: ignore[attr-defined]


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


# --- Sprint 57.109 (C2): compactor on the cheap tier --------------------------


def test_build_real_llm_routes_cheap_to_compactor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sprint 57.109 (C2): the compactor's semantic summarize runs on the cheap
    deployment; the user-facing action turn stays on the strong one."""
    _set_azure_env(monkeypatch, strong="strong-deploy")
    monkeypatch.setenv("AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME", "cheap-deploy")
    monkeypatch.delenv("AZURE_OPENAI_CHEAP_MODEL_NAME", raising=False)

    loop = build_real_llm_handler()
    compactor = loop._compactor  # type: ignore[attr-defined]

    assert compactor is not None
    assert compactor.semantic.chat_client.config.deployment_name == "cheap-deploy"
    assert loop._chat_client.config.deployment_name == "strong-deploy"  # type: ignore[attr-defined]


def test_build_real_llm_cheap_unset_compactor_shares_action_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cheap unset → the compactor's semantic client IS the loop client
    (cheap is action — byte-identical fallback, the 57.97 invariant)."""
    _set_azure_env(monkeypatch, strong="strong-deploy")
    monkeypatch.delenv("AZURE_OPENAI_CHEAP_DEPLOYMENT_NAME", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_CHEAP_MODEL_NAME", raising=False)

    loop = build_real_llm_handler()
    compactor = loop._compactor  # type: ignore[attr-defined]

    assert compactor is not None
    assert compactor.semantic.chat_client is loop._chat_client  # type: ignore[attr-defined]


# --- Sprint 57.110 (B4): child loops inherit the composed guardrail engine ----


def test_build_real_llm_child_loops_inherit_composed_guardrail_engine(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sprint 57.110 (B4): FORK + TEAMMATE child loops carry the parent's COMPOSED
    engine INSTANCE — a child is never a Cat 9 bypass (same tenant policy, no
    second policy surface). Capture-and-delegate on make_chat_subagent_dispatcher
    grabs the factory closures the handler wires."""
    _set_azure_env(monkeypatch, strong="strong-deploy")

    import api.v1.chat.handler as handler_mod

    captured: dict[str, Any] = {}
    real_factory = handler_mod.make_chat_subagent_dispatcher

    def _capturing(*args: Any, **kwargs: Any) -> Any:
        captured.update(kwargs)
        return real_factory(*args, **kwargs)

    monkeypatch.setattr(handler_mod, "make_chat_subagent_dispatcher", _capturing)

    loop = build_real_llm_handler(session_id=uuid4())
    engine = loop._guardrail_engine  # type: ignore[attr-defined]
    assert engine is not None

    child = captured["child_loop_factory"](SubagentBudget())
    teammate = captured["teammate_child_loop_factory"](SubagentBudget(), None)
    assert child._guardrail_engine is engine  # noqa: SLF001 — identity, not a copy
    assert teammate._guardrail_engine is engine  # noqa: SLF001
