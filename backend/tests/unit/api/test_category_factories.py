"""
File: backend/tests/unit/api/test_category_factories.py
Purpose: Unit tests for Sprint 57.63 chat-path Cat 4 / Cat 7 factory helpers
    (_category_factories.make_chat_compactor / make_chat_state_deps).
Category: Tests
Created: 2026-05-31 (Sprint 57.63 Day 1)
Modified: 2026-05-31

Description:
    Pure unit tests (no DB / no env / no real LLM). Verify:
    - make_chat_compactor returns a HybridCompactor built from the supplied
      ChatClient (D1-corrected ctor: keyword-only, token_threshold_ratio).
    - make_chat_state_deps is all-three-or-nothing: returns (DefaultReducer,
      DBCheckpointer) only when db + session_id + tenant_id are all present,
      else (None, None) so AgentLoopImpl's Cat 7 path stays a no-op.
"""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from adapters._testing.mock_clients import MockChatClient
from agent_harness.context_mgmt.compactor.hybrid import HybridCompactor
from agent_harness.error_handling import (
    DefaultCircuitBreaker,
    DefaultErrorTerminator,
    ErrorPolicy,
    RetryPolicyMatrix,
    TenantErrorBudget,
)
from agent_harness.state_mgmt import DBCheckpointer, DefaultReducer
from api.v1.chat._category_factories import (
    _DEFAULT_CHAT_TOKEN_BUDGET,
    _DEFAULT_KEEP_RECENT_TURNS,
    _compaction_keep_recent_turns,
    _compaction_token_budget,
    _compaction_tool_anchored_keep,
    make_chat_compactor,
    make_chat_error_deps,
    make_chat_state_deps,
)


def test_make_chat_compactor_returns_hybrid() -> None:
    compactor = make_chat_compactor(MockChatClient(responses=[]))
    assert isinstance(compactor, HybridCompactor)


def test_make_chat_state_deps_all_present() -> None:
    reducer, checkpointer = make_chat_state_deps(MagicMock(), uuid4(), uuid4())
    assert isinstance(reducer, DefaultReducer)
    assert isinstance(checkpointer, DBCheckpointer)


def test_make_chat_state_deps_none_when_db_missing() -> None:
    reducer, checkpointer = make_chat_state_deps(None, uuid4(), uuid4())
    assert reducer is None
    assert checkpointer is None


def test_make_chat_state_deps_none_when_session_missing() -> None:
    reducer, checkpointer = make_chat_state_deps(MagicMock(), None, uuid4())
    assert reducer is None
    assert checkpointer is None


def test_make_chat_state_deps_none_when_tenant_missing() -> None:
    reducer, checkpointer = make_chat_state_deps(MagicMock(), uuid4(), None)
    assert reducer is None
    assert checkpointer is None


def test_make_chat_error_deps_returns_five_wired_deps() -> None:
    policy, retry, breaker, budget, terminator = make_chat_error_deps()
    assert isinstance(policy, ErrorPolicy)
    assert isinstance(retry, RetryPolicyMatrix)
    assert isinstance(breaker, DefaultCircuitBreaker)
    assert isinstance(budget, TenantErrorBudget)
    assert isinstance(terminator, DefaultErrorTerminator)


def test_make_chat_error_deps_terminator_composes_breaker_and_budget() -> None:
    _, _, breaker, budget, terminator = make_chat_error_deps()
    # The terminator must share the SAME breaker + budget instances so all three
    # reason over one set of counters (loop.py _handle_tool_error chain).
    assert terminator._circuit_breaker is breaker
    assert terminator._error_budget is budget


def test_make_chat_verifier_registry_registers_one_llm_judge() -> None:
    # Sprint 57.63 Cat 10: a real LLMJudgeVerifier in a VerifierRegistry of size 1.
    # Local imports keep this test independent of the module-level import block.
    from agent_harness.verification import VerifierRegistry
    from api.v1.chat._category_factories import make_chat_verifier_registry

    registry = make_chat_verifier_registry(MockChatClient(responses=[]), "safety_review")
    assert isinstance(registry, VerifierRegistry)
    # correction_loop.py gates on len(registry) == 0 → must be non-empty (1).
    assert len(registry) == 1


# === Sprint 57.109 (C2): CHAT_COMPACTION_TOKEN_BUDGET env knob ===============


def test_compaction_budget_default_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CHAT_COMPACTION_TOKEN_BUDGET", raising=False)
    assert _compaction_token_budget() == _DEFAULT_CHAT_TOKEN_BUDGET == 100_000


def test_compaction_budget_env_honored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHAT_COMPACTION_TOKEN_BUDGET", "2000")
    assert _compaction_token_budget() == 2_000


