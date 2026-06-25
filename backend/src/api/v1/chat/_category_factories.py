"""
File: backend/src/api/v1/chat/_category_factories.py
Purpose: API-layer constructors for the Cat 4 / Cat 5 / Cat 7 / Cat 8 / Cat 10 deps
    injected into the production chat-path AgentLoopImpl (Sprint 57.63 / 57.64).
Category: API / chat-path category activation (delegates to agent_harness owners)
Scope: Phase 57 / Sprint 57.63 (+ Cat 5 in 57.64)

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
    - make_chat_prompt_builder(chat_client, memory_retrieval=None) -> PromptBuilder  (Cat 5)
    - make_chat_memory_deps(db) -> (MemoryRetrieval, dict[str, MemoryLayer])  (Cat 3)
    - make_chat_subagent_dispatcher(chat_client) -> SubagentDispatcher  (Cat 11)
    - make_chat_state_deps(db, session_id, tenant_id) -> (Reducer|None, Checkpointer|None)  (Cat 7)

Created: 2026-05-31 (Sprint 57.63 Day 1)
Last Modified: 2026-06-11

Modification History (newest-first):
    - 2026-06-12: Sprint 57.109 C2 — compaction budget env knob + thread to sub-compactors
    - 2026-06-11: Sprint 57.103 (B2b) — inbox_factory → inbox_scope (register child queue)
    - 2026-06-11: Sprint 57.102 (B2a) — thread teammate factory + inbox_factory + mailbox
    - 2026-06-09: Sprint 57.95 — make_chat_subagent_dispatcher threads event_emitter (SSE relay)
    - 2026-06-05: Sprint 57.81 — error budget store via maybe_get_budget_store (B-7 wiring)
    - 2026-06-01: Sprint 57.65 — make_chat_prompt_builder accepts real MemoryRetrieval (A-1 Tier2)
    - 2026-06-01: Sprint 57.64 Day 2 — add Cat 3 memory deps + Cat 11 subagent dispatcher factories
    - 2026-06-01: Add make_chat_prompt_builder (Sprint 57.64 Day 1) — Cat 5 keystone factory
    - 2026-05-31: Initial creation (Sprint 57.63 Day 1) — Cat 4 + Cat 7 chat-path factories

Related:
    - api/v1/chat/handler.py — build_real_llm_handler consumer
    - agent_harness/orchestrator_loop/loop.py — AgentLoopImpl opt-in deps (L195-204)
    - 17-cross-category-interfaces.md §2.1 — Compactor / PromptBuilder / Reducer / Checkpointer ABCs
    - sprint-57-63-plan.md §3 (D1 ctor correction applied) / sprint-57-64-plan.md §3.1
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING
from uuid import UUID

from agent_harness.context_mgmt import Compactor
from agent_harness.context_mgmt.cache_manager import InMemoryCacheManager
from agent_harness.context_mgmt.compactor.chained import ChainedCompactor
from agent_harness.context_mgmt.compactor.hybrid import HybridCompactor
from agent_harness.context_mgmt.compactor.preclear import PreClearCompactor
from agent_harness.context_mgmt.compactor.semantic import SemanticCompactor
from agent_harness.context_mgmt.compactor.structural import StructuralCompactor
from agent_harness.context_mgmt.token_counter.tiktoken_counter import TiktokenCounter
from agent_harness.error_handling import (
    DefaultCircuitBreaker,
    DefaultErrorPolicy,
    DefaultErrorTerminator,
    ErrorPolicy,
    InMemoryBudgetStore,
    RetryPolicyMatrix,
    TenantErrorBudget,
)
from agent_harness.memory import MemoryLayer, MemoryRetrieval
from agent_harness.memory.layers.role_layer import RoleLayer
from agent_harness.memory.layers.session_layer import SessionLayer
from agent_harness.memory.layers.system_layer import SystemLayer
from agent_harness.memory.layers.tenant_layer import TenantLayer
from agent_harness.memory.layers.user_layer import UserLayer
from agent_harness.prompt_builder import PromptBuilder
from agent_harness.prompt_builder.builder import DefaultPromptBuilder
from agent_harness.state_mgmt import (
    Checkpointer,
    DBCheckpointer,
    DBMessageStore,
    DBTodoStore,
    DefaultReducer,
    MessageStore,
    Reducer,
    TodoStore,
)
from agent_harness.subagent import DefaultSubagentDispatcher
from agent_harness.verification import VerifierRegistry
from agent_harness.verification.llm_judge import LLMJudgeVerifier
from infrastructure.db.engine import get_session_factory
from platform_layer.governance.error_budget_provider import maybe_get_budget_store

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from adapters._base.chat_client import ChatClient
    from agent_harness._contracts import (
        ChildLoopFactory,
        TeammateChildLoopFactory,
        TeammateInboxScope,
    )
    from agent_harness.subagent import MailboxStore
    from agent_harness.subagent.dispatcher import SubagentEventEmitter

# Cat 4 budget — defaults mirror AgentLoopImpl default (loop.py:193) so compaction
# triggers at the same threshold the loop reasons about. Sprint 57.109 (C2): the
# env knob lets ops tune the COMPACTION budget independently of the loop budget
# (intentional divergence — e.g. compact earlier on memory-constrained deployments;
# also the drive-through trigger lever). Invalid / unset env → default.
_DEFAULT_CHAT_TOKEN_BUDGET = 100_000
_CHAT_TOKEN_THRESHOLD_RATIO = 0.75


_DEFAULT_KEEP_RECENT_TURNS = 5


def _compaction_token_budget() -> int:
    """Resolve the compaction token budget (CHAT_COMPACTION_TOKEN_BUDGET env knob)."""
    raw = os.environ.get("CHAT_COMPACTION_TOKEN_BUDGET", "")
    try:
        budget = int(raw) if raw else _DEFAULT_CHAT_TOKEN_BUDGET
    except ValueError:
        return _DEFAULT_CHAT_TOKEN_BUDGET
    return budget if budget > 0 else _DEFAULT_CHAT_TOKEN_BUDGET


def _compaction_keep_recent_turns() -> int:
    """Resolve keep_recent_turns (CHAT_COMPACTION_KEEP_RECENT_TURNS env knob).

    57.109 D-DAY3-2: the chat main flow runs ONE user message per loop run
    (continuity lives in Cat 3 memory, not restored history), so the semantic
    cutoff `len(user_indices) > keep_recent_turns` is unreachable at the
    default 5 unless mid-run injection (B1) adds user turns. The knob lets a
    deployment compact more aggressively. Min 1 (a value of 0 would make the
    cutoff index `user_indices[-0]` == `[0]` — a silent full-keep bug)."""
    raw = os.environ.get("CHAT_COMPACTION_KEEP_RECENT_TURNS", "")
    try:
        keep = int(raw) if raw else _DEFAULT_KEEP_RECENT_TURNS
    except ValueError:
        return _DEFAULT_KEEP_RECENT_TURNS
    return keep if keep >= 1 else _DEFAULT_KEEP_RECENT_TURNS


def _compaction_preclear_ratio() -> float:
    """Resolve the ACON tool-result preclear trigger ratio (CHAT_COMPACTION_PRECLEAR_RATIO).

    Sprint 57.139 (#4 layered compaction): when set to a valid (0, 1) value the
    factory prepends a cheap, LLM-free PreClearCompactor (tool-result clearing)
    that fires at this LOWER ratio so the expensive semantic stage may be
    deferred. DEFAULT unset / 0 / invalid → OFF (the factory returns the bare
    HybridCompactor — byte-identical to pre-57.139 behaviour). Evidence-first:
    the harness sets the enable recommendation; default stays OFF.
    """
    raw = os.environ.get("CHAT_COMPACTION_PRECLEAR_RATIO", "")
    try:
        ratio = float(raw) if raw else 0.0
    except ValueError:
        return 0.0
    return ratio if 0.0 < ratio < 1.0 else 0.0


def make_chat_compactor(chat_client: ChatClient) -> Compactor:
    """Cat 4: HybridCompactor (structural-first, semantic fallback).

    D1 (Sprint 57.63 Day 0 drift): HybridCompactor.__init__ is keyword-only and
    the threshold param is `token_threshold_ratio` (NOT `threshold`);
    SemanticCompactor needs keyword `chat_client`; StructuralCompactor() has no
    required deps.

    Sprint 57.109 (C2): `chat_client` is the CHEAP tier (handler passes
    profile.cheap — summarisation is not user-facing reasoning). The budget is
    threaded to BOTH sub-compactors too (57.109 D13: their own defaults happened
    to match the hybrid's, so the gap was invisible until the env knob existed —
    hybrid delegates should_compact to the sub-strategies, so all three must
    agree on the threshold).
    """
    budget = _compaction_token_budget()
    keep_recent = _compaction_keep_recent_turns()
    hybrid = HybridCompactor(
        structural=StructuralCompactor(
            keep_recent_turns=keep_recent,
            token_budget=budget,
            token_threshold_ratio=_CHAT_TOKEN_THRESHOLD_RATIO,
        ),
        semantic=SemanticCompactor(
            chat_client=chat_client,
            keep_recent_turns=keep_recent,
            token_budget=budget,
            token_threshold_ratio=_CHAT_TOKEN_THRESHOLD_RATIO,
        ),
        token_budget=budget,
        token_threshold_ratio=_CHAT_TOKEN_THRESHOLD_RATIO,
    )

    # Sprint 57.139 (#4 layered compaction): when the preclear ratio is enabled,
    # prepend a cheap, LLM-free tool-result clearing layer that fires EARLIER
    # (lower ratio) so the expensive semantic stage in `hybrid` may be deferred.
    # DEFAULT (ratio unset/0) → return the bare hybrid, byte-identical to the
    # pre-57.139 path. The PreClearCompactor counts post-mask tokens with its own
    # TiktokenCounter (the chat-flow counter) so the threaded hybrid sees the
    # real reduction via should_compact.
    preclear_ratio = _compaction_preclear_ratio()
    if preclear_ratio > 0.0:
        return ChainedCompactor(
            compactors=[
                PreClearCompactor(
                    token_counter=TiktokenCounter(model="gpt-4o"),
                    preclear_ratio=preclear_ratio,
                    keep_recent_turns=keep_recent,
                    token_budget=budget,
                ),
                hybrid,
            ]
        )
    return hybrid


def make_chat_prompt_builder(
    chat_client: ChatClient,
    memory_retrieval: MemoryRetrieval | None = None,
) -> PromptBuilder:
    """Cat 5 (KEYSTONE): the centralized DefaultPromptBuilder for the chat path.

    Wiring this into AgentLoopImpl(prompt_builder=...) flips the loop from its
    naked fallback prompt assembly (taken whenever self._prompt_builder is None,
    loop.py:881 false-branch) to the structured 6-section build() that emits
    PromptBuilt and feeds memory layers / cache breakpoints. This closes AP-8
    (no centralized PromptBuilder) on the production main flow.

    Sprint 57.65 (A-1 Tier2 — memory auto-inject): when `memory_retrieval` is
    supplied, the builder renders a per-turn, scope-grouped memory summary block
    (capped ≤2000 tokens) into the prompt and injects verify-before-use rules for
    flagged hints. When None, an empty MemoryRetrieval (no layers) makes
    _inject_memory_layers return {} and the builder still assembles system +
    tools + conversation + user sections — preserving the 57.64 standalone
    behaviour for callers that have no memory deps (echo demo / tests).

    LLM-neutrality: the only LLM-touching dep is the TiktokenCounter (pure
    tokenizer, no provider SDK; used both for the prompt estimate and the Tier2
    memory cap). The ChatClient ABC is accepted for signature parity with the
    other make_chat_* factories; the builder itself issues no provider call. No
    openai / anthropic import here or downstream.

    Args:
        chat_client: the adapter (ChatClient ABC) the loop runs on; accepted for
            signature parity (Cat 5 build() makes no LLM call itself).
        memory_retrieval: the real 5-scope MemoryRetrieval (from
            make_chat_memory_deps) so the prompt and the executor's memory tools
            share ONE retrieval; None preserves the empty-memory standalone path.
    """
    del chat_client  # signature parity; the builder issues no provider call
    return DefaultPromptBuilder(
        memory_retrieval=(
            memory_retrieval if memory_retrieval is not None else MemoryRetrieval(layers={})
        ),
        cache_manager=InMemoryCacheManager(),
        token_counter=TiktokenCounter(model="gpt-4o"),
    )


def make_chat_memory_deps(
    db: AsyncSession | None = None,
) -> tuple[MemoryRetrieval, dict[str, MemoryLayer]]:
    """Cat 3: build the real MemoryRetrieval + 5-scope MemoryLayer map for the chat path.

    Returns (retrieval, layers) ready for
    ``register_builtin_tools(registry, handlers, memory_retrieval=retrieval,
    memory_layers=layers)`` so the chat executor exposes the REAL
    ``memory_search`` / ``memory_write`` handlers (NOT the
    ``memory_placeholder_handler`` fallback — AP-4 Potemkin guard).

    Multi-tenant scoping (per .claude/rules/multi-tenant-data.md 鐵律): tenant_id /
    user_id / session_id are NOT bound here — they arrive per-call via the
    server-authoritative ExecutionContext that AgentLoopImpl builds from the
    request TraceContext (loop.py:1136 reads ctx.tenant_id / ctx.user_id /
    ctx.session_id). Each concrete layer then filters its storage query by
    tenant_id + user_id (UserLayer.read loop.py-equivalent: WHERE tenant_id == ...
    AND user_id == ...). So a tenant A request can never read tenant B rows even
    though the layers are constructed once per request — the scope is the
    request's authenticated identity, supplied at execute() time.

    Layer backends:
      - user / role / tenant / system → PostgreSQL via the module session
        factory (each layer owns its own AsyncSession lifecycle; matches the
        UserLayer(session_factory) ctor). The `db` request session is accepted
        for signature parity / future per-request binding but the layers use
        the shared session factory because they open/commit their own sessions
        (the request `db` is reserved by the StreamingResponse iterator).
      - session → in-memory dict (SessionLayer; per-request instance, no DB).

    Args:
        db: the request AsyncSession (reserved; layers use get_session_factory()).
    """
    del db  # reserved for future per-request session binding; layers self-manage.
    session_factory = get_session_factory()
    layers: dict[str, MemoryLayer] = {
        "system": SystemLayer(session_factory),
        "tenant": TenantLayer(session_factory),
        "role": RoleLayer(session_factory),
        "user": UserLayer(session_factory),
        "session": SessionLayer(),
    }
    retrieval = MemoryRetrieval(layers=layers)
    return retrieval, layers


def make_chat_subagent_dispatcher(
    chat_client: ChatClient,
    *,
    child_loop_factory: ChildLoopFactory | None = None,
    event_emitter: SubagentEventEmitter | None = None,
    teammate_child_loop_factory: TeammateChildLoopFactory | None = None,
    inbox_scope: TeammateInboxScope | None = None,
    mailbox: MailboxStore | None = None,
) -> DefaultSubagentDispatcher:
    """Cat 11 (A-3a): the DefaultSubagentDispatcher for the chat path.

    Wraps the loop's own ChatClient adapter so TEAMMATE single-shot subagents run
    on the SAME provider the parent loop runs on. Sprint 57.94: FORK (and AS_TOOL,
    which delegates to the same ForkExecutor) now runs a REAL child AgentLoop via
    `child_loop_factory` — built at composition where the full Cat 1 dep-set is in
    scope. HANDOFF is intentionally NOT exposed as a chat tool (its executor is a
    hollow stub) — but dispatcher.handoff() remains present.

    Per-request DI (AD-Test-1, 53.6): a fresh dispatcher per chat request — NOT a
    module-level singleton — so its in-flight task map / mailbox are scoped to
    this conversation.

    LLM-neutrality: receives the adapter as the ChatClient ABC; the dispatcher /
    ForkExecutor issue provider calls only through that ABC (the child loop too).
    No openai / anthropic import here or downstream in agent_harness.

    Args:
        chat_client: the adapter (ChatClient ABC) the loop runs on.
        child_loop_factory: builds a fresh child AgentLoop per FORK spawn (Sprint
            57.94). None → FORK fails closed (no single-shot fallback).
        event_emitter: best-effort async sink for SubagentSpawned / SubagentCompleted
            (Sprint 57.95). None → dispatcher emission no-ops (the pre-57.95 chat
            default). The chat router supplies one so the Inspector "Tree" tab shows
            the subagent node instead of "no subagents" (Cat 11 → Cat 12 SSE relay).
    """
    return DefaultSubagentDispatcher(
        chat_client=chat_client,
        child_loop_factory=child_loop_factory,
        event_emitter=event_emitter,
        # Sprint 57.102 (B2a): TEAMMATE now runs a real child loop (mirror FORK) +
        # carries the B1 inbox (Sprint 57.103 B2b: inbox_scope registers the child's
        # queue while it runs, keyed by subagent_id; the chat-user inject is the producer)
        # + a send_to_parent tool; the shared per-request mailbox is threaded so the
        # tool delivery + the executor drain use the SAME instance.
        teammate_child_loop_factory=teammate_child_loop_factory,
        inbox_scope=inbox_scope,
        mailbox=mailbox,
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


def make_chat_message_store(
    db: AsyncSession | None,
    session_id: UUID | None,
    tenant_id: UUID | None,
) -> MessageStore | None:
    """Cat 7: a DBMessageStore (per-session Cat-3 message ledger) when all three
    inputs are present, else None.

    Sprint 57.127 (AD-ChatV2-Live-MultiTurn-Context): the main chat loop self-loads
    prior conversation from + persists new messages to this ledger so a follow-up
    send keeps multi-turn context. Mirrors make_chat_state_deps' all-three-or-nothing
    guard — None on legacy / test callers leaves the loop at single-turn baseline.
    Subagent child loops are built WITHOUT a store (no rehydration / persistence).

    Sprint 57.143 (AD-UserStop-Resume-Context): the store opens its OWN tenant-scoped
    session per load/append (durable appends survive a user-Stop request rollback), so
    it takes the session factory, not the request `db`. `db` is kept only as the
    all-three-present signal (mirrors the memory-layer factories' `del db` precedent).
    """
    if db is None or session_id is None or tenant_id is None:
        return None
    return DBMessageStore(get_session_factory(), session_id=session_id, tenant_id=tenant_id)


def make_chat_todo_store(
    db: AsyncSession | None,
    session_id: UUID | None,
    tenant_id: UUID | None,
) -> TodoStore | None:
    """Cat 7: a DBTodoStore (per-session durable todo list) when all three inputs
    are present, else None.

    Sprint 57.140 (research #1 task primitive): the chat loop's `write_todos` tool
    persists a structured plan here + the loop re-injects it at run-start so a
    follow-up send rehydrates "what's left / what's done". Mirrors
    make_chat_message_store's all-three-or-nothing guard — None on legacy / test
    callers leaves the loop without the task primitive (the agent still works,
    just with no durable plan). Subagent child loops are built WITHOUT a store.
    """
    if db is None or session_id is None or tenant_id is None:
        return None
    return DBTodoStore(db, session_id=session_id, tenant_id=tenant_id)


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

    Budget store: the process-wide store wired at startup (RedisBudgetStore from
    settings.redis_url, _wire_error_budget) via maybe_get_budget_store(); falls
    back to InMemoryBudgetStore when no shared store is wired (dev / test / Redis
    down). Sprint 57.81 (B-7) closed the prior AP-2 gap where this hardcoded a
    fresh InMemoryBudgetStore per request — counters reset every request. The
    TenantErrorBudget wrapper is stateless, so a per-request wrapper over the
    SHARED store accumulates correctly. tenant_id is passed per-call inside the
    loop, NOT at construction. The terminator composes the circuit breaker + error
    budget so all three share one set of counters.
    """
    error_policy: ErrorPolicy = DefaultErrorPolicy()
    retry_policy = RetryPolicyMatrix()
    circuit_breaker = DefaultCircuitBreaker()
    error_budget = TenantErrorBudget(maybe_get_budget_store() or InMemoryBudgetStore())
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

    Unlike a no-op empty-rules RulesBasedVerifier, this registers a real
    `LLMJudgeVerifier` that makes an independent LLM call to judge the chat's
    final output. Fail-closed (any judge error → passed=False).

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
    "make_chat_prompt_builder",
    "make_chat_memory_deps",
    "make_chat_subagent_dispatcher",
    "make_chat_state_deps",
    "make_chat_error_deps",
    "make_chat_verifier_registry",
]
