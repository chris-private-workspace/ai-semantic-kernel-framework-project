"""
File: backend/tests/integration/api/test_admin_tenant_rate_limits_usage.py
Purpose: Integration tests — GET /admin/tenants/{id}/rate-limits/usage (Sprint 57.58 Track C).
Category: Tests / Integration / API (Phase 58.x RateLimits RuntimeEnforcement)
Scope: Sprint 57.58 Day 1 Track C

Description:
    Verifies the GET /admin/tenants/{tenant_id}/rate-limits/usage live-usage
    endpoint (RateLimitCounter.peek projection over the {label, value} config):
    - 401 when no JWT context (require_admin_platform_role)
    - 404 when tenant not found (_load_tenant_or_404)
    - 200 populated response: per-resource {resource, window, limit, current,
      reset_at}; current reflects the live counter (peek, no increment); non-rate
      items (e.g. "50 concurrent") are skipped.

Created: 2026-05-28 (Sprint 57.58 Day 1)

Modification History (newest-first):
    - 2026-05-28: Initial creation (Sprint 57.58 Track C — RateLimits live usage GET)
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any
from uuid import UUID, uuid4

import pytest
from fakeredis.aioredis import FakeRedis
from fastapi import FastAPI, Request, Response
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.admin.tenants import router as admin_tenants_router
from infrastructure.db.models.identity import Tenant, TenantPlan, TenantState
from infrastructure.db.session import get_db_session
from platform_layer.identity.auth import require_admin_platform_role
from platform_layer.tenant.rate_limit_counter import (
    RedisRateLimitCounter,
    reset_rate_limit_counter,
    set_rate_limit_counter,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def _reset_counter() -> Any:
    reset_rate_limit_counter()
    yield
    reset_rate_limit_counter()


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


def _unique_code() -> str:
    return f"RATE_LIMIT_USAGE_{uuid4().hex[:8]}"


async def test_usage_401_without_auth() -> None:
    app = _build_app()
    tenant_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant_id}/rate-limits/usage")
    assert resp.status_code == 401


async def test_usage_404_when_tenant_not_found(db_session: AsyncSession) -> None:
    app = _build_app(db_session=db_session)
    missing_id = uuid4()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{missing_id}/rate-limits/usage")
    assert resp.status_code == 404


async def test_usage_populated_response_shape(db_session: AsyncSession) -> None:
    """200 returns per-resource live usage; non-rate items skipped; current peeked."""
    fake_redis = FakeRedis(decode_responses=False)
    counter = RedisRateLimitCounter(fake_redis)
    set_rate_limit_counter(counter)

    tenant = await _seed_tenant(
        db_session,
        code=_unique_code(),
        meta_data={
            "rate_limits": [
                {"label": "API requests", "value": "100 / min"},
                {"label": "Tool calls", "value": "1,000 / min"},
                {"label": "SSE connections", "value": "50 concurrent"},  # skipped (non-rate)
            ]
        },
    )

    # Pre-consume 3 api_requests so the peek shows current=3.
    for _ in range(3):
        await counter.check_and_increment(tenant.id, "api_requests", 60, 100)

    app = _build_app(db_session=db_session)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/rate-limits/usage")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    # Only the two rate items (api_requests + tool_calls); concurrency skipped.
    resources = {item["resource"] for item in body["items"]}
    assert resources == {"api_requests", "tool_calls"}

    api = next(item for item in body["items"] if item["resource"] == "api_requests")
    assert api["limit"] == 100
    assert api["window"] == 60
    assert api["current"] == 3  # peek reflects the 3 pre-consumed requests
    assert {"resource", "window", "limit", "current", "reset_at"}.issubset(set(api.keys()))

    # peek MUST NOT increment — a second usage GET still shows current=3.
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp2 = await ac.get(f"/api/v1/admin/tenants/{tenant.id}/rate-limits/usage")
    api2 = next(item for item in resp2.json()["items"] if item["resource"] == "api_requests")
    assert api2["current"] == 3

    # tool_calls has no consumption yet → current=0.
    tool = next(item for item in body["items"] if item["resource"] == "tool_calls")
    assert tool["current"] == 0
