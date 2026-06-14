"""
File: backend/tests/unit/agent_harness/skills/test_render_skill_instructions.py
Purpose: Unit tests for render_skill_instructions (DRY body helper; 57.115 US-1).
Category: Tests / Unit (範疇 5 Prompt Construction — Skills System)
Created: 2026-06-14 (Sprint 57.115)

The helper is the single source for a skill's framed instruction body, shared by
the read_skill tool and the force-load path. The key guarantee: the read_skill
tool's returned string is BYTE-IDENTICAL after the DRY refactor (the helper +
the tool's own trailing directive line reproduce the pre-57.115 literal exactly).
"""

from __future__ import annotations

import pytest

from agent_harness._contracts import ToolCall
from agent_harness.skills import Skill, render_skill_instructions
from agent_harness.skills.registry import SkillRegistry
from agent_harness.skills.tool import make_read_skill_handler


def test_render_skill_instructions_shape() -> None:
    skill = Skill(name="release-notes", description="d", instructions="Heading / Highlights")
    assert render_skill_instructions(skill) == "# Skill: release-notes\n\nHeading / Highlights"


def test_render_skill_instructions_no_trailing_directive() -> None:
    # The trailing "Follow these instructions…" line is TOOL-local, NOT part of
    # the shared body (the force-load path frames it under "## Active Skill").
    skill = Skill(name="s", description="d", instructions="body")
    assert "Follow these instructions" not in render_skill_instructions(skill)


@pytest.mark.asyncio
async def test_read_skill_output_byte_identical_after_dry_refactor() -> None:
    reg = SkillRegistry()
    reg.register(
        Skill(name="code-review", description="Review code", instructions="Do the review.")
    )
    handler = make_read_skill_handler(reg)
    out = await handler(ToolCall(id="1", name="read_skill", arguments={"name": "code-review"}))
    # The exact pre-refactor literal (Sprint 57.113 tool.py) — must not drift.
    assert out == (
        "# Skill: code-review\n\n"
        "Do the review.\n\n"
        "Follow these instructions for the current task."
    )
