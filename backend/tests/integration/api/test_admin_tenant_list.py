"""
File: backend/tests/integration/api/test_admin_tenant_list.py
Purpose: Integration tests — GET /admin/tenants list endpoint (Sprint 57.4 US-1).
Category: Tests / Integration / API (Phase 57+ SaaS Frontend 3/N)
Scope: Sprint 57.4 / Day 1 / US-1 (closes plan-time D1 RED finding)

Description:
    Verifies the GET /admin/tenants list endpoint:
    - 401 when no JWT context (no X-Test-User header)
    - 403 when role is not admin/platform_admin
    - 200 happy path with default pagination (50 / 0)
    - 200 filter by state — only matching tenants returned
    - 200 filter by plan — only matching tenants returned
    - 200 search by ILIKE on code substring
    - 200 pagination limit + offset behavior
    - 200 empty result for non-matching search
    - Response shape matches TenantListResponse

    Mirrors test_admin_tenant_get.py + test_admin_tenant_patch.py
    patterns (FastAPI test app with X-Test-User / X-Test-Roles
    middleware + dependency_overrides for db_session +
    require_admin_platform_role).

Created: 2026-05-07 (Sprint 57.4 Day 1)

Modification History (newest-first):
    - 2026-05-26: Sprint 57.47 Day 1 — shape 7→12 fields + region filter tests (AD-AdminT-Ext)
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI, Request, Response
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.admin.tenants import router as admin_tenants_router
from infrastructure.db.models.identity import Tenant, TenantPlan, TenantState
from infrastructure.db.session import get_db_session
from platform_layer.identity.auth import require_admin_platform_role

pytestmark = pytest.mark.asyncio


def _build_app(db_session: AsyncSession | None = None) -> FastAPI:
    """Build app with admin tenants router + role middleware + DB override."""
    app = FastAPI()
    app.include_router(admin_tenants_router, prefix="/api/v1")

    @app.middleware("http")
    async def _populate_test_state(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        user_header = request.headers.get("X-Test-User")
        roles_header = request.headers.get("X-Test-Roles")
        request.state.user_id = UUID(user_header) if user_header else None
        request.state.roles = json.loads(roles_header) if roles_header else None
        return await call_next(request)

    if db_session is not None:

        async def _override_session() -> AsyncIterator[AsyncSession]:
            yield db_session

        async def _override_admin() -> UUID:
            return UUID("00000000-0000-0000-0000-000000000001")

        app.dependency_overrides[get_db_session] = _override_session
        app.dependency_overrides[require_admin_platform_role] = _override_admin

    return app


async def _seed_tenant_with(
    session: AsyncSession,
    *,
    code: str,
    display_name: str | None = None,
    state: TenantState = TenantState.REQUESTED,
    plan: TenantPlan = TenantPlan.ENTERPRISE,
    region: str | None = None,
    locale: str | None = None,
    retention_days: int | None = None,
    sso_enabled: bool | None = None,
    seats: int | None = None,
) -> Tenant:
    """Create + flush a Tenant with explicit state + plan for filter tests.

    Note: Phase 56+ Stage 1 only ships TenantPlan.ENTERPRISE; STANDARD lands
    in Stage 2. Plan filter test therefore exercises the filter parameter
    parsing path rather than exclusion.

    Sprint 57.47 — adds optional region/locale/retention_days/sso_enabled/seats
    kwargs (default `None` → relies on ORM server_default values:
    region='global' / locale='en-US' / retention_days=90 / sso_enabled=False /
    seats=5; see identity.py L145-169).
    """
    kwargs: dict[str, Any] = {
        "code": code,
        "display_name": display_name or f"Tenant {code}",
        "state": state,
        "plan": plan,
    }
    if region is not None:
        kwargs["region"] = region
    if locale is not None:
        kwargs["locale"] = locale
    if retention_days is not None:
        kwargs["retention_days"] = retention_days
    if sso_enabled is not None:
        kwargs["sso_enabled"] = sso_enabled
    if seats is not None:
        kwargs["seats"] = seats
    t = Tenant(**kwargs)
    session.add(t)
    await session.flush()
    await session.refresh(t)
    return t


async def test_list_tenants_401_without_auth() -> None:
    """No X-Test-User header → require_admin_platform_role 401."""
    app = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants")
    assert resp.status_code == 401


async def test_list_tenants_403_wrong_role() -> None:
    """tenant_admin role insufficient → 403."""
    app = _build_app()
    user_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            "/api/v1/admin/tenants",
            headers={
                "X-Test-User": str(user_id),
                "X-Test-Roles": json.dumps(["tenant_admin"]),
            },
        )
    assert resp.status_code == 403


async def test_list_tenants_happy_no_filter(db_session: AsyncSession) -> None:
    """Admin auth + seeded tenants → 200 + items + total >= 1 + correct shape."""
    await _seed_tenant_with(db_session, code="LIST_T1", display_name="Tenant One")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "items" in body and "total" in body and "limit" in body and "offset" in body
    assert body["limit"] == 50
    assert body["offset"] == 0
    assert body["total"] >= 1
    # Each item should have the 12 TenantListItem fields (Sprint 57.47 +5 cols);
    # no progress/meta_data.
    sample = body["items"][0]
    expected = {
        "id",
        "code",
        "display_name",
        "state",
        "plan",
        "region",
        "locale",
        "retention_days",
        "sso_enabled",
        "seats",
        "created_at",
        "updated_at",
    }
    assert expected.issubset(set(sample.keys()))
    assert "meta_data" not in sample
    assert "provisioning_progress" not in sample
    assert "onboarding_progress" not in sample


async def test_list_tenants_filter_by_state(db_session: AsyncSession) -> None:
    """Filter state=active returns only ACTIVE tenants (excludes REQUESTED)."""
    await _seed_tenant_with(db_session, code="STATE_ACT", state=TenantState.ACTIVE)
    await _seed_tenant_with(db_session, code="STATE_REQ", state=TenantState.REQUESTED)
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants?state=active")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert all(item["state"] == "active" for item in body["items"])
    assert any(item["code"] == "STATE_ACT" for item in body["items"])
    assert all(item["code"] != "STATE_REQ" for item in body["items"])


async def test_list_tenants_filter_by_plan(db_session: AsyncSession) -> None:
    """Filter plan=enterprise parses + returns matching tenants.

    Phase 56+ Stage 1 only ships TenantPlan.ENTERPRISE — exclusion test
    requires Stage 2 STANDARD to be added. This test verifies the filter
    parameter parses and the response items all have plan=enterprise.
    """
    await _seed_tenant_with(db_session, code="PLAN_ENT", plan=TenantPlan.ENTERPRISE)
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants?plan=enterprise")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert all(item["plan"] == "enterprise" for item in body["items"])
    assert any(item["code"] == "PLAN_ENT" for item in body["items"])


async def test_list_tenants_search_by_code(db_session: AsyncSession) -> None:
    """Search ILIKE matches code substring."""
    await _seed_tenant_with(db_session, code="ACME_CORP", display_name="Acme Corp")
    await _seed_tenant_with(db_session, code="OTHER_CO", display_name="Other Co")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants?search=ACME")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    codes = [item["code"] for item in body["items"]]
    assert "ACME_CORP" in codes
    assert "OTHER_CO" not in codes


async def test_list_tenants_pagination(db_session: AsyncSession) -> None:
    """limit + offset return distinct paginated slices.

    Uses ILIKE search to isolate the 3 seeded PAGE_* tenants so the test
    is independent of any other tenants seeded by sibling fixtures.
    Endpoint orders by (created_at DESC, id DESC) for deterministic
    pagination even when tenants share the same created_at timestamp.
    """
    for i in range(3):
        await _seed_tenant_with(db_session, code=f"PAGE_{i}")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        page1 = await ac.get("/api/v1/admin/tenants?search=PAGE_&limit=2&offset=0")
        page2 = await ac.get("/api/v1/admin/tenants?search=PAGE_&limit=2&offset=2")
    assert page1.status_code == 200 and page2.status_code == 200
    body1 = page1.json()
    body2 = page2.json()
    assert body1["limit"] == 2 and body1["offset"] == 0
    assert body2["limit"] == 2 and body2["offset"] == 2
    assert body1["total"] == 3 and body2["total"] == 3
    assert len(body1["items"]) == 2
    assert len(body2["items"]) == 1
    # Pages must not overlap.
    ids1 = {item["id"] for item in body1["items"]}
    ids2 = {item["id"] for item in body2["items"]}
    assert ids1.isdisjoint(ids2)


async def test_list_tenants_empty_filter(db_session: AsyncSession) -> None:
    """Search with no match → items=[] + total=0."""
    await _seed_tenant_with(db_session, code="EXISTING_CODE")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants?search=NONEXISTENT_TENANT_99999")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0


async def test_list_tenants_invalid_query_limit(db_session: AsyncSession) -> None:
    """limit > 200 → 422 Unprocessable Entity (Pydantic Query validation)."""
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants?limit=500")
    assert resp.status_code == 422


# =====================================================================
# Sprint 57.47 — TenantListItem 7→12 field exposure tests (Track A US-1)
# =====================================================================
async def test_list_tenants_response_has_region_field(db_session: AsyncSession) -> None:
    """Sprint 57.47 US-1: each list item exposes `region` matching ORM."""
    await _seed_tenant_with(db_session, code="REGION_T1", region="apac")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants?search=REGION_T1")
    assert resp.status_code == 200, resp.text
    item = resp.json()["items"][0]
    assert "region" in item
    assert item["region"] == "apac"


async def test_list_tenants_response_has_locale_field(db_session: AsyncSession) -> None:
    """Sprint 57.47 US-1: each list item exposes `locale` matching ORM."""
    await _seed_tenant_with(db_session, code="LOCALE_T1", locale="zh-TW")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants?search=LOCALE_T1")
    assert resp.status_code == 200, resp.text
    item = resp.json()["items"][0]
    assert "locale" in item
    assert item["locale"] == "zh-TW"


async def test_list_tenants_response_has_retention_days_field(db_session: AsyncSession) -> None:
    """Sprint 57.47 US-1: each list item exposes `retention_days` matching ORM."""
    await _seed_tenant_with(db_session, code="RETENT_T1", retention_days=365)
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants?search=RETENT_T1")
    assert resp.status_code == 200, resp.text
    item = resp.json()["items"][0]
    assert "retention_days" in item
    assert item["retention_days"] == 365


async def test_list_tenants_response_has_sso_enabled_field(db_session: AsyncSession) -> None:
    """Sprint 57.47 US-1: each list item exposes `sso_enabled` matching ORM."""
    await _seed_tenant_with(db_session, code="SSO_T1", sso_enabled=True)
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants?search=SSO_T1")
    assert resp.status_code == 200, resp.text
    item = resp.json()["items"][0]
    assert "sso_enabled" in item
    assert item["sso_enabled"] is True


async def test_list_tenants_response_has_seats_field(db_session: AsyncSession) -> None:
    """Sprint 57.47 US-1: each list item exposes `seats` matching ORM."""
    await _seed_tenant_with(db_session, code="SEATS_T1", seats=42)
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants?search=SEATS_T1")
    assert resp.status_code == 200, resp.text
    item = resp.json()["items"][0]
    assert "seats" in item
    assert item["seats"] == 42


async def test_list_tenants_response_default_settings_via_server_defaults(
    db_session: AsyncSession,
) -> None:
    """Sprint 57.47 US-1: ORM server_defaults (region='global', locale='en-US',
    retention_days=90, sso_enabled=FALSE, seats=5) populate via from_attributes
    when not explicitly set at insert time.

    Mirrors identity.py L145-169 server_default declarations.
    """
    await _seed_tenant_with(db_session, code="DEFAULT_T1")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants?search=DEFAULT_T1")
    assert resp.status_code == 200, resp.text
    item = resp.json()["items"][0]
    assert item["region"] == "global"
    assert item["locale"] == "en-US"
    assert item["retention_days"] == 90
    assert item["sso_enabled"] is False
    assert item["seats"] == 5


# =====================================================================
# Sprint 57.47 — region filter tests (Track A US-2)
# =====================================================================
async def test_list_tenants_filter_by_region_positive_match(
    db_session: AsyncSession,
) -> None:
    """Sprint 57.47 US-2: filter `region=apac` returns only apac tenants."""
    await _seed_tenant_with(db_session, code="APAC_T1", region="apac")
    await _seed_tenant_with(db_session, code="EMEA_T1", region="emea")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants?region=apac")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert all(item["region"] == "apac" for item in body["items"])
    codes = [item["code"] for item in body["items"]]
    assert "APAC_T1" in codes
    assert "EMEA_T1" not in codes


async def test_list_tenants_filter_by_region_no_match(db_session: AsyncSession) -> None:
    """Sprint 57.47 US-2: filter `region=americas` with no matches → empty list."""
    await _seed_tenant_with(db_session, code="REGION_ONLY_APAC", region="apac")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Use a unique region value + search to isolate this assertion from
        # any sibling-fixture-seeded tenants in the test DB.
        resp = await ac.get("/api/v1/admin/tenants?region=americas&search=REGION_ONLY_APAC")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0


async def test_list_tenants_filter_region_plus_plan_combined(
    db_session: AsyncSession,
) -> None:
    """Sprint 57.47 US-2: `region=apac&plan=enterprise` AND-combines filters."""
    await _seed_tenant_with(
        db_session, code="COMBO_APAC_ENT", region="apac", plan=TenantPlan.ENTERPRISE
    )
    await _seed_tenant_with(
        db_session, code="COMBO_EMEA_ENT", region="emea", plan=TenantPlan.ENTERPRISE
    )
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants?region=apac&plan=enterprise")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    codes = [item["code"] for item in body["items"]]
    assert "COMBO_APAC_ENT" in codes
    assert "COMBO_EMEA_ENT" not in codes
    assert all(item["region"] == "apac" and item["plan"] == "enterprise" for item in body["items"])


async def test_list_tenants_filter_region_plus_state_combined(
    db_session: AsyncSession,
) -> None:
    """Sprint 57.47 US-2: `region=apac&state=active` AND-combines filters."""
    await _seed_tenant_with(
        db_session, code="RSCOMB_APAC_ACT", region="apac", state=TenantState.ACTIVE
    )
    await _seed_tenant_with(
        db_session, code="RSCOMB_APAC_REQ", region="apac", state=TenantState.REQUESTED
    )
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants?region=apac&state=active")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    codes = [item["code"] for item in body["items"]]
    assert "RSCOMB_APAC_ACT" in codes
    assert "RSCOMB_APAC_REQ" not in codes
    assert all(item["region"] == "apac" and item["state"] == "active" for item in body["items"])


async def test_list_tenants_no_region_filter_returns_all_regions(
    db_session: AsyncSession,
) -> None:
    """Sprint 57.47 US-2: omitting `region` param preserves backward-compat
    (no filter applied; results span all regions).
    """
    await _seed_tenant_with(db_session, code="BCOMPAT_APAC", region="apac")
    await _seed_tenant_with(db_session, code="BCOMPAT_EMEA", region="emea")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants?search=BCOMPAT_")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    regions = {item["region"] for item in body["items"]}
    assert {"apac", "emea"}.issubset(regions)


async def test_list_tenants_filter_region_max_length_validation(
    db_session: AsyncSession,
) -> None:
    """Sprint 57.47 US-2: region param has max_length=32 → over-long → 422."""
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    over_long = "a" * 33
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants?region={over_long}")
    assert resp.status_code == 422
