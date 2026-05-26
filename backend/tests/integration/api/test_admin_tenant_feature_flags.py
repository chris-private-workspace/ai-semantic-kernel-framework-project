"""
File: backend/tests/integration/api/test_admin_tenant_feature_flags.py
Purpose: Integration tests — GET /admin/tenants/{tenant_id}/feature-flags (Sprint 57.48 Track B).
Category: Tests / Integration / API (Phase 58+ Backend Schema Extension wave)
Scope: Sprint 57.48 Day 1 Track B (closes AD-TenantSettings-FeatureFlags-Backend-AdminGet)

Description:
    Verifies the GET /admin/tenants/{tenant_id}/feature-flags endpoint:
    - 401 when no JWT context
    - 404 when tenant not found
    - 200 with empty list when no flags registered
    - 200 with resolved values (tenant_overrides applied over default_enabled)
    - Multi-tenant isolation (tenant A's override does NOT bleed into tenant B)
    - Response shape: items + total + limit + offset; items carry
      name/value/default_enabled/overridden/description/updated_at
    - Pagination (limit + offset) ordered by name ASC

Created: 2026-05-26 (Sprint 57.48 Day 1)

Modification History (newest-first):
    - 2026-05-26: Sprint 57.55 — +12 PUT tests + composite-replace clear behavior coverage
    - 2026-05-26: Initial creation (Sprint 57.48 Day 1 Track B — FeatureFlags admin GET)
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
from infrastructure.db.models.feature_flag import FeatureFlag
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


async def _seed_flag(
    session: AsyncSession,
    *,
    name: str,
    default_enabled: bool = False,
    tenant_overrides: dict[str, Any] | None = None,
    description: str | None = None,
) -> FeatureFlag:
    ff = FeatureFlag(
        name=name,
        default_enabled=default_enabled,
        tenant_overrides=tenant_overrides or {},
        description=description,
    )
    session.add(ff)
    await session.flush()
    await session.refresh(ff)
    return ff


async def test_list_feature_flags_401_without_auth() -> None:
    app = _build_app()
    tenant_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant_id}/feature-flags")
    assert resp.status_code == 401


async def test_list_feature_flags_404_when_tenant_not_found(db_session: AsyncSession) -> None:
    app = _build_app(db_session=db_session)
    missing_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{missing_id}/feature-flags")
    assert resp.status_code == 404


async def test_list_feature_flags_empty_when_registry_empty(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code="FF_EMPTY_T1")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/feature-flags")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0


async def test_list_feature_flags_resolves_default_when_no_override(
    db_session: AsyncSession,
) -> None:
    tenant = await _seed_tenant(db_session, code="FF_DEF_T1")
    await _seed_flag(db_session, name="ff.alpha", default_enabled=True)
    await _seed_flag(db_session, name="ff.beta", default_enabled=False)

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/feature-flags")
    assert resp.status_code == 200, resp.text
    items = resp.json()["items"]
    by_name = {item["name"]: item for item in items}
    assert by_name["ff.alpha"]["value"] is True
    assert by_name["ff.alpha"]["overridden"] is False
    assert by_name["ff.beta"]["value"] is False
    assert by_name["ff.beta"]["overridden"] is False


async def test_list_feature_flags_applies_tenant_override(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code="FF_OVR_T1")
    await _seed_flag(
        db_session,
        name="ff.gamma",
        default_enabled=False,
        tenant_overrides={str(tenant.id): True},
    )

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/feature-flags")
    assert resp.status_code == 200, resp.text
    item = next(i for i in resp.json()["items"] if i["name"] == "ff.gamma")
    assert item["value"] is True
    assert item["overridden"] is True
    assert item["default_enabled"] is False


async def test_list_feature_flags_response_shape(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code="FF_SHAPE_T1")
    await _seed_flag(db_session, name="ff.shape", default_enabled=True, description="desc")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/feature-flags")
    assert resp.status_code == 200, resp.text
    item = resp.json()["items"][0]
    expected = {"name", "value", "default_enabled", "overridden", "description", "updated_at"}
    assert expected.issubset(set(item.keys()))


async def test_list_feature_flags_tenant_isolation(db_session: AsyncSession) -> None:
    """Tenant A's override does not appear in tenant B's response."""
    tenant_a = await _seed_tenant(db_session, code="FF_ISO_A")
    tenant_b = await _seed_tenant(db_session, code="FF_ISO_B")
    await _seed_flag(
        db_session,
        name="ff.iso",
        default_enabled=False,
        tenant_overrides={str(tenant_a.id): True},
    )

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp_a = await ac.get(f"/api/v1/admin/tenants/{tenant_a.id}/feature-flags")
        resp_b = await ac.get(f"/api/v1/admin/tenants/{tenant_b.id}/feature-flags")

    item_a = next(i for i in resp_a.json()["items"] if i["name"] == "ff.iso")
    item_b = next(i for i in resp_b.json()["items"] if i["name"] == "ff.iso")
    assert item_a["value"] is True and item_a["overridden"] is True
    assert item_b["value"] is False and item_b["overridden"] is False


async def test_list_feature_flags_pagination(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code="FF_PAGE_T1")
    for i in range(3):
        await _seed_flag(db_session, name=f"ff.page{i}", default_enabled=False)

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        page1 = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/feature-flags?limit=2&offset=0")
        page2 = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/feature-flags?limit=2&offset=2")
    assert page1.status_code == 200 and page2.status_code == 200
    assert page1.json()["total"] == 3
    assert len(page1.json()["items"]) == 2
    assert len(page2.json()["items"]) == 1


# =====================================================================
# Sprint 57.55 Track A — PUT /{tenant_id}/feature-flags upsert tests
# =====================================================================
# IMPORTANT: PUT tests call FeatureFlagsService.set/clear_tenant_override
# which trigger db.commit() via the endpoint. To avoid "duplicate key"
# cross-test leakage on the unique tenants.code, each PUT test seeds its
# tenant with a uuid4-suffixed code (mirrors Sprint 57.54 HITL_PUT_% pattern;
# conftest.py extends LIKE 'FF_PUT_%' cleanup sweep).
#
# feature_flags table is global registry (no FK to tenants), so flag rows
# persist across tests; we use uuid4-suffixed flag names per test to avoid
# unique constraint collisions on `name`.


def _unique_code(prefix: str) -> str:
    """Return a unique tenant code suffix to survive committed-row leakage."""
    return f"{prefix}_{uuid4().hex[:8]}"


def _unique_flag(prefix: str) -> str:
    """Return a unique feature-flag name (registry has UNIQUE(name) PK)."""
    return f"{prefix}.{uuid4().hex[:8]}"


async def test_put_requires_admin_role() -> None:
    """No JWT context → 401/403 from require_admin_platform_role."""
    app = _build_app()
    tenant_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant_id}/feature-flags",
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
            f"/api/v1/admin/tenants/{missing_id}/feature-flags",
            json={"overrides": {}},
        )
    assert resp.status_code == 404


async def test_put_creates_new_overrides(db_session: AsyncSession) -> None:
    """No prior overrides → PUT sets values; resolved value flips per override."""
    tenant = await _seed_tenant(db_session, code=_unique_code("FF_PUT_CREATE"))
    flag_a = _unique_flag("ff.create_a")
    flag_b = _unique_flag("ff.create_b")
    await _seed_flag(db_session, name=flag_a, default_enabled=False)
    await _seed_flag(db_session, name=flag_b, default_enabled=True)
    await db_session.commit()

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/feature-flags",
            json={"overrides": {flag_a: True, flag_b: False}},
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["saved_overrides"] == {flag_a: True, flag_b: False}
    by_name = {item["name"]: item for item in body["items"]}
    assert by_name[flag_a]["value"] is True
    assert by_name[flag_a]["overridden"] is True
    assert by_name[flag_b]["value"] is False
    assert by_name[flag_b]["overridden"] is True


async def test_put_updates_existing_overrides(db_session: AsyncSession) -> None:
    """Prior overrides for SAME tenant get replaced when PUT-ed."""
    tenant = await _seed_tenant(db_session, code=_unique_code("FF_PUT_UPDATE"))
    flag = _unique_flag("ff.update")
    await _seed_flag(
        db_session,
        name=flag,
        default_enabled=False,
        tenant_overrides={str(tenant.id): True},
    )
    await db_session.commit()

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/feature-flags",
            json={"overrides": {flag: False}},
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    item = next(i for i in body["items"] if i["name"] == flag)
    assert item["value"] is False
    assert item["overridden"] is True


async def test_put_response_projects_items_matching_get(db_session: AsyncSession) -> None:
    """PUT then GET return identical projected items (cache hydration consistency)."""
    tenant = await _seed_tenant(db_session, code=_unique_code("FF_PUT_PROJECT"))
    flag = _unique_flag("ff.project")
    await _seed_flag(db_session, name=flag, default_enabled=False)
    await db_session.commit()

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        put_resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/feature-flags",
            json={"overrides": {flag: True}},
        )
        get_resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/feature-flags")
    assert put_resp.status_code == 200, put_resp.text
    assert get_resp.status_code == 200, get_resp.text
    # PUT response items contain all flags (no pagination); GET defaults limit=50
    # so for small test suites both should match. Compare by name → item dict.
    put_by_name = {item["name"]: item for item in put_resp.json()["items"]}
    get_by_name = {item["name"]: item for item in get_resp.json()["items"]}
    assert put_by_name[flag] == get_by_name[flag]


async def test_put_unknown_flag_rejected(db_session: AsyncSession) -> None:
    """Payload includes a non-existent flag name → 422."""
    tenant = await _seed_tenant(db_session, code=_unique_code("FF_PUT_UNKNOWN"))
    await db_session.commit()

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/feature-flags",
            json={"overrides": {"ff.does_not_exist_xyz": True}},
        )
    assert resp.status_code == 422, resp.text
    assert "ff.does_not_exist_xyz" in resp.text


async def test_put_extra_field_rejected(db_session: AsyncSession) -> None:
    """Unknown top-level field in payload → 422 via extra='forbid'."""
    tenant = await _seed_tenant(db_session, code=_unique_code("FF_PUT_EXTRA"))
    await db_session.commit()

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/feature-flags",
            json={"overrides": {}, "unknown_field": "leak"},
        )
    assert resp.status_code == 422


async def test_put_multi_tenant_isolation(db_session: AsyncSession) -> None:
    """PUT to tenant_b MUST NOT affect tenant_a's override (multi-tenant rule)."""
    tenant_a = await _seed_tenant(db_session, code=_unique_code("FF_PUT_ISO_A"))
    tenant_b = await _seed_tenant(db_session, code=_unique_code("FF_PUT_ISO_B"))
    flag = _unique_flag("ff.iso")
    await _seed_flag(
        db_session,
        name=flag,
        default_enabled=False,
        tenant_overrides={str(tenant_a.id): True},
    )
    await db_session.commit()

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp_b = await ac.put(
            f"/api/v1/admin/tenants/{tenant_b.id}/feature-flags",
            json={"overrides": {flag: False}},
        )
    assert resp_b.status_code == 200, resp_b.text

    # Verify tenant_a's override unchanged via direct ORM re-read.
    row = (
        await db_session.execute(select(FeatureFlag).where(FeatureFlag.name == flag))
    ).scalar_one()
    assert row.tenant_overrides.get(str(tenant_a.id)) is True
    assert row.tenant_overrides.get(str(tenant_b.id)) is False


