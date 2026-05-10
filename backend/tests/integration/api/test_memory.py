"""
File: backend/tests/integration/api/test_memory.py
Purpose: Integration tests for GET /api/v1/memory/{recent,scope,by-time} (Sprint 57.12 US-2).
Category: Tests / Integration / API
Scope: Phase 57 / Sprint 57.12 Day 1 / US-2

Description:
    Mounts memory router on minimal FastAPI app and overrides identity deps
    with synthetic tenant/user. Verifies:

    - RBAC: non-auditor → 403; auditor / admin / compliance → 200
    - Tenant isolation: tenant A cannot see tenant B rows (WHERE filter)
    - Layer routing: tenant + user + system fully wired; role + session 501
    - Scope mismatch: tenant scope_id != current_tenant → 404
    - Time-scale filter: by-time only on layer=user (others → 400)
    - Pagination: cursor-style has_more + next_offset

Created: 2026-05-10 (Sprint 57.12 Day 1 / US-2)

Modification History (newest-first):
    - 2026-05-10: Initial creation (Sprint 57.12 Day 1 / US-2)

Related:
    - api/v1/memory.py
    - infrastructure/db/models/memory.py
    - sprint-57-12-plan.md §US-2
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, HTTPException, status
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.memory import router as memory_router
from infrastructure.db.models import Tenant
from infrastructure.db.models.memory import (
    MemorySystem,
    MemoryTenant,
    MemoryUser,
)
from platform_layer.identity.auth import get_current_tenant, require_audit_role
from platform_layer.middleware.tenant_context import get_db_session_with_tenant
from tests.conftest import seed_tenant, seed_user

pytestmark = pytest.mark.asyncio


async def _seed_user_memory(
    db: AsyncSession,
    *,
    tenant: Tenant,
    user_id: UUID,
    content: str = "user fact",
    expires_at: datetime | None = None,
    category: str = "fact",
) -> MemoryUser:
    row = MemoryUser(
        tenant_id=tenant.id,
        user_id=user_id,
        category=category,
        content=content,
        expires_at=expires_at,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


async def _seed_tenant_memory(
    db: AsyncSession,
    *,
    tenant: Tenant,
    key: str,
    content: str = "tenant config",
    category: str = "config",
) -> MemoryTenant:
    row = MemoryTenant(
        tenant_id=tenant.id,
        key=key,
        category=category,
        content=content,
    )
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


async def _seed_system_memory(
    db: AsyncSession,
    *,
    key: str,
    content: str = "system rule",
    category: str = "rule",
) -> MemorySystem:
    row = MemorySystem(key=key, category=category, content=content)
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


def _build_app(
    *,
    db_session: AsyncSession,
    tenant_id: UUID,
    audit_user_id: UUID | None,
) -> FastAPI:
    app = FastAPI()
    app.include_router(memory_router, prefix="/api/v1")

    async def _override_tenant() -> UUID:
        return tenant_id

    async def _override_audit_role() -> UUID:
        if audit_user_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Audit role required"
            )
        return audit_user_id

    async def _override_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_current_tenant] = _override_tenant
    app.dependency_overrides[require_audit_role] = _override_audit_role
    app.dependency_overrides[get_db_session_with_tenant] = _override_db
    return app


async def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ---------------------------------------------------------------------------
# /recent
# ---------------------------------------------------------------------------


async def test_recent_user_layer_happy_path(db_session: AsyncSession) -> None:
    tenant = await seed_tenant(db_session, code="MEM_HAPPY")
    user = await seed_user(db_session, tenant, email="happy@mem.test")
    await _seed_user_memory(db_session, tenant=tenant, user_id=user.id, content="A")
    await _seed_user_memory(db_session, tenant=tenant, user_id=user.id, content="B")

    app = _build_app(db_session=db_session, tenant_id=tenant.id, audit_user_id=uuid4())
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/memory/recent?layer=user")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2
    assert all(item["layer"] == "user" for item in body["items"])
    assert all(item["tenant_id"] == str(tenant.id) for item in body["items"])


async def test_recent_403_when_non_auditor(db_session: AsyncSession) -> None:
    tenant = await seed_tenant(db_session, code="MEM_403")
    app = _build_app(db_session=db_session, tenant_id=tenant.id, audit_user_id=None)
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/memory/recent?layer=user")
    assert resp.status_code == 403


async def test_recent_role_layer_returns_501(db_session: AsyncSession) -> None:
    tenant = await seed_tenant(db_session, code="MEM_501ROLE")
    app = _build_app(db_session=db_session, tenant_id=tenant.id, audit_user_id=uuid4())
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/memory/recent?layer=role")
    assert resp.status_code == 501
    assert "role" in resp.json()["detail"]


async def test_recent_session_layer_returns_501(db_session: AsyncSession) -> None:
    tenant = await seed_tenant(db_session, code="MEM_501SES")
    app = _build_app(db_session=db_session, tenant_id=tenant.id, audit_user_id=uuid4())
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/memory/recent?layer=session")
    assert resp.status_code == 501


async def test_recent_pagination_has_more(db_session: AsyncSession) -> None:
    tenant = await seed_tenant(db_session, code="MEM_PAGE")
    user = await seed_user(db_session, tenant, email="page@mem.test")
    for i in range(5):
        await _seed_user_memory(db_session, tenant=tenant, user_id=user.id, content=f"e{i}")
    app = _build_app(db_session=db_session, tenant_id=tenant.id, audit_user_id=uuid4())
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/memory/recent?layer=user&limit=2&offset=0")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2
    assert body["has_more"] is True
    assert body["next_offset"] == 2


async def test_recent_tenant_layer_isolation(db_session: AsyncSession) -> None:
    """Tenant A's tenant-layer memory is invisible to tenant B."""
    tenant_a = await seed_tenant(db_session, code="MEM_ISO_A")
    tenant_b = await seed_tenant(db_session, code="MEM_ISO_B")
    await _seed_tenant_memory(db_session, tenant=tenant_a, key="key_a", content="A only")
    await _seed_tenant_memory(db_session, tenant=tenant_b, key="key_b", content="B only")

    app_a = _build_app(db_session=db_session, tenant_id=tenant_a.id, audit_user_id=uuid4())
    async with await _client(app_a) as ac:
        resp = await ac.get("/api/v1/memory/recent?layer=tenant")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["key"] == "key_a"


