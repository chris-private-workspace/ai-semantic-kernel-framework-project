"""
File: backend/src/agent_harness/_contracts/events.py
Purpose: Single-source LoopEvent type tree (22 subclasses per 17.md §4).
Category: cross-category single-source contracts (per 17.md §1)
Scope: Phase 49 / Sprint 49.1

Description:
    AgentLoop.run() yields AsyncIterator[LoopEvent]. Different categories
    emit different subclasses (e.g. category 6 emits ToolCallRequested,
    category 2 emits ToolCallExecuted). API / SSE handlers consume the
    stream.

Key Components:
    - LoopEvent: abstract base (timestamp + trace_context)
    - 22 concrete subclasses (one per emit point in 17.md §4.1)

Sync callbacks NOT supported (per 17.md §4.2 — Anti-Pattern 11).

Owner: 01-eleven-categories-spec.md §範疇 1
Single-source: 17.md §4.1

Created: 2026-04-29 (Sprint 49.1)
Last Modified: 2026-04-29

Modification History (newest-first):
    - 2026-06-02: Sprint 57.69 A-3b — add LoopCompleted.handoff_context (in-process carry)
    - 2026-06-02: Sprint 57.68 A-3b — add AgentHandoff event + LoopCompleted.handoff_target/reason
    - 2026-06-01: Sprint 57.65 A-2 — add cached_input_tokens + cache_hit_rate (prompt-cache obs)
    - 2026-04-30: Add 3 new Cat 1-owned events (Sprint 50.2 Day 2.2) —
        TurnStarted / LLMRequested / LLMResponded for per-turn SSE granularity.
        Extend ToolCallExecuted with `result_content: str = ""` so tool result
        text reaches frontend (backward-compatible default).
    - 2026-04-30: Fix `datetime.utcnow()` → `datetime.now(UTC)` (Sprint 50.2 Day 0
        CARRY-002) — clears 28+ DeprecationWarning emitted per loop test run.
    - 2026-04-29: Initial creation (Sprint 49.1) — 22 stub subclasses

Related:
    - 01-eleven-categories-spec.md §範疇 1
    - 17-cross-category-interfaces.md §4 (LoopEvent table)
    - 02-architecture-design.md §SSE 事件規範
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from agent_harness._contracts.chat import Message
from agent_harness._contracts.observability import TraceContext


@dataclass(frozen=True)
class LoopEvent:
    """Abstract base. Concrete subclasses are emitted by specific categories."""

    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    trace_context: TraceContext | None = None


# === Category 1: Orchestrator Loop ===========================================


@dataclass(frozen=True)
class LoopStarted(LoopEvent):
    session_id: UUID | None = None


@dataclass(frozen=True)
class TurnStarted(LoopEvent):
    """Emitted by Cat 1 at the top of each TAO loop iteration. (Sprint 50.2)"""

    turn_num: int = 0


@dataclass(frozen=True)
class LLMRequested(LoopEvent):
    """Emitted by Cat 1 immediately before chat_client.chat(). (Sprint 50.2)

    `tokens_in` is the prompt token count if available (best-effort; 0 when
    Loop hasn't yet wired count_tokens()).
    """

    model: str = ""
    tokens_in: int = 0


@dataclass(frozen=True)
class LLMResponded(LoopEvent):
    """Emitted by Cat 1 after parser.parse(response). (Sprint 50.2)

    Carries the canonical (content, tool_calls, thinking) tuple per
    02-architecture-design.md §SSE `llm_response` schema. Replaces SSE-level
    Thinking in 50.2; Thinking event itself stays for 50.1 test backward-compat.

    Sprint 57.2 US-1+US-2 bundled (AD-Cost-Ledger-Token-Split + Provider-Attribution):
    `provider / model / input_tokens / output_tokens` carry per-call metadata
    sourced from ChatResponse.model + ChatResponse.usage.{prompt,completion}_tokens.
    LoopMetricsAccumulator consumes per-event for LoopCompleted aggregation.
    """

    content: str = ""
    tool_calls: tuple[Any, ...] = field(default_factory=tuple)  # tuple[ToolCall, ...]
    thinking: str | None = None
    # Sprint 57.2 US-1+US-2 bundled: per-call metadata
    provider: str = ""
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    # Sprint 57.65 A-2 Tier2: prompt-cache observability. Neutral cached-input
    # token count sourced from TokenUsage.cached_input_tokens (Azure
    # prompt_tokens_details.cached_tokens). LoopMetricsAccumulator sums this
    # per-event so LoopCompleted can report a cache-hit-rate. Default 0 covers
    # providers/turns with no cache hit.
    cached_input_tokens: int = 0


@dataclass(frozen=True)
class Thinking(LoopEvent):
    text: str = ""


@dataclass(frozen=True)
class LoopCompleted(LoopEvent):
    stop_reason: str = "end_turn"
    total_turns: int = 0
    # Sprint 56.2 US-3: cumulative total_tokens (input + output) across all
    # LLM calls in this loop run, sourced from ChatResponse.usage.total_tokens
    # accumulator (loop.py L944). Default 0 covers early-termination paths
    # before any LLM call (input guardrail block / tripwire). Consumed by
    # chat router to reconcile QuotaEnforcer reservation post-loop.
    total_tokens: int = 0
    # Sprint 57.2 US-1+US-2 bundled (AD-Cost-Ledger-Token-Split +
    # Provider-Attribution + Cat10-Cat11-LoopMetricsAccumulator):
    # accumulator-sourced cumulative split + dominant provider/model.
    # input_tokens + output_tokens = total_tokens (invariant). provider/
    # model from last LLM call (most-recent-wins for multi-model loops;
    # majority of loops use single model so this is dominant attribution).
    # Default empty/0 covers early-termination paths.
    input_tokens: int = 0
    output_tokens: int = 0
    provider: str = ""
    model: str = ""
    # Sprint 57.65 A-2 Tier2 (prompt-cache observability): accumulator-sourced
    # cumulative cached-input tokens across the loop + the derived cache-hit
    # rate (cached_input_tokens / input_tokens; 0.0 when input_tokens == 0,
    # div-by-0 guarded). Cat 12 consumes these off the event (no separate
    # Tracer/MetricsRegistry — loop metrics travel as LoopCompleted fields).
    # Default 0 / 0.0 covers early-termination paths before any LLM call.
    cached_input_tokens: int = 0
    cache_hit_rate: float = 0.0
    # Sprint 57.68 A-3b (HANDOFF control transfer): when a HANDOFF output ends
    # the parent loop, stop_reason="handoff" and these carry the parsed target
    # agent + reason out to the platform layer (router post-loop hook → session
    # boot). Default None covers every non-handoff termination path.
    handoff_target: str | None = None
    handoff_reason: str | None = None
    # Sprint 57.69 A-3b slice 2 (HANDOFF agent-side context carry): in-process
    # snapshot of the parent's in-memory conversation at HANDOFF, carried to the
    # platform layer (router post-loop hook -> boot_handoff) to seed the child with
    # the prior conversation. NOT in the loop_end wire schema (sse.py maps 4 fields)
    # -> server-side only. Default None covers non-handoff terminations.
    handoff_context: list[Message] | None = None


# === Category 6: Output Parser ==============================================


@dataclass(frozen=True)
class ToolCallRequested(LoopEvent):
    tool_call_id: str = ""
    tool_name: str = ""
    arguments: dict[str, Any] = field(default_factory=dict)


# === Category 2: Tools ======================================================


@dataclass(frozen=True)
class ToolCallExecuted(LoopEvent):
    tool_call_id: str = ""
    tool_name: str = ""
    duration_ms: float = 0.0
    result_content: str = ""  # Sprint 50.2: tool output text (default empty for backward compat)


@dataclass(frozen=True)
class ToolCallFailed(LoopEvent):
    tool_call_id: str = ""
    tool_name: str = ""
    error: str = ""


# === Category 3: Memory =====================================================


@dataclass(frozen=True)
class MemoryAccessed(LoopEvent):
    layer: str = ""  # system / tenant / role / user / session
    operation: str = ""  # read / write / evict
    key: str = ""


# === Category 4: Context Mgmt ==============================================


@dataclass(frozen=True)
class ContextCompacted(LoopEvent):
    tokens_before: int = 0
    tokens_after: int = 0
    compaction_strategy: str = ""
    messages_compacted: int = 0  # 52.1 Day 2.7 — compaction observability payload
    duration_ms: float = 0.0  # 52.1 Day 2.7 — compaction observability payload


# === Category 5: Prompt Builder =============================================


@dataclass(frozen=True)
class PromptBuilt(LoopEvent):
    """Emitted by Cat 1 Loop after Cat 5 PromptBuilder.build() each turn.

    Sprint 52.2 Day 3.3: full payload schema per plan §2.7 + §3.3:
      - messages_count: artifact.messages length
      - estimated_input_tokens: artifact.estimated_input_tokens (Cat 4 token_counter)
      - cache_breakpoints_count: artifact.cache_breakpoints length
      - memory_layers_used: artifact.layer_metadata["memory_layers_used"]
      - position_strategy_used: artifact.layer_metadata["position_strategy"]
      - duration_ms: build() wall-clock duration

    Frozen tuple (not list) for memory_layers_used so the dataclass remains
    hashable / immutable per LoopEvent base contract.
    """

    messages_count: int = 0
    estimated_input_tokens: int = 0
    cache_breakpoints_count: int = 0
    memory_layers_used: tuple[str, ...] = ()
    position_strategy_used: str = ""
    duration_ms: float = 0.0


# === Category 7: State Mgmt =================================================


@dataclass(frozen=True)
class StateCheckpointed(LoopEvent):
    version: int = 0


# === Category 8: Error Handling =============================================


@dataclass(frozen=True)
class ErrorRetried(LoopEvent):
    attempt: int = 0
    error_class: str = ""
    backoff_ms: float = 0.0


@dataclass(frozen=True)
class LoopTerminated(LoopEvent):
    """Loop ended early via Cat 8 ErrorTerminator (NOT Cat 9 Tripwire).

    Reasons (TerminationReason): budget_exceeded / circuit_open /
    fatal_exception / max_retries_exhausted. Per 17.md §6 boundary,
    Tripwire violations are emitted by GuardrailTriggered (Cat 9), not
    here.
    """

    reason: str = ""
    detail: str | None = None
    last_state_version: int | None = None


# === Category 9: Guardrails =================================================


@dataclass(frozen=True)
class GuardrailTriggered(LoopEvent):
    guardrail_type: str = ""  # input / output / tool
    action: str = ""  # block / sanitize / escalate / reroll
    reason: str = ""


@dataclass(frozen=True)
class TripwireTriggered(LoopEvent):
    """Severe policy violation — terminates loop immediately (per 17.md §6)."""

    violation_type: str = ""
    detail: str = ""


# === Category 10: Verification ==============================================


@dataclass(frozen=True)
class VerificationPassed(LoopEvent):
    """Sprint 54.1: extended with optional score / verifier_type for SSE clients.

    All new fields are optional with defaults — backward compatible with the
    49.1 stub (single `verifier` field).
    """

    verifier: str = ""
    score: float | None = None
    verifier_type: str = ""  # "rules_based" / "llm_judge" / "external"


@dataclass(frozen=True)
class VerificationFailed(LoopEvent):
    """Sprint 54.1: extended with optional reason / suggested_correction / verifier_type.

    All new fields are optional with defaults — backward compatible with the
    49.1 stub (single `verifier` field).
    """

    verifier: str = ""
    reason: str | None = None
    suggested_correction: str | None = None
    verifier_type: str = ""
    correction_attempt: int = 0


# === Category 11: Subagent ==================================================


@dataclass(frozen=True)
class SubagentSpawned(LoopEvent):
    subagent_id: UUID | None = None
    mode: str = ""  # fork / teammate / handoff / as_tool
    parent_session_id: UUID | None = None


@dataclass(frozen=True)
class SubagentCompleted(LoopEvent):
    subagent_id: UUID | None = None
    summary: str = ""
    tokens_used: int = 0


@dataclass(frozen=True)
class AgentHandoff(LoopEvent):
    """Sprint 57.68 A-3b (Cat 11 HANDOFF): control-transfer event emitted by the
    platform layer AFTER a child session is booted for the target agent (so
    new_session_id is populated). Carries enough for the client to later pivot.

    Defined here (single-source LoopEvent tree); the SSE wire registration +
    serializer branch are Stage-2 work (event_wire_schema.py / sse.py).
    """

    target_agent: str = ""
    reason: str = ""
    parent_session_id: UUID | None = None
    new_session_id: UUID | None = None


# === HITL Centralization ====================================================


@dataclass(frozen=True)
class ApprovalRequested(LoopEvent):
    approval_request_id: UUID | None = None
    risk_level: str = ""


@dataclass(frozen=True)
class ApprovalReceived(LoopEvent):
    approval_request_id: UUID | None = None
    decision: str = ""  # APPROVED / REJECTED / ESCALATED


# === Category 12: Observability ============================================


@dataclass(frozen=True)
class SpanStarted(LoopEvent):
    span_name: str = ""
    span_id: str = ""


@dataclass(frozen=True)
class SpanEnded(LoopEvent):
    span_name: str = ""
    span_id: str = ""
    duration_ms: float = 0.0


@dataclass(frozen=True)
class MetricRecorded(LoopEvent):
    metric_name: str = ""
    value: float = 0.0
    labels: dict[str, str] = field(default_factory=dict)
