"""
File: backend/src/api/v1/chat/event_wire_schema.py
Purpose: Declarative single-source wire-schema for the 25 chat SSE event types.
Category: api/v1/chat
Scope: Phase 57 / Sprint 57.67 (A-5b — event schema codegen)

Description:
    The authoritative, machine-readable contract for every event the chat SSE
    stream emits. It is authored from the SERIALIZER's hand-built `data` dict
    in `sse.py:serialize_loop_event`/`_serialize_inner` (NOT from the dataclass
    fields, which diverge — `arguments`→`args`, `result_content`→`result`, base
    fields dropped, `trace_id`/`is_error` added).

    This module is PURE STDLIB (dict + small helper). It is intentionally free
    of `agent_harness` / `sqlalchemy` / any heavy import so the codegen and the
    CI parity lint can load it by file path alone (via
    `importlib.util.spec_from_file_location`) without installing the backend
    package. Two downstream consumers read `WIRE_SCHEMA` + `BASE_FIELDS`:
      1. `scripts/codegen/generate_event_schemas.py` — generates the frontend
         `events.json` snapshot + `loopEvents.generated.ts` interfaces.
      2. `backend/tests/.../test_event_wire_schema_parity.py` — asserts the
         registry field set matches the live serializer output (drift guard).

    Field NAME + SET are authoritative from `sse.py` (minus `trace_id`, which is
    universal — injected by the `serialize_loop_event` wrapper at sse.py:116 and
    declared once in `BASE_FIELDS`). Field TS TYPE strings are authoritative from
    `frontend/src/features/chat_v2/types.ts` (reproduced verbatim).

Key Components:
    - WIRE_SCHEMA: 25 ordered wire-type → ordered {field: ts_type} entries.
    - BASE_FIELDS: universal fields the wrapper adds to every frame (trace_id).
    - TOOL_CALL_ELEMENT_TYPE_NAME / TOOL_CALL_ELEMENT_FIELDS: the named
      `tool_calls` element TS type (mirrors types.ts `LLMToolCall`).
    - validate_ts_type(spec): pragmatic TS-type-string sanity check.

Created: 2026-06-02 (Sprint 57.67)
Last Modified: 2026-06-16

Modification History (newest-first):
    - 2026-06-16: Sprint 57.130 — add loop_terminated wire-type (Cat 8 fatal-terminate) 24→25
    - 2026-06-14: Sprint 57.116 — loop_start +active_skill field (count 24 unchanged)
    - 2026-06-12: Sprint 57.108 — approval_requested +tool_name/reason; llm_response +in/out tokens
    - 2026-06-11: Sprint 57.101 — add message_injected wire-type (Cat 1 injection) 23→24
    - 2026-06-10: Sprint 57.100 — approval_requested +kind field (no new wire-type; 22 unchanged)
    - 2026-06-09: Sprint 57.96 — add subagent_child wire-type (Cat 11 Scope B turn-stream) 22→23
    - 2026-06-03: Sprint 57.75 A-5c — add span_started/span_ended/memory_accessed wire-types 19→22
    - 2026-06-02: Sprint 57.68 A-3b — add agent_handoff wire-type (Cat 11 HANDOFF) 18→19
    - 2026-06-02: Initial creation (Sprint 57.67 A-5b) — declarative wire-schema registry

Related:
    - backend/src/api/v1/chat/sse.py (serialize_loop_event — field-name/set ground truth)
    - frontend/src/features/chat_v2/types.ts (TS-type ground truth)
    - scripts/codegen/generate_event_schemas.py (codegen consumer)
    - 02-architecture-design.md §SSE 事件規範
    - 17-cross-category-interfaces.md §4 (LoopEvent table)
"""

from __future__ import annotations

# === BASE_FIELDS: universal frame fields ====================================
# Why: `serialize_loop_event` (sse.py:116) injects `trace_id` into EVERY frame's
# `data` dict after the per-event inner serializer runs. Declaring it once here
# (instead of in each of the 18 entries) keeps WIRE_SCHEMA aligned 1:1 with the
# inner serializer branches and lets the codegen prepend it uniformly.
BASE_FIELDS: dict[str, str] = {"trace_id": "string | null"}


