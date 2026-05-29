"""
File: backend/tests/integration/api/test_admin_tenant_rate_limits.py
Purpose: Integration tests — GET /admin/tenants/{tenant_id}/rate-limits (Sprint 57.48 Track D).
Category: Tests / Integration / API (Phase 58+ Backend Schema Extension wave)
Scope: Sprint 57.48 Day 1 Track D Option A (closes AD-TenantSettings-RateLimits-Backend)

Description:
    Verifies the GET /admin/tenants/{tenant_id}/rate-limits endpoint
    (source of truth: the rate_limit_configs table since Sprint 57.59):
    - 401 when no JWT context
    - 404 when tenant not found
    - 200 returns DEFAULT_RATE_LIMITS (3 items) when the config table is empty
    - 200 returns tenant-overridden list when config rows are present
    - Response shape: items + total + limit + offset; items carry label + value
    - Multi-tenant isolation (tenant A's override does NOT show in tenant B)

Created: 2026-05-26 (Sprint 57.48 Day 1)

Modification History (newest-first):
    - 2026-05-29: Sprint 57.60 — convert meta_data seeds/asserts to config-table (cleanup)
    - 2026-05-27: Sprint 57.57 Track A — +10 PUT tests covering composite-replace + audit chain
    - 2026-05-26: Initial creation (Sprint 57.48 Day 1 Track D — RateLimits admin GET Option A)
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, Request, Response
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.admin.tenants import router as admin_tenants_router
from infrastructure.db.models.api_keys import RateLimitConfig
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


async def _seed_tenant(
    session: AsyncSession,
    *,
    code: str,
    meta_data: dict[str, Any] | None = None,
) -> Tenant:
    t = Tenant(
        code=code,
        display_name=f"Tenant {code}",
        state=TenantState.ACTIVE,
        plan=TenantPlan.ENTERPRISE,
        meta_data=meta_data or {},
    )
    session.add(t)
    await session.flush()
    await session.refresh(t)
    return t


async def _seed_config_rows(
    session: AsyncSession,
    tenant_id: UUID,
    items: list[dict[str, str]],
) -> None:
    """Seed rate_limit_configs rows from {label, value} display items.

    Mirrors how the live PUT path persists overrides (Sprint 57.59 source of
    truth) so GET-override tests no longer depend on the retired meta_data
    fallback.
    """
    from platform_layer.tenant.rate_limit_config_store import parse_config_item

    for item in items:
        parsed = parse_config_item(item)
        assert parsed is not None, f"unparseable seed item: {item}"
        resource_type, window_type, quota = parsed
        session.add(
            RateLimitConfig(
                tenant_id=tenant_id,
                resource_type=resource_type,
                window_type=window_type,
                quota=quota,
            )
        )
    await session.flush()


async def test_list_rate_limits_401_without_auth() -> None:
    app = _build_app()
    tenant_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant_id}/rate-limits")
    assert resp.status_code == 401


async def test_list_rate_limits_404_when_tenant_not_found(db_session: AsyncSession) -> None:
    app = _build_app(db_session=db_session)
    missing_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{missing_id}/rate-limits")
    assert resp.status_code == 404


async def test_list_rate_limits_returns_defaults_when_no_override(
    db_session: AsyncSession,
) -> None:
    """meta_data lacks rate_limits → DEFAULT_RATE_LIMITS (3 items)."""
    tenant = await _seed_tenant(db_session, code="RL_DEF_T1")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/rate-limits")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 3
    labels = {item["label"] for item in body["items"]}
    assert labels == {"API requests", "Tool calls", "SSE connections"}


async def test_list_rate_limits_applies_tenant_override(db_session: AsyncSession) -> None:
    """Config rows are honoured when present (table is the source of truth)."""
    custom = [
        {"label": "API requests", "value": "500 / min"},
        {"label": "Tool calls", "value": "5,000 / min"},
    ]
    tenant = await _seed_tenant(db_session, code="RL_OVR_T1")
    await _seed_config_rows(db_session, tenant.id, custom)
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/rate-limits")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 2
    api = next(item for item in body["items"] if item["label"] == "API requests")
    assert api["value"] == "500 / min"


async def test_list_rate_limits_ignores_stale_meta_data(db_session: AsyncSession) -> None:
    """Sprint 57.60: meta_data['rate_limits'] is NO LONGER read.

    Seed a stale meta_data blob + leave the config table empty → GET must return
    DEFAULT_RATE_LIMITS (the steady-state display default), proving the
    transitional meta_data fallback is fully removed.
    """
    tenant = await _seed_tenant(
        db_session,
        code="RL_NOFB_T1",
        meta_data={"rate_limits": [{"label": "Stale only", "value": "1 / min"}]},
    )
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/rate-limits")
    assert resp.status_code == 200, resp.text
    labels = {item["label"] for item in resp.json()["items"]}
    # DEFAULT_RATE_LIMITS — NOT the stale meta_data value.
    assert labels == {"API requests", "Tool calls", "SSE connections"}
    assert "Stale only" not in labels


async def test_list_rate_limits_response_shape(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code="RL_SHAPE_T1")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/rate-limits")
    item = resp.json()["items"][0]
    assert {"label", "value"}.issubset(set(item.keys()))


async def test_list_rate_limits_tenant_isolation(db_session: AsyncSession) -> None:
    tenant_a = await _seed_tenant(db_session, code="RL_ISO_A")
    await _seed_config_rows(
        db_session, tenant_a.id, [{"label": "API requests", "value": "9 / min"}]
    )
    tenant_b = await _seed_tenant(db_session, code="RL_ISO_B")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp_a = await ac.get(f"/api/v1/admin/tenants/{tenant_a.id}/rate-limits")
        resp_b = await ac.get(f"/api/v1/admin/tenants/{tenant_b.id}/rate-limits")
    assert resp_a.status_code == 200 and resp_b.status_code == 200
    items_a = resp_a.json()["items"]
    labels_b = {item["label"] for item in resp_b.json()["items"]}
    # tenant_a has exactly its one configured override (table-scoped); tenant_b
    # has no config rows → DEFAULT_RATE_LIMITS.
    assert items_a == [{"label": "API requests", "value": "9 / min"}]
    assert labels_b == {"API requests", "Tool calls", "SSE connections"}


# =====================================================================
# Sprint 57.57 Track A — PUT /{tenant_id}/rate-limits upsert tests
# =====================================================================
# IMPORTANT: PUT tests call db.commit() inside the endpoint to persist the
# tenant.meta_data["rate_limits"] JSONB write + the audit chain entry. To
# avoid "duplicate key" cross-test leakage on the unique tenants.code, each
# PUT test seeds its tenant with a uuid4-suffixed code (mirrors Sprint 57.56
# QUOTA_PUT_% pattern; conftest.py extends LIKE 'RATE_PUT_%' cleanup sweep).


def _unique_code() -> str:
    """Return a unique tenant code suffix to survive committed-row leakage."""
    return f"RATE_PUT_{uuid4().hex[:8]}"


async def test_put_requires_admin_role() -> None:
    """No JWT context → 401/403 from require_admin_platform_role."""
    app = _build_app()
    tenant_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant_id}/rate-limits",
            json={"items": []},
        )
    assert resp.status_code in (401, 403)


async def test_put_tenant_not_found(db_session: AsyncSession) -> None:
    """Nonexistent tenant_id → 404 via _load_tenant_or_404."""
    app = _build_app(db_session=db_session)
    missing_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{missing_id}/rate-limits",
            json={"items": []},
        )
    assert resp.status_code == 404


async def test_put_creates_new_items(db_session: AsyncSession) -> None:
    """No prior overrides → PUT persists payload to the rate_limit_configs table."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    payload_items = [
        {"label": "API requests", "value": "999 / min"},
        {"label": "Custom limit", "value": "42 / hour"},
    ]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/rate-limits",
            json={"items": payload_items},
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 2
    assert body["items"] == payload_items

    # Verify ORM state: config rows written; meta_data NOT (dual-write retired).
    config_rows = (
        (
            await db_session.execute(
                select(RateLimitConfig).where(RateLimitConfig.tenant_id == tenant.id)
            )
        )
        .scalars()
        .all()
    )
    assert {(r.resource_type, r.window_type, r.quota) for r in config_rows} == {
        ("api_requests", "min", 999),
        ("custom_limit", "hour", 42),
    }
    row = (await db_session.execute(select(Tenant).where(Tenant.id == tenant.id))).scalar_one()
    assert "rate_limits" not in (row.meta_data or {})


