"""
File: backend/src/agent_harness/tools/note_tool.py
Purpose: note_tool built-in — a deterministic, NON-escalate demo tool (returns its 'text').
Category: 範疇 2 (Tool Layer)
Scope: Phase 57.92 / Sprint 57.92 (地基 A Slice 3 leg 2)

Description:
    `note_tool` returns its `text` argument verbatim — the same deterministic
    shape as echo_tool, but WITHOUT being in CHAT_HITL_ESCALATE_TOOLS, so it
    executes normally inside a turn (no tool-call ESCALATE pause). Its purpose is
    to make a between-turns boundary reachable on 主流量: a `note` request runs a
    full turn 0 (LLM → note_tool → result) INSIDE the loop so turn_count
    increments to 1 and the between-turns guardrail can run at the top of turn 1
    on note_tool's deterministic result. echo_tool cannot serve this role: it
    tool-escalates at turn 0's tool check, and a tool resume execs the pending
    tool OUTSIDE the loop, so turn_count never reaches 1.

Key Components:
    - NOTE_TOOL_SPEC: ToolSpec (read-only, AUTO HITL, LOW risk)
    - note_handler(call): returns the 'text' argument verbatim

Created: 2026-06-08 (Sprint 57.92)
Last Modified: 2026-06-08

Modification History (newest-first):
    - 2026-06-08: Initial creation (Sprint 57.92) — non-escalate demo tool (between-turns)

Related:
    - agent_harness/tools/echo_tool.py — the escalate-gated sibling (Sprint 57.88)
    - api/v1/chat/handler.py — DEMO_SYSTEM_PROMPT drives note_tool; the between-turns gate trips
"""

from __future__ import annotations

from agent_harness._contracts import (
    ConcurrencyPolicy,
    RiskLevel,
    ToolAnnotations,
    ToolCall,
    ToolHITLPolicy,
    ToolSpec,
)

NOTE_TOOL_SPEC: ToolSpec = ToolSpec(
    name="note_tool",
    description="Records a note: returns the 'text' argument back verbatim. Test-only built-in.",
    input_schema={
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Text to record as a note.",
            },
        },
        "required": ["text"],
    },
    annotations=ToolAnnotations(
        read_only=True,
        destructive=False,
        idempotent=True,
        open_world=False,
    ),
    concurrency_policy=ConcurrencyPolicy.READ_ONLY_PARALLEL,
    hitl_policy=ToolHITLPolicy.AUTO,
    risk_level=RiskLevel.LOW,
    tags=("builtin", "note"),
)


async def note_handler(call: ToolCall) -> str:
    """Return the 'text' argument verbatim."""
    return str(call.arguments.get("text", ""))
