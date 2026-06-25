"""
File: backend/tests/integration/agent_harness/state_mgmt/test_message_store.py
Purpose: Integration tests for DBMessageStore against real PostgreSQL (Sprint 57.127 + 57.143).
Category: Tests / 範疇 7
Scope: Phase 57 / Sprint 57.127 (ledger) + Sprint 57.143 (own-session durability)

Description:
    Real-PG integration tests for the per-session Cat-3 Message ledger
    (AD-ChatV2-Live-MultiTurn-Context + AD-UserStop-Resume-Context):
    - append() + load() round-trip equality (incl. tool_calls fidelity)
    - sequence_num continues from MAX across appends (no collision)
    - tenant isolation: a store bound to tenant_b cannot load tenant_a's rows
    - append() survives the request session being rolled back (the user-Stop case)
    - make_chat_message_store None-guard (legacy / test callers)

    Sprint 57.143 ctor change: DBMessageStore now takes a session FACTORY and
    opens its OWN tenant-scoped session per call (set_config + commit). So the
    seed (tenant/user/session) must be COMMITTED for the store's own session to
    see it (FK), and committed rows are cleaned by deleting the tenant (FK CASCADE
    drops users/sessions/messages) — mirrors tests/integration/api/conftest.py's
    _clear_committed_test_tenants pattern (committed-endpoint test cleanup).

Pre-requisite (per tests/conftest.py):
    docker compose -f docker-compose.dev.yml up -d postgres
    cd backend && alembic upgrade head

Created: 2026-06-16 (Sprint 57.127)

Modification History (newest-first):
    - 2026-06-25: Sprint 57.143 — own-session ctor + committed-seed fixture + durability test
    - 2026-06-16: Initial creation (Sprint 57.127)
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from agent_harness._contracts import Message, ToolCall
from agent_harness.state_mgmt import DBMessageStore
from api.v1.chat._category_factories import make_chat_message_store
from infrastructure.db import get_session_factory
from infrastructure.db.models import Session as SessionModel
from tests.conftest import seed_tenant, seed_user


@pytest_asyncio.fixture
async def committed_session(db_session: AsyncSession) -> AsyncIterator[tuple[object, object]]:
    """Seed tenant/user/session and COMMIT, then yield (session_id, tenant_id).

    The 57.143 DBMessageStore opens its OWN session per call, so the seed must be
    committed for that session to satisfy the message → session FK. Cleanup deletes
    the tenant (FK CASCADE drops user/session/messages), keeping the suite isolated
    despite the real commits (mirrors the api/conftest committed-test sweep).
    """
    tenant = await seed_tenant(db_session, code=f"MSGDUR_{uuid4().hex[:8]}")
    user = await seed_user(db_session, tenant, email=f"{uuid4().hex[:8]}@test.com")
    session_row = SessionModel(tenant_id=tenant.id, user_id=user.id)
    db_session.add(session_row)
    await db_session.flush()
    await db_session.refresh(session_row)
    sid, tid = session_row.id, tenant.id
    await db_session.commit()
    try:
        yield sid, tid
    finally:
        factory = get_session_factory()
        async with factory() as s:
            await s.execute(text("DELETE FROM tenants WHERE id = :tid"), {"tid": str(tid)})
            await s.commit()


@pytest.mark.asyncio
async def test_append_load_round_trip(committed_session: tuple[object, object]) -> None:
    """append() then load() returns the messages verbatim, incl. tool_calls."""
    sid, tid = committed_session
    store = DBMessageStore(get_session_factory(), session_id=sid, tenant_id=tid)

    sent = [
        Message(role="user", content="What is the capital of France?"),
        Message(
            role="assistant",
            content="Let me look that up.",
            tool_calls=[ToolCall(id="tc1", name="search", arguments={"q": "France capital"})],
        ),
        Message(role="tool", content="Paris", tool_call_id="tc1"),
        Message(role="assistant", content="The capital of France is Paris."),
    ]
    await store.append(sent, turn_num=0)

    loaded = await store.load()
    assert [m.role for m in loaded] == ["user", "assistant", "tool", "assistant"]
    assert loaded[0].content == "What is the capital of France?"
    assert loaded[3].content == "The capital of France is Paris."
    # tool_calls fidelity (the reason Approach A was chosen over event-reconstruction)
    assert loaded[1].tool_calls is not None
    assert loaded[1].tool_calls[0].id == "tc1"
    assert loaded[1].tool_calls[0].name == "search"
    assert loaded[1].tool_calls[0].arguments == {"q": "France capital"}
    assert loaded[2].tool_call_id == "tc1"


@pytest.mark.asyncio
async def test_sequence_continues_across_appends(committed_session: tuple[object, object]) -> None:
    """A 2nd append continues sequence_num from MAX — no collision, ordered load."""
    sid, tid = committed_session
    store = DBMessageStore(get_session_factory(), session_id=sid, tenant_id=tid)

    # send 1
    await store.append(
        [
            Message(role="user", content="capital of France?"),
            Message(role="assistant", content="Paris"),
        ],
        turn_num=0,
    )
    # send 2 (a follow-up — the multi-turn case)
    await store.append(
        [
            Message(role="user", content="its population?"),
            Message(role="assistant", content="About 2.1 million"),
        ],
        turn_num=1,
    )

    loaded = await store.load()
    # globally monotonic, send-1 then send-2 (ORDER BY sequence_num)
    assert [m.content for m in loaded] == [
        "capital of France?",
        "Paris",
        "its population?",
        "About 2.1 million",
    ]


@pytest.mark.asyncio
async def test_cross_tenant_load_returns_empty(committed_session: tuple[object, object]) -> None:
    """A store bound to a different tenant cannot read another tenant's ledger (鐵律)."""
    sid, tenant_a_id = committed_session
    store_a = DBMessageStore(get_session_factory(), session_id=sid, tenant_id=tenant_a_id)
    await store_a.append([Message(role="user", content="tenant A secret")], turn_num=0)

    # A store bound to a DIFFERENT tenant id, same session_id → must see nothing.
    store_b = DBMessageStore(get_session_factory(), session_id=sid, tenant_id=uuid4())
    assert await store_b.load() == []
    # tenant A still sees its row.
    assert len(await store_a.load()) == 1


