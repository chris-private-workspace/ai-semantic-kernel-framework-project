"""
File: backend/tests/integration/api/test_admin_tenant_skills.py
Purpose: Integration tests — /admin/tenants/{id}/skills CRUD (Sprint 57.114 per-tenant catalog).
Category: Tests / Integration / API (Skills System per-tenant catalog)
Scope: Sprint 57.114 / US-4 + 57.117 quota/body-size

Description:
    Verifies the per-tenant Skills admin endpoints (mirrors the model-policy C1
    integration test):
    - POST: 401/403 without admin, 404 missing tenant, 422 (extra field / non-kebab
      name), 409 duplicate (tenant, name), 201 persists + audit
    - GET: lists the tenant's skills (scoped)
    - PUT: 200 update, 404 missing skill, cross-tenant write → 404
    - DELETE: 204, 404 missing skill
    - Multi-tenant isolation (B never lists A's skill; cross-tenant PUT → 404)
    - The resolver TTL cache is invalidated by a create (next resolve reflects it)
    - 57.117: 409 over the per-tenant quota, 422 oversized instructions, GET list
      carries max_skills / max_instructions_chars
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

from api.v1.admin.tenants import router as admin_tenants_router
from infrastructure.db.models.audit import AuditLog
from infrastructure.db.models.identity import Tenant, TenantPlan, TenantState
from infrastructure.db.session import get_db_session
from platform_layer.identity.auth import require_admin_platform_role
from platform_layer.skills.service import (
    SKILLS_MAX_INSTRUCTIONS_CHARS,
    SKILLS_MAX_PER_TENANT,
    resolve_tenant_skill_registry,
)

pytestmark = pytest.mark.asyncio


def _build_app(db_session: AsyncSession | None = None) -> FastAPI:
    app = FastAPI()
    app.include_router(admin_tenants_router, prefix="/api/v1")

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

        async def _override_admin() -> UUID:
            return UUID("00000000-0000-0000-0000-000000000001")

        app.dependency_overrides[get_db_session] = _override_session
        app.dependency_overrides[require_admin_platform_role] = _override_admin

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
    """Unique tenant code; conftest sweeps SKILL_ADMIN_% (committing endpoints leak rows)."""
    return f"SKILL_ADMIN_{uuid4().hex[:8]}"


def _payload(name: str = "release-notes") -> dict[str, str]:
    return {
        "name": name,
        "description": "Turn a changelog into a release note",
        "instructions": "Heading / Highlights / Upgrade notes",
    }


# === auth + 404 ===============================================================


async def test_create_requires_admin_role() -> None:
    app = _build_app()  # no overrides → real require_admin_platform_role
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(f"/api/v1/admin/tenants/{uuid4()}/skills", json=_payload())
    assert resp.status_code in (401, 403)


async def test_create_tenant_not_found(db_session: AsyncSession) -> None:
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(f"/api/v1/admin/tenants/{uuid4()}/skills", json=_payload())
    assert resp.status_code == 404


# === create + list ============================================================


async def test_create_201_then_list(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        created = await ac.post(f"/api/v1/admin/tenants/{tenant.id}/skills", json=_payload())
        listed = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/skills")
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["name"] == "release-notes"
    assert body["description"] == "Turn a changelog into a release note"
    assert body["id"]
    assert listed.status_code == 200
    names = [s["name"] for s in listed.json()["skills"]]
    assert names == ["release-notes"]


async def test_create_duplicate_name_409(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        first = await ac.post(f"/api/v1/admin/tenants/{tenant.id}/skills", json=_payload("dup"))
        second = await ac.post(f"/api/v1/admin/tenants/{tenant.id}/skills", json=_payload("dup"))
    assert first.status_code == 201
    assert second.status_code == 409, second.text


async def test_create_non_kebab_name_422(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(f"/api/v1/admin/tenants/{tenant.id}/skills", json=_payload("Bad Name"))
    assert resp.status_code == 422


async def test_create_extra_field_422(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    body = _payload()
    body["unknown_field"] = "leak"
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(f"/api/v1/admin/tenants/{tenant.id}/skills", json=body)
    assert resp.status_code == 422


# === update ===================================================================


async def test_update_200(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        created = await ac.post(f"/api/v1/admin/tenants/{tenant.id}/skills", json=_payload())
        skill_id = created.json()["id"]
        updated = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/skills/{skill_id}",
            json={"description": "New description"},
        )
    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert body["description"] == "New description"
    assert body["name"] == "release-notes"  # unchanged


async def test_update_skill_not_found_404(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/skills/{uuid4()}",
            json={"description": "x"},
        )
    assert resp.status_code == 404


# === delete ===================================================================


async def test_delete_204_then_gone(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        created = await ac.post(f"/api/v1/admin/tenants/{tenant.id}/skills", json=_payload())
        skill_id = created.json()["id"]
        deleted = await ac.delete(f"/api/v1/admin/tenants/{tenant.id}/skills/{skill_id}")
        listed = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/skills")
    assert deleted.status_code == 204
    assert listed.json()["skills"] == []


async def test_delete_not_found_404(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.delete(f"/api/v1/admin/tenants/{tenant.id}/skills/{uuid4()}")
    assert resp.status_code == 404


# === multi-tenant isolation ===================================================


async def test_multi_tenant_isolation(db_session: AsyncSession) -> None:
    tenant_a = await _seed_tenant(db_session, code=_unique_code())
    tenant_b = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        created_a = await ac.post(
            f"/api/v1/admin/tenants/{tenant_a.id}/skills", json=_payload("a-secret")
        )
        a_skill_id = created_a.json()["id"]
        # B never lists A's skill (read scoping).
        b_list = await ac.get(f"/api/v1/admin/tenants/{tenant_b.id}/skills")
        # Cross-tenant write: PUT A's skill under B's path → 404 (never 403).
        cross_put = await ac.put(
            f"/api/v1/admin/tenants/{tenant_b.id}/skills/{a_skill_id}",
            json={"description": "hijack"},
        )
    assert created_a.status_code == 201
    assert b_list.json()["skills"] == []
    assert cross_put.status_code == 404


# === audit + cache invalidation ===============================================


async def test_create_emits_audit(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(f"/api/v1/admin/tenants/{tenant.id}/skills", json=_payload())
    assert resp.status_code == 201
    rows = (
        (
            await db_session.execute(
                select(AuditLog)
                .where(AuditLog.tenant_id == tenant.id)
                .where(AuditLog.operation == "tenant_skill_create")
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1
    assert rows[0].resource_type == "tenant_skill"
    assert rows[0].operation_data["name"] == "release-notes"
    assert rows[0].operation_result == "success"


async def test_create_invalidates_resolver_cache(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    # Prime the cache with the bundled-only registry for this tenant.
    before = await resolve_tenant_skill_registry(db_session, tenant.id)
    assert before.get("release-notes") is None

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        created = await ac.post(f"/api/v1/admin/tenants/{tenant.id}/skills", json=_payload())
    assert created.status_code == 201

    # The endpoint invalidated the cache → the next resolve reflects the new skill.
    after = await resolve_tenant_skill_registry(db_session, tenant.id)
    assert after.get("release-notes") is not None


# === Sprint 57.117: quota + body-size + list limits ==========================


async def test_create_over_quota_409(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A POST when the tenant is at SKILLS_MAX_PER_TENANT → 409 (SkillQuotaExceededError)."""
    monkeypatch.setattr("platform_layer.skills.service.SKILLS_MAX_PER_TENANT", 2)
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for n in range(2):  # fill to the cap — these succeed
            ok = await ac.post(f"/api/v1/admin/tenants/{tenant.id}/skills", json=_payload(f"s-{n}"))
            assert ok.status_code == 201, ok.text
        over = await ac.post(f"/api/v1/admin/tenants/{tenant.id}/skills", json=_payload("over"))
    assert over.status_code == 409, over.text


async def test_create_oversized_instructions_422(db_session: AsyncSession) -> None:
    """An instructions body over the SKILLS_MAX_INSTRUCTIONS_CHARS Pydantic cap → 422."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    body = _payload()
    body["instructions"] = "x" * (SKILLS_MAX_INSTRUCTIONS_CHARS + 1)  # 1 over the cap
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(f"/api/v1/admin/tenants/{tenant.id}/skills", json=body)
    assert resp.status_code == 422


async def test_list_response_carries_limits(db_session: AsyncSession) -> None:
    """GET list surfaces the effective limits (single-source for the FE)."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        listed = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/skills")
    assert listed.status_code == 200
    body = listed.json()
    assert body["max_skills"] == SKILLS_MAX_PER_TENANT
    assert body["max_instructions_chars"] == SKILLS_MAX_INSTRUCTIONS_CHARS
