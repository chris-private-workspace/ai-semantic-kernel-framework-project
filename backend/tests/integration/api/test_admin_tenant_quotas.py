"""
File: backend/tests/integration/api/test_admin_tenant_quotas.py
Purpose: Integration tests — GET /admin/tenants/{tenant_id}/quotas (Sprint 57.48 Track C).
Category: Tests / Integration / API (Phase 58+ Backend Schema Extension wave)
Scope: Sprint 57.48 Day 1 Track C (closes AD-TenantSettings-Quotas-Backend)

Description:
    Verifies the GET /admin/tenants/{tenant_id}/quotas endpoint:
    - 401 when no JWT context
    - 404 when tenant not found
    - 200 happy path returns 4 PlanQuota fields projected as items
    - Response shape: items + total + limit + offset; each item carries
      resource/limit/unit/period/current_usage
    - Pagination (limit + offset)
    - Multi-tenant isolation: different tenants on same plan see same quota
      structure but each request is scoped to its tenant_id (verified via 404 path)
    - limit > 200 → 422

Created: 2026-05-26 (Sprint 57.48 Day 1)

Modification History (newest-first):
    - 2026-05-27: Sprint 57.56 Track A — +12 PUT tests covering composite-replace + audit chain
    - 2026-05-26: Initial creation (Sprint 57.48 Day 1 Track C — Quotas admin GET)
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


async def test_list_quotas_401_without_auth() -> None:
    app = _build_app()
    tenant_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant_id}/quotas")
    assert resp.status_code == 401


async def test_list_quotas_404_when_tenant_not_found(db_session: AsyncSession) -> None:
    app = _build_app(db_session=db_session)
    missing_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{missing_id}/quotas")
    assert resp.status_code == 404


async def test_list_quotas_happy_path_returns_4_quota_fields(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code="QUOTA_HAPPY_T1")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/quotas")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 4
    assert len(body["items"]) == 4
    resources = {item["resource"] for item in body["items"]}
    assert resources == {
        "tokens_per_day",
        "cost_usd_per_day",
        "sessions_per_user_concurrent",
        "api_keys_max",
    }


async def test_list_quotas_response_shape(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code="QUOTA_SHAPE_T1")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/quotas")
    assert resp.status_code == 200, resp.text
    item = resp.json()["items"][0]
    expected = {"resource", "limit", "unit", "period", "current_usage"}
    assert expected.issubset(set(item.keys()))
    assert item["current_usage"] is None  # always null at admin layer this sprint


async def test_list_quotas_tokens_field_has_correct_unit(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code="QUOTA_UNIT_T1")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/quotas")
    body = resp.json()
    tokens = next(item for item in body["items"] if item["resource"] == "tokens_per_day")
    assert tokens["unit"] == "tokens"
    assert tokens["period"] == "day"
    assert tokens["limit"] > 0


async def test_list_quotas_pagination(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code="QUOTA_PAGE_T1")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        page1 = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/quotas?limit=2&offset=0")
        page2 = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/quotas?limit=2&offset=2")
    assert page1.status_code == 200 and page2.status_code == 200
    assert page1.json()["total"] == 4
    assert len(page1.json()["items"]) == 2
    assert len(page2.json()["items"]) == 2


async def test_list_quotas_tenant_isolation(db_session: AsyncSession) -> None:
    """Different tenants must each see a quota response scoped to their own ID
    (no cross-tenant leak via path)."""
    tenant_a = await _seed_tenant(db_session, code="QUOTA_ISO_A")
    tenant_b = await _seed_tenant(db_session, code="QUOTA_ISO_B")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp_a = await ac.get(f"/api/v1/admin/tenants/{tenant_a.id}/quotas")
        resp_b = await ac.get(f"/api/v1/admin/tenants/{tenant_b.id}/quotas")
    assert resp_a.status_code == 200 and resp_b.status_code == 200
    # Same plan (ENTERPRISE) so structure matches, but both must succeed via
    # their respective tenant paths (404 path proven separately above).
    assert resp_a.json()["total"] == 4
    assert resp_b.json()["total"] == 4


async def test_list_quotas_invalid_query_limit(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code="QUOTA_LIM_T1")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/quotas?limit=500")
    assert resp.status_code == 422


# =====================================================================
# Sprint 57.56 Track A — PUT /{tenant_id}/quotas upsert tests
# =====================================================================
# IMPORTANT: PUT tests call db.commit() inside the endpoint to persist the
# tenant.meta_data["quota_overrides"] JSONB write + the audit chain entry.
# To avoid "duplicate key" cross-test leakage on the unique tenants.code,
# each PUT test seeds its tenant with a uuid4-suffixed code (mirrors Sprint
# 57.55 FF_PUT_% pattern; conftest.py extends LIKE 'QUOTA_PUT_%' cleanup sweep).


def _unique_code() -> str:
    """Return a unique tenant code suffix to survive committed-row leakage."""
    return f"QUOTA_PUT_{uuid4().hex[:8]}"


async def test_put_requires_admin_role() -> None:
    """No JWT context → 401/403 from require_admin_platform_role."""
    app = _build_app()
    tenant_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant_id}/quotas",
            json={"overrides": {}},
        )
    assert resp.status_code in (401, 403)


async def test_put_tenant_not_found(db_session: AsyncSession) -> None:
    """Nonexistent tenant_id → 404 via _load_tenant_or_404."""
    app = _build_app(db_session=db_session)
    missing_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{missing_id}/quotas",
            json={"overrides": {}},
        )
    assert resp.status_code == 404


async def test_put_creates_new_overrides(db_session: AsyncSession) -> None:
    """No prior overrides → PUT persists payload to tenant.meta_data["quota_overrides"]."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    payload_overrides = {
        "tokens_per_day": 500_000.0,
        "cost_usd_per_day": 250.0,
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/quotas",
            json={"overrides": payload_overrides},
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["saved_overrides"] == payload_overrides

    # Verify ORM state via direct re-read.
    row = (await db_session.execute(select(Tenant).where(Tenant.id == tenant.id))).scalar_one()
    assert row.meta_data is not None
    assert row.meta_data.get("quota_overrides") == payload_overrides


