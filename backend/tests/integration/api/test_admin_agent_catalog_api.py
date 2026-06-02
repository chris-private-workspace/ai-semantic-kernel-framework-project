"""
File: backend/tests/integration/api/test_admin_agent_catalog_api.py
Purpose: Integration tests — admin CRUD API for per-tenant AgentSpec definitions.
Category: Tests / Integration / API (Sprint 57.70 Stage-1b — agent_catalog CRUD)
Scope: Sprint 57.70 Stage-1b

Description:
    Verifies api/v1/admin/agents.py:
        - create (201) + row persisted (tenant-scoped) + audit row
        - list returns the tenant's agents
        - update (fields changed + audit) + 404 on unknown id
        - delete (204) + gone + audit + 404 on unknown id
        - 409 on duplicate key
        - 403 without require_admin_platform_role (non-admin caller)
        - cross-tenant: a tenant-A-scoped (non-admin) caller cannot list /
          create / update tenant B's agents (403 via
          require_tenant_match_or_platform_admin); platform admin cannot leak
          tenant B's rows under tenant A's path (tenant-scoped repo).

    Mirrors test_admin_tenant_quotas.py fixture pattern (X-Test-* middleware +
    dependency_overrides). Mutation endpoints commit, so each mutating test
    seeds a uuid4-suffixed AGENT_PUT_% tenant (conftest LIKE sweep cleans up).

Created: 2026-06-02 (Sprint 57.70 Stage-1b)

Modification History (newest-first):
    - 2026-06-02: Initial creation (Sprint 57.70 Stage-1b — agent_catalog admin CRUD)
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Awaitable, Callable
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, Request, Response
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.admin.agents import router as admin_agents_router
from infrastructure.db.models.agent_catalog import AgentCatalog
from infrastructure.db.models.audit import AuditLog
from infrastructure.db.models.identity import Tenant, TenantPlan, TenantState
from infrastructure.db.session import get_db_session
from platform_layer.identity.auth import (
    require_admin_platform_role,
    require_tenant_match_or_platform_admin,
)

pytestmark = pytest.mark.asyncio

_ADMIN_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _build_app(db_session: AsyncSession | None = None, *, override_admin: bool = True) -> FastAPI:
    """Build a test app mounting the agents router.

    When `db_session` is provided, override get_db_session with it. When
    `override_admin` is True (default), also override require_admin_platform_role
    so the admin role check passes (the role check is tested separately via the
    X-Test-* middleware path). Set `override_admin=False` to exercise the real
    auth dependencies using X-Test-User / X-Test-Roles / X-Test-Tenant headers.
    """
    app = FastAPI()
    app.include_router(admin_agents_router, prefix="/api/v1")

    @app.middleware("http")
    async def _populate_test_state(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        user_header = request.headers.get("X-Test-User")
        roles_header = request.headers.get("X-Test-Roles")
        tenant_header = request.headers.get("X-Test-Tenant")
        request.state.user_id = UUID(user_header) if user_header else None
        request.state.roles = json.loads(roles_header) if roles_header else None
        request.state.tenant_id = UUID(tenant_header) if tenant_header else None
        return await call_next(request)

    if db_session is not None:

        async def _override_session() -> AsyncIterator[AsyncSession]:
            yield db_session

        app.dependency_overrides[get_db_session] = _override_session

        if override_admin:

            async def _override_admin() -> UUID:
                return _ADMIN_USER_ID

            app.dependency_overrides[require_admin_platform_role] = _override_admin
            # GET list uses require_tenant_match_or_platform_admin; override it
            # too so the admin-app path passes (the real guard is exercised by
            # the override_admin=False cross-tenant tests).
            app.dependency_overrides[require_tenant_match_or_platform_admin] = _override_admin

    return app


async def _seed_tenant(session: AsyncSession, *, code: str) -> Tenant:
    t = Tenant(
        code=code,
        display_name=f"Tenant {code}",
        state=TenantState.ACTIVE,
        plan=TenantPlan.ENTERPRISE,
    )
    session.add(t)
    await session.flush()
    await session.refresh(t)
    return t


def _unique_code() -> str:
    """Unique tenant code to survive committed-row leakage (conftest sweep)."""
    return f"AGENT_PUT_{uuid4().hex[:8]}"


# =====================================================================
# Create
# =====================================================================


async def test_create_agent_201_and_persists(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    payload = {
        "key": "researcher",
        "name": "Researcher",
        "system_prompt": "You research things.",
        "model": "gpt-4o",
        "allowed_modes": ["fork", "as_tool"],
        "status": "live",
        "meta_data": {"budget": {"max_tokens": 1000}, "tools": ["search"]},
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(f"/api/v1/admin/tenants/{tenant.id}/agents", json=payload)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["key"] == "researcher"
    assert body["tenant_id"] == str(tenant.id)
    assert body["allowed_modes"] == ["fork", "as_tool"]
    assert body["meta_data"]["tools"] == ["search"]

    # Persisted, tenant-scoped.
    row = (
        await db_session.execute(
            select(AgentCatalog).where(
                (AgentCatalog.tenant_id == tenant.id) & (AgentCatalog.key == "researcher")
            )
        )
    ).scalar_one()
    assert row.name == "Researcher"


async def test_create_agent_writes_audit(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            f"/api/v1/admin/tenants/{tenant.id}/agents",
            json={"key": "reviewer", "name": "Reviewer", "system_prompt": "Review."},
        )
    assert resp.status_code == 201, resp.text
    entries = (
        (
            await db_session.execute(
                select(AuditLog)
                .where(AuditLog.tenant_id == tenant.id)
                .where(AuditLog.operation == "agent_catalog.create")
            )
        )
        .scalars()
        .all()
    )
    assert len(entries) == 1
    assert entries[0].resource_type == "agent_catalog"
    assert entries[0].operation_result == "success"


async def test_create_duplicate_key_409(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    body = {"key": "planner", "name": "Planner", "system_prompt": "Plan."}
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        first = await ac.post(f"/api/v1/admin/tenants/{tenant.id}/agents", json=body)
        second = await ac.post(f"/api/v1/admin/tenants/{tenant.id}/agents", json=body)
    assert first.status_code == 201, first.text
    assert second.status_code == 409, second.text


async def test_create_tenant_not_found_404(db_session: AsyncSession) -> None:
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            f"/api/v1/admin/tenants/{uuid4()}/agents",
            json={"key": "x", "name": "X", "system_prompt": "p"},
        )
    assert resp.status_code == 404


# =====================================================================
# List
# =====================================================================


async def test_list_agents_returns_tenant_rows(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post(
            f"/api/v1/admin/tenants/{tenant.id}/agents",
            json={"key": "a1", "name": "A1", "system_prompt": "p1"},
        )
        await ac.post(
            f"/api/v1/admin/tenants/{tenant.id}/agents",
            json={"key": "a2", "name": "A2", "system_prompt": "p2"},
        )
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/agents")
    assert resp.status_code == 200, resp.text
    keys = {item["key"] for item in resp.json()}
    assert {"a1", "a2"}.issubset(keys)


async def test_list_agents_404_tenant_not_found(db_session: AsyncSession) -> None:
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{uuid4()}/agents")
    assert resp.status_code == 404


# =====================================================================
# Update
# =====================================================================


async def test_update_agent_changes_fields_and_audit(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        created = await ac.post(
            f"/api/v1/admin/tenants/{tenant.id}/agents",
            json={"key": "u1", "name": "Old", "system_prompt": "old"},
        )
        agent_id = created.json()["id"]
        upd = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/agents/{agent_id}",
            json={"name": "New", "status": "staging"},
        )
    assert upd.status_code == 200, upd.text
    assert upd.json()["name"] == "New"
    assert upd.json()["status"] == "staging"
    assert upd.json()["key"] == "u1"  # immutable

    entries = (
        (
            await db_session.execute(
                select(AuditLog)
                .where(AuditLog.tenant_id == tenant.id)
                .where(AuditLog.operation == "agent_catalog.update")
            )
        )
        .scalars()
        .all()
    )
    assert len(entries) == 1
    assert "name" in entries[0].operation_data["changed_fields"]


async def test_update_unknown_id_404(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/agents/{uuid4()}",
            json={"name": "Nope"},
        )
    assert resp.status_code == 404


# =====================================================================
# Delete
# =====================================================================


async def test_delete_agent_204_and_gone_and_audit(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        created = await ac.post(
            f"/api/v1/admin/tenants/{tenant.id}/agents",
            json={"key": "d1", "name": "D1", "system_prompt": "p"},
        )
        agent_id = created.json()["id"]
        deleted = await ac.delete(f"/api/v1/admin/tenants/{tenant.id}/agents/{agent_id}")
        listed = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/agents")
    assert deleted.status_code == 204, deleted.text
    keys = {item["key"] for item in listed.json()}
    assert "d1" not in keys

    entries = (
        (
            await db_session.execute(
                select(AuditLog)
                .where(AuditLog.tenant_id == tenant.id)
                .where(AuditLog.operation == "agent_catalog.delete")
            )
        )
        .scalars()
        .all()
    )
    assert len(entries) == 1


async def test_delete_unknown_id_404(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.delete(f"/api/v1/admin/tenants/{tenant.id}/agents/{uuid4()}")
    assert resp.status_code == 404


# =====================================================================
# Auth — 403 without admin role
# =====================================================================


async def test_create_403_without_admin_role(db_session: AsyncSession) -> None:
    """A caller whose JWT roles lack platform-admin → 403 from require_admin_platform_role."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session, override_admin=False)
    transport = ASGITransport(app=app)
    headers = {
        "X-Test-User": str(uuid4()),
        "X-Test-Roles": json.dumps(["user"]),
        "X-Test-Tenant": str(tenant.id),
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            f"/api/v1/admin/tenants/{tenant.id}/agents",
            json={"key": "x", "name": "X", "system_prompt": "p"},
            headers=headers,
        )
    assert resp.status_code == 403, resp.text