async def test_put_replaces_existing_items(db_session: AsyncSession) -> None:
    """Second PUT replaces first composite (composite-replace semantics)."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        first = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/rate-limits",
            json={"items": [{"label": "A", "value": "1 / min"}]},
        )
        second = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/rate-limits",
            json={"items": [{"label": "B", "value": "2 / min"}]},
        )
    assert first.status_code == 200 and second.status_code == 200
    # 2nd PUT replaces 1st: only "B" remains.
    assert second.json()["items"] == [{"label": "B", "value": "2 / min"}]


async def test_put_response_projects_items_matching_get(db_session: AsyncSession) -> None:
    """PUT then GET return identical items (cache hydration consistency)."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    custom = [
        {"label": "API requests", "value": "777 / min"},
        {"label": "Tool calls", "value": "8,888 / min"},
    ]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        put_resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/rate-limits",
            json={"items": custom},
        )
        get_resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/rate-limits")
    assert put_resp.status_code == 200, put_resp.text
    assert get_resp.status_code == 200, get_resp.text
    assert put_resp.json()["items"] == get_resp.json()["items"] == custom
    # Pagination envelope is consistent between PUT response and GET.
    assert put_resp.json()["total"] == get_resp.json()["total"] == 2


async def test_put_extra_field_rejected(db_session: AsyncSession) -> None:
    """Unknown top-level field in payload → 422 via extra='forbid'."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/rate-limits",
            json={"items": [], "unknown_field": "leak"},
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
            f"/api/v1/admin/tenants/{tenant_a.id}/rate-limits",
            json={"items": [{"label": "OnlyA", "value": "1 / min"}]},
        )
        resp_b = await ac.put(
            f"/api/v1/admin/tenants/{tenant_b.id}/rate-limits",
            json={"items": [{"label": "OnlyB", "value": "2 / min"}]},
        )
    assert resp_a.status_code == 200 and resp_b.status_code == 200

    # Verify via direct ORM re-read — each tenant's config rows hold only its own
    # override (table-scoped by tenant_id); cross-tenant leak would manifest as
    # merged rows. meta_data is no longer written (dual-write retired).
    rows_a = (
        (
            await db_session.execute(
                select(RateLimitConfig).where(RateLimitConfig.tenant_id == tenant_a.id)
            )
        )
        .scalars()
        .all()
    )
    rows_b = (
        (
            await db_session.execute(
                select(RateLimitConfig).where(RateLimitConfig.tenant_id == tenant_b.id)
            )
        )
        .scalars()
        .all()
    )
    assert {(r.resource_type, r.quota) for r in rows_a} == {("onlya", 1)}
    assert {(r.resource_type, r.quota) for r in rows_b} == {("onlyb", 2)}


async def test_put_empty_items_clears_all(db_session: AsyncSession) -> None:
    """PUT with [] clears any prior overrides → GET reverts to DEFAULT_RATE_LIMITS."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # First seed an override.
        await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/rate-limits",
            json={"items": [{"label": "Custom", "value": "42 / min"}]},
        )
        # Then clear all.
        clear = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/rate-limits",
            json={"items": []},
        )
        get_resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/rate-limits")
    assert clear.status_code == 200, clear.text
    assert clear.json()["items"] == []
    # GET should now reflect DEFAULT_RATE_LIMITS (3 items) — fallback path.
    labels = {item["label"] for item in get_resp.json()["items"]}
    assert labels == {"API requests", "Tool calls", "SSE connections"}


