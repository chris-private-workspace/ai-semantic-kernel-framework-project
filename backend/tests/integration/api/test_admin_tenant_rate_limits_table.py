"""
File: backend/tests/integration/api/test_admin_tenant_rate_limits_table.py
Purpose: Integration tests — GET/PUT /rate-limits re-pointed to rate_limit_configs table.
Category: Tests / Integration / API (Phase 58.x RateLimits Potemkin close)
Scope: Sprint 57.59 Day 1 / US-2 (closes AD-RateLimits-Potemkin-Migration-Phase58)

Description:
    Verifies the Sprint 57.59 re-point of the admin RateLimits endpoints to the
    durable rate_limit_configs table (the sole source of truth since Sprint 57.60
    retired the transitional meta_data fallback):
    - GET reads config-table rows (projected back to {label, value})
    - GET falls back to DEFAULT_RATE_LIMITS when the table is empty (meta_data
      is no longer consulted)
    - PUT replaces config-table rows (composite-replace); no meta_data dual-write
    - PUT emits the tenant_rate_limits_upsert audit chain entry
    - Multi-tenant PUT isolation (tenant_b's PUT never touches tenant_a's config)
    - API response shape UNCHANGED ({label, value} + pagination envelope)

    PUT tests call db.commit() inside the endpoint, persisting tenant +
    rate_limit_configs rows past the db_session rollback. Each PUT test seeds a
    uuid4-suffixed RATE_LIMIT_CONFIG_% code; conftest.py sweeps those (FK CASCADE
    drops the tenant's config rows).

Created: 2026-05-28 (Sprint 57.59 Day 1)

Modification History (newest-first):
    - 2026-05-29: Sprint 57.60 — meta_data fallback retired; GET-fallback test → DEFAULT
    - 2026-05-28: Initial creation (Sprint 57.59 Day 1 / US-2 — table re-point)
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


def _unique_code() -> str:
    """Unique tenant code (survives committed-row leakage; conftest RATE_LIMIT_CONFIG_% sweep)."""
    return f"RATE_LIMIT_CONFIG_{uuid4().hex[:8]}"


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


# =====================================================================
# GET — reads config table; falls back to DEFAULT when table empty
# =====================================================================


async def test_get_reads_from_config_table(db_session: AsyncSession) -> None:
    """Config rows present → GET projects them (NOT meta_data)."""
    tenant = await _seed_tenant(
        db_session,
        code="RLC_GET_TBL",
        meta_data={"rate_limits": [{"label": "Stale meta", "value": "1 / min"}]},
    )
    # Seed the config table with a DIFFERENT value than meta_data.
    db_session.add(
        RateLimitConfig(
            tenant_id=tenant.id, resource_type="api_requests", window_type="min", quota=250
        )
    )
    await db_session.flush()

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/rate-limits")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # Table wins over the stale meta_data.
    assert body["total"] == 1
    assert body["items"] == [{"label": "API requests", "value": "250 / min"}]


async def test_get_ignores_stale_meta_data_when_no_config_rows(
    db_session: AsyncSession,
) -> None:
    """Sprint 57.60: stale meta_data is NO LONGER read → GET returns DEFAULT.

    Previously (Sprint 57.59) an empty config table fell back to
    meta_data['rate_limits']; that transitional fallback was removed in Sprint
    57.60, so a seeded-but-stale meta_data blob must be ignored and GET must
    return DEFAULT_RATE_LIMITS.
    """
    tenant = await _seed_tenant(
        db_session,
        code="RLC_GET_FB",
        meta_data={"rate_limits": [{"label": "Fallback only", "value": "9 / min"}]},
    )
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/rate-limits")
    assert resp.status_code == 200, resp.text
    labels = {item["label"] for item in resp.json()["items"]}
    # DEFAULT_RATE_LIMITS — NOT the stale meta_data value.
    assert labels == {"API requests", "Tool calls", "SSE connections"}
    assert "Fallback only" not in labels


async def test_get_falls_back_to_defaults_when_no_config_and_no_meta(
    db_session: AsyncSession,
) -> None:
    """No config rows + no meta_data → DEFAULT_RATE_LIMITS (3 items)."""
    tenant = await _seed_tenant(db_session, code="RLC_GET_DEF")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/rate-limits")
    assert resp.status_code == 200, resp.text
    labels = {item["label"] for item in resp.json()["items"]}
    assert labels == {"API requests", "Tool calls", "SSE connections"}


# =====================================================================
# PUT — writes config table (composite-replace) + audit + isolation
# =====================================================================


async def test_put_writes_config_table(db_session: AsyncSession) -> None:
    """PUT persists parseable items as config-table rows."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    payload_items = [
        {"label": "API requests", "value": "777 / min"},
        {"label": "Tool calls", "value": "8,888 / min"},
    ]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/rate-limits",
            json={"items": payload_items},
        )
    assert resp.status_code == 200, resp.text
    # Response shape unchanged + thousands separator round-trips.
    assert resp.json()["items"] == payload_items

    rows = (
        (
            await db_session.execute(
                select(RateLimitConfig).where(RateLimitConfig.tenant_id == tenant.id)
            )
        )
        .scalars()
        .all()
    )
    assert {(r.resource_type, r.window_type, r.quota) for r in rows} == {
        ("api_requests", "min", 777),
        ("tool_calls", "min", 8888),
    }


