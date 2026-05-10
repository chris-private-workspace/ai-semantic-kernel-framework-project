"""
File: backend/tests/integration/api/test_admin_sla_reports.py
Purpose: Integration tests — GET /admin/tenants/{tid}/sla-report endpoint.
Category: Tests / Integration / API (Phase 56 SaaS Stage 1)
Scope: Sprint 56.3 / Day 2 / 2 integration US-2.

Description:
    Two flows:
    - test_admin_sla_report_endpoint_403_without_admin_role — non-admin → 403
    - test_admin_sla_report_endpoint_returns_json_with_4_metrics — admin role
      hits the endpoint;empty Redis sliding window → all p99 fields None +
      violations_count = 0;response shape conforms to SLAReportResponse.

Created: 2026-05-06 (Sprint 56.3 Day 2)
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Awaitable, Callable
from uuid import UUID, uuid4

import pytest
from fakeredis.aioredis import FakeRedis
from fastapi import FastAPI, Request, Response
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.admin.sla_reports import router as admin_sla_reports_router
from infrastructure.db.session import get_db_session
from platform_layer.identity.auth import require_tenant_match_or_platform_admin
from platform_layer.observability.sla_monitor import (
    SLAMetricRecorder,
    set_sla_recorder,
)
from tests.conftest import seed_tenant

pytestmark = pytest.mark.asyncio


def _build_app(db_session: AsyncSession | None = None) -> FastAPI:
    app = FastAPI()
    app.include_router(admin_sla_reports_router, prefix="/api/v1")

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
        app.dependency_overrides[require_tenant_match_or_platform_admin] = _override_admin

    return app


async def test_admin_sla_report_endpoint_403_without_admin_role() -> None:
    """Non-admin role reaching for a different tenant via the URL → 403 (Sprint 57.13 US-A3)."""
    app = _build_app()
    user_id = uuid4()
    path_tenant_id = uuid4()
    caller_tenant_id = uuid4()  # different → cross-tenant
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            f"/api/v1/admin/tenants/{path_tenant_id}/sla-report?month=2026-05",
            headers={
                "X-Test-User": str(user_id),
                "X-Test-Roles": json.dumps(["tenant_admin"]),
                "X-Test-Tenant": str(caller_tenant_id),
            },
        )
    assert resp.status_code == 403
    assert "cross-tenant" in resp.json()["detail"]


async def test_admin_sla_report_endpoint_returns_json_with_4_metrics(
    db_session: AsyncSession,
) -> None:
    """Admin auth → 200 + JSON response shape with 4 latency metric fields."""
    t = await seed_tenant(db_session, code="SLA_EP_1")

    # Wire SLAMetricRecorder for the on-demand generate path.
    redis_client = FakeRedis(decode_responses=False)
    set_sla_recorder(SLAMetricRecorder(redis_client=redis_client))

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            f"/api/v1/admin/tenants/{t.id}/sla-report?month=2026-05",
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["tenant_id"] == str(t.id)
    assert body["month"] == "2026-05"
    # 4 latency metric categories present (None when no data).
    assert "loop_simple_p99_ms" in body
    assert "loop_medium_p99_ms" in body
    assert "loop_complex_p99_ms" in body
    assert "hitl_queue_notif_p99_ms" in body
    assert body["violations_count"] == 0

    await redis_client.aclose()
