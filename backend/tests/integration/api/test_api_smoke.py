"""
File: backend/tests/integration/api/test_api_smoke.py
Purpose: Connectivity smoke — every api/v1 router is mounted + answers a
representative GET with a dev JWT (status ∈ {200, 404}, valid JSON, never 500).
Category: Tests / Integration / API (Phase 57+ SaaS Frontend; Sprint 57.13 US-A5)
Scope: Sprint 57.13 / Day 3 / US-A5

Description:
    Builds the real app via api.main.create_app() (so middleware + router
    wiring is exactly what production runs), overrides only the DB session
    deps with the per-test rollback session, then hits one GET per router
    with a `platform_admin`-roled JWT. The contract is intentionally loose —
    we assert status ∈ {200, 404} and json-parseable body, NOT exact shape.
    The point is to catch import errors / un-mounted routers / 500s, the
    kind of regression that a focused per-endpoint test would miss because
    it builds its own mini-app.

    Roles ["admin", "platform_admin"] satisfy every RBAC dep in scope:
    require_admin_platform_role / require_audit_role (admin) /
    require_approver_role (admin) / require_tenant_match_or_platform_admin.

Created: 2026-05-10 (Sprint 57.13 Day 3)

Related:
    - backend/src/api/main.py (create_app — the thing under test)
    - backend/src/platform_layer/middleware/tenant_context.py (JWT decode)
    - backend/tests/conftest.py (db_session / seed_tenant / seed_user)
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from fakeredis.aioredis import FakeRedis
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.main import create_app
from infrastructure.db.session import get_db_session
from platform_layer.billing.pricing import PricingLoader, set_pricing_loader
from platform_layer.identity.jwt import JWTManager
from platform_layer.middleware.tenant_context import get_db_session_with_tenant
from platform_layer.observability.sla_monitor import SLAMetricRecorder, set_sla_recorder
from tests.conftest import seed_tenant, seed_user

pytestmark = pytest.mark.asyncio

# Same path the focused cost-summary test uses; parents[3] == backend/.
_PRICING_YAML = Path(__file__).resolve().parents[3] / "config" / "llm_pricing.yml"


async def test_api_v1_routers_smoke(db_session: AsyncSession) -> None:
    """Each api/v1 router responds 200/404 + valid JSON to a representative GET."""
    tenant = await seed_tenant(db_session, code="SMOKE_T", display_name="Smoke Tenant")
    user = await seed_user(db_session, tenant, email="smoke@test.com")
    token = JWTManager().encode(
        sub=str(user.id),
        tenant_id=tenant.id,
        roles=["admin", "platform_admin"],
    )

    # Strict singleton accessors (raise if unset) used by cost-summary +
    # sla-report. The autouse reset_* fixtures in this dir's conftest clean up.
    pl = PricingLoader()
    pl.load_from_yaml(_PRICING_YAML)
    set_pricing_loader(pl)
    set_sla_recorder(SLAMetricRecorder(redis_client=FakeRedis(decode_responses=False)))

    app = create_app()

    async def _override_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db_session] = _override_session
    app.dependency_overrides[get_db_session_with_tenant] = _override_session

    auth = {"Authorization": f"Bearer {token}"}
    month = "2026-05"
    paths = [
        ("/api/v1/health", {}),  # middleware-exempt, no auth needed
        ("/api/v1/auth/me", auth),
        ("/api/v1/admin/tenants", auth),
        (f"/api/v1/admin/tenants/{tenant.id}/cost-summary?month={month}", auth),
        (f"/api/v1/admin/tenants/{tenant.id}/sla-report?month={month}", auth),
        ("/api/v1/audit/log?limit=10", auth),
        ("/api/v1/verification/recent?limit=10", auth),
        ("/api/v1/memory/recent?layer=user&limit=10", auth),
        ("/api/v1/governance/approvals", auth),
    ]

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for path, headers in paths:
            resp = await ac.get(path, headers=headers)
            assert resp.status_code in (200, 404), f"{path} → {resp.status_code}: {resp.text}"
            # Body must be valid JSON regardless of 200/404 (FastAPI error envelopes are JSON).
            resp.json()


async def test_api_smoke_requires_auth(db_session: AsyncSession) -> None:
    """An auth-gated endpoint returns 401 with no JWT (middleware contract sanity)."""
    app = create_app()

    async def _override_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db_session] = _override_session
    app.dependency_overrides[get_db_session_with_tenant] = _override_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/admin/tenants")
    assert resp.status_code == 401
    resp.json()