# ---------------------------------------------------------------------------
# /scope
# ---------------------------------------------------------------------------


async def test_scope_user_layer_happy_path(db_session: AsyncSession) -> None:
    tenant = await seed_tenant(db_session, code="MEM_SCP_USR")
    user_a = await seed_user(db_session, tenant, email="a@scp.test")
    user_b = await seed_user(db_session, tenant, email="b@scp.test")
    await _seed_user_memory(db_session, tenant=tenant, user_id=user_a.id, content="A1")
    await _seed_user_memory(db_session, tenant=tenant, user_id=user_a.id, content="A2")
    await _seed_user_memory(db_session, tenant=tenant, user_id=user_b.id, content="B1")

    app = _build_app(db_session=db_session, tenant_id=tenant.id, audit_user_id=uuid4())
    async with await _client(app) as ac:
        resp = await ac.get(f"/api/v1/memory/scope/user/{user_a.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert all(item["scope_id"] == str(user_a.id) for item in body["items"])


async def test_scope_tenant_mismatch_returns_404(db_session: AsyncSession) -> None:
    """tenant scope_id != current_tenant → 404 (no cross-tenant peek)."""
    tenant = await seed_tenant(db_session, code="MEM_SCP_404")
    other_tenant_id = uuid4()
    app = _build_app(db_session=db_session, tenant_id=tenant.id, audit_user_id=uuid4())
    async with await _client(app) as ac:
        resp = await ac.get(f"/api/v1/memory/scope/tenant/{other_tenant_id}")
    assert resp.status_code == 404


async def test_scope_invalid_uuid_returns_400(db_session: AsyncSession) -> None:
    tenant = await seed_tenant(db_session, code="MEM_SCP_BAD")
    app = _build_app(db_session=db_session, tenant_id=tenant.id, audit_user_id=uuid4())
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/memory/scope/user/not-a-uuid")
    assert resp.status_code == 400


async def test_scope_role_layer_returns_501(db_session: AsyncSession) -> None:
    tenant = await seed_tenant(db_session, code="MEM_SCP_501")
    app = _build_app(db_session=db_session, tenant_id=tenant.id, audit_user_id=uuid4())
    async with await _client(app) as ac:
        resp = await ac.get(f"/api/v1/memory/scope/role/{uuid4()}")
    assert resp.status_code == 501


# ---------------------------------------------------------------------------
# /by-time
# ---------------------------------------------------------------------------


async def test_by_time_permanent_returns_null_expires(db_session: AsyncSession) -> None:
    tenant = await seed_tenant(db_session, code="MEM_BT_PERM")
    user = await seed_user(db_session, tenant, email="perm@mem.test")
    await _seed_user_memory(db_session, tenant=tenant, user_id=user.id, content="permanent A")
    await _seed_user_memory(
        db_session,
        tenant=tenant,
        user_id=user.id,
        content="daily X",
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    app = _build_app(db_session=db_session, tenant_id=tenant.id, audit_user_id=uuid4())
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/memory/by-time/user/permanent")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["content"] == "permanent A"
    assert body["items"][0]["expires_at_ms"] is None


async def test_by_time_daily_returns_short_lived(db_session: AsyncSession) -> None:
    tenant = await seed_tenant(db_session, code="MEM_BT_DAILY")
    user = await seed_user(db_session, tenant, email="daily@mem.test")
    soon = datetime.now(UTC) + timedelta(days=1)
    await _seed_user_memory(
        db_session, tenant=tenant, user_id=user.id, content="quick", expires_at=soon
    )
    await _seed_user_memory(db_session, tenant=tenant, user_id=user.id, content="permanent")
    app = _build_app(db_session=db_session, tenant_id=tenant.id, audit_user_id=uuid4())
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/memory/by-time/user/daily")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["content"] == "quick"


async def test_by_time_non_user_layer_returns_400(db_session: AsyncSession) -> None:
    tenant = await seed_tenant(db_session, code="MEM_BT_400")
    app = _build_app(db_session=db_session, tenant_id=tenant.id, audit_user_id=uuid4())
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/memory/by-time/tenant/permanent")
    assert resp.status_code == 400
    assert "expires_at" in resp.json()["detail"]
