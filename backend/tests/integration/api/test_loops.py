"""
File: backend/tests/integration/api/test_loops.py
Purpose: Integration tests for GET /api/v1/loops (Sprint 57.19 US-B1).
Category: Tests / Integration / API
Scope: Phase 57 / Sprint 57.19 Day 1 / US-B1

Description:
    Mounts loops router on minimal FastAPI app and overrides identity deps
    with a synthetic tenant. Verifies:

    - Happy path: list returns sessions for current tenant with aliased fields
    - Tenant isolation: tenant A cannot see tenant B sessions
    - Cursor pagination: 5 sessions, limit=2 → 3 pages (2 + 2 + 1, last has no next_cursor)
    - Status filter: only sessions matching ?status= returned
    - Since filter: only sessions started after ?since=ISO returned
    - Empty result: no sessions → items=[], next_cursor=None
    - Invalid cursor → 400
    - Field aliasing: total_turns→turn_count, total_tokens→token_usage per D-PRE-SCHEMA-2

Created: 2026-05-17 (Sprint 57.19 Day 1 / US-B1)

Modification History (newest-first):
    - 2026-05-17: Initial creation (Sprint 57.19 Day 1 / US-B1)

Related:
    - api/v1/loops.py (endpoint under test)
    - infrastructure/db/models/sessions.py (Session ORM)
    - sprint-57-19-plan.md §US-B1
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.loops import router as loops_router
from infrastructure.db.models import Tenant
from infrastructure.db.models.sessions import Session as SessionORM
from platform_layer.identity.auth import get_current_tenant
from platform_layer.middleware.tenant_context import get_db_session_with_tenant
from tests.conftest import seed_tenant, seed_user

pytestmark = pytest.mark.asyncio


async def _seed_session(
    db: AsyncSession,
    *,
    tenant: Tenant,
    user_id: UUID,
    status_val: str = "active",
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
    total_turns: int = 0,
    total_tokens: int = 0,
) -> SessionORM:
    row = SessionORM(
        tenant_id=tenant.id,
        user_id=user_id,
        status=status_val,
        total_turns=total_turns,
        total_tokens=total_tokens,
    )
    if started_at is not None:
        row.started_at = started_at
    if ended_at is not None:
        row.ended_at = ended_at
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


def _build_app(*, db_session: AsyncSession, tenant_id: UUID) -> FastAPI:
    app = FastAPI()
    app.include_router(loops_router, prefix="/api/v1")

    async def _override_tenant() -> UUID:
        return tenant_id

    async def _override_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_current_tenant] = _override_tenant
    app.dependency_overrides[get_db_session_with_tenant] = _override_db
    return app


async def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ---------------------------------------------------------------------------
# happy path + field aliasing (D-PRE-SCHEMA-2)
# ---------------------------------------------------------------------------


async def test_list_loops_happy_path(db_session: AsyncSession) -> None:
    tenant = await seed_tenant(db_session, code="LOOPS_HAPPY")
    user = await seed_user(db_session, tenant, email="happy@loops.test")
    await _seed_session(db_session, tenant=tenant, user_id=user.id, total_turns=3, total_tokens=120)
    await _seed_session(db_session, tenant=tenant, user_id=user.id, total_turns=1, total_tokens=40)

    app = _build_app(db_session=db_session, tenant_id=tenant.id)
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/loops")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["items"]) == 2
    item = body["items"][0]
    # D-PRE-SCHEMA-2 aliases: total_turns → turn_count, total_tokens → token_usage
    assert "turn_count" in item
    assert "token_usage" in item
    assert "session_id" in item
    assert "started_at_ms" in item
    assert "status" in item


# ---------------------------------------------------------------------------
# tenant isolation
# ---------------------------------------------------------------------------


async def test_list_loops_tenant_isolation(db_session: AsyncSession) -> None:
    """Tenant A's sessions are invisible to tenant B."""
    tenant_a = await seed_tenant(db_session, code="LOOPS_ISO_A")
    tenant_b = await seed_tenant(db_session, code="LOOPS_ISO_B")
    user_a = await seed_user(db_session, tenant_a, email="a@iso.test")
    user_b = await seed_user(db_session, tenant_b, email="b@iso.test")
    await _seed_session(db_session, tenant=tenant_a, user_id=user_a.id)
    await _seed_session(db_session, tenant=tenant_b, user_id=user_b.id)

    app_a = _build_app(db_session=db_session, tenant_id=tenant_a.id)
    async with await _client(app_a) as ac:
        resp = await ac.get("/api/v1/loops")
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1


