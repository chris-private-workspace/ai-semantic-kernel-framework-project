"""
File: backend/src/agent_harness/skills/__init__.py
Purpose: Skills System package — re-exports the registry + the read_skill / run_skill_script tools.
Category: 範疇 5 (Prompt Construction) + 範疇 2 (Tool Layer — read_skill / run_skill_script)
Scope: Phase 57 / Sprint 57.113 (read_skill) + 57.118 (run_skill_script)

Created: 2026-06-13 (Sprint 57.113)
"""

from __future__ import annotations

from agent_harness.skills.registry import (
    Skill,
    SkillRegistry,
    get_default_skill_registry,
    render_catalog_block,
    render_skill_instructions,
)
from agent_harness.skills.tool import (
    READ_SKILL_TOOL_SPEC,
    RUN_SKILL_SCRIPT_TOOL_SPEC,
    make_read_skill_handler,
    make_run_skill_script_handler,
)

__all__ = [
    "READ_SKILL_TOOL_SPEC",
    "RUN_SKILL_SCRIPT_TOOL_SPEC",
    "Skill",
    "SkillRegistry",
    "get_default_skill_registry",
    "make_read_skill_handler",
    "make_run_skill_script_handler",
    "render_catalog_block",
    "render_skill_instructions",
]