async def test_create_401_without_jwt(db_session: AsyncSession) -> None:
    """No JWT context at all → 401."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session, override_admin=False)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            f"/api/v1/admin/tenants/{tenant.id}/agents",
            json={"key": "x", "name": "X", "system_prompt": "p"},
        )
    assert resp.status_code in (401, 403)


# =====================================================================
# Cross-tenant isolation
# =====================================================================


async def test_cross_tenant_list_denied_for_non_admin(db_session: AsyncSession) -> None:
    """A tenant-A-scoped (non-admin) caller listing tenant B's agents → 403."""
    tenant_a = await _seed_tenant(db_session, code=_unique_code())
    tenant_b = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session, override_admin=False)
    transport = ASGITransport(app=app)
    headers = {
        "X-Test-User": str(uuid4()),
        "X-Test-Roles": json.dumps(["user"]),
        "X-Test-Tenant": str(tenant_a.id),
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            f"/api/v1/admin/tenants/{tenant_b.id}/agents",
            headers=headers,
        )
    assert resp.status_code == 403, resp.text


async def test_cross_tenant_update_denied_for_non_admin(db_session: AsyncSession) -> None:
    """A tenant-A-scoped (non-admin) caller updating a tenant-B agent → 403."""
    tenant_a = await _seed_tenant(db_session, code=_unique_code())
    tenant_b = await _seed_tenant(db_session, code=_unique_code())
    # Seed an agent in B via the admin app (committed so it survives).
    admin_app = _build_app(db_session=db_session)
    admin_transport = ASGITransport(app=admin_app)
    async with AsyncClient(transport=admin_transport, base_url="http://test") as ac:
        created = await ac.post(
            f"/api/v1/admin/tenants/{tenant_b.id}/agents",
            json={"key": "bsecret", "name": "BSecret", "system_prompt": "p"},
        )
    agent_id = created.json()["id"]

    app = _build_app(db_session=db_session, override_admin=False)
    transport = ASGITransport(app=app)
    headers = {
        "X-Test-User": str(uuid4()),
        "X-Test-Roles": json.dumps(["user"]),
        "X-Test-Tenant": str(tenant_a.id),
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant_b.id}/agents/{agent_id}",
            json={"name": "Hijack"},
            headers=headers,
        )
    assert resp.status_code == 403, resp.text


async def test_platform_admin_cannot_leak_b_rows_under_a_path(db_session: AsyncSession) -> None:
    """Even a platform admin sees only tenant A's rows when listing /tenants/A/agents
    (tenant-scoped repo) — B's agent never appears under A's path."""
    tenant_a = await _seed_tenant(db_session, code=_unique_code())
    tenant_b = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post(
            f"/api/v1/admin/tenants/{tenant_a.id}/agents",
            json={"key": "aonly", "name": "AOnly", "system_prompt": "p"},
        )
        await ac.post(
            f"/api/v1/admin/tenants/{tenant_b.id}/agents",
            json={"key": "bonly", "name": "BOnly", "system_prompt": "p"},
        )
        list_a = await ac.get(f"/api/v1/admin/tenants/{tenant_a.id}/agents")
    keys_a = {item["key"] for item in list_a.json()}
    assert "aonly" in keys_a
    assert "bonly" not in keys_a