async def test_put_updates_existing_overrides(db_session: AsyncSession) -> None:
    """Second PUT replaces first composite (composite-replace semantics)."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        first = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/quotas",
            json={"overrides": {"tokens_per_day": 100_000.0}},
        )
        second = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/quotas",
            json={"overrides": {"cost_usd_per_day": 99.5}},
        )
    assert first.status_code == 200 and second.status_code == 200
    # 2nd PUT replaces 1st: tokens_per_day override is cleared, cost is set.
    assert second.json()["saved_overrides"] == {"cost_usd_per_day": 99.5}


async def test_put_response_projects_items_matching_get(db_session: AsyncSession) -> None:
    """PUT then GET return identical items for the overridden resource (cache hydration)."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        put_resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/quotas",
            json={"overrides": {"tokens_per_day": 777_000.0}},
        )
        get_resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/quotas")
    assert put_resp.status_code == 200, put_resp.text
    assert get_resp.status_code == 200, get_resp.text
    put_tokens = next(i for i in put_resp.json()["items"] if i["resource"] == "tokens_per_day")
    get_tokens = next(i for i in get_resp.json()["items"] if i["resource"] == "tokens_per_day")
    assert put_tokens["limit"] == 777_000.0
    assert put_tokens == get_tokens


async def test_put_unknown_resource_rejected(db_session: AsyncSession) -> None:
    """Payload includes a non-whitelist resource name → 422."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/quotas",
            json={"overrides": {"bogus_resource": 1.0}},
        )
    assert resp.status_code == 422, resp.text
    assert "bogus_resource" in resp.text


async def test_put_extra_field_rejected(db_session: AsyncSession) -> None:
    """Unknown top-level field in payload → 422 via extra='forbid'."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/quotas",
            json={"overrides": {}, "unknown_field": "leak"},
        )
    assert resp.status_code == 422


