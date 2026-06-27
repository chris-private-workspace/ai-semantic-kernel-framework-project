"""
File: backend/src/agent_harness/tools/memory_tools.py
Purpose: memory_search / memory_write ToolSpecs + real handlers (51.2 Day 4).
Category: 範疇 2 (Tool Layer hosting Cat 3 backed handlers)
Scope: Phase 51 / Sprint 51.1 (placeholder) + Sprint 51.2 Day 4 (real handlers)
       + Sprint 52.5 Day 9 (P0 #18: ExecutionContext-based tenant)

Description:
    51.1 Day 4.3 introduced the placeholder ToolSpecs so the registry could
    list them consistently with 17.md §3.1. 51.2 Day 4 wires real handlers
    that route to MemoryRetrieval (search) and per-scope MemoryLayer.write
    (write).

    Tenant context (Sprint 52.5 P0 #18 onwards):
    - tenant_id / user_id / session_id come from ExecutionContext (server-
      authoritative, populated from JWT claims at the API boundary).
    - LLMs MUST NOT supply these in ToolCall.arguments. If args nonetheless
      contain `tenant_id` / `user_id` / `session_id` keys that disagree with
      ExecutionContext, the handler treats it as a forgery attempt and
      refuses the call.
    - Pre-52.5 handlers read tenant_id directly from ToolCall.arguments —
      that path is now closed (W4P-4 audit: LLM-controlled tenant_id was a
      W3-2 mirror vulnerability).

    Schema additions in 51.2:
    - memory_search: `time_scales` array (axis 2)
    - memory_write: `time_scale` + `confidence`

    Schemas no longer declare "placeholder" in tags. Importantly, the
    schemas do NOT include tenant_id / user_id / session_id properties —
    LLMs literally cannot mention them in well-formed tool calls because
    the executor would reject the call as schema-invalid before reaching
    the handler.

Owner: 範疇 3 (Memory) — handlers route into Cat 3 layers; 範疇 2 (Tool Layer)
       owns the spec registration.

Modification History:
    - 2026-06-27 (Sprint 57.148): add MEMORY_FORMATION_NUDGE (memory-formation Slice 1)
    - 2026-05-01 (Sprint 52.5 Day 9 P0 #18): handlers switch to dual-arity
      (call, context) protocol. tenant_id / user_id / session_id sourced
      from ExecutionContext. Forged args rejected before tool execution.
    - 2026-04-30 (Sprint 51.2 Day 4): replace memory_placeholder_handler
      with real factory functions (make_memory_search_handler /
      make_memory_write_handler); update schemas with time_scales /
      time_scale / confidence; drop "placeholder" tag.
    - 2026-04-30 (Sprint 51.1 Day 4.3): initial placeholder ToolSpecs.

Carry items resolved:
    - CARRY-030: ExecutionContext threading landed in Sprint 52.5 Day 9.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID

from agent_harness._contracts import (
    ConcurrencyPolicy,
    ExecutionContext,
    MemoryHint,
    RiskLevel,
    ToolAnnotations,
    ToolCall,
    ToolHITLPolicy,
    ToolSpec,
)
from agent_harness.memory import MemoryLayer, MemoryRetrieval

ToolHandler = Callable[[ToolCall, ExecutionContext], Awaitable[str]]


# Reserved argument names that the LLM is NOT allowed to set; handlers
# detect these in args and refuse forged values that disagree with the
# ExecutionContext. Pre-52.5, these were trusted input — now they are
# treated as a tamper signal.
_RESERVED_TENANT_KEYS = ("tenant_id", "user_id", "session_id")


def _detect_forged_scope_args(args: dict[str, Any], context: ExecutionContext) -> str | None:
    """Return human-readable error string if any reserved arg disagrees
    with the ExecutionContext, otherwise None.

    Tolerant rules:
    - args can omit reserved keys entirely (the canonical happy path).
    - args containing a key that EQUALS the context value is allowed
      (some legacy callers re-pass the same value; tolerating this avoids
      spurious failures during migration).
    - args containing a key whose value is None / "" is allowed (some
      JSON serialisers emit empty defaults; treated as "not set").
    - Otherwise → forgery signal.
    """
    ctx_view = {
        "tenant_id": context.tenant_id,
        "user_id": context.user_id,
        "session_id": context.session_id,
    }
    for key in _RESERVED_TENANT_KEYS:
        if key not in args:
            continue
        raw = args[key]
        if raw is None or raw == "":
            continue
        try:
            supplied = UUID(str(raw))
        except (ValueError, AttributeError):
            return (
                f"argument '{key}' is not a valid UUID; LLMs must not supply "
                "tenant scope arguments — they come from ExecutionContext"
            )
        expected = ctx_view[key]
        if expected is None or supplied != expected:
            return (
                f"argument '{key}' disagrees with ExecutionContext "
                f"(supplied={supplied!s}, context={expected!s}); refusing "
                "potentially forged tenant scope"
            )
    return None


MEMORY_SEARCH_SPEC: ToolSpec = ToolSpec(
    name="memory_search",
    description=(
        "Search across 5-layer memory (system / tenant / role / user / session) "
        "with optional time_scale axis (short_term / long_term / semantic). "
        "Returns top-k MemoryHints ranked by relevance * confidence."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "minLength": 1,
                "description": "Natural-language search query for relevant memories.",
            },
            "scopes": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["system", "tenant", "role", "user", "session"],
                },
                "default": ["session", "user", "tenant"],
                "description": "Optional memory layers to search (see enum for the 5 scopes).",
            },
            "time_scales": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["short_term", "long_term", "semantic"],
                },
                "default": ["long_term"],
                "description": "Optional time-scale axes to search (see enum).",
            },
            "top_k": {
                "type": "integer",
                "minimum": 1,
                "maximum": 50,
                "default": 5,
                "description": "Max number of ranked hints to return (1-50).",
            },
        },
        "required": ["query"],
    },
    annotations=ToolAnnotations(read_only=True, idempotent=True),
    concurrency_policy=ConcurrencyPolicy.READ_ONLY_PARALLEL,
    hitl_policy=ToolHITLPolicy.AUTO,
    risk_level=RiskLevel.LOW,
    tags=("builtin", "memory"),
)

MEMORY_WRITE_SPEC: ToolSpec = ToolSpec(
    name="memory_write",
    description=(
        "Persist a memory entry into the specified scope and time_scale. "
        "system scope is read-only at runtime (rejected). short_term writes "
        "for tenant/role layers are rejected (use session layer)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "scope": {
                "type": "string",
                "enum": ["session", "user", "tenant", "role"],
                "description": "Target memory layer (system layer is read-only).",
            },
            "key": {
                "type": "string",
                "minLength": 1,
                "description": "Unique key identifying this memory entry.",
            },
            "content": {
                "type": "string",
                "minLength": 1,
                "description": "The memory content to persist.",
            },
            "time_scale": {
                "type": "string",
                "enum": ["short_term", "long_term", "semantic"],
                "default": "long_term",
                "description": "Retention time scale (short_term / long_term / semantic).",
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "default": 0.5,
                "description": "Confidence score for this entry (0.0-1.0).",
            },
        },
        "required": ["scope", "key", "content"],
    },
    annotations=ToolAnnotations(read_only=False, destructive=False, idempotent=True),
    concurrency_policy=ConcurrencyPolicy.SEQUENTIAL,
    hitl_policy=ToolHITLPolicy.AUTO,
    risk_level=RiskLevel.LOW,
    tags=("builtin", "memory"),
)

MEMORY_TOOL_SPECS: tuple[ToolSpec, ...] = (MEMORY_SEARCH_SPEC, MEMORY_WRITE_SPEC)


# Sprint 57.148 (memory-formation Slice 1): the chat system-prompt nudge that
# makes the platform actually remember the user across sessions (CC-memory-file
# equivalent). The agent calls memory_write(scope='user') when the user states
# durable self-facts; the PromptBuilder's always-on profile() then surfaces them
# every future turn. Appended to the chat system prompt ONLY when the memory
# tools are wired (handler gates on memory_retrieval is not None) so the echo /
# no-memory path is byte-identical.
MEMORY_FORMATION_NUDGE = (
    "## Remembering the user\n"
    "When the user shares a durable fact about themselves — their name, role, "
    "team, current project, or a stable preference — call the memory_write tool "
    "with scope='user' and time_scale='long_term' so you remember it in future "
    "conversations. Use a short stable key (e.g. 'identity' or 'preferences') and "
    "store one clear fact per call. Do not store transient or one-off details, and "
    "do not ask for permission first — just record durable facts as they come up."
)


# ---------------------------------------------------------------------------
# Placeholder handler (kept as fallback for dev/test environments without DB)
# ---------------------------------------------------------------------------
async def memory_placeholder_handler(call: ToolCall, context: ExecutionContext) -> str:
    """Fallback handler used when no MemoryRetrieval / MemoryLayer is wired.

    Sprint 51.2 keeps this for backward compatibility with code paths that
    construct register_builtin_tools without injecting Cat 3 dependencies
    (e.g., dev startup before DB session_factory is ready). Production
    deployment must wire real handlers via make_memory_search_handler /
    make_memory_write_handler.

    Sprint 52.5 Day 9 (P0 #18): now accepts ExecutionContext as 2nd arg
    so it can flow through the dual-arity protocol unchanged.
    """
    del context  # not used; placeholder ignores
    return json.dumps(
        {
            "ok": False,
            "error": (
                f"memory tool '{call.name}' has no Cat 3 backend wired; "
                "construct register_builtin_tools(memory_retrieval=..., "
                "memory_layers=...) to enable."
            ),
        }
    )


# ---------------------------------------------------------------------------
# Real handler factories (51.2 Day 4)
# ---------------------------------------------------------------------------
def make_memory_search_handler(retrieval: MemoryRetrieval) -> ToolHandler:
    """Factory: handler that routes memory_search ToolCall -> MemoryRetrieval.

    Sprint 52.5 Day 9 (P0 #18): tenant_id / user_id / session_id come from
    `context: ExecutionContext`. Forged args (any reserved key in
    ToolCall.arguments that disagrees with the context) → refused.
    """

    async def handler(call: ToolCall, context: ExecutionContext) -> str:
        args: dict[str, Any] = dict(call.arguments)

        forge = _detect_forged_scope_args(args, context)
        if forge is not None:
            return json.dumps({"ok": False, "error": forge})

        query = str(args.get("query", "")).strip()
        if not query:
            return json.dumps({"ok": False, "error": "query is required"})

        scopes_raw = args.get("scopes") or ["session", "user", "tenant"]
        time_scales_raw = args.get("time_scales") or ["long_term"]
        top_k = int(args.get("top_k", 5))

        hints = await retrieval.search(
            query=query,
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            session_id=context.session_id,
            scopes=tuple(scopes_raw),
            time_scales=tuple(time_scales_raw),
            top_k=top_k,
        )

        return json.dumps({"ok": True, "hints": [_hint_to_dict(h) for h in hints]})

    return handler


def make_memory_write_handler(layers: dict[str, MemoryLayer]) -> ToolHandler:
    """Factory: handler that routes memory_write ToolCall -> MemoryLayer.write.

    scope=system -> rejected (system layer read-only at runtime).
    Sprint 52.5 Day 9 (P0 #18): tenant_id / user_id / session_id come from
    `context: ExecutionContext`. Forged args refused before write.
    """

    async def handler(call: ToolCall, context: ExecutionContext) -> str:
        args: dict[str, Any] = dict(call.arguments)

        forge = _detect_forged_scope_args(args, context)
        if forge is not None:
            return json.dumps({"ok": False, "error": forge})

        scope = str(args.get("scope", "")).strip()
        content = str(args.get("content", "")).strip()
        time_scale = args.get("time_scale", "long_term")
        confidence = float(args.get("confidence", 0.5))

        if scope == "system":
            return json.dumps(
                {
                    "ok": False,
                    "error": "system scope is read-only; use admin migration",
                }
            )

        layer = layers.get(scope)
        if layer is None:
            return json.dumps({"ok": False, "error": f"scope '{scope}' has no layer wired"})

        # Per-layer slot wiring: layers expecting user_id (user/role/tenant)
        # take context.user_id; the session layer historically overloads the
        # `user_id` parameter slot to carry session_id (Sprint 51.2 design).
        if scope == "session":
            slot_user_id = context.session_id
        else:
            slot_user_id = context.user_id

        try:
            entry_id = await layer.write(
                content=content,
                tenant_id=context.tenant_id,
                user_id=slot_user_id,
                time_scale=time_scale,
                confidence=confidence,
            )
        except (ValueError, NotImplementedError) as exc:
            return json.dumps({"ok": False, "error": str(exc)})

        return json.dumps({"ok": True, "entry_id": str(entry_id), "scope": scope})

    return handler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _parse_uuid(value: Any) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    try:
        return UUID(str(value))
    except (ValueError, AttributeError):
        return None


def _hint_to_dict(hint: MemoryHint) -> dict[str, Any]:
    """Serialize MemoryHint dataclass into a JSON-friendly dict."""
    return {
        "hint_id": str(hint.hint_id),
        "layer": hint.layer,
        "time_scale": hint.time_scale,
        "summary": hint.summary,
        "confidence": hint.confidence,
        "relevance_score": hint.relevance_score,
        "full_content_pointer": hint.full_content_pointer,
        "timestamp": hint.timestamp.isoformat(),
        "last_verified_at": (hint.last_verified_at.isoformat() if hint.last_verified_at else None),
        "verify_before_use": hint.verify_before_use,
        "source_tool_call_id": hint.source_tool_call_id,
        "expires_at": hint.expires_at.isoformat() if hint.expires_at else None,
        "tenant_id": str(hint.tenant_id) if hint.tenant_id else None,
    }


__all__ = [
    "MEMORY_SEARCH_SPEC",
    "MEMORY_WRITE_SPEC",
    "MEMORY_TOOL_SPECS",
    "make_memory_search_handler",
    "make_memory_write_handler",
    "memory_placeholder_handler",
]
