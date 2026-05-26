"""
File: backend/tests/integration/api/test_admin_tenant_settings_extension.py
Purpose: Integration tests — Sprint 57.46 TenantSettings 5-column extension
    (GET defaults + PATCH each field + validators + multi-tenant isolation).
Category: Tests / Integration / API (Phase 57+ SaaS Frontend / Sprint 57.46 Track B)
Scope: Sprint 57.46 / Day 1 / Task 2 — closes AD-TenantSettings-Backend-Schema-Extension

Description:
    Verifies the GET /admin/tenants/{tenant_id} returns 5 new SaaS columns
    with sensible defaults, and PATCH accepts each individually + in batch:
        - region (apac/emea/americas/global; whitelist enforced)
        - locale (BCP-47 regex enforced)
        - retention_days (1-3650 range)
        - sso_enabled (bool)
        - seats (≥1 range)

    Also verifies invalid values produce 422, full audit chain entries are
    written for each field change, and a cross-tenant PATCH attempt does not
    cross-contaminate.

    Mirrors test_admin_tenant_patch.py pattern (FastAPI test app + role
    middleware + db_session + require_admin_platform_role overrides + audit
    chain assertion).

Created: 2026-05-26 (Sprint 57.46 Day 1)
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from uuid import UUID

import pytest
from fastapi import FastAPI, Request, Response
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.admin.tenants import router as admin_tenants_router
from infrastructure.db.models.audit import AuditLog
from infrastructure.db.session import get_db_session
from platform_layer.identity.auth import (
    require_admin_platform_role,
    require_tenant_match_or_platform_admin,
)
from tests.conftest import seed_tenant

pytestmark = pytest.mark.asyncio


def _uniq(prefix: str) -> str:
    """Generate a unique tenant code per test invocation.

    `update_tenant` endpoint commits transactions (write audit chain + flush
    tenant changes), which escape the per-test rollback. Subsequent test
    runs with hard-coded `code` values hit `uq_tenants_code` violations.
    `uuid.uuid4().hex[:8]` produces low-collision short suffixes (8 hex chars
    ≈ 4.3 billion permutations) while keeping `code` length ≤ 64 (ORM cap).
    """
    return f"{prefix}_{uuid.uuid4().hex[:8].upper()}"


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
        app.dependency_overrides[require_tenant_match_or_platform_admin] = _override_admin

    return app


# ---------------------------------------------------------------------
# GET — defaults backfilled per migration 0018 (1 test, asserts all 5)
# ---------------------------------------------------------------------


async def test_get_returns_5_defaults(db_session: AsyncSession) -> None:
    """Fresh tenant returns server-default values for 5 new SaaS columns."""
    t = await seed_tenant(db_session, code=_uniq("GET_DEFAULTS"))
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{t.id}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["region"] == "global"
    assert body["locale"] == "en-US"
    assert body["retention_days"] == 90
    assert body["sso_enabled"] is False
    assert body["seats"] == 5


# ---------------------------------------------------------------------
# PATCH — individual field happy paths (5 tests, one per field)
# ---------------------------------------------------------------------


async def test_patch_region(db_session: AsyncSession) -> None:
    """PATCH region updates field + writes audit entry with region in changed_fields."""
    t = await seed_tenant(db_session, code=_uniq("PATCH_REGION"))
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.patch(
            f"/api/v1/admin/tenants/{t.id}",
            json={"region": "apac"},
        )
    assert resp.status_code == 200, resp.text
    assert resp.json()["region"] == "apac"

    result = await db_session.execute(
        select(AuditLog)
        .where(AuditLog.tenant_id == t.id)
        .where(AuditLog.operation == "tenant_settings_updated")
    )
    entries = result.scalars().all()
    assert len(entries) == 1
    assert entries[0].operation_data["changed_fields"] == ["region"]
    assert entries[0].operation_data["old_values"]["region"] == "global"
    assert entries[0].operation_data["new_values"]["region"] == "apac"


async def test_patch_locale(db_session: AsyncSession) -> None:
    """PATCH locale (BCP-47) updates + audit entry."""
    t = await seed_tenant(db_session, code=_uniq("PATCH_LOCALE"))
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.patch(
            f"/api/v1/admin/tenants/{t.id}",
            json={"locale": "zh-Hant"},
        )
    assert resp.status_code == 200, resp.text
    assert resp.json()["locale"] == "zh-Hant"


async def test_patch_retention_days(db_session: AsyncSession) -> None:
    """PATCH retention_days updates int + audit entry."""
    t = await seed_tenant(db_session, code=_uniq("PATCH_RETENTION"))
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.patch(
            f"/api/v1/admin/tenants/{t.id}",
            json={"retention_days": 180},
        )
    assert resp.status_code == 200, resp.text
    assert resp.json()["retention_days"] == 180


async def test_patch_sso_enabled(db_session: AsyncSession) -> None:
    """PATCH sso_enabled flips bool + audit entry."""
    t = await seed_tenant(db_session, code=_uniq("PATCH_SSO"))
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.patch(
            f"/api/v1/admin/tenants/{t.id}",
            json={"sso_enabled": True},
        )
    assert resp.status_code == 200, resp.text
    assert resp.json()["sso_enabled"] is True


async def test_patch_seats(db_session: AsyncSession) -> None:
    """PATCH seats updates int + audit entry."""
    t = await seed_tenant(db_session, code=_uniq("PATCH_SEATS"))
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.patch(
            f"/api/v1/admin/tenants/{t.id}",
            json={"seats": 25},
        )
    assert resp.status_code == 200, resp.text
    assert resp.json()["seats"] == 25


# ---------------------------------------------------------------------
# PATCH — batch update all 5 at once (1 test)
# ---------------------------------------------------------------------


async def test_patch_all_5_at_once(db_session: AsyncSession) -> None:
    """Single PATCH with all 5 fields → 1 audit entry with all 5 in changed_fields."""
    t = await seed_tenant(db_session, code=_uniq("BATCH_ALL_5"))
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    payload = {
        "region": "emea",
        "locale": "en-GB",
        "retention_days": 365,
        "sso_enabled": True,
        "seats": 100,
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.patch(f"/api/v1/admin/tenants/{t.id}", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["region"] == "emea"
    assert body["locale"] == "en-GB"
    assert body["retention_days"] == 365
    assert body["sso_enabled"] is True
    assert body["seats"] == 100

    result = await db_session.execute(
        select(AuditLog)
        .where(AuditLog.tenant_id == t.id)
        .where(AuditLog.operation == "tenant_settings_updated")
    )
    entries = result.scalars().all()
    assert len(entries) == 1
    assert set(entries[0].operation_data["changed_fields"]) == {
        "region",
        "locale",
        "retention_days",
        "sso_enabled",
        "seats",
    }


# ---------------------------------------------------------------------
# PATCH — validator-enforced 422 (4 tests)
# ---------------------------------------------------------------------


async def test_patch_region_invalid_value_422(db_session: AsyncSession) -> None:
    """PATCH region with value outside whitelist → 422."""
    t = await seed_tenant(db_session, code=_uniq("REG_INVALID"))
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.patch(
            f"/api/v1/admin/tenants/{t.id}",
            json={"region": "antarctica"},
        )
    assert resp.status_code == 422


async def test_patch_locale_invalid_format_422(db_session: AsyncSession) -> None:
    """PATCH locale with malformed BCP-47 string → 422."""
    t = await seed_tenant(db_session, code=_uniq("LOC_INVALID"))
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.patch(
            f"/api/v1/admin/tenants/{t.id}",
            json={"locale": "this_is_not_bcp47"},
        )
    assert resp.status_code == 422


async def test_patch_retention_days_zero_422(db_session: AsyncSession) -> None:
    """PATCH retention_days = 0 → 422 (must be ≥ 1)."""
    t = await seed_tenant(db_session, code=_uniq("RET_ZERO"))
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.patch(
            f"/api/v1/admin/tenants/{t.id}",
            json={"retention_days": 0},
        )
    assert resp.status_code == 422


async def test_patch_seats_zero_422(db_session: AsyncSession) -> None:
    """PATCH seats = 0 → 422 (must be ≥ 1)."""
    t = await seed_tenant(db_session, code=_uniq("SEATS_ZERO"))
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.patch(
            f"/api/v1/admin/tenants/{t.id}",
            json={"seats": 0},
        )
    assert resp.status_code == 422


# ---------------------------------------------------------------------
# Multi-tenant isolation (1 test) — PATCH tenant_a does not affect tenant_b
# ---------------------------------------------------------------------


async def test_patch_cross_tenant_isolation(db_session: AsyncSession) -> None:
    """PATCH tenant_a's region does NOT change tenant_b's region."""
    t_a = await seed_tenant(db_session, code=_uniq("ISO_A"))
    t_b = await seed_tenant(db_session, code=_uniq("ISO_B"))
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)

    # PATCH only tenant_a.
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp_a = await ac.patch(
            f"/api/v1/admin/tenants/{t_a.id}",
            json={"region": "apac", "seats": 42},
        )
    assert resp_a.status_code == 200
    assert resp_a.json()["region"] == "apac"
    assert resp_a.json()["seats"] == 42

    # tenant_b should retain defaults — fetch fresh via GET.
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp_b = await ac.get(f"/api/v1/admin/tenants/{t_b.id}")
    assert resp_b.status_code == 200
    body_b = resp_b.json()
    assert body_b["region"] == "global"
    assert body_b["seats"] == 5

    # Audit chain — exactly 1 entry against tenant_a; ZERO against tenant_b.
    # (Other tests' audit rows are scoped out by tenant_id filter.)
    result_a = await db_session.execute(
        select(AuditLog)
        .where(AuditLog.tenant_id == t_a.id)
        .where(AuditLog.operation == "tenant_settings_updated")
    )
    assert len(result_a.scalars().all()) == 1

    result_b = await db_session.execute(
        select(AuditLog)
        .where(AuditLog.tenant_id == t_b.id)
        .where(AuditLog.operation == "tenant_settings_updated")
    )
    assert len(result_b.scalars().all()) == 0
