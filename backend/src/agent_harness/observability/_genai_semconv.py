"""
File: backend/src/agent_harness/observability/_genai_semconv.py
Purpose: Pure bespoke→CNCF OpenTelemetry GenAI semantic-conventions span/attr mapping.
Category: 範疇 12 (Observability — cross-cutting)
Scope: Phase 57 / Sprint 57.142

Description:
    V2's loop emits OTel spans with BESPOKE names (`agent_loop.llm_call`) + attribute
    keys (`span_type` / `model` / `prompt_tokens`). This module translates the
    GenAI-relevant ones to the CNCF GenAI semantic conventions (`gen_ai.*`) so V2
    telemetry flows into any GenAI-aware APM without a bespoke adapter (closes
    research #5 `AD-Observability-OTel-GenAI-Schema`).

    The translation runs ONLY inside `OTelTracer._span_cm` (the single bespoke→OTel
    boundary) — so the INTERNAL view (loop.py emits, NoOp/RecordingTracer in tests
    see) stays bespoke, while the EXPORTED view (real OTel span) is `gen_ai.*`. This
    dual-view contract keeps loop.py + existing observability tests untouched.

Key Components:
    - STOP_REASON_TO_FINISH_REASON: provider-neutral StopReason.value → CNCF finish_reason
    - SPAN_TYPE_TO_OPERATION: bespoke span_type → gen_ai.operation.name
    - ATTR_MAP: bespoke attr key → gen_ai.* key (simple renames)
    - to_genai_span(): pure (name, attrs) → (mapped_name, mapped_attrs)
    - assert_genai_conformant(): conformance checker (returns violations; [] = conformant)

Pinned CNCF GenAI semconv snapshot: 2026-06-25 stable subset (operation.name /
    request.model / usage.input_tokens / usage.output_tokens / response.finish_reasons /
    tool.name). `gen_ai.provider.name` + content capture deferred (see design note 46).

Created: 2026-06-25 (Sprint 57.142)
Last Modified: 2026-06-25

Modification History (newest-first):
    - 2026-06-25: Initial creation (Sprint 57.142) — research #5 OTel GenAI mapping

Related:
    - tracer.py — OTelTracer._span_cm applies this at span start + close
    - 17-cross-category-interfaces.md §Contract 12 — Tracer ABC (unchanged; schema = values)
    - 46-otel-genai-semconv-design.md — design note (pinned snapshot + dual-view contract)
    - _contracts/chat.py StopReason — source enum for finish_reasons
"""

from __future__ import annotations

from typing import Any

# === CNCF GenAI semantic-convention attribute keys (pinned stable subset) ===
# Why these as named constants: re-used by the conformance harness + tests so a
# key-spelling drift fails in ONE place. The spec evolves (`gen_ai.system` →
# `gen_ai.provider.name`; `prompt_tokens` → `input_tokens`) — pin the snapshot in
# design note 46 and only adopt keys whose spelling is stable as of 2026-06-25.
GEN_AI_OPERATION_NAME = "gen_ai.operation.name"
GEN_AI_REQUEST_MODEL = "gen_ai.request.model"
GEN_AI_USAGE_INPUT_TOKENS = "gen_ai.usage.input_tokens"
GEN_AI_USAGE_OUTPUT_TOKENS = "gen_ai.usage.output_tokens"
GEN_AI_RESPONSE_FINISH_REASONS = "gen_ai.response.finish_reasons"
GEN_AI_TOOL_NAME = "gen_ai.tool.name"

# GenAI operation names (CNCF). Only these 3 bespoke spans are GenAI-semantic;
# TURN / PROMPT_BUILD / COMPACTION have NO CNCF operation → pass through bespoke.
OP_CHAT = "chat"
OP_EXECUTE_TOOL = "execute_tool"
OP_INVOKE_AGENT = "invoke_agent"

# === Mapping tables ===

# Provider-neutral StopReason.value → CNCF-canonical finish_reason string.
# Why normalize to OpenAI-style strings: lets V2 telemetry flow into any APM that
# expects the conventional finish_reason vocabulary (research #5: telemetry → any APM).
STOP_REASON_TO_FINISH_REASON: dict[str, str] = {
    "end_turn": "stop",
    "tool_use": "tool_calls",
    "max_tokens": "length",
    "stop_sequence": "stop",
    "safety_refusal": "content_filter",
    "provider_error": "error",
}

