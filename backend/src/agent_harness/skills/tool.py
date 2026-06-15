"""
File: backend/src/agent_harness/skills/tool.py
Purpose: the Skills Cat-2 tools — read_skill (lazy-load) + run_skill_script (run a bundled script).
Category: 範疇 2 (Tool Layer)
Scope: Phase 57 / Sprint 57.113 (read_skill) + 57.118 (run_skill_script)

Description:
    Two model-invoked Cat-2 tools over a SkillRegistry:

    - read_skill(name): the expensive half of the Skills lazy-load — the system
      prompt advertises skills cheaply (registry.render_catalog_block); when the
      model decides one fits, read_skill returns that skill's FULL instruction body
      framed as a directive. Read-only, no side effects.
    - run_skill_script(skill_name): (Sprint 57.118) runs a system-bundled skill's
      SERVER-controlled executable script (Skill.script — git-authored, NOT an
      LLM-supplied arg) via the existing SandboxBackend (Docker prod / Subprocess
      dev), returning JSON stdout/stderr/exit_code. The script source never passes
      through the LLM (deterministic, untamperable). MEDIUM risk (code execution).

    An unknown name / a skill with no bundled script returns a recoverable message
    (NOT an exception) so the model can correct itself.

    Registered via make_default_executor's `skill_registry` opt-in. Once registered,
    the chat path's registry-derived permission matrix auto-grants a PASS rule (the
    derivation is risk-blind — handler.py builds rules from registry.list()).

Key Components:
    - READ_SKILL_TOOL_SPEC + make_read_skill_handler(registry)
    - RUN_SKILL_SCRIPT_TOOL_SPEC + make_run_skill_script_handler(registry, sandbox=None)
    - _get_default_sandbox(): process-wide lazy SandboxBackend (probes Docker once)

Created: 2026-06-13 (Sprint 57.113)
Last Modified: 2026-06-15

Modification History (newest-first):
    - 2026-06-15: Sprint 57.118 — add run_skill_script (run a bundled script via SandboxBackend)
    - 2026-06-14: Sprint 57.115 — use render_skill_instructions (DRY; output byte-identical)
    - 2026-06-13: Initial creation (Sprint 57.113) — read_skill lazy-load tool

Related:
    - agent_harness/skills/registry.py — Skill (+ .script) / SkillRegistry / render_catalog_block
    - agent_harness/tools/sandbox.py — SandboxBackend / default_sandbox (run_skill_script reuses)
    - agent_harness/tools/exec_tools.py — python_sandbox handler (sandbox-call + JSON shape)
    - business_domain/_register_all.py — make_default_executor skill_registry opt-in
"""

from __future__ import annotations

import json
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
from agent_harness.tools.sandbox import SandboxBackend, default_sandbox

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


RUN_SKILL_SCRIPT_TOOL_SPEC: ToolSpec = ToolSpec(
    name="run_skill_script",
    description=(
        "Run the bundled executable script attached to a named skill. The script is "
        "server-controlled (shipped with the skill) and runs in a wall-time / "
        "memory-limited sandbox. Returns JSON with stdout / stderr / exit_code / "
        "duration_seconds / killed_by_timeout. Use when a skill's instructions tell "
        "you to run its script."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "skill_name": {
                "type": "string",
                "description": "The skill name from the Available Skills list.",
            },
        },
        "required": ["skill_name"],
        "additionalProperties": False,
    },
    annotations=ToolAnnotations(
        read_only=False,  # executes the skill's bundled script
        destructive=False,  # sandboxed (network-blocked, resource-capped); not host-destructive
        idempotent=False,
        open_world=False,
    ),
    concurrency_policy=ConcurrencyPolicy.READ_ONLY_PARALLEL,
    hitl_policy=ToolHITLPolicy.AUTO,
    risk_level=RiskLevel.MEDIUM,  # code execution — mirrors python_sandbox
    tags=("skills", "exec"),
)


# === run_skill_script: sandbox backend (lazy, process-wide) ===
# Why (Sprint 57.118 Day-0 refinement): default_sandbox() probes the Docker daemon to
# pick DockerSandbox vs SubprocessSandbox, and make_default_executor runs PER chat
# request — so resolving it at handler-build time would probe Docker on every request.
# A process-wide singleton probes once (first run_skill_script call ever); tests inject
# an explicit backend and never touch the singleton.
_default_sandbox_singleton: SandboxBackend | None = None


def _get_default_sandbox() -> SandboxBackend:
    """Return the process-wide default SandboxBackend (Docker when reachable, else Subprocess)."""
    global _default_sandbox_singleton
    if _default_sandbox_singleton is None:
        _default_sandbox_singleton = default_sandbox()
    return _default_sandbox_singleton


def make_run_skill_script_handler(
    registry: SkillRegistry,
    sandbox: SandboxBackend | None = None,
) -> Callable[[ToolCall], Awaitable[str]]:
    """Build the run_skill_script handler.

    Runs the named skill's SERVER-controlled bundled script (``Skill.script``) via a
    ``SandboxBackend`` — the script source is NEVER an LLM-supplied tool arg (only the
    skill name is). An unknown skill / a skill with no bundled script returns a
    recoverable message (NOT an exception) so the model can correct itself. The backend
    is resolved lazily (``_get_default_sandbox``) unless one is injected (tests).
    """

    async def run_skill_script_handler(call: ToolCall) -> str:
        skill_name = str(call.arguments.get("skill_name", "")).strip()
        skill = registry.get(skill_name)
        if skill is None:
            available = ", ".join(s.name for s in registry.list()) or "(none)"
            return f"Unknown skill {skill_name!r}. Available skills: {available}."
        if skill.script is None:
            return f"Skill {skill_name!r} has no bundled script to run."
        backend = sandbox if sandbox is not None else _get_default_sandbox()
        result = await backend.execute(
            skill.script,
            timeout_seconds=10.0,
            memory_mb=256,
            network_blocked=True,
        )
        return json.dumps(
            {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_code,
                "duration_seconds": round(result.duration_seconds, 3),
                "killed_by_timeout": result.killed_by_timeout,
            }
        )

    return run_skill_script_handler