async def test_put_empty_overrides_clears_all(db_session: AsyncSession) -> None:
    """PUT with {} clears all per-tenant overrides → resolved reverts to default."""
    tenant = await _seed_tenant(db_session, code=_unique_code("FF_PUT_CLEAR_ALL"))
    flag_a = _unique_flag("ff.clear_a")
    flag_b = _unique_flag("ff.clear_b")
    await _seed_flag(
        db_session,
        name=flag_a,
        default_enabled=False,
        tenant_overrides={str(tenant.id): True},
    )
    await _seed_flag(
        db_session,
        name=flag_b,
        default_enabled=True,
        tenant_overrides={str(tenant.id): False},
    )
    await db_session.commit()

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/feature-flags",
            json={"overrides": {}},
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    by_name = {item["name"]: item for item in body["items"]}
    # Both flags reverted to default_enabled; not overridden anymore.
    assert by_name[flag_a]["value"] is False
    assert by_name[flag_a]["overridden"] is False
    assert by_name[flag_b]["value"] is True
    assert by_name[flag_b]["overridden"] is False


async def test_put_composite_replace_clears_omitted(db_session: AsyncSession) -> None:
    """PUT with subset clears omitted prior overrides (composite-replace semantics)."""
    tenant = await _seed_tenant(db_session, code=_unique_code("FF_PUT_OMIT"))
    flag_keep = _unique_flag("ff.keep")
    flag_drop = _unique_flag("ff.drop")
    await _seed_flag(
        db_session,
        name=flag_keep,
        default_enabled=False,
        tenant_overrides={str(tenant.id): True},
    )
    await _seed_flag(
        db_session,
        name=flag_drop,
        default_enabled=False,
        tenant_overrides={str(tenant.id): True},
    )
    await db_session.commit()

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # PUT with only flag_keep → flag_drop's prior override should be cleared.
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/feature-flags",
            json={"overrides": {flag_keep: True}},
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    by_name = {item["name"]: item for item in body["items"]}
    assert by_name[flag_keep]["value"] is True
    assert by_name[flag_keep]["overridden"] is True
    assert by_name[flag_drop]["value"] is False  # default_enabled
    assert by_name[flag_drop]["overridden"] is False  # cleared


