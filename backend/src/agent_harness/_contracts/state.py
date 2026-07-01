"""
File: backend/src/agent_harness/_contracts/state.py
Purpose: Single-source loop state types (LoopState / TransientState / DurableState).
Category: cross-category single-source contracts (per 17.md §1)
Scope: Phase 49 / Sprint 49.1

Description:
    Splits loop state into transient (in-memory, recreatable) vs durable
    (DB-persisted) per Phase 53.1 design. Reducer in category 7 is the
    only mutator; categories 1-11 read from these types but mutate via
    Reducer.

Key Components:
    - TransientState: messages buffer / pending tool_calls / metrics-in-flight / injected_memory
    - DurableState: pending approvals / checkpoints / conversation summary
    - LoopState: composite (transient + durable + tenant context)
    - StateVersion: monotonic version for time-travel + Reducer correctness

Owner: 01-eleven-categories-spec.md §範疇 7
Single-source: 17.md §1.1

Created: 2026-04-29 (Sprint 49.1)
Last Modified: 2026-07-01

Modification History:
    - 2026-07-01: Sprint 57.153 — add TransientState.injected_memory (memory-aware judge grounding)
    - 2026-04-29: Initial creation (Sprint 49.1)

Related:
    - 01-eleven-categories-spec.md §範疇 7 (State Mgmt)
    - 17-cross-category-interfaces.md §1 (LoopState single-source)
    - 12-category-contracts.md (Reducer contract)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from agent_harness._contracts.chat import Message


@dataclass(frozen=True)
class StateVersion:
    """Monotonic state version for time-travel and Reducer ordering."""

    version: int
    parent_version: int | None
    created_at: datetime
    created_by_category: str  # e.g. "orchestrator_loop", "tools", "reducer"


@dataclass
class TransientState:
    """In-memory loop state; recreatable from DurableState if process dies."""

    messages: list[Message] = field(default_factory=list)
    pending_tool_calls: list[Any] = field(default_factory=list)  # ToolCall
    current_turn: int = 0
    elapsed_ms: float = 0.0
    token_usage_so_far: int = 0
    # Sprint 57.153 (AD-Verification-Judge-Memory-Inject-Blind): the memory injected
    # into THIS turn's prompt (the rendered 57.148 profile() / 57.151 recent_sessions()
    # block), captured so the in-loop Cat 10 judge can read what grounded the agent and
    # NOT false-positive-reject a memory-grounded recall as fabrication. The injected
    # memory lives in the per-turn PromptBuilder artifact (system prompt), never in
    # `messages`, and build_trace_block drops system messages — so the verify gate's
    # throwaway trace_state carries it here instead. None/"" = no grounding shown (the
    # naked-fallback / echo path, or the memory-grounding lever OFF) → judge byte-identical
    # to pre-57.153. Set only on the gate's throwaway snapshot (no Reducer involved).
    injected_memory: str | None = None


@dataclass
class DurableState:
    """DB-persisted state; survives process death + cross-session resume."""

    session_id: UUID
    tenant_id: UUID
    user_id: UUID | None = None
    pending_approval_ids: list[UUID] = field(default_factory=list)
    last_checkpoint_version: int = 0
    conversation_summary: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LoopState:
    """Top-level state. Composed of transient + durable + version."""

    transient: TransientState
    durable: DurableState
    version: StateVersion