@pytest.mark.parametrize("raw", ["abc", "-5", "0", ""])
def test_compaction_budget_invalid_falls_back(monkeypatch: pytest.MonkeyPatch, raw: str) -> None:
    monkeypatch.setenv("CHAT_COMPACTION_TOKEN_BUDGET", raw)
    assert _compaction_token_budget() == _DEFAULT_CHAT_TOKEN_BUDGET


def test_factory_threads_budget_to_sub_compactors(monkeypatch: pytest.MonkeyPatch) -> None:
    """57.109 D13: hybrid delegates should_compact to the sub-strategies — all
    three must agree on the (env-resolved) threshold or the knob is a no-op."""
    monkeypatch.setenv("CHAT_COMPACTION_TOKEN_BUDGET", "2000")
    compactor = make_chat_compactor(MockChatClient(responses=[]))
    assert compactor.token_budget == 2_000  # type: ignore[attr-defined]
    assert compactor.structural.token_budget == 2_000  # type: ignore[attr-defined]
    assert compactor.semantic.token_budget == 2_000  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("1", 1), ("3", 3), ("", _DEFAULT_KEEP_RECENT_TURNS)],
)
def test_compaction_keep_recent_turns_env(
    monkeypatch: pytest.MonkeyPatch, raw: str, expected: int
) -> None:
    monkeypatch.setenv("CHAT_COMPACTION_KEEP_RECENT_TURNS", raw)
    assert _compaction_keep_recent_turns() == expected


@pytest.mark.parametrize("raw", ["abc", "0", "-2"])
def test_compaction_keep_recent_turns_invalid_falls_back(
    monkeypatch: pytest.MonkeyPatch, raw: str
) -> None:
    """0 is rejected: `user_indices[-0]` == `[0]` would silently keep everything."""
    monkeypatch.setenv("CHAT_COMPACTION_KEEP_RECENT_TURNS", raw)
    assert _compaction_keep_recent_turns() == _DEFAULT_KEEP_RECENT_TURNS


def test_factory_threads_keep_recent_to_sub_compactors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CHAT_COMPACTION_KEEP_RECENT_TURNS", "1")
    compactor = make_chat_compactor(MockChatClient(responses=[]))
    assert compactor.structural.keep_recent_turns == 1  # type: ignore[attr-defined]
    assert compactor.semantic.keep_recent_turns == 1  # type: ignore[attr-defined]


# === Sprint 57.160: CHAT_COMPACTION_TOOL_ANCHORED_MASKING env lever ===========


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("2", 2), ("1", 1), ("", None), ("0", None), ("-3", None), ("abc", None)],
)
def test_compaction_tool_anchored_keep_env(
    monkeypatch: pytest.MonkeyPatch, raw: str, expected: int | None
) -> None:
    """>= 1 → N; unset / 0 / negative / garbage → None (OFF, user-anchored default)."""
    monkeypatch.setenv("CHAT_COMPACTION_TOOL_ANCHORED_MASKING", raw)
    assert _compaction_tool_anchored_keep() == expected


def test_compaction_tool_anchored_keep_unset_is_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CHAT_COMPACTION_TOOL_ANCHORED_MASKING", raising=False)
    assert _compaction_tool_anchored_keep() is None


def test_factory_default_masker_is_user_anchored(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lever OFF → structural gets a user-anchored masker (tool_anchor_keep is None)."""
    monkeypatch.delenv("CHAT_COMPACTION_TOOL_ANCHORED_MASKING", raising=False)
    compactor = make_chat_compactor(MockChatClient(responses=[]))
    assert compactor.structural.masker.tool_anchor_keep is None  # type: ignore[attr-defined]


def test_factory_injects_tool_anchored_masker_into_structural(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Lever ON → the SAME tool-anchored masker is injected into the structural stage."""
    monkeypatch.setenv("CHAT_COMPACTION_TOOL_ANCHORED_MASKING", "3")
    compactor = make_chat_compactor(MockChatClient(responses=[]))
    assert compactor.structural.masker.tool_anchor_keep == 3  # type: ignore[attr-defined]


def test_factory_injects_tool_anchored_masker_into_preclear(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Lever ON + preclear enabled → the preclear stage also gets the tool-anchored masker."""
    from agent_harness.context_mgmt.compactor.chained import ChainedCompactor

    monkeypatch.setenv("CHAT_COMPACTION_TOOL_ANCHORED_MASKING", "2")
    monkeypatch.setenv("CHAT_COMPACTION_PRECLEAR_RATIO", "0.5")
    compactor = make_chat_compactor(MockChatClient(responses=[]))
    assert isinstance(compactor, ChainedCompactor)
    preclear = compactor.compactors[0]
    assert preclear.masker.tool_anchor_keep == 2  # type: ignore[attr-defined]
