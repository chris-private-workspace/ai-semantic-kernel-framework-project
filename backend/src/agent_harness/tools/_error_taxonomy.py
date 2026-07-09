"""
File: backend/src/agent_harness/tools/_error_taxonomy.py
Purpose: Pure structured-error reflection for tool failures — classify a tool error
         into an actionable taxonomy and render a diagnostic observation for the LLM.
Category: 範疇 2 (Tool Layer)
Scope: Phase 57 / Sprint 57.144 (research #7 AD-Tool-Description-Lint-Reflection, Half B)

Description:
    Research #7 (consolidated-analysis §2.4): structured-error reflection — feeding the
    LLM a TYPED diagnosis of a tool failure (invocation / parameter / wrong-tool /
    failed-API) rather than an opaque "Error: <repr>" — measurably improves the model's
    next-turn correction. This is the "external verifiable signal" regime where
    self-correction provably helps (vs intrinsic self-reflection, which degrades).

    classify_tool_error / render_reflection are PURE (no I/O, no LLM, no DB, no
    agent_harness runtime imports); tool_error_reflection_enabled() reads one env flag.
    The taxonomy is orthogonal to Cat 8 ErrorClass (TRANSIENT/LLM_RECOVERABLE/HITL/FATAL
    = the *retry* decision); this answers "how should the model FIX it", not "retry?".
    The two coexist.

    Consumers (both gated by the CHAT_TOOL_ERROR_REFLECTION lever):
    - tools/executor.py — the dominant handler-exception + schema-validation failure paths
    - orchestrator_loop/loop.py — the rare executor-itself-raises path (B2 full coverage)

Key Components:
    - ErrorTaxonomy: the 5-value classification enum
    - classify_tool_error(): pure classifier from the signals available at a failure site
    - render_reflection(): a short, actionable diagnostic string for the LLM observation

Created: 2026-06-25 (Sprint 57.144)

Modification History (newest-first):
    - 2026-07-09: Sprint 57.163 — fix stale rare-path cross-ref (loop.py 3023-3030 -> 3068-3086)
    - 2026-06-25: Initial creation (Sprint 57.144) — research #7 Half B structured-error reflection

Related:
    - tools/executor.py (dominant failure paths) / orchestrator_loop/loop.py:3068-3086 (rare path)
    - error_handling/_abc.py (Cat 8 ErrorClass — orthogonal: retry decision, not fix-diagnosis)
    - claudedocs/5-status/tool-description-lint-reflection-thin-spike-eval-20260625.md §1.4
"""

from __future__ import annotations

import os
from enum import Enum

# Env lever name (default OFF). Documented alongside the other CHAT_* knobs in
# api/v1/chat/_category_factories.py; read here (per-call) so the executor + loop
# share one source without threading a bool through both constructors.
_REFLECTION_ENV = "CHAT_TOOL_ERROR_REFLECTION"
_TRUTHY = frozenset({"1", "true", "yes", "on"})


def tool_error_reflection_enabled() -> bool:
    """Whether structured-error reflection is enabled (CHAT_TOOL_ERROR_REFLECTION).

    Default OFF — evidence-first: the Sprint 57.144 A/B harness verdict decides
    whether to flip the default. Read PER-CALL (no module-level cache) so tests can
    toggle via monkeypatch and there is no stale-state leak across event loops
    (Risk Class C). The A/B harness itself does NOT depend on this lever — it calls
    classify_tool_error / render_reflection directly to compare both arms.
    """
    return os.environ.get(_REFLECTION_ENV, "").strip().lower() in _TRUTHY


class ErrorTaxonomy(str, Enum):
    """How the model should think about fixing a failed tool call (not retry policy)."""

    PARAMETER = "parameter"  # bad/missing arguments vs the input schema
    WRONG_TOOL = "wrong_tool"  # the tool does not exist / is not available
    FAILED_API = "failed_api"  # external dependency failed (network / timeout / upstream)
    INVOCATION = "invocation"  # the handler raised for some other reason
    UNKNOWN = "unknown"  # not enough signal to classify


