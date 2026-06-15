"""
File: backend/tests/unit/agent_harness/skills/test_skills_registry.py
Purpose: Unit tests for SkillRegistry — frontmatter + sibling-script loaders + catalog block.
Category: Tests
Scope: Phase 57 / Sprint 57.113 + 57.118 (Skill.script)
Created: 2026-06-13 (Sprint 57.113)
"""

from __future__ import annotations

import pytest

from agent_harness.skills.registry import (
    Skill,
    SkillRegistry,
    get_default_skill_registry,
    render_catalog_block,
)

_VALID_MD = """---
name: demo-skill
description: A demo skill for tests
---

# Demo
Do the demo thing.

- step one
- step two
"""

_NO_FRONTMATTER_MD = "# Just a heading\nNo frontmatter here.\n"

_MISSING_FIELD_MD = """---
name: only-name
---

Body without a description.
"""


def _write(tmp_path, name: str, text: str) -> None:
    (tmp_path / name).write_text(text, encoding="utf-8")


def test_from_dir_parses_valid_skill(tmp_path) -> None:
    _write(tmp_path, "demo-skill.md", _VALID_MD)
    reg = SkillRegistry.from_dir(tmp_path)
    skill = reg.get("demo-skill")
    assert skill is not None
    assert skill.name == "demo-skill"
    assert skill.description == "A demo skill for tests"
    # body retained (frontmatter stripped), instruction content present
    assert "Do the demo thing." in skill.instructions
    assert "step two" in skill.instructions
    assert "name: demo-skill" not in skill.instructions  # frontmatter not in body


def test_from_dir_skips_malformed_without_crashing(tmp_path) -> None:
    _write(tmp_path, "good.md", _VALID_MD)
    _write(tmp_path, "no-frontmatter.md", _NO_FRONTMATTER_MD)
    _write(tmp_path, "missing-field.md", _MISSING_FIELD_MD)
    reg = SkillRegistry.from_dir(tmp_path)  # must NOT raise
    assert reg.get("demo-skill") is not None
    assert len(reg.list()) == 1  # only the valid one loaded


def test_from_dir_missing_directory_returns_empty(tmp_path) -> None:
    reg = SkillRegistry.from_dir(tmp_path / "does-not-exist")
    assert reg.list() == []


def test_register_duplicate_raises() -> None:
    reg = SkillRegistry()
    reg.register(Skill(name="a", description="d", instructions="i"))
    with pytest.raises(ValueError, match="already registered"):
        reg.register(Skill(name="a", description="d2", instructions="i2"))


def test_get_hit_and_miss() -> None:
    reg = SkillRegistry()
    reg.register(Skill(name="a", description="d", instructions="i"))
    assert reg.get("a") is not None
    assert reg.get("nope") is None


def test_list_is_deterministic_by_insertion(tmp_path) -> None:
    _write(tmp_path, "b-skill.md", _VALID_MD.replace("demo-skill", "b-skill"))
    _write(tmp_path, "a-skill.md", _VALID_MD.replace("demo-skill", "a-skill"))
    reg = SkillRegistry.from_dir(tmp_path)
    # from_dir sorts the glob → a-skill before b-skill, deterministic
    assert [s.name for s in reg.list()] == ["a-skill", "b-skill"]


def test_bundled_skills_load() -> None:
    reg = get_default_skill_registry()
    names = {s.name for s in reg.list()}
    assert {"code-review", "summarize"} <= names
    for name in ("code-review", "summarize"):
        skill = reg.get(name)
        assert skill is not None
        assert skill.description  # non-empty
        assert len(skill.instructions) > 50  # a real body, not a stub


def test_get_default_skill_registry_singleton_stable() -> None:
    assert get_default_skill_registry() is get_default_skill_registry()


def test_render_catalog_block_empty_is_blank() -> None:
    assert render_catalog_block([]) == ""


def test_render_catalog_block_lists_names_and_descriptions() -> None:
    skills = [
        Skill(name="code-review", description="Review code", instructions="..."),
        Skill(name="summarize", description="Condense a thread", instructions="..."),
    ]
    block = render_catalog_block(skills)
    assert "## Available Skills" in block
    assert "read_skill(name)" in block  # the lazy-load instruction
    assert "- code-review: Review code" in block
    assert "- summarize: Condense a thread" in block


# === Sprint 57.118: Skill.script + the sibling-<stem>.py loader ===


def test_skill_script_defaults_none() -> None:
    # The tenant overlay constructs Skill(name, description, instructions) without a
    # script (platform_layer/skills/service.py) — the field must default to None.
    skill = Skill(name="a", description="d", instructions="i")
    assert skill.script is None


def test_from_dir_loads_sibling_script(tmp_path) -> None:
    _write(tmp_path, "demo-skill.md", _VALID_MD)
    _write(tmp_path, "demo-skill.py", "print('hello from the bundled script')\n")
    reg = SkillRegistry.from_dir(tmp_path)
    skill = reg.get("demo-skill")
    assert skill is not None
    assert skill.script == "print('hello from the bundled script')\n"


def test_from_dir_no_sibling_script_is_none(tmp_path) -> None:
    _write(tmp_path, "demo-skill.md", _VALID_MD)  # no sibling .py
    reg = SkillRegistry.from_dir(tmp_path)
    skill = reg.get("demo-skill")
    assert skill is not None
    assert skill.script is None


def test_from_dir_lone_py_is_ignored(tmp_path) -> None:
    # A .py with no matching .md is not a skill (from_dir globs *.md only).
    _write(tmp_path, "orphan.py", "print('no skill here')\n")
    reg = SkillRegistry.from_dir(tmp_path)
    assert reg.list() == []


def test_bundled_skills_have_no_script_by_default() -> None:
    # code-review / summarize ship as text-only (no sibling .py) → script is None.
    reg = get_default_skill_registry()
    for name in ("code-review", "summarize"):
        skill = reg.get(name)
        assert skill is not None
        assert skill.script is None


def test_with_overlay_tenant_skills_have_no_script() -> None:
    # The per-tenant overlay carries text-only DB rows → overlaid skills have script=None.
    bundled = SkillRegistry()
    bundled.register(Skill(name="bundled-a", description="d", instructions="i"))
    overlaid = bundled.with_overlay([Skill(name="tenant-b", description="d", instructions="i")])
    assert overlaid.get("tenant-b") is not None
    assert overlaid.get("tenant-b").script is None  # type: ignore[union-attr]
