"""
File: backend/src/agent_harness/subagent/tools.py
Purpose: LLM-callable tool factories for Cat 11 — task_spawn + handoff (per 17.md §3.1).
Category: 範疇 11 (Subagent Orchestration)
Scope: Sprint 54.2 US-5

Description:
    17-cross-category-interfaces.md §3.1 lists `task_spawn` and `handoff` as
    Cat 11 LLM-callable tools (the LLM decides when to invoke them). This
    module provides factories that wrap a SubagentDispatcher into Cat 2
    ToolSpec + handler pairs ready for ToolRegistry registration.

    Per Day 4 D18 design decision: AgentLoop is NOT modified. Tools auto-route
    through the existing `tool_executor.execute(tc)` path (loop.py:1018) once
    registered. The chat router (or any AgentLoop owner) calls this module's
    factories before constructing the loop, attaches the (ToolSpec, handler)
    pair to its ToolRegistry, and the LLM can invoke them like any tool.

    AgentLoop integration (Phase 55+): if SSE event emission for SubagentSpawned
    / SubagentCompleted is required, that's a separate concern handled by
    extending serialize_loop_event in api/v1/chat/sse.py and emitting the
    events from the tool handlers themselves (or a dispatcher hook). The 49.1
    stub events are wire-ready; emission is a Phase 55+ refinement.

Created: 2026-05-04 (Sprint 54.2)
Last Modified: 2026-06-11

Modification History:
    - 2026-06-12: Sprint 57.107 (B3) — make_handoff_tool → spec-only make_handoff_spec
    - 2026-06-11: Sprint 57.102 (B2a) — add make_send_to_parent_tool (TEAMMATE child→parent report)
    - 2026-05-04: Initial creation (Sprint 54.2 US-5)

Related:
    - subagent/dispatcher.py — DefaultSubagentDispatcher
    - 17-cross-category-interfaces.md §3.1 (task_spawn / handoff)
    - tools/registry.py — ToolRegistry consumer
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Awaitable, Callable
from uuid import UUID

from agent_harness._contracts import (
    SubagentBudget,
    SubagentMode,
    ToolSpec,
)
from agent_harness.subagent._abc import SubagentDispatcher

if TYPE_CHECKING:
    from agent_harness.subagent.mailbox import MailboxStore

ToolHandler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


def make_task_spawn_tool(
    *,
    dispatcher: SubagentDispatcher,
    parent_session_id: UUID,
) -> tuple[ToolSpec, ToolHandler]:
    """Factory: returns (ToolSpec, handler) for the `task_spawn` Cat 11 tool.

    LLM input schema: `{task: str, mode?: "fork"|"teammate"}`. Mode defaults
    to "fork" when LLM omits it.

    The handler synchronously waits for the subagent (uses dispatcher.wait_for
    internally). LLM caller blocks per turn — for fire-and-forget patterns
    callers can extend the schema to accept `wait: bool` in Phase 55+.
    """
    tool_spec = ToolSpec(
        name="task_spawn",
        description=(
            "Spawn a subagent to execute a delegated sub-task in fork (independent "
            "context) or teammate (mailbox-connected peer) mode. Returns subagent_id, "
            "success flag, and short summary of the subagent's response."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Sub-task description for the subagent.",
                },
                "mode": {
                    "type": "string",
                    "enum": ["fork", "teammate"],
                    "default": "fork",
                    "description": (
                        "Dispatch mode: 'fork' for independent exploration; "
                        "'teammate' for peer with mailbox communication."
                    ),
                },
            },
            "required": ["task"],
        },
    )

    async def handler(args: dict[str, Any]) -> dict[str, Any]:
        task = str(args.get("task", "")).strip()
        if not task:
            return {"success": False, "error": "missing_task"}
        mode_str = str(args.get("mode", "fork")).lower()
        try:
            mode = SubagentMode(mode_str)
        except ValueError:
            return {"success": False, "error": f"unknown_mode: {mode_str!r}"}
        if mode not in (SubagentMode.FORK, SubagentMode.TEAMMATE):
            return {
                "success": False,
                "error": f"task_spawn supports fork/teammate only, got {mode.value}",
            }
        try:
            subagent_id = await dispatcher.spawn(
                mode=mode,
                task=task,
                parent_session_id=parent_session_id,
                budget=SubagentBudget(),
            )
        except Exception as exc:  # noqa: BLE001 — surface as tool error
            return {"success": False, "error": f"spawn_failed: {type(exc).__name__}: {exc}"}
        result = await dispatcher.wait_for(subagent_id)
        return {
            "subagent_id": str(result.subagent_id),
            "success": result.success,
            "summary": result.summary,
            "tokens_used": result.tokens_used,
            "error": result.error,
        }

    return tool_spec, handler


# === make_handoff_spec: spec-only trigger for the loop-intercepted handoff ===
# Why: the loop's output classifier matches tc.name == HANDOFF_TOOL_NAME and
# terminates with stop_reason="handoff" BEFORE tool execution (loop.py HANDOFF
# branch) — booting the child session is the platform layer's job (router
# post-loop hook → HandoffService). The LLM therefore needs a ToolSpec it can
# SEE, but the handler must never run. The former make_handoff_tool routed
# through dispatcher.handoff() → HandoffExecutor (a UUID stub with zero 主流量
# callers) — retired Sprint 57.107 (AP-2/AP-11 convergence).
# Alternative considered: dispatcher delegating to HandoffService — rejected
# (Cat 11 must not import platform_layer; layering inversion).
def make_handoff_spec(
    *,
    suggested_targets: Sequence[str],
) -> tuple[ToolSpec, ToolHandler]:
    """Factory: returns (ToolSpec, defensive handler) for the `handoff` tool.

    Spec-only: the AgentLoop classifies a `handoff` tool_call as
    OutputType.HANDOFF and terminates the run with stop_reason="handoff"
    (carrying target_agent / reason) BEFORE any tool execution; the platform
    layer boots the child session. The handler raises if ever invoked —
    reaching it means the classifier interception was bypassed (a bug).

    `suggested_targets` is guidance for the LLM (listed in the description);
    boot-time validation (persona registry + tenant allowlist) is authoritative.
    """
    targets_hint = ", ".join(suggested_targets) if suggested_targets else "none configured"
    tool_spec = ToolSpec(
        name="handoff",
        description=(
            "Transfer complete control of this conversation to another agent "
            f"identity. Available target agents: {targets_hint}. Use ONLY when "
            "the user explicitly asks to hand the conversation to another agent, "
            "or the task clearly belongs to a different specialist — this ENDS "
            "the current agent's responsibility for the conversation."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "target_agent": {
                    "type": "string",
                    "description": "Identifier of the target agent role.",
                },
                "reason": {
                    "type": "string",
                    "description": "Short reason for the handoff (shown to the user).",
                },
            },
            "required": ["target_agent"],
        },
    )

    async def handler(args: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError(
            "handoff is loop-intercepted: the output classifier must terminate "
            "the run before tool execution; reaching this handler is a bug"
        )

    return tool_spec, handler


def make_send_to_parent_tool(
    *,
    mailbox: "MailboxStore",
    parent_session_id: UUID,
    role: str = "teammate",
) -> tuple[ToolSpec, ToolHandler]:
    """Factory: returns (ToolSpec, handler) for the `send_to_parent` Cat 11 tool.

    Sprint 57.102 (B2a): a TEAMMATE child loop calls this to send a short progress
    report / finding to the parent agent that spawned it, mid-loop (before its final
    answer). The report is delivered to the parent's mailbox queue (recipient="parent");
    the TeammateExecutor drains the queue after the child completes and folds the
    reports into the SubagentResult summary the parent integrates (await-completion:
    the reports surface to the parent when the teammate finishes — see plan §3.3).
    LLM input schema: `{message: str}`. Registered ONLY in the teammate child's tool
    registry (NOT FORK's, NOT the parent's).
    """
    tool_spec = ToolSpec(
        name="send_to_parent",
        description=(
            "Send a short progress report or finding to the parent agent that spawned "
            "you. Use this to share interim findings BEFORE your final answer; the parent "
            "receives your reports alongside your final summary."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The report / finding to send to the parent agent.",
                },
            },
            "required": ["message"],
        },
    )

    async def handler(args: dict[str, Any]) -> dict[str, Any]:
        message = str(args.get("message", "")).strip()
        if not message:
            return {"delivered": False, "error": "empty_message"}
        try:
            await mailbox.send(
                session_id=parent_session_id,
                sender=role,
                recipient="parent",
                content=message,
            )
        except Exception as exc:  # noqa: BLE001 — surface as tool error
            return {"delivered": False, "error": f"send_failed: {type(exc).__name__}: {exc}"}
        return {"delivered": True}

    return tool_spec, handler