# Fully-qualified exception-class substrings that indicate an external/API failure.
# Matched case-insensitively against ToolResult.error_class (e.g.
# "aiohttp.ClientConnectionError", "asyncio.TimeoutError", "httpx.ConnectError").
_FAILED_API_MARKERS = (
    "timeout",
    "connection",
    "connect",
    "clienterror",
    "aiohttp",
    "httpx",
    "socket",
    "httperror",
    "ssl",
)

# Error-message substrings that indicate a schema/argument problem when no explicit
# is_schema_error flag is passed (e.g. a jsonschema ValidationError message).
_PARAMETER_MARKERS = (
    "required property",
    "is not of type",
    "is a required",
    "does not match",
    "additional properties",
    "is not valid under",
    "is too short",
    "is too long",
)


def classify_tool_error(
    *,
    error_class: str | None = None,
    error_msg: str = "",
    is_schema_error: bool = False,
    is_unknown_tool: bool = False,
) -> ErrorTaxonomy:
    """Classify a tool failure into an actionable taxonomy.

    Signals (each optional; pass what the call site has):
    - error_class: fully-qualified exception class name (ToolResult.error_class), if any
    - error_msg: the human-readable error string
    - is_schema_error: True when the failure came from input-schema validation
    - is_unknown_tool: True when the tool name is not registered

    Precedence: explicit flags first (schema / unknown-tool), then external-API markers
    on the exception class, then message heuristics, then a generic invocation/unknown.
    """
    if is_schema_error:
        return ErrorTaxonomy.PARAMETER
    if is_unknown_tool:
        return ErrorTaxonomy.WRONG_TOOL

    ec = (error_class or "").lower()
    if ec and any(marker in ec for marker in _FAILED_API_MARKERS):
        return ErrorTaxonomy.FAILED_API

    msg = (error_msg or "").lower()
    if msg and any(marker in msg for marker in _PARAMETER_MARKERS):
        return ErrorTaxonomy.PARAMETER
    if msg and any(marker in msg for marker in _FAILED_API_MARKERS):
        return ErrorTaxonomy.FAILED_API

    if error_class:
        return ErrorTaxonomy.INVOCATION
    return ErrorTaxonomy.UNKNOWN


# Per-taxonomy guidance appended after the raw error so the model knows what to DO.
_GUIDANCE = {
    ErrorTaxonomy.PARAMETER: (
        "Check the tool's input schema (required fields / types) and retry with "
        "corrected arguments."
    ),
    ErrorTaxonomy.WRONG_TOOL: (
        "This tool is not available — choose a valid tool from the provided list."
    ),
    ErrorTaxonomy.FAILED_API: (
        "An external dependency failed; this may be transient — consider retrying or a "
        "different approach."
    ),
    ErrorTaxonomy.INVOCATION: ("Review the arguments and retry, or try a different approach."),
    ErrorTaxonomy.UNKNOWN: "Adjust your approach and retry.",
}

_LABEL = {
    ErrorTaxonomy.PARAMETER: "parameter error",
    ErrorTaxonomy.WRONG_TOOL: "wrong-tool error",
    ErrorTaxonomy.FAILED_API: "tool execution failed (external/API error)",
    ErrorTaxonomy.INVOCATION: "tool invocation error",
    ErrorTaxonomy.UNKNOWN: "tool error",
}


def render_reflection(taxonomy: ErrorTaxonomy, error_msg: str) -> str:
    """Render a short, actionable diagnostic observation for the LLM.

    Shape: "<label>: <raw error>. <what-to-do guidance>".
    """
    raw = (error_msg or "").strip() or "(no detail)"
    return f"{_LABEL[taxonomy]}: {raw}. {_GUIDANCE[taxonomy]}"
