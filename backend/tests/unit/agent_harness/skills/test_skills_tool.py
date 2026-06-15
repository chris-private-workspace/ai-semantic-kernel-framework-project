"""
File: backend/tests/unit/agent_harness/skills/test_skills_tool.py
Purpose: Unit tests for the read_skill + run_skill_script tools (run / recovery / spec validity).
Category: Tests
Scope: Phase 57 / Sprint 57.113 (read_skill) + 57.118 (run_skill_script)
Created: 2026-06-13 (Sprint 57.113)
"""

from __future__ import annotations

import json

import pytest

from agent_harness._contracts import ToolCall
from agent_harness.skills.registry import Skill, SkillRegistry
from agent_harness.skills.tool import (
    READ_SKILL_TOOL_SPEC,
    RUN_SKILL_SCRIPT_TOOL_SPEC,
    make_read_skill_handler,
    make_run_skill_script_handler,
)
from agent_harness.tools.registry import ToolRegistryImpl
from agent_harness.tools.sandbox import SandboxBackend, SandboxResult


def _registry() -> SkillRegistry:
    reg = SkillRegistry()
    reg.register(
        Skill(name="code-review", description="Review code", instructions="Do the review.")
    )
    return reg


class _StubSandbox(SandboxBackend):
    """A SandboxBackend that records the executed code and returns a canned result."""

    def __init__(self, result: SandboxResult) -> None:
        self._result = result
        self.executed_code: str | None = None

    async def execute(
        self,
        code: str,
        *,
        timeout_seconds: float,
        memory_mb: int,
        network_blocked: bool = True,
    ) -> SandboxResult:
        self.executed_code = code
        return self._result


@pytest.mark.asyncio
async def test_read_skill_returns_framed_instructions() -> None:
    handler = make_read_skill_handler(_registry())
    out = await handler(ToolCall(id="1", name="read_skill", arguments={"name": "code-review"}))
    assert "# Skill: code-review" in out
    assert "Do the review." in out
    assert "Follow these instructions" in out


@pytest.mark.asyncio
async def test_read_skill_unknown_is_recoverable_not_raised() -> None:
    handler = make_read_skill_handler(_registry())
    out = await handler(ToolCall(id="1", name="read_skill", arguments={"name": "nope"}))
    assert "Unknown skill" in out
    assert "code-review" in out  # lists the available skills so the model can recover


@pytest.mark.asyncio
async def test_read_skill_missing_arg_is_recoverable() -> None:
    handler = make_read_skill_handler(_registry())
    out = await handler(ToolCall(id="1", name="read_skill", arguments={}))
    assert "Unknown skill" in out


def test_read_skill_spec_registers_in_tool_registry() -> None:
    # The spec must survive ToolRegistryImpl.register (valid Draft-2012 input_schema).
    reg = ToolRegistryImpl()
    reg.register(READ_SKILL_TOOL_SPEC)
    assert any(s.name == "read_skill" for s in reg.list())


# === Sprint 57.118: run_skill_script (runs a skill's bundled script via SandboxBackend) ===


def _script_registry() -> SkillRegistry:
    reg = SkillRegistry()
    reg.register(
        Skill(
            name="digest",
            description="Compute a digest",
            instructions="Run the script.",
            script="print('computed-value')\n",
        )
    )
    reg.register(Skill(name="text-only", description="No script", instructions="Just text."))
    return reg


@pytest.mark.asyncio
async def test_run_skill_script_runs_via_sandbox() -> None:
    stub = _StubSandbox(
        SandboxResult(
            stdout="computed-value\n",
            stderr="",
            exit_code=0,
            duration_seconds=0.012,
            killed_by_timeout=False,
        )
    )
    handler = make_run_skill_script_handler(_script_registry(), sandbox=stub)
    out = await handler(
        ToolCall(id="1", name="run_skill_script", arguments={"skill_name": "digest"})
    )
    # The SERVER-controlled script source (not an LLM arg) is what ran.
    assert stub.executed_code == "print('computed-value')\n"
    payload = json.loads(out)
    assert payload["stdout"] == "computed-value\n"
    assert payload["exit_code"] == 0
    assert payload["killed_by_timeout"] is False


@pytest.mark.asyncio
async def test_run_skill_script_unknown_skill_recoverable() -> None:
    stub = _StubSandbox(
        SandboxResult(
            stdout="", stderr="", exit_code=0, duration_seconds=0.0, killed_by_timeout=False
        )
    )
    handler = make_run_skill_script_handler(_script_registry(), sandbox=stub)
    out = await handler(ToolCall(id="1", name="run_skill_script", arguments={"skill_name": "nope"}))
    assert "Unknown skill" in out
    assert "digest" in out  # lists the available skills
    assert stub.executed_code is None  # nothing ran


@pytest.mark.asyncio
async def test_run_skill_script_no_script_recoverable() -> None:
    stub = _StubSandbox(
        SandboxResult(
            stdout="", stderr="", exit_code=0, duration_seconds=0.0, killed_by_timeout=False
        )
    )
    handler = make_run_skill_script_handler(_script_registry(), sandbox=stub)
    out = await handler(
        ToolCall(id="1", name="run_skill_script", arguments={"skill_name": "text-only"})
    )
    assert "no bundled script" in out
    assert stub.executed_code is None  # a text-only skill never reaches the sandbox


def test_run_skill_script_spec_registers_in_tool_registry() -> None:
    reg = ToolRegistryImpl()
    reg.register(RUN_SKILL_SCRIPT_TOOL_SPEC)
    assert any(s.name == "run_skill_script" for s in reg.list())
