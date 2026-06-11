"""
File: backend/src/api/v1/chat/sse.py
Purpose: LoopEvent → SSE wire-format serializer (per 02-architecture-design §SSE).
Category: api/v1/chat
Scope: Phase 50 / Sprint 50.2 (Day 1.3)

Description:
    Pure transformation: turns a `LoopEvent` instance into the
    `{event, data}` shape specified in 02-architecture-design.md §SSE.
    `format_sse_message()` then encodes that shape into the SSE wire
    format (`event: ...\\ndata: <json>\\n\\n`).

    Day 2 wiring (after Sprint 50.2 Day 2.4 Loop event additions):
        loop_start          ← LoopStarted        (Cat 1)
        turn_start          ← TurnStarted        (Cat 1, NEW Day 2)
        llm_request         ← LLMRequested       (Cat 1, NEW Day 2)
        llm_response        ← LLMResponded       (Cat 1, NEW Day 2; canonical)
        tool_call_request   ← ToolCallRequested  (Cat 6)
        tool_call_result    ← ToolCallExecuted   (Cat 2; success path)
        tool_call_result    ← ToolCallFailed     (Cat 2; error path)
        loop_end            ← LoopCompleted      (Cat 1)

    `Thinking` (Cat 1) → returns None → router skips: LLMResponded carries
    the same content via the canonical llm_response schema so emitting both
    would duplicate the frame. Thinking event itself stays in 50.1
    test_loop assertions; only the SSE projection drops it.

    All other LoopEvent subclasses (HITL / Guardrails / Verification / etc.)
    are deferred to their owner sprints (53-54) and currently raise
    NotImplementedError with a clear "not in 50.2 scope" message.

Key Components:
    - serialize_loop_event(event) -> dict[str, Any] | None
    - format_sse_message(event_type, data) -> bytes

Created: 2026-04-30 (Sprint 50.2 Day 1.3)
Last Modified: 2026-06-10

Modification History (newest-first):
    - 2026-06-11: Sprint 57.101 B1 — serialize MessageInjected → message_injected (between-turns)
    - 2026-06-10: Sprint 57.100 — approval_requested serializer +kind (pause kind on the wire)
    - 2026-06-09: Sprint 57.96 — serialize SubagentChildEvent → subagent_child (Cat 11 Scope B)
    - 2026-06-03: Sprint 57.75 A-5c — serialize SpanStarted/Ended + MemoryAccessed (3 wire types)
    - 2026-06-02: Sprint 57.68 (A-3b) — serialize AgentHandoff → agent_handoff (Cat 11 HANDOFF)
    - 2026-06-02: FIX-025 — _jsonable: str-coerce UUID only, not float (cache_hit_rate wire type)
    - 2026-06-01: Sprint 57.66 (A-5a+) — serialize 4 diagnostic events + carry 57.65 cache fields
    - 2026-05-10: Sprint 57.12 US-1 — add Subagent SSE mappers (AD-Cat11-SSEEvents)
    - 2026-05-04: Add GuardrailTriggered serializer (Sprint 53.6 D2 — Day 0 探勘)
        — yielded 7× from loop.py (Cat 9 Stage 1/2/3) but missing isinstance
        branch since 53.3 introduced the event. Pre-existing gap that escaped
        53.4 + 53.5 because chat router never wired guardrails. Adding now
        before US-4 production HITL wiring + US-2/US-3 Playwright e2e specs.
    - 2026-05-04: Add HITL approval events (Sprint 53.5 US-2) — ApprovalRequested
        → "approval_requested"; ApprovalReceived → "approval_received". Loop
        emits these when Cat 9 ESCALATE → HITLManager.request_approval +
        wait_for_decision (53.5 _cat9_hitl_branch).
    - 2026-04-30: Wire 3 new Day 2 events + skip-Thinking + ToolCallFailed
        (Sprint 50.2 Day 2.5) — TurnStarted / LLMRequested / LLMResponded;
        Thinking returns None (LLMResponded canonical); ToolCallExecuted
        carries result_content; ToolCallFailed → tool_call_result is_error=True.
    - 2026-04-30: Initial creation (Sprint 50.2 Day 1.3) — 4 50.1-emit events
        serialize; rest raise NotImplementedError with sprint pointer.

Related:
    - 02-architecture-design.md §SSE 事件規範
    - agent_harness/_contracts/events.py (single-source LoopEvent tree)
    - .router (consumes serialize + format)
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any
from uuid import UUID

from agent_harness._contracts import (
    AgentHandoff,
    ApprovalReceived,
    ApprovalRequested,
    ContextCompacted,
    GuardrailTriggered,
    LLMRequested,
    LLMResponded,
    LoopCompleted,
    LoopEvent,
    LoopStarted,
    MemoryAccessed,
    MessageInjected,
    PromptBuilt,
    SpanEnded,
    SpanStarted,
    StateCheckpointed,
    SubagentChildEvent,
    SubagentCompleted,
    SubagentSpawned,
    Thinking,
    ToolCallExecuted,
    ToolCallFailed,
    ToolCallRequested,
    TripwireTriggered,
    TurnStarted,
    VerificationFailed,
    VerificationPassed,
)


def serialize_loop_event(event: LoopEvent) -> dict[str, Any] | None:
    """Map a LoopEvent instance to the SSE event_dict shape per 02.md §SSE.

    Returns a dict with keys ``type`` (SSE event type string) and ``data``
    (dict serializable as JSON, with ``trace_id`` field injected from
    ``event.trace_context``), or None to signal "skip this event" (used
    for Thinking, replaced by LLMResponded in Day 2). Raises
    NotImplementedError for events not yet wired in 50.2 scope.

    Sprint 52.5 P0 #12: ``trace_id`` always present in ``data`` (or None
    if event has no trace_context — should not happen in main flow now
    that chat router always creates a root TraceContext).
    """
    payload = _serialize_inner(event)
    if payload is None:
        return None
    # P0 #12 — inject trace_id into every emitted SSE frame so frontend
    # can correlate live events with backend logs / Jaeger traces.
    trace_ctx = getattr(event, "trace_context", None)
    payload["data"]["trace_id"] = trace_ctx.trace_id if trace_ctx else None
    return payload


def _serialize_inner(event: LoopEvent) -> dict[str, Any] | None:
    """Inner serializer — same logic as before P0 #12, no trace_id injection.

    Pulled out so ``serialize_loop_event`` can wrap it with cross-cutting
    concerns (currently: trace_id injection; future: tenant attribution).
    """
    if isinstance(event, LoopStarted):
        return {
            "type": "loop_start",
            "data": {
                "session_id": str(event.session_id) if event.session_id else None,
                "request_id": str(event.event_id),
            },
        }

    if isinstance(event, TurnStarted):
        return {
            "type": "turn_start",
            "data": {"turn_num": event.turn_num},
        }

    if isinstance(event, LLMRequested):
        return {
            "type": "llm_request",
            "data": {"model": event.model, "tokens_in": event.tokens_in},
        }

    if isinstance(event, LLMResponded):
        # Day 2: canonical llm_response carrier per 02.md §SSE.
        return {
            "type": "llm_response",
            "data": {
                "content": event.content,
                "tool_calls": [
                    {
                        "id": getattr(tc, "id", ""),
                        "name": getattr(tc, "name", ""),
                        "arguments": getattr(tc, "arguments", {}),
                    }
                    for tc in event.tool_calls
                ],
                "thinking": event.thinking,
                # Sprint 57.65 A-2 Tier2 cache field (carried to client).
                "cached_input_tokens": event.cached_input_tokens,
            },
        }

    if isinstance(event, Thinking):
        # Day 2: skip — LLMResponded carries the same content via canonical
        # llm_response. Returning None signals the router to drop the frame.
        return None

    if isinstance(event, ToolCallRequested):
        return {
            "type": "tool_call_request",
            "data": {
                "tool_call_id": event.tool_call_id,
                "tool_name": event.tool_name,
                "args": event.arguments,
            },
        }

    if isinstance(event, ToolCallExecuted):
        return {
            "type": "tool_call_result",
            "data": {
                "tool_call_id": event.tool_call_id,
                "tool_name": event.tool_name,
                "duration_ms": event.duration_ms,
                "result": event.result_content,
                "is_error": False,
            },
        }

    if isinstance(event, ToolCallFailed):
        return {
            "type": "tool_call_result",
            "data": {
                "tool_call_id": event.tool_call_id,
                "tool_name": event.tool_name,
                "duration_ms": 0.0,
                "result": event.error,
                "is_error": True,
            },
        }

    if isinstance(event, LoopCompleted):
        return {
            "type": "loop_end",
            "data": {
                "stop_reason": event.stop_reason,
                "total_turns": event.total_turns,
                # Sprint 57.65 A-2 Tier2 cache fields (carried to client).
                "cached_input_tokens": event.cached_input_tokens,
                "cache_hit_rate": event.cache_hit_rate,
            },
        }

    # Sprint 57.101 B1 (Cat 1): a mid-run injected message DRAINED at a turn
    # boundary (the _run_turns top, before the between-turns guardrail). Fired on
    # drain (proof it landed in the loop), not when the inject POST returned.
    if isinstance(event, MessageInjected):
        return {
            "type": "message_injected",
            "data": {"text": event.text},
        }

    # Sprint 53.5 US-2: HITL approval events. Loop emits ApprovalRequested when
    # Cat 9 ESCALATE → HITLManager.request_approval persists; ApprovalReceived
    # when wait_for_decision returns. Frontend renders inline ApprovalCard.
    if isinstance(event, ApprovalRequested):
        return {
            "type": "approval_requested",
            "data": {
                "approval_request_id": (
                    str(event.approval_request_id) if event.approval_request_id else None
                ),
                "risk_level": event.risk_level,
                "kind": event.kind,
            },
        }

    if isinstance(event, ApprovalReceived):
        return {
            "type": "approval_received",
            "data": {
                "approval_request_id": (
                    str(event.approval_request_id) if event.approval_request_id else None
                ),
                "decision": event.decision,
            },
        }

    # Sprint 53.6 D2: GuardrailTriggered serializer.
    # Yielded 7× from agent_harness/orchestrator_loop/loop.py covering Cat 9
    # Stage 1 (input) / Stage 2 (output) / Stage 3 (tool escalate/reject/timeout
    # block paths). Pre-existing gap from Sprint 53.3 — chat router never wired
    # guardrails before Sprint 53.6 US-4 production HITL wiring would have
    # crashed any chat session that triggered Cat 9 detection.
    if isinstance(event, GuardrailTriggered):
        return {
            "type": "guardrail_triggered",
            "data": {
                "guardrail_type": event.guardrail_type,
                "action": event.action,
                "reason": event.reason,
            },
        }

    # Sprint 57.66 (A-5a+): TripwireTriggered serializer — Cat 9 severe-policy
    # violation that terminates the loop (per 17.md §6). Already yielded on the
    # chat path but previously dropped at the serializer (no isinstance branch).
    if isinstance(event, TripwireTriggered):
        return {
            "type": "tripwire_triggered",
            "data": {
                "violation_type": event.violation_type,
                "detail": event.detail,
            },
        }

    # Sprint 54.1 US-3: Cat 10 verification events.
    # Emitted by the in-loop Cat 10 gate during agent_loop.run() (Sprint 57.98 A1).
    # SSE clients render these next to the LLM final output to surface
    # verification verdict + correction guidance.
    if isinstance(event, VerificationPassed):
        return {
            "type": "verification_passed",
            "data": {
                "verifier": event.verifier,
                "verifier_type": event.verifier_type,
                "score": event.score,
            },
        }

    if isinstance(event, VerificationFailed):
        return {
            "type": "verification_failed",
            "data": {
                "verifier": event.verifier,
                "verifier_type": event.verifier_type,
                "reason": event.reason,
                "suggested_correction": event.suggested_correction,
            },
        }

    # Sprint 57.12 US-1: Cat 11 subagent lifecycle events.
    # Emitted by DefaultSubagentDispatcher.spawn (Spawned at start, Completed
    # when the asyncio.Task resolves). Frontend SubagentTree (US-6) consumes
    # via chatStore.mergeEvent (per CONVENTION.md §7 3-edit checklist).
    if isinstance(event, SubagentSpawned):
        return {
            "type": "subagent_spawned",
            "data": {
                "subagent_id": (str(event.subagent_id) if event.subagent_id else None),
                "mode": event.mode,
                "parent_session_id": (
                    str(event.parent_session_id) if event.parent_session_id else None
                ),
            },
        }

    if isinstance(event, SubagentCompleted):
        return {
            "type": "subagent_completed",
            "data": {
                "subagent_id": (str(event.subagent_id) if event.subagent_id else None),
                "summary": event.summary,
                "tokens_used": event.tokens_used,
            },
        }

    # Sprint 57.96 (Cat 11 Scope B): wraps a child subagent loop's inner TAO
    # event so the chat-v2 Inspector Tree node EXPANDS to the child's per-turn
    # loop. The inner is re-serialized via its OWN branch (recursion reuses the
    # existing per-type serializers) → flattened to {inner_type, inner} where
    # inner is the inner event's `data` dict (a Record on the wire). inner_payload
    # is None only for a non-serializable / Thinking inner (the ForkExecutor TAO
    # filter guarantees a serializable inner; the guard is defensive → skip).
    if isinstance(event, SubagentChildEvent):
        inner_payload = _serialize_inner(event.inner) if event.inner is not None else None
        if inner_payload is None:
            return None
        return {
            "type": "subagent_child",
            "data": {
                "subagent_id": (str(event.subagent_id) if event.subagent_id else None),
                "inner_type": inner_payload["type"],
                "inner": inner_payload["data"],
            },
        }

    # Sprint 57.66 (A-5a+): diagnostic events already yielded on the chat path
    # (Cat 4 context compaction / Cat 5 prompt build / Cat 7 state checkpoint)
    # but previously dropped at the serializer (no isinstance branch). Surfacing
    # them lets the client observe per-turn loop internals without a loop.py edit.
    if isinstance(event, ContextCompacted):
        return {
            "type": "context_compacted",
            "data": {
                "tokens_before": event.tokens_before,
                "tokens_after": event.tokens_after,
                "compaction_strategy": event.compaction_strategy,
                "messages_compacted": event.messages_compacted,
                "duration_ms": event.duration_ms,
            },
        }

    if isinstance(event, PromptBuilt):
        return {
            "type": "prompt_built",
            "data": {
                "messages_count": event.messages_count,
                "estimated_input_tokens": event.estimated_input_tokens,
                "cache_breakpoints_count": event.cache_breakpoints_count,
                # Scope-key names (e.g. ["session", "tenant"]), not memory
                # content — safe to expose. tuple → list for JSON.
                "memory_layers_used": list(event.memory_layers_used),
                "position_strategy_used": event.position_strategy_used,
                "duration_ms": event.duration_ms,
            },
        }

    if isinstance(event, StateCheckpointed):
        return {
            "type": "state_checkpointed",
            "data": {
                "version": event.version,
            },
        }

    # Sprint 57.68 (A-3b): AgentHandoff serializer — Cat 11 HANDOFF control
    # transfer. Emitted by the chat router's post-loop hook AFTER HandoffService
    # boots the child session (so new_session_id is populated). UUIDs → str()
    # for the wire (mirrors SubagentSpawned); trace_id auto-injected by the
    # serialize_loop_event wrapper.
    if isinstance(event, AgentHandoff):
        return {
            "type": "agent_handoff",
            "data": {
                "target_agent": event.target_agent,
                "reason": event.reason,
                "parent_session_id": (
                    str(event.parent_session_id) if event.parent_session_id else None
                ),
                "new_session_id": (str(event.new_session_id) if event.new_session_id else None),
            },
        }

    # Sprint 57.75 (A-5c): Cat 12 span lifecycle events. Emitted by the loop at
    # all 6 span sites (LOOP / TURN / LLM_CALL / TOOL_EXEC / PROMPT_BUILD /
    # COMPACTION). The chat-v2 Inspector Trace tab reconstructs the waterfall from
    # span_id + parent_span_id (indent depth) + span_type (color band); SpanEnded
    # carries the loop-measured duration_ms for the per-row bar. parent_span_id is
    # "" for a root (LOOP) span.
    if isinstance(event, SpanStarted):
        return {
            "type": "span_started",
            "data": {
                "span_name": event.span_name,
                "span_id": event.span_id,
                "parent_span_id": event.parent_span_id,
                "span_type": event.span_type,
            },
        }

    if isinstance(event, SpanEnded):
        return {
            "type": "span_ended",
            "data": {
                "span_name": event.span_name,
                "span_id": event.span_id,
                "span_type": event.span_type,
                "duration_ms": event.duration_ms,
            },
        }

    # Sprint 57.75 (A-5c): Cat 3 memory access. Emitted by the loop per retrieved
    # hint after PromptBuilder.build() (real_llm path only — echo_demo has no
    # prompt_builder so the Memory tab stays honestly empty). `summary` is the
    # hint's capped token-cheap summary (PII-safe); `key` is the content pointer.
    if isinstance(event, MemoryAccessed):
        return {
            "type": "memory_accessed",
            "data": {
                "layer": event.layer,
                "operation": event.operation,
                "key": event.key,
                "summary": event.summary,
                "time_scale": event.time_scale,
            },
        }

    raise NotImplementedError(
        f"SSE serialization for {type(event).__name__} is not in Sprint 50.2 scope."
        " See sprint-50-2-plan.md §3.2 deferred / 02-architecture-design.md §SSE for owner sprint."
    )


def format_sse_message(event_type: str, data: dict[str, Any]) -> bytes:
    """Encode an SSE message frame: ``event: <type>\\ndata: <json>\\n\\n``."""
    payload = json.dumps(_jsonable(data), ensure_ascii=False, separators=(",", ":"))
    return f"event: {event_type}\ndata: {payload}\n\n".encode("utf-8")


def _jsonable(value: Any) -> Any:
    """Recursively coerce dataclasses + UUIDs to JSON-friendly forms."""
    if is_dataclass(value) and not isinstance(value, type):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    # datetime → ISO string; UUID → canonical hyphenated string.
    if hasattr(value, "isoformat"):  # datetime
        return value.isoformat()
    # FIX-025: match UUID explicitly. The prior `hasattr(value, "hex")` heuristic
    # also matched float (float.hex exists) + bool, stringifying them — so float
    # wire fields (cache_hit_rate / duration_ms) were emitted as JSON strings.
    if isinstance(value, UUID):
        return str(value)
    return value