async def test_put_multi_tenant_isolation(db_session: AsyncSession) -> None:
    """PUT to tenant_b MUST NOT affect tenant_a's meta_data (multi-tenant rule)."""
    tenant_a = await _seed_tenant(db_session, code=_unique_code())
    tenant_b = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp_a = await ac.put(
            f"/api/v1/admin/tenants/{tenant_a.id}/quotas",
            json={"overrides": {"tokens_per_day": 1.0}},
        )
        resp_b = await ac.put(
            f"/api/v1/admin/tenants/{tenant_b.id}/quotas",
            json={"overrides": {"cost_usd_per_day": 2.0}},
        )
    assert resp_a.status_code == 200 and resp_b.status_code == 200

    # Verify via direct ORM re-read — each tenant's meta_data holds only its
    # own override; cross-tenant leak would manifest as merged keys.
    row_a = (await db_session.execute(select(Tenant).where(Tenant.id == tenant_a.id))).scalar_one()
    row_b = (await db_session.execute(select(Tenant).where(Tenant.id == tenant_b.id))).scalar_one()
    assert row_a.meta_data["quota_overrides"] == {"tokens_per_day": 1.0}
    assert row_b.meta_data["quota_overrides"] == {"cost_usd_per_day": 2.0}


async def test_put_empty_overrides_clears_all(db_session: AsyncSession) -> None:
    """PUT with {} clears any prior overrides → GET reverts to plan defaults."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # First seed an override.
        await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/quotas",
            json={"overrides": {"tokens_per_day": 42.0}},
        )
        # Then clear all.
        clear = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/quotas",
            json={"overrides": {}},
        )
        get_resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/quotas")
    assert clear.status_code == 200, clear.text
    assert clear.json()["saved_overrides"] == {}
    # GET should now reflect plan defaults (no override == 42.0 for tokens).
    tokens = next(i for i in get_resp.json()["items"] if i["resource"] == "tokens_per_day")
    assert tokens["limit"] != 42.0  # plan default, not the cleared override


async def test_put_idempotent_same_payload_twice(db_session: AsyncSession) -> None:
    """PUT same payload twice → consistent final state."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    payload = {"overrides": {"sessions_per_user_concurrent": 7.0}}
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        first = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/quotas",
            json=payload,
        )
        second = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/quotas",
            json=payload,
        )
    assert first.status_code == 200 and second.status_code == 200
    assert first.json()["saved_overrides"] == second.json()["saved_overrides"]
    # Items match too (resource ordering is deterministic by _QUOTA_RESOURCE_META).
    assert first.json()["items"] == second.json()["items"]


async def test_put_persists_to_db_via_subsequent_get(db_session: AsyncSession) -> None:
    """Post-PUT GET reflects override across all 4 quota items."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    overrides = {
        "tokens_per_day": 1_000_000.0,
        "cost_usd_per_day": 500.0,
        "sessions_per_user_concurrent": 20.0,
        "api_keys_max": 50.0,
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/quotas",
            json={"overrides": overrides},
        )
        get_resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/quotas")
    assert get_resp.status_code == 200, get_resp.text
    by_resource = {i["resource"]: i["limit"] for i in get_resp.json()["items"]}
    for resource, expected_limit in overrides.items():
        assert (
            by_resource[resource] == expected_limit
        ), f"{resource}: got {by_resource.get(resource)} expected {expected_limit}"


async def test_put_audit_chain_emitted(db_session: AsyncSession) -> None:
    """PUT emits exactly 1 audit_log row with operation=tenant_quota_overrides_upsert."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/quotas",
            json={"overrides": {"api_keys_max": 25.0}},
        )
    assert resp.status_code == 200, resp.text

    result = await db_session.execute(
        select(AuditLog)
        .where(AuditLog.tenant_id == tenant.id)
        .where(AuditLog.operation == "tenant_quota_overrides_upsert")
    )
    entries = result.scalars().all()
    assert len(entries) == 1
    audit = entries[0]
    assert audit.resource_type == "tenant"
    assert audit.resource_id == str(tenant.id)
    assert audit.operation_data["overrides"] == {"api_keys_max": 25.0}
    assert audit.operation_result == "success"
