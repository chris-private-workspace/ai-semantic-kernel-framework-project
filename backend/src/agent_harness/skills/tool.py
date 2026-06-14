"""
File: backend/src/agent_harness/skills/tool.py
Purpose: the read_skill tool — model-invoked lazy-load of a skill's full instructions.
Category: 範疇 2 (Tool Layer)
Scope: Phase 57 / Sprint 57.113 (Skills System epic — first thin vertical)

Description:
    The expensive half of the Skills lazy-load: the system prompt advertises
    skills cheaply (registry.render_catalog_block); when the model decides one
    fits, it calls read_skill(name) and this handler returns that skill's FULL
    instruction body framed as a directive the model then follows. An unknown
    name returns a recoverable message (NOT an exception) so the model can
    correct itself. Read-only, no DB, no side effects.

    Registered via make_default_executor's `skill_registry` opt-in (mirrors the
    echo + handoff_targets registration pattern). Once registered, the chat
    path's registry-derived permission matrix auto-grants it a PASS rule.

Key Components:
    - READ_SKILL_TOOL_SPEC: the LLM-neutral ToolSpec (input_schema {name})
    - make_read_skill_handler(registry): the async ToolHandler closure

Created: 2026-06-13 (Sprint 57.113)
Last Modified: 2026-06-14

Modification History (newest-first):
    - 2026-06-14: Sprint 57.115 — use render_skill_instructions (DRY; output byte-identical)
    - 2026-06-13: Initial creation (Sprint 57.113) — read_skill lazy-load tool

Related:
    - agent_harness/skills/registry.py — Skill / SkillRegistry / render_catalog_block
    - agent_harness/tools/echo_tool.py — the built-in spec+handler shape mirrored here
    - business_domain/_register_all.py — make_default_executor skill_registry opt-in
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from agent_harness._contracts import (
    ConcurrencyPolicy,
    RiskLevel,
    ToolAnnotations,
    ToolCall,
    ToolHITLPolicy,
    ToolSpec,
)
from agent_harness.skills.registry import SkillRegistry, render_skill_instructions

READ_SKILL_TOOL_SPEC: ToolSpec = ToolSpec(
    name="read_skill",
    description=(
        "Load the full instructions for a named skill from the Available Skills list. "
        "Call this before applying a skill to the user's request."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "The skill name from the Available Skills list.",
            },
        },
        "required": ["name"],
        "additionalProperties": False,
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
    tags=("skills",),
)


def make_read_skill_handler(
    registry: SkillRegistry,
) -> Callable[[ToolCall], Awaitable[str]]:
    """Build the read_skill handler bound to `registry` (returns the framed instructions)."""

    async def read_skill_handler(call: ToolCall) -> str:
        name = str(call.arguments.get("name", "")).strip()
        skill = registry.get(name)
        if skill is None:
            available = ", ".join(s.name for s in registry.list()) or "(none)"
            return f"Unknown skill {name!r}. Available skills: {available}."
        # Sprint 57.115: render_skill_instructions is the shared (DRY) body; the
        # tool appends its own trailing directive (byte-identical to pre-refactor).
        return (
            f"{render_skill_instructions(skill)}\n\n"
            "Follow these instructions for the current task."
        )

    return read_skill_handler
