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
Last Modified: 2026-05-10

Modification History (newest-first):
    - 2026-05-10: Sprint 57.12 US-1 — add SubagentSpawned/Completed mappers (closes AD-Cat11-SSEEvents)
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

from agent_harness._contracts import (
    ApprovalReceived,
    ApprovalRequested,
    GuardrailTriggered,
    LLMRequested,
    LLMResponded,
    LoopCompleted,
    LoopEvent,
    LoopStarted,
    SubagentCompleted,
    SubagentSpawned,
    Thinking,
    ToolCallExecuted,
    ToolCallFailed,
    ToolCallRequested,
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
            },
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

    # Sprint 54.1 US-3: Cat 10 verification events.
    # Emitted by run_with_verification() wrapper after agent_loop.run() completes.
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
                "subagent_id": (
                    str(event.subagent_id) if event.subagent_id else None
                ),
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
                "subagent_id": (
                    str(event.subagent_id) if event.subagent_id else None
                ),
                "summary": event.summary,
                "tokens_used": event.tokens_used,
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
    # uuid.UUID, datetime, etc. — fall back to str repr
    if hasattr(value, "isoformat"):  # datetime
        return value.isoformat()
    if hasattr(value, "hex") and not isinstance(value, (bytes, bytearray, str, int)):
        return str(value)  # UUID
    return value