# ---------------------------------------------------------------------------
# cursor pagination (5 sessions, limit=2 → 3 pages)
# ---------------------------------------------------------------------------


async def test_list_loops_cursor_pagination(db_session: AsyncSession) -> None:
    tenant = await seed_tenant(db_session, code="LOOPS_PAGE")
    user = await seed_user(db_session, tenant, email="page@loops.test")
    base = datetime.now(UTC)
    # Seed 5 sessions with monotonically older started_at (so DESC order is stable + distinct).
    for i in range(5):
        await _seed_session(
            db_session,
            tenant=tenant,
            user_id=user.id,
            started_at=base - timedelta(minutes=i),
        )

    app = _build_app(db_session=db_session, tenant_id=tenant.id)
    async with await _client(app) as ac:
        page1 = await ac.get("/api/v1/loops?limit=2")
        body1 = page1.json()
        assert len(body1["items"]) == 2
        assert body1["next_cursor"] is not None

        page2 = await ac.get(f"/api/v1/loops?limit=2&cursor={body1['next_cursor']}")
        body2 = page2.json()
        assert len(body2["items"]) == 2
        assert body2["next_cursor"] is not None

        page3 = await ac.get(f"/api/v1/loops?limit=2&cursor={body2['next_cursor']}")
        body3 = page3.json()
        assert len(body3["items"]) == 1
        assert body3["next_cursor"] is None


# ---------------------------------------------------------------------------
# status filter
# ---------------------------------------------------------------------------


async def test_list_loops_status_filter(db_session: AsyncSession) -> None:
    tenant = await seed_tenant(db_session, code="LOOPS_STATUS")
    user = await seed_user(db_session, tenant, email="status@loops.test")
    await _seed_session(db_session, tenant=tenant, user_id=user.id, status_val="active")
    await _seed_session(db_session, tenant=tenant, user_id=user.id, status_val="ended")
    await _seed_session(db_session, tenant=tenant, user_id=user.id, status_val="active")

    app = _build_app(db_session=db_session, tenant_id=tenant.id)
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/loops?status=active")
    body = resp.json()
    assert len(body["items"]) == 2
    assert all(item["status"] == "active" for item in body["items"])


# ---------------------------------------------------------------------------
# since filter
# ---------------------------------------------------------------------------


async def test_list_loops_since_filter(db_session: AsyncSession) -> None:
    tenant = await seed_tenant(db_session, code="LOOPS_SINCE")
    user = await seed_user(db_session, tenant, email="since@loops.test")
    base = datetime.now(UTC)
    await _seed_session(
        db_session, tenant=tenant, user_id=user.id, started_at=base - timedelta(hours=2)
    )
    await _seed_session(
        db_session, tenant=tenant, user_id=user.id, started_at=base - timedelta(minutes=10)
    )
    await _seed_session(
        db_session, tenant=tenant, user_id=user.id, started_at=base - timedelta(minutes=5)
    )

    # URL-encode `+` in timezone offset (`+00:00` → `%2B00:00`) so FastAPI parses correctly.
    from urllib.parse import quote

    cutoff = quote((base - timedelta(minutes=30)).isoformat(), safe="")
    app = _build_app(db_session=db_session, tenant_id=tenant.id)
    async with await _client(app) as ac:
        resp = await ac.get(f"/api/v1/loops?since={cutoff}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # Only the 2 sessions started after cutoff (10m + 5m ago) should appear.
    assert len(body["items"]) == 2


# ---------------------------------------------------------------------------
# empty result
# ---------------------------------------------------------------------------


async def test_list_loops_empty(db_session: AsyncSession) -> None:
    tenant = await seed_tenant(db_session, code="LOOPS_EMPTY")
    app = _build_app(db_session=db_session, tenant_id=tenant.id)
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/loops")
    body = resp.json()
    assert body["items"] == []
    assert body["next_cursor"] is None


# ---------------------------------------------------------------------------
# invalid cursor → 400
# ---------------------------------------------------------------------------


async def test_list_loops_invalid_cursor(db_session: AsyncSession) -> None:
    tenant = await seed_tenant(db_session, code="LOOPS_BADC")
    app = _build_app(db_session=db_session, tenant_id=tenant.id)
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/loops?cursor=not-valid-base64$$$")
    assert resp.status_code == 400
    assert "invalid cursor" in resp.json()["detail"]
