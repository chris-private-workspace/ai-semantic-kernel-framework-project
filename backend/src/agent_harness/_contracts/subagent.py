"""
File: backend/src/agent_harness/_contracts/subagent.py
Purpose: Single-source subagent types (SubagentBudget / SubagentResult / SubagentMode).
Category: cross-category single-source contracts (per 17.md §1)
Scope: Phase 49 / Sprint 49.1

Description:
    V2 supports 4 subagent dispatch modes (per 11-categories-spec §11):
    fork (parallel) / teammate (mailbox) / handoff (transfer control) /
    as_tool (LLM-callable). Worktree mode is INTENTIONALLY OMITTED — V2
    runs server-side, no per-process git worktree.

    Subagents enforce token / duration / concurrency budgets to prevent
    runaway cost.

Owner: 01-eleven-categories-spec.md §範疇 11
Single-source: 17.md §1.1

Created: 2026-04-29 (Sprint 49.1)
Last Modified: 2026-06-11

Modification History:
    - 2026-06-11: Add TeammateInboxScope (Sprint 57.103 B2b) — lifecycle-scoped teammate inbox
    - 2026-06-11: Add TeammateChildLoopFactory (Sprint 57.102 B2a) — TEAMMATE child loop + B1 inbox
    - 2026-06-09: Add ChildLoopFactory type (Sprint 57.94) — FORK real child loop
    - 2026-05-04: Add AgentSpec dataclass (Sprint 54.2 US-2; needed by AsToolWrapper
      and Phase 55 multi-role subagent registries). Closes Day 0 D7 partial.
    - 2026-04-29: Initial creation (Sprint 49.1)

Related:
    - 01-eleven-categories-spec.md §範疇 11 (Subagent Orchestration)
    - 17-cross-category-interfaces.md §1.1
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable
from uuid import UUID

if TYPE_CHECKING:
    # Type-only reference to the Cat 1 loop ABC for ChildLoopFactory. Guarded so
    # there is NO runtime Cat 11 -> Cat 1 import (loop.py imports these contracts).
    from contextlib import AbstractAsyncContextManager

    from agent_harness._contracts.inbox import MessageInbox
    from agent_harness.orchestrator_loop._abc import AgentLoop


class SubagentMode(Enum):
    """4 subagent dispatch modes. Worktree DELIBERATELY ABSENT."""

    FORK = "fork"  # parallel sub-task; results merged back
    TEAMMATE = "teammate"  # peer-to-peer mailbox communication
    HANDOFF = "handoff"  # transfer control to another agent
    AS_TOOL = "as_tool"  # LLM calls subagent as if it were a tool


@dataclass(frozen=True)
class SubagentBudget:
    """Token / duration / concurrency caps for a subagent invocation."""

    max_tokens: int = 10_000
    max_duration_s: int = 300
    max_concurrent: int = 5
    max_subagent_depth: int = 3  # prevent recursive spawn explosion


@dataclass(frozen=True)
class SubagentResult:
    """Subagent.run() output. Includes mandatory ≤ N-token summary."""

    subagent_id: UUID
    mode: SubagentMode
    success: bool
    summary: str  # MUST be short (≤ 500 tokens by convention)
    full_artifact_pointer: str | None = None  # DB ref for full output
    tokens_used: int = 0
    duration_ms: float = 0.0
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentSpec:
    """Spec for a subagent role; used by AsToolWrapper and TeammateExecutor.

    Sprint 54.2 US-2: minimal fields (role + prompt + model). Phase 55+ may
    extend with allowed tools / memory scopes / risk limits — those are
    role-config concerns NOT covered by Cat 11 dispatcher itself.
    """

    role: str  # short identifier, e.g. "researcher" / "writer"
    prompt: str | None = None  # initial system / role prompt
    model: str | None = None  # provider model id; None = inherit parent's
    metadata: dict[str, Any] = field(default_factory=dict)


# Sprint 57.94 (地基 A payoff): a factory that builds a FRESH child agent loop for
# a FORK / AS_TOOL subagent. It is supplied at composition (build_real_llm_handler)
# where every Cat 1 dep is already in scope; Cat 11 only needs the type to annotate
# the dispatcher / ForkExecutor, so AgentLoop is TYPE_CHECKING-only (no runtime
# Cat 11 -> Cat 1 import). The SubagentBudget arg lets the factory cap the child's
# token_budget per spawn; each call MUST return a NEW loop instance (own session).
ChildLoopFactory = Callable[[SubagentBudget], "AgentLoop"]


# Sprint 57.102 (B2a): a TEAMMATE child loop factory. Like ChildLoopFactory, but the
# teammate child ALSO takes an optional MessageInbox (the B1 between-turns inbox,
# Sprint 57.101) so a mid-run message can reach the teammate at a turn boundary (the
# live producer = B2b). A SEPARATE alias (not an extended ChildLoopFactory) so FORK's
# ChildLoopFactory + every FORK call site stay byte-identical.
TeammateChildLoopFactory = Callable[[SubagentBudget, "MessageInbox | None"], "AgentLoop"]


# Sprint 57.103 (B2b): the lifecycle-scoped teammate inbox. Replaces the B2a sync
# inbox_factory with an async context manager keyed by subagent_id that REGISTERS the
# child's InjectionRegistry queue on enter (so a concurrent chat-user inject POST can
# reach it) and UNREGISTERS it on exit (success / timeout / exception) — so put() can
# tell a live teammate from a finished one (no Potemkin dead queue). The concrete CM
# lives in the api layer (handler builds it over the InjectionRegistry); Cat 11 only
# needs the type to annotate the executor, so AbstractAsyncContextManager + MessageInbox
# are TYPE_CHECKING-only (no runtime Cat 11 -> api / Cat 1 import).
TeammateInboxScope = Callable[[UUID], "AbstractAsyncContextManager[MessageInbox | None]"]
