"""
File: backend/tests/integration/agent_harness/state_mgmt/test_message_store.py
Purpose: Integration tests for DBMessageStore against real PostgreSQL (Sprint 57.127).
Category: Tests / 範疇 7
Scope: Phase 57 / Sprint 57.127

Description:
    Real-PG integration tests for the per-session Cat-3 Message ledger
    (AD-ChatV2-Live-MultiTurn-Context):
    - append() + load() round-trip equality (incl. tool_calls fidelity)
    - sequence_num continues from MAX across appends (no collision)
    - tenant isolation: a store bound to tenant_b cannot load tenant_a's rows
    - make_chat_message_store None-guard (legacy / test callers)

Pre-requisite (per tests/conftest.py):
    docker compose -f docker-compose.dev.yml up -d postgres
    cd backend && alembic upgrade head

Created: 2026-06-16 (Sprint 57.127)
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from agent_harness._contracts import Message, ToolCall
from agent_harness.state_mgmt import DBMessageStore
from api.v1.chat._category_factories import make_chat_message_store
from infrastructure.db.models import Session as SessionModel
from tests.conftest import seed_tenant, seed_user


async def _build_session(
    db_session: AsyncSession, *, tenant_code: str = "MSGSTORE_TEST"
) -> tuple[SessionModel, object]:
    """Seed tenant + user + session row; return (session, tenant)."""
    tenant = await seed_tenant(db_session, code=tenant_code)
    user = await seed_user(db_session, tenant, email=f"{tenant_code.lower()}@test.com")
    session_row = SessionModel(tenant_id=tenant.id, user_id=user.id)
    db_session.add(session_row)
    await db_session.flush()
    await db_session.refresh(session_row)
    return session_row, tenant


@pytest.mark.asyncio
async def test_append_load_round_trip(db_session: AsyncSession) -> None:
    """append() then load() returns the messages verbatim, incl. tool_calls."""
    session_row, tenant = await _build_session(db_session, tenant_code="RT")
    store = DBMessageStore(db_session, session_id=session_row.id, tenant_id=tenant.id)

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
async def test_sequence_continues_across_appends(db_session: AsyncSession) -> None:
    """A 2nd append continues sequence_num from MAX — no collision, ordered load."""
    session_row, tenant = await _build_session(db_session, tenant_code="SEQ")
    store = DBMessageStore(db_session, session_id=session_row.id, tenant_id=tenant.id)

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
async def test_cross_tenant_load_returns_empty(db_session: AsyncSession) -> None:
    """A store bound to a different tenant cannot read another tenant's ledger (鐵律)."""
    session_row, tenant_a = await _build_session(db_session, tenant_code="TENANT_A")
    store_a = DBMessageStore(db_session, session_id=session_row.id, tenant_id=tenant_a.id)
    await store_a.append([Message(role="user", content="tenant A secret")], turn_num=0)

    # A store bound to a DIFFERENT tenant id, same session_id → must see nothing.
    store_b = DBMessageStore(db_session, session_id=session_row.id, tenant_id=uuid4())
    assert await store_b.load() == []
    # tenant A still sees its row.
    assert len(await store_a.load()) == 1


@pytest.mark.asyncio
async def test_append_empty_is_noop(db_session: AsyncSession) -> None:
    """append([]) writes nothing (guard)."""
    session_row, tenant = await _build_session(db_session, tenant_code="EMPTY")
    store = DBMessageStore(db_session, session_id=session_row.id, tenant_id=tenant.id)
    await store.append([], turn_num=0)
    assert await store.load() == []


def test_factory_none_guard() -> None:
    """make_chat_message_store returns None when db / session / tenant is missing."""
    sid, tid = uuid4(), uuid4()
    assert make_chat_message_store(None, sid, tid) is None
    assert make_chat_message_store(object(), None, tid) is None  # type: ignore[arg-type]
    assert make_chat_message_store(object(), sid, None) is None  # type: ignore[arg-type]