async def test_put_replaces_config_rows(db_session: AsyncSession) -> None:
    """2nd PUT composite-replaces config rows (only the 2nd payload survives)."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/rate-limits",
            json={"items": [{"label": "API requests", "value": "1 / min"}]},
        )
        second = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/rate-limits",
            json={"items": [{"label": "Tool calls", "value": "2 / hour"}]},
        )
    assert second.status_code == 200, second.text

    rows = (
        (
            await db_session.execute(
                select(RateLimitConfig).where(RateLimitConfig.tenant_id == tenant.id)
            )
        )
        .scalars()
        .all()
    )
    assert {(r.resource_type, r.window_type, r.quota) for r in rows} == {("tool_calls", "hour", 2)}


async def test_put_empty_clears_config_rows(db_session: AsyncSession) -> None:
    """PUT [] clears all config rows → GET falls back to DEFAULT_RATE_LIMITS."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/rate-limits",
            json={"items": [{"label": "API requests", "value": "42 / min"}]},
        )
        clear = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/rate-limits",
            json={"items": []},
        )
    assert clear.status_code == 200, clear.text
    assert clear.json()["items"] == []

    rows = (
        (
            await db_session.execute(
                select(RateLimitConfig).where(RateLimitConfig.tenant_id == tenant.id)
            )
        )
        .scalars()
        .all()
    )
    assert rows == []


async def test_put_emits_audit_chain(db_session: AsyncSession) -> None:
    """PUT writes exactly 1 audit_log row operation=tenant_rate_limits_upsert."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    payload_items = [{"label": "API requests", "value": "99 / min"}]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/rate-limits",
            json={"items": payload_items},
        )
    assert resp.status_code == 200, resp.text

    entries = (
        (
            await db_session.execute(
                select(AuditLog)
                .where(AuditLog.tenant_id == tenant.id)
                .where(AuditLog.operation == "tenant_rate_limits_upsert")
            )
        )
        .scalars()
        .all()
    )
    assert len(entries) == 1
    assert entries[0].operation_data["items"] == payload_items
    assert entries[0].operation_result == "success"


async def test_put_multi_tenant_isolation(db_session: AsyncSession) -> None:
    """PUT to tenant_b MUST NOT alter tenant_a's config rows (multi-tenant rule)."""
    tenant_a = await _seed_tenant(db_session, code=_unique_code())
    tenant_b = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.put(
            f"/api/v1/admin/tenants/{tenant_a.id}/rate-limits",
            json={"items": [{"label": "API requests", "value": "11 / min"}]},
        )
        await ac.put(
            f"/api/v1/admin/tenants/{tenant_b.id}/rate-limits",
            json={"items": [{"label": "Tool calls", "value": "22 / hour"}]},
        )

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
    assert {(r.resource_type, r.quota) for r in rows_a} == {("api_requests", 11)}
    assert {(r.resource_type, r.quota) for r in rows_b} == {("tool_calls", 22)}


async def test_put_response_shape_unchanged(db_session: AsyncSession) -> None:
    """Response carries {label, value} items + total/limit/offset envelope."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/rate-limits",
            json={"items": [{"label": "API requests", "value": "5 / min"}]},
        )
    body = resp.json()
    assert {"items", "total", "limit", "offset"}.issubset(set(body.keys()))
    assert {"label", "value"}.issubset(set(body["items"][0].keys()))
