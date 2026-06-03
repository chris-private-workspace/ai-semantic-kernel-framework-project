"""
File: backend/tests/integration/api/test_memory_matrix.py
Purpose: Integration tests for GET /api/v1/memory/matrix (Sprint 57.73 Track B).
Category: Tests / Integration / API
Scope: Phase 57 / Sprint 57.73 Track B

Description:
    Mounts memory router on minimal FastAPI app and overrides identity deps
    with synthetic tenant/user (mirrors test_memory.py). Verifies the
    layer×time_scale count aggregate:

    - Happy path: system + tenant + user (varied expires_at) cells + total
    - gapped_layers == [role, session]
    - Cross-tenant isolation: tenant A excludes tenant B's tenant/user rows
    - Empty → total == 0, cells == []

Created: 2026-06-03 (Sprint 57.73 Track B)

Modification History (newest-first):
    - 2026-06-03: Initial creation (Sprint 57.73 Track B)

Related:
    - api/v1/memory.py (get_matrix)
    - tests/integration/api/test_memory.py (fixture pattern reuse)
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
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Audit role required")
        return audit_user_id

    async def _override_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_current_tenant] = _override_tenant
    app.dependency_overrides[require_audit_role] = _override_audit_role
    app.dependency_overrides[get_db_session_with_tenant] = _override_db
    return app


async def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _cell(body: dict, layer: str, time_scale: str) -> int | None:
    """Return count for a (layer, time_scale) cell, or None if absent (omitted)."""
    for c in body["cells"]:
        if c["layer"] == layer and c["time_scale"] == time_scale:
            return int(c["count"])
    return None


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


async def test_matrix_happy_path_all_layers(db_session: AsyncSession) -> None:
    """system + tenant + user (permanent/quarterly/daily) → correct cells + total."""
    tenant = await seed_tenant(db_session, code="MX_HAPPY")
    user = await seed_user(db_session, tenant, email="happy@mx.test")

    await _seed_system_memory(db_session, key="mx_sys_1")
    await _seed_tenant_memory(db_session, tenant=tenant, key="mx_tnt_1")
    await _seed_tenant_memory(db_session, tenant=tenant, key="mx_tnt_2")

    # user: 1 permanent (NULL), 1 quarterly (>30d), 2 daily (<=30d)
    await _seed_user_memory(db_session, tenant=tenant, user_id=user.id, content="perm")
    await _seed_user_memory(
        db_session,
        tenant=tenant,
        user_id=user.id,
        content="quarterly",
        expires_at=datetime.now(UTC) + timedelta(days=90),
    )
    await _seed_user_memory(
        db_session,
        tenant=tenant,
        user_id=user.id,
        content="daily 1",
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    await _seed_user_memory(
        db_session,
        tenant=tenant,
        user_id=user.id,
        content="daily 2",
        expires_at=datetime.now(UTC) + timedelta(days=5),
    )

    app = _build_app(db_session=db_session, tenant_id=tenant.id, audit_user_id=uuid4())
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/memory/matrix")
    assert resp.status_code == 200
    body = resp.json()

    assert _cell(body, "system", "permanent") == 1
    assert _cell(body, "tenant", "permanent") == 2
    assert _cell(body, "user", "permanent") == 1
    assert _cell(body, "user", "quarterly") == 1
    assert _cell(body, "user", "daily") == 2
    # total = 1 + 2 + 1 + 1 + 2 = 7
    assert body["total"] == 7


async def test_matrix_gapped_layers_reported_not_queried(db_session: AsyncSession) -> None:
    tenant = await seed_tenant(db_session, code="MX_GAP")
    app = _build_app(db_session=db_session, tenant_id=tenant.id, audit_user_id=uuid4())
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/memory/matrix")
    assert resp.status_code == 200
    assert resp.json()["gapped_layers"] == ["role", "session"]


async def test_matrix_omits_zero_cells(db_session: AsyncSession) -> None:
    """Layers with no rows produce no cell (FE defaults absent → 0)."""
    tenant = await seed_tenant(db_session, code="MX_OMIT")
    user = await seed_user(db_session, tenant, email="omit@mx.test")
    # only one user permanent row; no system, no tenant, no user daily/quarterly
    await _seed_user_memory(db_session, tenant=tenant, user_id=user.id, content="only")
    app = _build_app(db_session=db_session, tenant_id=tenant.id, audit_user_id=uuid4())
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/memory/matrix")
    assert resp.status_code == 200
    body = resp.json()
    assert _cell(body, "user", "permanent") == 1
    assert _cell(body, "user", "daily") is None
    assert _cell(body, "user", "quarterly") is None
    assert _cell(body, "tenant", "permanent") is None
    assert body["total"] == 1


# ---------------------------------------------------------------------------
# Cross-tenant isolation (multi-tenant-data.md 鐵律)
# ---------------------------------------------------------------------------


async def test_matrix_cross_tenant_isolation(db_session: AsyncSession) -> None:
    """Tenant A's matrix EXCLUDES tenant B's tenant + user rows."""
    tenant_a = await seed_tenant(db_session, code="MX_ISO_A")
    tenant_b = await seed_tenant(db_session, code="MX_ISO_B")
    user_a = await seed_user(db_session, tenant_a, email="a@mxiso.test")
    user_b = await seed_user(db_session, tenant_b, email="b@mxiso.test")

    # tenant A: 1 tenant-mem, 1 user-mem (permanent)
    await _seed_tenant_memory(db_session, tenant=tenant_a, key="iso_a")
    await _seed_user_memory(db_session, tenant=tenant_a, user_id=user_a.id, content="A only")

    # tenant B: 2 tenant-mem, 3 user-mem (should be invisible to A)
    await _seed_tenant_memory(db_session, tenant=tenant_b, key="iso_b1")
    await _seed_tenant_memory(db_session, tenant=tenant_b, key="iso_b2")
    await _seed_user_memory(db_session, tenant=tenant_b, user_id=user_b.id, content="B1")
    await _seed_user_memory(db_session, tenant=tenant_b, user_id=user_b.id, content="B2")
    await _seed_user_memory(db_session, tenant=tenant_b, user_id=user_b.id, content="B3")

    app_a = _build_app(db_session=db_session, tenant_id=tenant_a.id, audit_user_id=uuid4())
    async with await _client(app_a) as ac:
        resp = await ac.get("/api/v1/memory/matrix")
    assert resp.status_code == 200
    body = resp.json()
    assert _cell(body, "tenant", "permanent") == 1  # A only, not 3
    assert _cell(body, "user", "permanent") == 1  # A only, not 4
    # total counts only A's rows (system is global; none seeded here)
    assert body["total"] == 2


# ---------------------------------------------------------------------------
# Empty + RBAC
# ---------------------------------------------------------------------------


async def test_matrix_empty_total_zero(db_session: AsyncSession) -> None:
    tenant = await seed_tenant(db_session, code="MX_EMPTY")
    app = _build_app(db_session=db_session, tenant_id=tenant.id, audit_user_id=uuid4())
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/memory/matrix")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 0
    assert body["cells"] == []
    assert body["gapped_layers"] == ["role", "session"]


async def test_matrix_403_when_non_auditor(db_session: AsyncSession) -> None:
    tenant = await seed_tenant(db_session, code="MX_403")
    app = _build_app(db_session=db_session, tenant_id=tenant.id, audit_user_id=None)
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/memory/matrix")
    assert resp.status_code == 403
