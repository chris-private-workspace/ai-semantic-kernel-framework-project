"""
File: backend/src/agent_harness/skills/registry.py
Purpose: Skills System core — bundled SKILL.md registry + the discovery prompt block.
Category: 範疇 5 (Prompt Construction)
Scope: Phase 57 / Sprint 57.113 (Skills System epic — first thin vertical)

Description:
    A Claude-Code-style skills capability: each skill is a markdown file with a
    YAML frontmatter (`name` + `description`) and a full-instruction body. The
    registry loads the bundled skills once at startup; the cheap name+description
    list is injected into the system prompt (render_catalog_block) so the model
    knows what skills exist without paying for their bodies, and the FULL
    instructions are lazy-loaded on demand via the `read_skill` tool (see tool.py).

    Mirrors the ToolRegistryImpl shape (name-keyed register/get/list) and the
    capability_matrix.from_yaml load pattern (yaml.safe_load). System-bundled
    only this spike — no DB, no tenant_id; per-tenant catalogs are deferred.

Key Components:
    - Skill: frozen value object (name / description / instructions)
    - SkillRegistry: register / get / list + from_dir markdown loader
    - get_default_skill_registry(): module singleton over the bundled/ dir
    - render_catalog_block(skills): the "## Available Skills" system-prompt block
    - render_skill_instructions(skill): one skill's framed body (DRY: read_skill + force-load)

Created: 2026-06-13 (Sprint 57.113)
Last Modified: 2026-06-14

Modification History (newest-first):
    - 2026-06-14: Sprint 57.115 — add render_skill_instructions (DRY body helper)
    - 2026-06-13: Sprint 57.114 — add SkillRegistry.with_overlay (per-tenant overlay primitive)
    - 2026-06-13: Initial creation (Sprint 57.113) — Skills System first vertical

Related:
    - 01-eleven-categories-spec.md §範疇5 — Prompt Construction
    - agent_harness/skills/tool.py — the read_skill lazy-load tool (Cat 2)
    - agent_harness/guardrails/tool/capability_matrix.py — the from_yaml loader precedent
    - claudedocs/5-status/agent-harness-cc-parity-20260607.md row 9 — the cc-parity gap
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import yaml  # type: ignore[import-untyped, unused-ignore]

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Skill:
    """A loadable skill: a cheap name+description plus the full instruction body."""

    name: str
    description: str
    instructions: str


# === Frontmatter parsing ===
# Why: a SKILL.md is `---\n<yaml>\n---\n<body>`. We reuse yaml.safe_load (the
# capability_matrix.from_yaml convention) rather than a hand-rolled key:value
# parser so a description containing ':' / quotes parses correctly. maxsplit=2
# keeps any '---' inside the body (markdown rules / table separators) intact.
def _parse_frontmatter(text: str) -> tuple[dict[str, object], str] | None:
    """Return (frontmatter_dict, body) or None when the file has no valid frontmatter."""
    if not text.lstrip().startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        meta = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None
    if not isinstance(meta, dict):
        return None
    return meta, parts[2].strip()


# === SkillRegistry ===
# Why: mirrors ToolRegistryImpl (name-keyed dict + register/get/list) so the
# Skills capability reads like the rest of the harness. A bad bundled file must
# NOT crash chat startup, so from_dir skips malformed files with a warning
# rather than raising (the registry is loaded eagerly by get_default_*).
class SkillRegistry:
    """A name-keyed registry of Skills loaded from bundled markdown files."""

    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        if skill.name in self._skills:
            raise ValueError(f"Skill '{skill.name}' already registered")
        self._skills[skill.name] = skill

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def list(self) -> list[Skill]:
        return list(self._skills.values())

    # === Per-tenant overlay ===
    # Why: a tenant's custom skills (loaded from the tenant_skills table by
    # platform_layer/skills) are merged ON TOP of the bundled set — a same-name
    # tenant skill REPLACES the bundled body (override-by-name), new names are
    # added, the rest of the bundled set stays. Pure (no DB / no I/O): neither
    # this registry nor the bundled singleton is mutated; a fresh registry is
    # built each call so the resolver can cache it per tenant. Dict insertion
    # order keeps bundled names first, then new tenant names (deterministic).
    def with_overlay(self, extra: Sequence[Skill]) -> "SkillRegistry":
        """Return a NEW registry: this registry's skills with `extra` overlaid by name."""
        merged: dict[str, Skill] = {skill.name: skill for skill in self.list()}
        merged.update({skill.name: skill for skill in extra})
        overlaid = SkillRegistry()
        overlaid._skills = merged
        return overlaid

    @classmethod
    def from_dir(cls, path: str | Path) -> "SkillRegistry":
        """Load every *.md skill from `path` (sorted, deterministic). Skips malformed files."""
        registry = cls()
        directory = Path(path)
        if not directory.is_dir():
            _logger.warning("skills: bundled dir %s not found — no skills loaded", directory)
            return registry
        for md_path in sorted(directory.glob("*.md")):
            try:
                text = md_path.read_text(encoding="utf-8")
            except OSError as exc:  # pragma: no cover - defensive
                _logger.warning("skills: cannot read %s: %s", md_path.name, exc)
                continue
            parsed = _parse_frontmatter(text)
            if parsed is None:
                _logger.warning("skills: skipping %s (no/invalid frontmatter)", md_path.name)
                continue
            meta, body = parsed
            name = meta.get("name")
            description = meta.get("description")
            if not name or not description or not body:
                _logger.warning("skills: skipping %s (missing name/description/body)", md_path.name)
                continue
            try:
                registry.register(
                    Skill(name=str(name), description=str(description), instructions=body)
                )
            except ValueError:
                _logger.warning(
                    "skills: duplicate skill name %r in %s — skipped", name, md_path.name
                )
        return registry