# bespoke span_type → gen_ai.operation.name (only the 3 GenAI-semantic kinds).
SPAN_TYPE_TO_OPERATION: dict[str, str] = {
    "LLM_CALL": OP_CHAT,
    "TOOL_EXEC": OP_EXECUTE_TOOL,
    "LOOP": OP_INVOKE_AGENT,
}

# bespoke attr key → gen_ai.* key (simple renames; finish_reason handled specially).
ATTR_MAP: dict[str, str] = {
    "model": GEN_AI_REQUEST_MODEL,
    "prompt_tokens": GEN_AI_USAGE_INPUT_TOKENS,
    "completion_tokens": GEN_AI_USAGE_OUTPUT_TOKENS,
    "tool": GEN_AI_TOOL_NAME,
}

# Bespoke keys that MUST be translated away on a GenAI span — their presence on an
# exported GenAI span signals a mapping bug (used by the conformance checker).
_BESPOKE_GENAI_KEYS: tuple[str, ...] = (
    "model",
    "prompt_tokens",
    "completion_tokens",
    "tool",
    "finish_reason",
)

# Required gen_ai.* keys per operation for the conformance check (the HARD subset
# always knowable at span start; usage/finish_reasons are asserted on COMPLETED
# spans by the harness, not here, since they arrive post-response).
_REQUIRED_BY_OP: dict[str, tuple[str, ...]] = {
    OP_CHAT: (GEN_AI_REQUEST_MODEL,),
    OP_EXECUTE_TOOL: (GEN_AI_TOOL_NAME,),
    OP_INVOKE_AGENT: (),
}


def _finish_reasons(value: Any) -> list[str]:
    """Map a provider-neutral StopReason.value to a 1-element CNCF finish_reasons list."""
    return [STOP_REASON_TO_FINISH_REASON.get(str(value), str(value))]


def to_genai_span(name: str, attributes: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Translate a bespoke (span name, attrs) to CNCF GenAI conventions.

    Pure: no I/O, no mutation of the input. For non-GenAI spans (span_type not in
    SPAN_TYPE_TO_OPERATION) returns (name, copy-of-attrs) unchanged. For GenAI spans
    renames mapped attrs to gen_ai.*, adds gen_ai.operation.name, rebuilds the span
    name as `{operation} {target}`, and preserves enterprise/diagnostic attrs
    (category / trace_id_neutral / tenant_id / user_id / session_id / span_type).
    """
    span_type = str(attributes.get("span_type", ""))
    operation = SPAN_TYPE_TO_OPERATION.get(span_type)
    if operation is None:
        # Not a GenAI-semantic span — pass through bespoke (TURN / PROMPT_BUILD / COMPACTION).
        return name, dict(attributes)

    out: dict[str, Any] = {GEN_AI_OPERATION_NAME: operation}
    for key, value in attributes.items():
        if key == "finish_reason":
            out[GEN_AI_RESPONSE_FINISH_REASONS] = _finish_reasons(value)
        elif key in ATTR_MAP:
            out[ATTR_MAP[key]] = value
        else:
            out[key] = value  # enterprise / diagnostic / unmapped — preserved verbatim

    # Span name = `{operation} {target}` (CNCF). target: chat→model, tool→tool name.
    target = ""
    if operation == OP_CHAT:
        target = str(attributes.get("model", "")).strip()
    elif operation == OP_EXECUTE_TOOL:
        target = str(attributes.get("tool", "")).strip()
    new_name = f"{operation} {target}".strip()
    return new_name, out


def assert_genai_conformant(span_name: str, attributes: dict[str, Any]) -> list[str]:
    """Return CNCF GenAI conformance violations for an EXPORTED span ([] = conformant).

    Non-GenAI spans (no gen_ai.operation.name) are exempt → []. For GenAI spans:
    span name must be operation-prefixed, required-per-op gen_ai.* keys present, and
    NO un-translated bespoke GenAI key may leak.
    """
    violations: list[str] = []
    operation = attributes.get(GEN_AI_OPERATION_NAME)
    if operation is None:
        return violations  # non-GenAI span — exempt by design

    if span_name.split(" ", 1)[0] != operation:
        violations.append(f"span name '{span_name}' not prefixed by operation '{operation}'")

    for required in _REQUIRED_BY_OP.get(str(operation), ()):
        if required not in attributes:
            violations.append(f"missing required attr '{required}' for op '{operation}'")

    for bespoke in _BESPOKE_GENAI_KEYS:
        if bespoke in attributes:
            violations.append(f"un-translated bespoke key '{bespoke}' leaked on GenAI span")

    return violations
