"""
File: backend/tests/integration/agent_harness/test_rate_limit_middleware.py
Purpose: Integration tests — RateLimitMiddleware runtime enforcement (Sprint 57.58 Track A).
Category: Tests / Integration / Middleware (Phase 58.x RateLimits RuntimeEnforcement)
Scope: Sprint 57.58 Day 1 Track A

Description:
    Verifies RateLimitMiddleware end-to-end against a fakeredis-backed
    RedisRateLimitCounter:
    - enforce pass: under-limit requests reach the route (200)
    - enforce block: over-limit request gets 429 + Retry-After + X-RateLimit-*
    - bypass admin role: admin JWT role skips enforcement
    - bypass no tenant: request with no tenant_id skips enforcement
    - multi-tenant isolation: tenant A hitting its limit does NOT block tenant B
    - 429 response shape: error / resource / limit / window / retry_after_seconds

    The middleware reads the tenant's {label, value} rate-limit list from the DB
    via _load_rate_limits; here we monkeypatch that read so the tests are
    DB-free and deterministic (the DB read path is exercised by the Track C
    usage endpoint + admin GET/PUT integration tests).

Created: 2026-05-28 (Sprint 57.58 Day 1)

Modification History (newest-first):
    - 2026-05-28: Sprint 57.59 — restore class-level _load_rate_limits monkeypatch after each test
    - 2026-05-28: Initial creation (Sprint 57.58 Track A — RateLimits RuntimeEnforcement)
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID, uuid4

import pytest
from fakeredis.aioredis import FakeRedis
from fastapi import FastAPI, Request, Response
from httpx import ASGITransport, AsyncClient

from platform_layer.middleware.rate_limit import RateLimitMiddleware
from platform_layer.tenant.rate_limit_counter import (
    RedisRateLimitCounter,
    reset_rate_limit_counter,
    set_rate_limit_counter,
)

pytestmark = pytest.mark.asyncio


@pytest.fixture
def fake_redis() -> FakeRedis:
    return FakeRedis(decode_responses=False)


@pytest.fixture(autouse=True)
def _reset_counter() -> Any:
    reset_rate_limit_counter()
    yield
    reset_rate_limit_counter()


@pytest.fixture(autouse=True)
def _restore_load_rate_limits() -> Any:
    """Restore RateLimitMiddleware._load_rate_limits after each test.

    _build_app monkeypatches the method at CLASS level (so the middleware
    instance the app creates internally picks it up). Without restoring it the
    fake leaks into other tests in the same process that exercise the real DB
    read path (e.g. Sprint 57.59 test_rate_limit_usage_persistence). Save +
    restore the original here (Risk Class C — module/class-level mutation needs
    reset per testing.md).
    """
    original = RateLimitMiddleware._load_rate_limits
    yield
    RateLimitMiddleware._load_rate_limits = original  # type: ignore[method-assign]


def _build_app(
    *,
    items: list[dict[str, str]],
    tenant_id: UUID | None,
    roles: list[str] | None,
) -> FastAPI:
    """App with RateLimitMiddleware + a test route + state-populating shim.

    `_load_rate_limits` is patched on the middleware instance so no DB is hit;
    request.state.{tenant_id, roles} are injected by an inner http middleware
    (mirrors the X-Test-* pattern used by api integration tests).
    """
    app = FastAPI()

    @app.get("/api/v1/ping")
    async def ping() -> dict[str, str]:
        return {"ok": "pong"}

    app.add_middleware(RateLimitMiddleware)

    @app.middleware("http")
    async def _populate_state(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request.state.tenant_id = tenant_id
        request.state.roles = roles
        return await call_next(request)

    # Patch the per-request DB read so no DB is hit. The middleware calls
    # self._load_rate_limits(tenant_id); the patched method ignores self +
    # tenant_id and returns the fixed items list.
    async def _fake_load(_self: RateLimitMiddleware, _tenant_id: UUID) -> list[object]:
        return list(items)

    RateLimitMiddleware._load_rate_limits = _fake_load  # type: ignore[assignment,method-assign]

    return app


async def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_enforce_pass_under_limit(fake_redis: FakeRedis) -> None:
    """Requests under the limit reach the route (200)."""
    set_rate_limit_counter(RedisRateLimitCounter(fake_redis))
    tenant_id = uuid4()
    app = _build_app(
        items=[{"label": "API requests", "value": "5 / min"}],
        tenant_id=tenant_id,
        roles=["member"],
    )
    async with await _client(app) as ac:
        for _ in range(5):
            resp = await ac.get("/api/v1/ping")
            assert resp.status_code == 200, resp.text


async def test_enforce_block_over_limit_headers(fake_redis: FakeRedis) -> None:
    """The (limit+1)th request gets 429 with Retry-After + X-RateLimit-* headers."""
    set_rate_limit_counter(RedisRateLimitCounter(fake_redis))
    tenant_id = uuid4()
    app = _build_app(
        items=[{"label": "API requests", "value": "2 / min"}],
        tenant_id=tenant_id,
        roles=["member"],
    )
    async with await _client(app) as ac:
        assert (await ac.get("/api/v1/ping")).status_code == 200
        assert (await ac.get("/api/v1/ping")).status_code == 200
        blocked = await ac.get("/api/v1/ping")
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers
    assert blocked.headers["X-RateLimit-Limit"] == "2"
    assert blocked.headers["X-RateLimit-Remaining"] == "0"
    assert "X-RateLimit-Reset" in blocked.headers
    assert int(blocked.headers["Retry-After"]) >= 1


async def test_bypass_admin_role(fake_redis: FakeRedis) -> None:
    """Admin role skips enforcement even far past the limit."""
    set_rate_limit_counter(RedisRateLimitCounter(fake_redis))
    tenant_id = uuid4()
    app = _build_app(
        items=[{"label": "API requests", "value": "1 / min"}],
        tenant_id=tenant_id,
        roles=["admin"],
    )
    async with await _client(app) as ac:
        for _ in range(5):
            assert (await ac.get("/api/v1/ping")).status_code == 200


async def test_bypass_no_tenant(fake_redis: FakeRedis) -> None:
    """No tenant_id (internal call) skips enforcement."""
    set_rate_limit_counter(RedisRateLimitCounter(fake_redis))
    app = _build_app(
        items=[{"label": "API requests", "value": "1 / min"}],
        tenant_id=None,
        roles=["member"],
    )
    async with await _client(app) as ac:
        for _ in range(5):
            assert (await ac.get("/api/v1/ping")).status_code == 200


async def test_multi_tenant_isolation(fake_redis: FakeRedis) -> None:
    """Tenant A exhausting its limit does NOT block tenant B (separate keys)."""
    counter = RedisRateLimitCounter(fake_redis)
    set_rate_limit_counter(counter)
    tenant_a = uuid4()
    tenant_b = uuid4()

    # Tenant A: limit 1 — exhaust it directly via the counter.
    first = await counter.check_and_increment(tenant_a, "api_requests", 60, 1)
    assert first.allowed is True
    second = await counter.check_and_increment(tenant_a, "api_requests", 60, 1)
    assert second.allowed is False

    # Tenant B with the same resource + limit 1 is unaffected.
    app_b = _build_app(
        items=[{"label": "API requests", "value": "1 / min"}],
        tenant_id=tenant_b,
        roles=["member"],
    )
    async with await _client(app_b) as ac:
        assert (await ac.get("/api/v1/ping")).status_code == 200


async def test_429_response_shape(fake_redis: FakeRedis) -> None:
    """429 body carries error / resource / limit / window / retry_after_seconds."""
    set_rate_limit_counter(RedisRateLimitCounter(fake_redis))
    tenant_id = uuid4()
    app = _build_app(
        items=[{"label": "API requests", "value": "1 / min"}],
        tenant_id=tenant_id,
        roles=["member"],
    )
    async with await _client(app) as ac:
        assert (await ac.get("/api/v1/ping")).status_code == 200
        blocked = await ac.get("/api/v1/ping")
    assert blocked.status_code == 429
    body = json.loads(blocked.content)
    assert body["error"] == "rate_limit_exceeded"
    assert body["resource"] == "api_requests"
    assert body["limit"] == 1
    assert body["window"] == 60
    assert body["retry_after_seconds"] >= 1
