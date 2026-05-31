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
