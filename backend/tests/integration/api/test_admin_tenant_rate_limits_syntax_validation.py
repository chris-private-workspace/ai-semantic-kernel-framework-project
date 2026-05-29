"""
File: backend/tests/integration/api/test_admin_tenant_rate_limits_syntax_validation.py
Purpose: Integration tests — PUT /rate-limits 422 syntax validation (malformed value/label).
Category: Tests / Integration / API (Phase 58.x RateLimits SyntaxValidation)
Scope: Sprint 57.61 Day 1 / US-1 (closes AD-RateLimits-SyntaxValidation-Phase58)

Description:
    Verifies the Sprint 57.61 PUT-time syntax validation on RateLimitsUpsertRequest:
    - malformed value (garbage / unsupported window / non-positive / non-numeric /
      empty) → 422 with a per-item reason (no silent drop)
    - empty label → 422
    - enforceable rate ('N / sec|min|hour|day') → 200 + persisted to rate_limit_configs
    - display-only 'N concurrent' → 200 (accepted, not enforced)
    - DEFAULT_RATE_LIMITS verbatim round-trip (incl. '50 concurrent') → 200
    - GET unaffected (no validation on the shared RateLimitItem)
    - multi-tenant isolation: validation doesn't leak across tenants

    Mirrors the harness in test_admin_tenant_rate_limits_table.py (X-Test headers +
    dependency overrides). 200-path PUTs commit inside the endpoint, persisting
    tenant + rate_limit_configs rows past db_session rollback; each uses a
    uuid4-suffixed RATE_LIMIT_CONFIG_% code swept by conftest.py (FK CASCADE).

Created: 2026-05-29 (Sprint 57.61 Day 1)

Modification History (newest-first):
    - 2026-05-29: Initial creation (Sprint 57.61 Day 1 / US-1 — PUT-time syntax validation)
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

from api.v1.admin.tenants import DEFAULT_RATE_LIMITS
from api.v1.admin.tenants import router as admin_tenants_router
from infrastructure.db.models.api_keys import RateLimitConfig
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


async def _seed_tenant(session: AsyncSession, *, code: str) -> Tenant:
    t = Tenant(
        code=code,
        display_name=f"Tenant {code}",
        state=TenantState.ACTIVE,
        plan=TenantPlan.ENTERPRISE,
        meta_data={},
    )
    session.add(t)
    await session.flush()
    await session.refresh(t)
    return t


# =====================================================================
# 422 — malformed value / label rejected (no silent drop)
# =====================================================================


@pytest.mark.parametrize(
    "bad_value",
    [
        "foo",  # no slash, not concurrent
        "50 / week",  # unsupported window
        "0 / min",  # non-positive quota
        "-5 / min",  # leading '-' not matched by [\d,]+ → falls to shape branch
        "abc / min",  # non-numeric quota (regex requires [\d,]+ → shape reject)
        "",  # empty value
        "100 bananas",  # garbage trailing word
        "concurrent",  # bare keyword, no number
    ],
)
async def test_put_malformed_value_returns_422(db_session: AsyncSession, bad_value: str) -> None:
    """A malformed value is rejected with 422 instead of being silently dropped."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/rate-limits",
            json={"items": [{"label": "API requests", "value": bad_value}]},
        )
    assert resp.status_code == 422, resp.text


async def test_put_empty_label_returns_422(db_session: AsyncSession) -> None:
    """An empty/whitespace label is rejected with 422."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/rate-limits",
            json={"items": [{"label": "", "value": "100 / min"}]},
        )
    assert resp.status_code == 422, resp.text


async def test_put_422_detail_contains_per_item_reason(db_session: AsyncSession) -> None:
    """The 422 body surfaces an actionable per-item reason mentioning the bad value."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/rate-limits",
            json={"items": [{"label": "API requests", "value": "50 / week"}]},
        )
    assert resp.status_code == 422, resp.text
    # FastAPI nests the ValueError msg under detail[].msg ("Value error, ...").
    detail_text = json.dumps(resp.json())
    assert "50 / week" in detail_text
    assert "unsupported window" in detail_text


async def test_put_malformed_item_does_not_persist(db_session: AsyncSession) -> None:
    """A rejected PUT leaves the config table empty (the 422 blocks the write)."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/rate-limits",
            json={"items": [{"label": "API requests", "value": "garbage"}]},
        )
    assert resp.status_code == 422, resp.text
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


# =====================================================================
# 200 — valid rate / concurrency / defaults round-trip accepted
# =====================================================================


async def test_put_valid_rate_accepted_and_persisted(db_session: AsyncSession) -> None:
    """An enforceable rate is accepted (200) and persisted to rate_limit_configs."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    payload_items = [
        {"label": "API requests", "value": "100 / min"},
        {"label": "Tool calls", "value": "1,000 / hour"},
    ]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/rate-limits",
            json={"items": payload_items},
        )
    assert resp.status_code == 200, resp.text
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
        ("api_requests", "min", 100),
        ("tool_calls", "hour", 1000),
    }


async def test_put_concurrency_value_accepted(db_session: AsyncSession) -> None:
    """A display-only 'N concurrent' value is accepted (200) though not enforced."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/rate-limits",
            json={"items": [{"label": "SSE connections", "value": "50 concurrent"}]},
        )
    assert resp.status_code == 200, resp.text
    # Display-only: not persisted as an enforceable config row (replace_configs skips it).
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


async def test_put_defaults_roundtrip_accepted(db_session: AsyncSession) -> None:
    """DEFAULT_RATE_LIMITS verbatim (incl. '50 concurrent') → 200 (no false reject).

    This is the critical load-defaults → edit → save round-trip: the validator
    must NOT reject the unchanged '50 concurrent' default.
    """
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/rate-limits",
            json={"items": list(DEFAULT_RATE_LIMITS)},
        )
    assert resp.status_code == 200, resp.text


# =====================================================================
# GET unaffected + multi-tenant isolation
# =====================================================================


async def test_get_unaffected_by_validation(db_session: AsyncSession) -> None:
    """GET returns DEFAULT_RATE_LIMITS without triggering request-model validation."""
    tenant = await _seed_tenant(db_session, code="RLC_SYN_GET")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/rate-limits")
    assert resp.status_code == 200, resp.text
    labels = {item["label"] for item in resp.json()["items"]}
    # GET projects the '50 concurrent' default without a 422 (validator is PUT-only).
    assert labels == {"API requests", "Tool calls", "SSE connections"}


async def test_validation_does_not_leak_across_tenants(db_session: AsyncSession) -> None:
    """A 422 PUT to tenant_b leaves tenant_a's valid config untouched."""
    tenant_a = await _seed_tenant(db_session, code=_unique_code())
    tenant_b = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ok = await ac.put(
            f"/api/v1/admin/tenants/{tenant_a.id}/rate-limits",
            json={"items": [{"label": "API requests", "value": "11 / min"}]},
        )
        bad = await ac.put(
            f"/api/v1/admin/tenants/{tenant_b.id}/rate-limits",
            json={"items": [{"label": "Tool calls", "value": "garbage"}]},
        )
    assert ok.status_code == 200, ok.text
    assert bad.status_code == 422, bad.text

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
    assert rows_b == []
