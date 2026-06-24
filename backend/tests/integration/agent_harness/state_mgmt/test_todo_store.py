"""
File: backend/tests/integration/agent_harness/state_mgmt/test_todo_store.py
Purpose: Integration tests for DBTodoStore against real PostgreSQL (Sprint 57.140).
Category: Tests / 範疇 7
Scope: Phase 57 / Sprint 57.140

Description:
    Real-PG integration tests for the per-session durable todo list (research #1
    task primitive):
    - replace() + load() round-trip equality
    - replace-whole-list: a 2nd replace OVERWRITES (not appends) — 1 row/session
    - tenant isolation: a store bound to tenant_b cannot load tenant_a's row (鐵律)
    - session isolation: a store bound to a different session sees nothing
    - load() on a fresh session → []

Pre-requisite (per tests/conftest.py):
    docker compose -f docker-compose.dev.yml up -d postgres
    cd backend && alembic upgrade head   # must include 0031_session_todos

Created: 2026-06-24 (Sprint 57.140)
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from agent_harness._contracts.todo import Todo
from agent_harness.state_mgmt import DBTodoStore
from infrastructure.db.models import Session as SessionModel
from tests.conftest import seed_tenant, seed_user


async def _build_session(
    db_session: AsyncSession, *, tenant_code: str = "TODOSTORE_TEST"
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
async def test_replace_load_round_trip(db_session: AsyncSession) -> None:
    """replace() then load() returns the todo list verbatim."""
    session_row, tenant = await _build_session(db_session, tenant_code="TODO_RT")
    store = DBTodoStore(db_session, session_id=session_row.id, tenant_id=tenant.id)

    todos = [
        Todo(id="1", title="Gather the requirements", status="completed"),
        Todo(id="2", title="Write the code", status="in_progress"),
        Todo(id="3", title="Run the tests", status="pending"),
    ]
    await store.replace(todos)

    loaded = await store.load()
    assert loaded == todos


@pytest.mark.asyncio
async def test_replace_overwrites_whole_list(db_session: AsyncSession) -> None:
    """A 2nd replace OVERWRITES (CC replace-whole-list) — not appends; 1 row/session."""
    session_row, tenant = await _build_session(db_session, tenant_code="TODO_OVR")
    store = DBTodoStore(db_session, session_id=session_row.id, tenant_id=tenant.id)

    await store.replace([Todo(id="1", title="step one", status="pending")])
    # progress update: mark step one done, add step two
    await store.replace(
        [
            Todo(id="1", title="step one", status="completed"),
            Todo(id="2", title="step two", status="in_progress"),
        ]
    )

    loaded = await store.load()
    assert [(t.id, t.status) for t in loaded] == [
        ("1", "completed"),
        ("2", "in_progress"),
    ]


@pytest.mark.asyncio
async def test_cross_tenant_load_returns_empty(db_session: AsyncSession) -> None:
    """A store bound to a different tenant cannot read another tenant's todos (鐵律)."""
    session_row, tenant_a = await _build_session(db_session, tenant_code="TODO_TA")
    store_a = DBTodoStore(db_session, session_id=session_row.id, tenant_id=tenant_a.id)
    await store_a.replace([Todo(id="1", title="tenant A plan", status="pending")])

    store_b = DBTodoStore(db_session, session_id=session_row.id, tenant_id=uuid4())
    assert await store_b.load() == []
    # tenant A still sees its row.
    assert len(await store_a.load()) == 1


@pytest.mark.asyncio
async def test_cross_session_load_returns_empty(db_session: AsyncSession) -> None:
    """A store bound to a different session sees nothing (per-session scope)."""
    session_row, tenant = await _build_session(db_session, tenant_code="TODO_SESS")
    store = DBTodoStore(db_session, session_id=session_row.id, tenant_id=tenant.id)
    await store.replace([Todo(id="1", title="plan", status="pending")])

    other = DBTodoStore(db_session, session_id=uuid4(), tenant_id=tenant.id)
    assert await other.load() == []


@pytest.mark.asyncio
async def test_load_empty_session(db_session: AsyncSession) -> None:
    """load() on a session with no todos returns []."""
    session_row, tenant = await _build_session(db_session, tenant_code="TODO_EMP")
    store = DBTodoStore(db_session, session_id=session_row.id, tenant_id=tenant.id)
    assert await store.load() == []
