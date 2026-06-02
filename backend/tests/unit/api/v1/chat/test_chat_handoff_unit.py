"""
File: backend/tests/unit/api/v1/chat/test_chat_handoff_unit.py
Purpose: Unit tests for Sprint 57.68 A-3b handler per-session persona resolution
    (resolve_session_persona).
Category: Tests
Scope: Phase 57 / Sprint 57.68 A-3b (Stage 2)

Description:
    No DB / no network. resolve_session_persona returns the target persona when
    the (fake) session row carries meta_data["agent_role"], and falls back to
    DEMO_SYSTEM_PROMPT otherwise / on missing inputs / unknown role. The
    SessionRepository it imports is monkeypatched to a fake; the `db` argument is
    a bare object() (never a real connection) so these never open an asyncpg
    connection — keeping the unit file DB-connection-free.

    The router post-loop hook tests (emit / fail-soft / skip) that drive the REAL
    _stream_loop_events live in the integration file
    (tests/integration/api/test_chat_handoff.py) where the managed `db_session`
    fixture's dispose_engine() teardown prevents a real connection leaking onto a
    closed event loop (Risk Class C).

Created: 2026-06-02 (Sprint 57.68 A-3b Stage 2)
Last Modified: 2026-06-02 (Sprint 57.70 Stage-1a — stub AgentCatalogRepository for resolve_persona)
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

import pytest

import api.v1.chat.handler as handler_mod
from api.v1.chat.handler import DEMO_SYSTEM_PROMPT, resolve_session_persona
from platform_layer.handoff.context_carry import _CARRIED_CONTEXT_HEADER

# ============================================================
# Handler persona resolution (resolve_session_persona)
# ============================================================


class _FakeSessionRow:
    def __init__(self, meta_data: dict[str, Any] | None) -> None:
        self.meta_data = meta_data


def _patch_repo(monkeypatch: pytest.MonkeyPatch, *, returns: _FakeSessionRow | None) -> None:
    """Patch the SessionRepository + AgentCatalogRepository symbols resolution imports.

    Sprint 57.70: resolve_session_persona resolves the role via the async
    per-tenant resolve_persona, which constructs AgentCatalogRepository(db).
    Stub it to return no catalog row so resolution falls back to the hardcoded
    DEFAULT_AGENTS — keeping this unit file DB-connection-free + deterministic
    (no reliance on the fail-safe exception path).
    """
    import infrastructure.db.repositories.agent_catalog_repository as catalog_mod
    import infrastructure.db.repositories.session_repository as repo_mod

    class _FakeRepo:
        def __init__(self, db: Any) -> None:
            self._db = db

        async def get_session(self, *, session_id: UUID, tenant_id: UUID) -> Any:
            return returns

    class _FakeCatalogRepo:
        def __init__(self, db: Any) -> None:
            self._db = db

        async def get_by_key(self, *, tenant_id: UUID, key: str) -> Any:
            return None  # no per-tenant override → DEFAULT_AGENTS fallback

    monkeypatch.setattr(repo_mod, "SessionRepository", _FakeRepo)
    monkeypatch.setattr(catalog_mod, "AgentCatalogRepository", _FakeCatalogRepo)


@pytest.mark.asyncio
async def test_persona_resolves_target_role(monkeypatch: pytest.MonkeyPatch) -> None:
    """agent_role in meta_data → the target persona system prompt (not DEMO)."""
    _patch_repo(monkeypatch, returns=_FakeSessionRow({"agent_role": "researcher"}))
    prompt = await resolve_session_persona(object(), uuid4(), uuid4())
    assert prompt != DEMO_SYSTEM_PROMPT
    assert "research specialist" in prompt


@pytest.mark.asyncio
async def test_persona_falls_back_when_no_agent_role(monkeypatch: pytest.MonkeyPatch) -> None:
    """A session without agent_role → DEMO_SYSTEM_PROMPT."""
    _patch_repo(monkeypatch, returns=_FakeSessionRow({}))
    prompt = await resolve_session_persona(object(), uuid4(), uuid4())
    assert prompt == DEMO_SYSTEM_PROMPT


@pytest.mark.asyncio
async def test_persona_falls_back_when_session_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """No session row → DEMO_SYSTEM_PROMPT."""
    _patch_repo(monkeypatch, returns=None)
    prompt = await resolve_session_persona(object(), uuid4(), uuid4())
    assert prompt == DEMO_SYSTEM_PROMPT


@pytest.mark.asyncio
async def test_persona_falls_back_when_unknown_role(monkeypatch: pytest.MonkeyPatch) -> None:
    """An unknown agent_role → DEMO_SYSTEM_PROMPT (persona registry miss)."""
    _patch_repo(monkeypatch, returns=_FakeSessionRow({"agent_role": "nope-not-real"}))
    prompt = await resolve_session_persona(object(), uuid4(), uuid4())
    assert prompt == DEMO_SYSTEM_PROMPT


@pytest.mark.asyncio
async def test_persona_falls_back_when_no_db() -> None:
    """No db / session_id / tenant_id → DEMO_SYSTEM_PROMPT (ordinary session)."""
    assert await resolve_session_persona(None, uuid4(), uuid4()) == DEMO_SYSTEM_PROMPT
    assert await resolve_session_persona(object(), None, uuid4()) == DEMO_SYSTEM_PROMPT
    assert await resolve_session_persona(object(), uuid4(), None) == DEMO_SYSTEM_PROMPT


# === Sprint 57.69 A-3b slice 2: carried_context appended to persona ==========


@pytest.mark.asyncio
async def test_persona_appends_carried_context_block(monkeypatch: pytest.MonkeyPatch) -> None:
    """carried_context present → persona prompt embeds the carried-context block."""
    _patch_repo(
        monkeypatch,
        returns=_FakeSessionRow(
            {
                "agent_role": "researcher",
                "carried_context": [
                    {"role": "user", "content": "what is X?"},
                    {"role": "assistant", "content": "X is Y"},
                ],
            }
        ),
    )
    prompt = await resolve_session_persona(object(), uuid4(), uuid4())
    assert prompt != DEMO_SYSTEM_PROMPT
    # Persona prompt still present AND the carried block appended below it.
    assert "research specialist" in prompt
    assert _CARRIED_CONTEXT_HEADER in prompt
    assert "[user] what is X?" in prompt
    assert "[assistant] X is Y" in prompt


@pytest.mark.asyncio
async def test_persona_no_carried_context_is_plain_persona(monkeypatch: pytest.MonkeyPatch) -> None:
    """No carried_context → resolved persona prompt with no carried block."""
    _patch_repo(monkeypatch, returns=_FakeSessionRow({"agent_role": "researcher"}))
    prompt = await resolve_session_persona(object(), uuid4(), uuid4())
    assert "research specialist" in prompt
    assert _CARRIED_CONTEXT_HEADER not in prompt


@pytest.mark.asyncio
async def test_persona_malformed_carried_context_fails_open(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A malformed carried_context never crashes nor loses the resolved persona.

    A non-list / non-dict carried_context makes the render raise; the nested
    fail-open guard returns the persona prompt WITHOUT the carried block.
    """
    # carried_context is a string of dicts-worth of nonsense → render iterates a
    # str → entry.get(...) raises AttributeError → fail-open to persona prompt.
    _patch_repo(
        monkeypatch,
        returns=_FakeSessionRow({"agent_role": "researcher", "carried_context": "not-a-list"}),
    )
    prompt = await resolve_session_persona(object(), uuid4(), uuid4())
    assert "research specialist" in prompt  # persona NOT lost
    assert _CARRIED_CONTEXT_HEADER not in prompt  # carried block omitted


def test_handler_module_exposes_resolve() -> None:
    """resolve_session_persona is importable from the handler module."""
    assert hasattr(handler_mod, "resolve_session_persona")
