"""
File: backend/src/agent_harness/_contracts/tools.py
Purpose: Single-source tool contracts (ToolSpec / ToolCall / ToolResult / annotations).
Category: cross-category single-source contracts (per 17.md §1)
Scope: Phase 49 / Sprint 49.1

Description:
    Defines tool definitions, calls, and results in an LLM-neutral form.
    Adapters convert these to/from provider-native formats (OpenAI
    function calling / Anthropic tools / etc.).

Key Components:
    - ToolSpec: tool definition (name + schema + annotations + concurrency)
    - ToolAnnotations: MCP 4-hint flags (read_only / destructive / etc.)
    - ConcurrencyPolicy: how the executor may parallelize this tool
    - ToolCall: shared with chat.py (re-exported for convenience)
    - ToolResult: tool execution outcome

Owner: 01-eleven-categories-spec.md §範疇 2
Single-source: 17.md §1.1

Created: 2026-04-29 (Sprint 49.1)
Last Modified: 2026-06-16

Modification History (newest-first):
    - 2026-06-16: Sprint 57.124 — docstrings reflect PermissionChecker removal
    - 2026-04-30: Add first-class ToolHITLPolicy enum + risk_level field on
      ToolSpec (Sprint 51.1 Day 1; CARRY-021 from 51.0 retro). Replaces
      tags-encoded `hitl_policy:*` / `risk:*` workaround. Reuses existing
      RiskLevel enum from _contracts.hitl (single-source). ToolHITLPolicy
      named distinctly from per-tenant HITLPolicy dataclass to avoid
      collision; values map to 51.0 tag strings (auto / ask_once /
      always_ask).
    - 2026-04-29: Initial creation (Sprint 49.1)

Related:
    - 01-eleven-categories-spec.md §範疇 2 (Tools)
    - 17-cross-category-interfaces.md §1.1 (ToolSpec dataclass) / §3 (cross-category tools)
    - 08b-business-tools-spec.md (business-domain tools)
    - sprint-51-1-plan.md §決策 1 (CARRY-021)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal
from uuid import UUID

from agent_harness._contracts.hitl import RiskLevel


class ConcurrencyPolicy(Enum):
    """How a tool may be parallelized within a single LLM turn."""

    SEQUENTIAL = "sequential"
    READ_ONLY_PARALLEL = "read_only_parallel"
    ALL_PARALLEL = "all_parallel"


class ToolHITLPolicy(Enum):
    """Per-tool HITL behavior policy.

    Distinct from per-tenant HITLPolicy (in _contracts.hitl) which encodes
    tenant-level approval routing. This enum encodes the tool's intrinsic
    HITL stance: whether each invocation requires human approval before
    handler execution. The loop's `_cat9_tool_check` + per-tenant `HITLPolicy`
    (Sprint 57.122/57.124) gate execution from this + risk_level +
    annotations.destructive (the former PermissionChecker was removed in 57.124).
    """

    AUTO = "auto"  # no HITL required (subject to risk_level + tenant policy)
    ASK_ONCE = "ask_once"  # first call in session requires approval
    ALWAYS_ASK = "always_ask"  # every call requires approval


@dataclass(frozen=True)
class ToolAnnotations:
    """MCP-style 4 hints; used by guardrails + concurrency planner."""

    read_only: bool = False
    destructive: bool = False
    idempotent: bool = False
    open_world: bool = False  # accesses external systems / network


@dataclass(frozen=True)
class ToolSpec:
    """LLM-neutral tool definition. Adapters convert to provider format."""

    name: str
    description: str
    input_schema: dict[str, Any]  # JSON Schema
    annotations: ToolAnnotations = field(default_factory=ToolAnnotations)
    concurrency_policy: ConcurrencyPolicy = ConcurrencyPolicy.SEQUENTIAL
    hitl_policy: ToolHITLPolicy = ToolHITLPolicy.AUTO
    risk_level: RiskLevel = RiskLevel.LOW
    version: str = "1.0"
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class ExecutionContext:
    """Per-call invocation context for ToolExecutor pipeline.

    Forward-compatible for Phase 53.3 RBAC wiring (tenant-scoped role checks
    will read tenant_id) and HITL tracking (session_id ties first-call
    state to session). `explicit_approval` was consumed only by the removed
    PermissionChecker (Sprint 57.124); the field is retained for forward-compat
    (AD-ExecutionContext-ExplicitApproval-Tidy tracks removing it).

    Sprint 52.5 P0 #18 (CARRY-030): `user_id` was added so memory_tools
    handlers can attribute writes / reads to the authenticated user from
    server-side state instead of trusting LLM-supplied arguments. The
    Loop must build ExecutionContext from the request's authenticated
    state (JWT claims) and pass it to ToolExecutor.execute(context=...);
    handlers MUST treat any args["tenant_id"] / args["user_id"] /
    args["session_id"] that disagrees with this context as a forgery
    attempt and refuse the call.
    """

    tenant_id: UUID | None = None
    user_id: UUID | None = None
    session_id: UUID | None = None
    explicit_approval: bool = False


@dataclass(frozen=True)
class ToolResult:
    """Output of a single tool execution.

    `result_content_types` indicates which content forms are present;
    Anthropic supports image content, OpenAI is string-only.
    """

    tool_call_id: str
    tool_name: str
    success: bool
    content: str | list[dict[str, Any]]  # text or content blocks
    result_content_types: tuple[Literal["text", "image", "json"], ...] = ("text",)
    error: str | None = None
    duration_ms: float | None = None
    # Sprint 53.3 US-9 (AD-Cat8-3): preserve original exception type for
    # soft-failure path so DefaultErrorPolicy.classify_by_string() can
    # recover ErrorClass without the original exception object.
    # Format: fully-qualified class name e.g. "aiohttp.ClientConnectionError".
    # None when ToolResult.success=True OR when failure is non-exception
    # (e.g. permission denied / schema mismatch / unknown tool).
    error_class: str | None = None
    # Sprint 57.144 US-2 (research #7 Half B): structured-error reflection taxonomy
    # (ErrorTaxonomy.value — "parameter"/"wrong_tool"/"failed_api"/"invocation"/
    # "unknown"). Set ONLY when the CHAT_TOOL_ERROR_REFLECTION lever is on; stored as
    # str (not the enum) so this contract takes no dependency on tools/_error_taxonomy.
    # Orthogonal to error_class (which feeds the Cat 8 retry decision).
    error_taxonomy: str | None = None