# === tool_calls element type ================================================
# Why: the `llm_response` event's `tool_calls` field is an array of a structured
# object. types.ts models this as a NAMED type `LLMToolCall` so the generated
# .ts is self-contained. We mirror that name + field shape here; the codegen
# emits the `LLMToolCall` interface and references it as `LLMToolCall[]`.
TOOL_CALL_ELEMENT_TYPE_NAME: str = "LLMToolCall"
TOOL_CALL_ELEMENT_FIELDS: dict[str, str] = {
    "id": "string",
    "name": "string",
    "arguments": "Record<string, unknown>",
}


# === WIRE_SCHEMA: 25 ordered wire-type entries ==============================
# Why: single declarative source of truth for the SSE event contract. Insertion
# order of the outer dict = generated interface declaration order; insertion
# order of each inner dict = generated interface FIELD order. Field NAME/SET is
# authoritative from sse.py `_serialize_inner` (minus trace_id); field TS TYPE
# is authoritative from types.ts (e.g. verification score/reason nullability,
# verifier_type union, tool_calls element shape).
WIRE_SCHEMA: dict[str, dict[str, str]] = {
    "loop_start": {
        "session_id": "string | null",
        "request_id": "string",
        # Sprint 57.116: the server-confirmed force-load skill name (or null).
        # Additive field on an existing type — the 24 wire-TYPE count is unchanged.
        "active_skill": "string | null",
    },
    "turn_start": {
        "turn_num": "number",
    },
    "llm_request": {
        "model": "string",
        "tokens_in": "number",
    },
    "llm_response": {
        "content": "string",
        "tool_calls": "LLMToolCall[]",
        "thinking": "string | null",
        "cached_input_tokens": "number",
        "input_tokens": "number",
        "output_tokens": "number",
    },
    "tool_call_request": {
        "tool_call_id": "string",
        "tool_name": "string",
        "args": "Record<string, unknown>",
    },
    "tool_call_result": {
        "tool_call_id": "string",
        "tool_name": "string",
        "duration_ms": "number",
        "result": "string",
        "is_error": "boolean",
    },
    "loop_end": {
        "stop_reason": "string",
        "total_turns": "number",
        "cached_input_tokens": "number",
        "cache_hit_rate": "number",
    },
    "approval_requested": {
        "approval_request_id": "string | null",
        "risk_level": "string",
        "kind": "string",
        "tool_name": "string | null",
        "reason": "string",
    },
    "approval_received": {
        "approval_request_id": "string | null",
        "decision": "string",
    },
    "guardrail_triggered": {
        "guardrail_type": "string",
        "action": "string",
        "reason": "string",
    },
    "tripwire_triggered": {
        "violation_type": "string",
        "detail": "string",
    },
    "verification_passed": {
        "verifier": "string",
        "verifier_type": '"rules_based" | "llm_judge" | "external"',
        "score": "number | null",
    },
    "verification_failed": {
        "verifier": "string",
        "verifier_type": '"rules_based" | "llm_judge" | "external"',
        "reason": "string | null",
        "suggested_correction": "string | null",
    },
    "subagent_spawned": {
        "subagent_id": "string | null",
        "mode": "string",
        "parent_session_id": "string | null",
    },
    "subagent_completed": {
        "subagent_id": "string | null",
        "summary": "string",
        "tokens_used": "number",
    },
    # Sprint 57.96 (Cat 11 Scope B): a child subagent loop's inner TAO event,
    # tagged by subagent_id so the chat-v2 Inspector Tree node expands to the
    # child's per-turn loop. `inner_type` is the inner event's wire type (e.g.
    # "llm_response" / "tool_call_request"); `inner` is that inner event's `data`
    # dict (an opaque Record on the wire — the store projects it per inner_type).
    "subagent_child": {
        "subagent_id": "string | null",
        "inner_type": "string",
        "inner": "Record<string, unknown>",
    },
    "context_compacted": {
        "tokens_before": "number",
        "tokens_after": "number",
        "compaction_strategy": "string",
        "messages_compacted": "number",
        "duration_ms": "number",
    },
    "prompt_built": {
        "messages_count": "number",
        "estimated_input_tokens": "number",
        "cache_breakpoints_count": "number",
        "memory_layers_used": "string[]",
        "position_strategy_used": "string",
        "duration_ms": "number",
    },
    "state_checkpointed": {
        "version": "number",
    },
    "agent_handoff": {
        "target_agent": "string",
        "reason": "string",
        "parent_session_id": "string",
        "new_session_id": "string",
    },
    # Sprint 57.75 (A-5c): Cat 12 span lifecycle + Cat 3 memory access — feed the
    # chat-v2 Inspector Trace + Memory tabs. parent_span_id is "" for a root span;
    # span_type ∈ {LOOP,TURN,LLM_CALL,TOOL_EXEC,PROMPT_BUILD,COMPACTION}.
    "span_started": {
        "span_name": "string",
        "span_id": "string",
        "parent_span_id": "string",
        "span_type": "string",
    },
    "span_ended": {
        "span_name": "string",
        "span_id": "string",
        "span_type": "string",
        "duration_ms": "number",
    },
    "memory_accessed": {
        "layer": "string",
        "operation": "string",
        "key": "string",
        "summary": "string",
        "time_scale": "string",
    },
    # Sprint 57.101 B1 (Cat 1): a mid-run injected message drained at a turn boundary.
    "message_injected": {
        "text": "string",
    },
    # Sprint 57.130 (Cat 8): a fatal terminate (ErrorTerminator) — surfaced so the
    # chat-v2 UI shows a terminal reason + clears a stuck pending tool chip.
    "loop_terminated": {
        "reason": "string",
        "detail": "string | null",
        "last_state_version": "number | null",
    },
}