@pytest.mark.asyncio
async def test_append_survives_request_session_rollback(
    db_session: AsyncSession, committed_session: tuple[object, object]
) -> None:
    """AD-UserStop-Resume-Context: an append commits in its OWN session, so it
    survives the SSE request transaction being rolled back (the user-Stop disconnect
    case — the bug this sprint fixes). A pre-57.143 SAVEPOINT-on-request-session
    append would vanish on this rollback."""
    sid, tid = committed_session
    store = DBMessageStore(get_session_factory(), session_id=sid, tenant_id=tid)
    await store.append([Message(role="user", content="interrupted question")], turn_num=0)

    # Simulate the SSE request dying (client disconnect → get_db_session rollback).
    await db_session.rollback()

    # A fresh store (a brand-new own session) STILL sees the durably-committed row.
    fresh = DBMessageStore(get_session_factory(), session_id=sid, tenant_id=tid)
    loaded = await fresh.load()
    assert [m.content for m in loaded] == ["interrupted question"]


@pytest.mark.asyncio
async def test_append_empty_is_noop(committed_session: tuple[object, object]) -> None:
    """append([]) writes nothing (guard)."""
    sid, tid = committed_session
    store = DBMessageStore(get_session_factory(), session_id=sid, tenant_id=tid)
    await store.append([], turn_num=0)
    assert await store.load() == []


def test_factory_none_guard() -> None:
    """make_chat_message_store returns None when db / session / tenant is missing."""
    sid, tid = uuid4(), uuid4()
    assert make_chat_message_store(None, sid, tid) is None
    assert make_chat_message_store(object(), None, tid) is None  # type: ignore[arg-type]
    assert make_chat_message_store(object(), sid, None) is None  # type: ignore[arg-type]