# === Module singleton ===
# Why: the bundled skills are system-global + static (like the tool registry /
# capability matrix), so they load once and are shared across all requests. The
# chat router passes this into build_handler; tests pass an explicit registry.
_BUNDLED_DIR = Path(__file__).parent / "bundled"
_default_registry: SkillRegistry | None = None


def get_default_skill_registry() -> SkillRegistry:
    """Return the process-wide registry of bundled skills (lazy-loaded on first call)."""
    global _default_registry
    if _default_registry is None:
        _default_registry = SkillRegistry.from_dir(_BUNDLED_DIR)
    return _default_registry


# === System-prompt discovery block ===
# Why: the cheap always-on layer — the model sees skill names + descriptions
# (paid every turn, but tiny) and self-selects; the expensive instruction body
# is paid only when it calls read_skill. Empty registry → "" so the system
# prompt is byte-identical to the no-skills path (regression-safe).
def render_catalog_block(skills: list[Skill]) -> str:
    """Render the '## Available Skills' block for the system prompt ('' when no skills)."""
    if not skills:
        return ""
    lines = [
        "## Available Skills",
        (
            "You have skills you can load on demand. When one fits the user's request, "
            "call read_skill(name) to load its full instructions before applying it."
        ),
    ]
    lines.extend(f"- {skill.name}: {skill.description}" for skill in skills)
    return "\n".join(lines)


# === Skill instruction body ===
# Why: the framed full-instruction body for ONE skill. Shared (DRY) by the
# read_skill tool (model-invoked lazy-load, tool.py appends its own trailing
# "Follow these instructions…" line) AND the user-invoked force-load path
# (Sprint 57.115 — build_handler appends this under a "## Active Skill" header
# when the user picks a skill via the /skill-name slash command). Single source
# so the two load paths never drift.
def render_skill_instructions(skill: Skill) -> str:
    """Render a skill's full instruction body ('# Skill: <name>\\n\\n<instructions>')."""
    return f"# Skill: {skill.name}\n\n{skill.instructions}"
