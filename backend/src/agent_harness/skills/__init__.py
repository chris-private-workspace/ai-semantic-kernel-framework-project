"""
File: backend/src/agent_harness/skills/__init__.py
Purpose: Skills System package — re-exports the registry + the read_skill tool.
Category: 範疇 5 (Prompt Construction) + 範疇 2 (Tool Layer — read_skill)
Scope: Phase 57 / Sprint 57.113

Created: 2026-06-13 (Sprint 57.113)
"""

from __future__ import annotations

from agent_harness.skills.registry import (
    Skill,
    SkillRegistry,
    get_default_skill_registry,
    render_catalog_block,
)
from agent_harness.skills.tool import READ_SKILL_TOOL_SPEC, make_read_skill_handler

__all__ = [
    "READ_SKILL_TOOL_SPEC",
    "Skill",
    "SkillRegistry",
    "get_default_skill_registry",
    "make_read_skill_handler",
    "render_catalog_block",
]