async def test_put_idempotent_same_payload_twice(db_session: AsyncSession) -> None:
    """PUT same payload twice → consistent final state."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    payload = {"items": [{"label": "API requests", "value": "555 / min"}]}
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        first = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/rate-limits",
            json=payload,
        )
        second = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/rate-limits",
            json=payload,
        )
    assert first.status_code == 200 and second.status_code == 200
    assert first.json()["items"] == second.json()["items"]


async def test_put_audit_chain_emitted(db_session: AsyncSession) -> None:
    """PUT emits exactly 1 audit_log row with operation=tenant_rate_limits_upsert."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    payload_items = [{"label": "Audited", "value": "99 / min"}]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/rate-limits",
            json={"items": payload_items},
        )
    assert resp.status_code == 200, resp.text

    result = await db_session.execute(
        select(AuditLog)
        .where(AuditLog.tenant_id == tenant.id)
        .where(AuditLog.operation == "tenant_rate_limits_upsert")
    )
    entries = result.scalars().all()
    assert len(entries) == 1
    audit = entries[0]
    assert audit.resource_type == "tenant"
    assert audit.resource_id == str(tenant.id)
    assert audit.operation_data["items"] == payload_items
    assert audit.operation_data["items_count"] == 1
    assert audit.operation_result == "success"
