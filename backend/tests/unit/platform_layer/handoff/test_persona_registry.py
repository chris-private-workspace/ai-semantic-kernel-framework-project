"""
File: backend/tests/unit/platform_layer/handoff/test_persona_registry.py
Purpose: Unit tests for the Cat 11 HANDOFF persona resolution
    (Sprint 57.70 — async per-tenant DB-backed resolve_persona + sync
    resolve_default_persona; replaces the 57.68 sync global stand-in tests).
Category: Tests
Created: 2026-06-02
Modified: 2026-06-02

No live DB: the AgentCatalogRepository symbol that resolve_persona imports is
monkeypatched to a fake; `db` is a bare object() so no asyncpg connection opens.
Covers the resolution chain: DB hit (override) / DB miss → DEFAULT_AGENTS /
unknown → None / inactive row → DEFAULT_AGENTS fallback / DB-error → fallback;
empty/whitespace key → None; sync resolve_default_persona.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import pytest

import platform_layer.handoff.persona_registry as persona_mod
from platform_layer.handoff.persona_registry import (
    DEFAULT_AGENTS,
    resolve_default_persona,
    resolve_persona,
)


class _FakeRow:
    def __init__(self, *, system_prompt: str, is_active: bool = True) -> None:
        self.system_prompt = system_prompt
        self.is_active = is_active


def _patch_repo(
    monkeypatch: pytest.MonkeyPatch,
    *,
    returns: _FakeRow | None = None,
    raises: Exception | None = None,
) -> None:
    """Patch AgentCatalogRepository where resolve_persona imports it (local import)."""
    import infrastructure.db.repositories.agent_catalog_repository as repo_mod

    class _FakeRepo:
        def __init__(self, db: Any) -> None:
            self._db = db

        async def get_by_key(self, *, tenant_id: UUID, key: str) -> Any:
            if raises is not None:
                raise raises
            return returns

    monkeypatch.setattr(repo_mod, "AgentCatalogRepository", _FakeRepo)


# === sync resolve_default_persona =========================================


def test_default_persona_known_returns_prompt() -> None:
    for agent in DEFAULT_AGENTS:
        prompt = resolve_default_persona(agent)
        assert prompt is not None
        assert isinstance(prompt, str)
        assert prompt.strip()


def test_default_persona_trims_whitespace() -> None:
    assert resolve_default_persona("  researcher  ") == DEFAULT_AGENTS["researcher"]


def test_default_persona_unknown_returns_none() -> None:
    assert resolve_default_persona("nonexistent-agent") is None


def test_default_persona_empty_returns_none() -> None:
    assert resolve_default_persona("") is None
    assert resolve_default_persona("   ") is None


# === async resolve_persona (DB catalog → defaults → None) =================


@pytest.mark.asyncio
async def test_resolve_persona_db_hit_overrides_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An active DB catalog row wins over the hardcoded default."""
    _patch_repo(monkeypatch, returns=_FakeRow(system_prompt="CUSTOM tenant prompt"))
    prompt = await resolve_persona(object(), uuid4(), "researcher")  # type: ignore[arg-type]
    assert prompt == "CUSTOM tenant prompt"
    assert prompt != DEFAULT_AGENTS["researcher"]


@pytest.mark.asyncio
async def test_resolve_persona_db_miss_falls_back_to_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No DB row for a known key → the hardcoded DEFAULT_AGENTS prompt."""
    _patch_repo(monkeypatch, returns=None)
    prompt = await resolve_persona(object(), uuid4(), "researcher")  # type: ignore[arg-type]
    assert prompt == DEFAULT_AGENTS["researcher"]


@pytest.mark.asyncio
async def test_resolve_persona_unknown_key_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No DB row + not a default → None (reject)."""
    _patch_repo(monkeypatch, returns=None)
    result = await resolve_persona(object(), uuid4(), "nope-not-real")  # type: ignore[arg-type]
    assert result is None


@pytest.mark.asyncio
async def test_resolve_persona_inactive_row_falls_back_to_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An inactive DB row is ignored → DEFAULT_AGENTS fallback for a known key."""
    _patch_repo(
        monkeypatch,
        returns=_FakeRow(system_prompt="disabled prompt", is_active=False),
    )
    prompt = await resolve_persona(object(), uuid4(), "researcher")  # type: ignore[arg-type]
    assert prompt == DEFAULT_AGENTS["researcher"]


@pytest.mark.asyncio
async def test_resolve_persona_inactive_unknown_key_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Inactive row for an unknown key → no default → None."""
    _patch_repo(
        monkeypatch,
        returns=_FakeRow(system_prompt="disabled", is_active=False),
    )
    result = await resolve_persona(object(), uuid4(), "nope-not-real")  # type: ignore[arg-type]
    assert result is None


@pytest.mark.asyncio
async def test_resolve_persona_db_error_falls_back_to_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A DB lookup error is fail-safe → known key still resolves to the default."""
    _patch_repo(monkeypatch, raises=RuntimeError("db down"))
    prompt = await resolve_persona(object(), uuid4(), "reviewer")  # type: ignore[arg-type]
    assert prompt == DEFAULT_AGENTS["reviewer"]


@pytest.mark.asyncio
async def test_resolve_persona_trims_whitespace(monkeypatch: pytest.MonkeyPatch) -> None:
    """Key is trimmed before both the DB lookup and the default fallback."""
    _patch_repo(monkeypatch, returns=None)
    prompt = await resolve_persona(object(), uuid4(), "  planner  ")  # type: ignore[arg-type]
    assert prompt == DEFAULT_AGENTS["planner"]


@pytest.mark.asyncio
async def test_resolve_persona_empty_key_returns_none_without_db(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Empty / whitespace key short-circuits to None (no DB call)."""

    def _boom(db: Any) -> Any:  # pragma: no cover - must NOT be reached
        raise AssertionError("repo must not be constructed for an empty key")

    monkeypatch.setattr(persona_mod, "AgentCatalogRepository", _boom, raising=False)
    assert await resolve_persona(object(), uuid4(), "") is None  # type: ignore[arg-type]
    assert await resolve_persona(object(), uuid4(), "   ") is None  # type: ignore[arg-type]
