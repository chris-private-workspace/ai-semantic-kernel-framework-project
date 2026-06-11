"""
File: backend/tests/integration/api/test_admin_tenant_model_policy.py
Purpose: Integration tests — PUT/GET /admin/tenants/{id}/model-policy (Sprint 57.104 C1).
Category: Tests / Integration / API (config tiering)
Scope: Sprint 57.104 (C1 — per-tenant model policy admin write/read)

Description:
    Verifies the model-policy admin endpoints:
    - PUT: 401/403 without admin, 404 missing/cross-tenant, 422 unknown field
      (extra=forbid) + 422 unpriced model, 200 persists to meta_data["model_policy"]
      + composite-replace + audit chain + multi-tenant isolation
    - GET: 404 missing, 200 stored overrides (sparse), empty when unset

Created: 2026-06-11 (Sprint 57.104 C1)

Modification History (newest-first):
    - 2026-06-11: Initial creation (Sprint 57.104 C1)
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from pathlib import Path
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
from platform_layer.billing.pricing import (
    PricingLoader,
    maybe_get_pricing_loader,
    set_pricing_loader,
)
from platform_layer.identity.auth import require_admin_platform_role

pytestmark = pytest.mark.asyncio

# A real, priced azure_openai model + a guaranteed-unpriced one (Day-0 D4).
_PRICED_MODEL = "gpt-5.2"
_UNPRICED_MODEL = "totally-bogus-model-xyz"


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
    """Unique tenant code to survive committed-row leakage (conftest sweeps MODELPOL_PUT_%)."""
    return f"MODELPOL_PUT_{uuid4().hex[:8]}"


@pytest.fixture
def _pricing_loaded() -> Iterator[PricingLoader]:
    """Install a real PricingLoader (so model validation runs); restore prior after."""
    prior = maybe_get_pricing_loader()
    loader = PricingLoader()
    loader.load_from_yaml(str(Path(__file__).parents[3] / "config" / "llm_pricing.yml"))
    set_pricing_loader(loader)
    try:
        yield loader
    finally:
        set_pricing_loader(prior)


# === PUT: auth + 404 ===========================================================


async def test_put_requires_admin_role() -> None:
    app = _build_app()
    tenant_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant_id}/model-policy",
            json={"action_deployment": "x"},
        )
    assert resp.status_code in (401, 403)


async def test_put_tenant_not_found(db_session: AsyncSession) -> None:
    app = _build_app(db_session=db_session)
    missing_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{missing_id}/model-policy",
            json={"action_deployment": "x"},
        )
    assert resp.status_code == 404


# === PUT: persistence + composite-replace ======================================


async def test_put_creates_policy(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    payload = {"action_deployment": "tenant-deploy", "cheap_deployment": "tenant-cheap"}
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/model-policy",
            json=payload,
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["action_deployment"] == "tenant-deploy"
    assert body["cheap_deployment"] == "tenant-cheap"
    assert body["action_model"] is None

    row = (await db_session.execute(select(Tenant).where(Tenant.id == tenant.id))).scalar_one()
    assert row.meta_data is not None
    assert row.meta_data.get("model_policy") == payload


async def test_put_composite_replace(db_session: AsyncSession) -> None:
    """A 2nd PUT replaces the whole policy (omitted fields cleared)."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        first = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/model-policy",
            json={"action_deployment": "a", "cheap_deployment": "c"},
        )
        second = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/model-policy",
            json={"action_deployment": "a2"},
        )
    assert first.status_code == 200 and second.status_code == 200
    body = second.json()
    assert body["action_deployment"] == "a2"
    assert body["cheap_deployment"] is None  # cleared


async def test_put_empty_clears_policy(db_session: AsyncSession) -> None:
    """PUT {} clears any stored policy → meta_data drops model_policy entirely."""
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/model-policy",
            json={"action_deployment": "x"},
        )
        clear = await ac.put(f"/api/v1/admin/tenants/{tenant.id}/model-policy", json={})
    assert clear.status_code == 200, clear.text
    assert clear.json()["action_deployment"] is None
    row = (await db_session.execute(select(Tenant).where(Tenant.id == tenant.id))).scalar_one()
    assert "model_policy" not in (row.meta_data or {})


# === PUT: validation ===========================================================


async def test_put_extra_field_rejected(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/model-policy",
            json={"action_deployment": "x", "unknown_field": "leak"},
        )
    assert resp.status_code == 422


async def test_put_unpriced_model_rejected(
    db_session: AsyncSession, _pricing_loaded: PricingLoader
) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/model-policy",
            json={"action_model": _UNPRICED_MODEL},
        )
    assert resp.status_code == 422, resp.text
    assert _UNPRICED_MODEL in resp.text


async def test_put_priced_model_accepted(
    db_session: AsyncSession, _pricing_loaded: PricingLoader
) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/model-policy",
            json={"action_model": _PRICED_MODEL},
        )
    assert resp.status_code == 200, resp.text
    assert resp.json()["action_model"] == _PRICED_MODEL


# === PUT: isolation + audit ====================================================


async def test_put_multi_tenant_isolation(db_session: AsyncSession) -> None:
    tenant_a = await _seed_tenant(db_session, code=_unique_code())
    tenant_b = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp_a = await ac.put(
            f"/api/v1/admin/tenants/{tenant_a.id}/model-policy",
            json={"action_deployment": "a-deploy"},
        )
        resp_b = await ac.put(
            f"/api/v1/admin/tenants/{tenant_b.id}/model-policy",
            json={"cheap_deployment": "b-cheap"},
        )
    assert resp_a.status_code == 200 and resp_b.status_code == 200
    row_a = (await db_session.execute(select(Tenant).where(Tenant.id == tenant_a.id))).scalar_one()
    row_b = (await db_session.execute(select(Tenant).where(Tenant.id == tenant_b.id))).scalar_one()
    assert row_a.meta_data["model_policy"] == {"action_deployment": "a-deploy"}
    assert row_b.meta_data["model_policy"] == {"cheap_deployment": "b-cheap"}


async def test_put_audit_chain_emitted(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/model-policy",
            json={"action_deployment": "audit-deploy"},
        )
    assert resp.status_code == 200, resp.text
    result = await db_session.execute(
        select(AuditLog)
        .where(AuditLog.tenant_id == tenant.id)
        .where(AuditLog.operation == "tenant_model_policy_upsert")
    )
    entries = result.scalars().all()
    assert len(entries) == 1
    audit = entries[0]
    assert audit.resource_type == "tenant"
    assert audit.resource_id == str(tenant.id)
    assert audit.operation_data["policy"] == {"action_deployment": "audit-deploy"}
    assert audit.operation_result == "success"


# === GET =======================================================================


async def test_get_404_when_tenant_not_found(db_session: AsyncSession) -> None:
    app = _build_app(db_session=db_session)
    missing_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{missing_id}/model-policy")
    assert resp.status_code == 404


async def test_get_empty_when_unset(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code="MODELPOL_GET_UNSET")
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/model-policy")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body == {
        "action_deployment": None,
        "action_model": None,
        "cheap_deployment": None,
        "cheap_model": None,
    }


async def test_get_reflects_put(db_session: AsyncSession) -> None:
    tenant = await _seed_tenant(db_session, code=_unique_code())
    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.put(
            f"/api/v1/admin/tenants/{tenant.id}/model-policy",
            json={"action_deployment": "d1", "cheap_deployment": "d2"},
        )
        get_resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/model-policy")
    assert get_resp.status_code == 200, get_resp.text
    body = get_resp.json()
    assert body["action_deployment"] == "d1"
    assert body["cheap_deployment"] == "d2"