# === TS-type validation =====================================================
# Why: a pragmatic typo guard only. tsc + the pytest parity test are the real
# contract guards; this catches obviously-malformed type strings at codegen time
# so a fat-fingered entry fails loud instead of emitting broken .ts. The named
# `tool_calls` element array (`LLMToolCall[]`) and the literal-union verifier
# type are passed through (documented complex types), not rejected.
_RECOGNIZED_TS_TYPES: frozenset[str] = frozenset(
    {
        "string",
        "number",
        "boolean",
        "string[]",
        "number[]",
        "string | null",
        "number | null",
        "Record<string, unknown>",
    }
)

# Documented passthrough types — complex/nested shapes the codegen emits as-is.
_PASSTHROUGH_TS_TYPES: frozenset[str] = frozenset(
    {
        f"{TOOL_CALL_ELEMENT_TYPE_NAME}[]",
        '"rules_based" | "llm_judge" | "external"',
    }
)


def validate_ts_type(spec: str) -> str:
    """Validate (pragmatically) a WIRE_SCHEMA TS-type string; return it unchanged.

    Raises ValueError on an obviously-malformed spec (empty / blank /
    unbalanced angle braces). Recognized-vocabulary and documented-passthrough
    types pass; anything else still passes (tsc is the real guard) UNLESS it is
    structurally broken. Pragmatic by design — catches typos, not type errors.
    """
    if not spec or not spec.strip():
        raise ValueError("TS type spec must be a non-empty string")
    if spec.count("<") != spec.count(">"):
        raise ValueError(f"Unbalanced angle braces in TS type spec: {spec!r}")
    if spec in _RECOGNIZED_TS_TYPES or spec in _PASSTHROUGH_TS_TYPES:
        return spec
    # Unknown but structurally-sound type strings are allowed through; tsc + the
    # parity test will catch a genuinely-wrong type. We only hard-fail on the
    # malformed cases above.
    return spec
