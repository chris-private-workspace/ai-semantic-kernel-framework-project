"""
File: backend/src/api/v1/chat/_category_factories.py
Purpose: API-layer constructors for the Cat 4 / Cat 7 (+ Cat 8 from Day 2) deps
    injected into the production chat-path AgentLoopImpl (Sprint 57.63).
Category: API / chat-path category activation (delegates to agent_harness owners)
Scope: Phase 57 / Sprint 57.63

Description:
    build_real_llm_handler wires Cat 9 guardrails today but leaves Cat 4
    (context compaction) and Cat 7 (state reducer + checkpointer) un-injected.
    Those deps exist in AgentLoopImpl as opt-in `| None = None` params and
    activate by injection alone — verified Sprint 57.63 Day 0 at the loop
    call-sites (Cat 4: loop.py:828/847/861; Cat 7: loop.py:1350/1373/1381).
    These helpers build the deps so the handler stays small + readable.

    LLM-neutrality: this module lives in the api layer, so it may import
    agent_harness concrete impls. The Cat 4 dep that needs an LLM receives the
    already-constructed ChatClient (neutral ABC) — no openai / anthropic import
    here or downstream in agent_harness.

Key Components:
    - make_chat_compactor(chat_client) -> Compactor  (Cat 4)
    - make_chat_state_deps(db, session_id, tenant_id) -> (Reducer|None, Checkpointer|None)  (Cat 7)

Created: 2026-05-31 (Sprint 57.63 Day 1)
Last Modified: 2026-05-31

Modification History (newest-first):
    - 2026-05-31: Initial creation (Sprint 57.63 Day 1) — Cat 4 + Cat 7 chat-path factories

Related:
    - api/v1/chat/handler.py — build_real_llm_handler consumer
    - agent_harness/orchestrator_loop/loop.py — AgentLoopImpl opt-in deps (L195-204)
    - 17-cross-category-interfaces.md §2.1 — Compactor / Reducer / Checkpointer ABCs
    - sprint-57-63-plan.md §3 (D1 ctor correction applied)
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from agent_harness.context_mgmt import Compactor
from agent_harness.context_mgmt.compactor.hybrid import HybridCompactor
from agent_harness.context_mgmt.compactor.semantic import SemanticCompactor
from agent_harness.context_mgmt.compactor.structural import StructuralCompactor
from agent_harness.error_handling import (
    DefaultCircuitBreaker,
    DefaultErrorPolicy,
    DefaultErrorTerminator,
    ErrorPolicy,
    InMemoryBudgetStore,
    RetryPolicyMatrix,
    TenantErrorBudget,
)
from agent_harness.state_mgmt import Checkpointer, DBCheckpointer, DefaultReducer, Reducer
from agent_harness.verification import VerifierRegistry
from agent_harness.verification.llm_judge import LLMJudgeVerifier

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from adapters._base.chat_client import ChatClient

# Cat 4 budget — mirrors AgentLoopImpl default (loop.py:193) so compaction
# triggers at the same threshold the loop reasons about.
_CHAT_TOKEN_BUDGET = 100_000
_CHAT_TOKEN_THRESHOLD_RATIO = 0.75


def make_chat_compactor(chat_client: ChatClient) -> Compactor:
    """Cat 4: HybridCompactor (structural-first, semantic fallback).

    D1 (Sprint 57.63 Day 0 drift): HybridCompactor.__init__ is keyword-only and
    the threshold param is `token_threshold_ratio` (NOT `threshold`);
    SemanticCompactor needs keyword `chat_client`; StructuralCompactor() has no
    required deps.
    """
    return HybridCompactor(
        structural=StructuralCompactor(),
        semantic=SemanticCompactor(chat_client=chat_client),
        token_budget=_CHAT_TOKEN_BUDGET,
        token_threshold_ratio=_CHAT_TOKEN_THRESHOLD_RATIO,
    )


def make_chat_state_deps(
    db: AsyncSession | None,
    session_id: UUID | None,
    tenant_id: UUID | None,
) -> tuple[Reducer | None, Checkpointer | None]:
    """Cat 7: (DefaultReducer, DBCheckpointer) when all three inputs present.

    Returns (None, None) when any input is missing so AgentLoopImpl's Cat 7
    integration stays a no-op (all-three-or-nothing per loop.py:1350 guard).
    Idiom confirmed against tests/integration/.../test_checkpointer_db.py:86.
    """
    if db is None or session_id is None or tenant_id is None:
        return None, None
    reducer: Reducer = DefaultReducer()
    checkpointer: Checkpointer = DBCheckpointer(db, session_id=session_id, tenant_id=tenant_id)
    return reducer, checkpointer


def make_chat_error_deps() -> tuple[
    ErrorPolicy,
    RetryPolicyMatrix,
    DefaultCircuitBreaker,
    TenantErrorBudget,
    DefaultErrorTerminator,
]:
    """Cat 8: the 5 error-handling deps AgentLoopImpl wires into its tool-error chain.

    `_handle_tool_error` (loop.py:265, called at 1157/1225) runs classify → record
    budget → check terminator when these are injected. Defaults match plan §3.3.

    Budget store: InMemoryBudgetStore (per-process; chosen for this sprint).
    RedisBudgetStore (cross-instance) is deferred — no shared error-budget Redis
    client is wired yet. tenant_id is passed per-call inside the loop, NOT at
    construction (see TenantErrorBudget.record/...). The terminator composes the
    circuit breaker + error budget so all three share one set of counters.
    """
    error_policy: ErrorPolicy = DefaultErrorPolicy()
    retry_policy = RetryPolicyMatrix()
    circuit_breaker = DefaultCircuitBreaker()
    error_budget = TenantErrorBudget(InMemoryBudgetStore())
    error_terminator = DefaultErrorTerminator(
        circuit_breaker=circuit_breaker,
        error_budget=error_budget,
    )
    return error_policy, retry_policy, circuit_breaker, error_budget, error_terminator


def make_chat_verifier_registry(
    chat_client: ChatClient,
    judge_template: str,
) -> VerifierRegistry:
    """Cat 10: a VerifierRegistry with one real LLMJudgeVerifier (final-output judge).

    Unlike the no-op `build_default_verifier_registry()` (empty RulesBasedVerifier),
    this registers a real `LLMJudgeVerifier` that makes an independent LLM call to
    judge the chat's final output. Fail-closed (any judge error → passed=False).

    Built here (api layer) because LLMJudgeVerifier needs the SAME ChatClient
    adapter the loop uses; the registry is threaded back to the router alongside
    the loop (approach A — user-confirmed 2026-05-31). LLM-neutral: receives the
    adapter as the ChatClient ABC.

    Args:
        chat_client: the adapter (ChatClient ABC) the loop runs on.
        judge_template: a template name (e.g. "safety_review", loaded from
            verification/templates/) or a raw string containing `{output}`.
    """
    registry = VerifierRegistry()
    registry.register(LLMJudgeVerifier(chat_client=chat_client, judge_template=judge_template))
    return registry


__all__ = [
    "make_chat_compactor",
    "make_chat_state_deps",
    "make_chat_error_deps",
    "make_chat_verifier_registry",
]