async def test_put_idempotent_same_payload_twice(db_session: AsyncSession) -> None:
    """PUT same payload twice → consistent state across both calls."""
    tenant = await _seed_tenant(db_session, code=_unique_code("FF_PUT_IDEMP"))
    flag = _unique_flag("ff.idemp")
    await _seed_flag(db_session, name=flag, default_enabled=False)
    await db_session.commit()

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        first = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/feature-flags",
            json={"overrides": {flag: True}},
        )
        second = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/feature-flags",
            json={"overrides": {flag: True}},
        )
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    # Compare items by flag name (other flags from earlier tests may exist in
    # registry but their values won't differ between calls)
    first_item = next(i for i in first.json()["items"] if i["name"] == flag)
    second_item = next(i for i in second.json()["items"] if i["name"] == flag)
    assert first_item == second_item
    assert first.json()["saved_overrides"] == second.json()["saved_overrides"]


async def test_put_persists_to_db_via_subsequent_get(db_session: AsyncSession) -> None:
    """Post-PUT GET reflects new resolved_value (db persistence verified)."""
    tenant = await _seed_tenant(db_session, code=_unique_code("FF_PUT_PERSIST"))
    flag = _unique_flag("ff.persist")
    await _seed_flag(db_session, name=flag, default_enabled=False)
    await db_session.commit()

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        put_resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/feature-flags",
            json={"overrides": {flag: True}},
        )
        get_resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/feature-flags")
    assert put_resp.status_code == 200, put_resp.text
    assert get_resp.status_code == 200, get_resp.text
    item = next(i for i in get_resp.json()["items"] if i["name"] == flag)
    assert item["value"] is True
    assert item["overridden"] is True
