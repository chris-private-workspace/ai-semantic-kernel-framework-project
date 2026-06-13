"""
File: backend/tests/unit/agent_harness/skills/test_skills_tool.py
Purpose: Unit tests for the read_skill tool (framed instructions / miss recovery / spec validity).
Category: Tests
Scope: Phase 57 / Sprint 57.113
Created: 2026-06-13 (Sprint 57.113)
"""

from __future__ import annotations

import pytest

from agent_harness._contracts import ToolCall
from agent_harness.skills.registry import Skill, SkillRegistry
from agent_harness.skills.tool import READ_SKILL_TOOL_SPEC, make_read_skill_handler
from agent_harness.tools.registry import ToolRegistryImpl


def _registry() -> SkillRegistry:
    reg = SkillRegistry()
    reg.register(
        Skill(name="code-review", description="Review code", instructions="Do the review.")
    )
    return reg


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
