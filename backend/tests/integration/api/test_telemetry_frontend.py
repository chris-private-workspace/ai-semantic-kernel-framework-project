"""
File: backend/tests/integration/api/test_telemetry_frontend.py
Purpose: Integration tests — POST /api/v1/telemetry/frontend + /frontend-error (Sprint 57.13 US-B4).
Category: Tests / Integration / API (範疇 12 Observability — frontend telemetry sink)
Scope: Sprint 57.13 / Day 6 / US-B4

Description:
    Verifies the two anonymous telemetry beacon endpoints:
    - POST /telemetry/frontend       — a Web-Vitals sample → 204, no auth needed
    - POST /telemetry/frontend-error — an uncaught frontend error → 204, no auth needed
    - malformed bodies → 422 (Pydantic), not 500
    - the endpoints accept no JWT (they're in EXEMPT_PATH_PREFIXES) — here we
      just mount the router with no auth middleware, mirroring the prod posture.

Created: 2026-05-10 (Sprint 57.13 Day 6)

Related:
    - backend/src/api/v1/telemetry.py (the router under test)
    - frontend/src/lib/observability.ts (the beacon producer)
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.v1.telemetry import router as telemetry_router

pytestmark = pytest.mark.asyncio


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(telemetry_router, prefix="/api/v1")
    return app


async def test_web_vital_returns_204() -> None:
    app = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/v1/telemetry/frontend",
            json={
                "name": "LCP",
                "value": 1234.5,
                "id": "v3-1700000000000-1234567890123",
                "rating": "good",
                "navigationType": "navigate",
                "url": "http://localhost:3007/cost-dashboard",
            },
        )
    assert resp.status_code == 204
    assert resp.content == b""


async def test_web_vital_minimal_body_ok() -> None:
    """Only name/value/id are required; rating/navigationType/url are optional."""
    app = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/v1/telemetry/frontend",
            json={"name": "CLS", "value": 0.02, "id": "x"},
        )
    assert resp.status_code == 204


async def test_web_vital_bad_body_is_422_not_500() -> None:
    app = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/telemetry/frontend", json={"name": "CLS"})  # missing value/id
    assert resp.status_code == 422


async def test_frontend_error_returns_204() -> None:
    app = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/v1/telemetry/frontend-error",
            json={
                "message": "Cannot read properties of undefined (reading 'foo')",
                "stack": "Error: ...\n  at App (App.tsx:1:1)",
                "url": "http://localhost:3007/governance",
                "user_agent": "Mozilla/5.0",
                "context": {"componentStack": "  at Foo\n  at Bar"},
            },
        )
    assert resp.status_code == 204
    assert resp.content == b""


async def test_frontend_error_minimal_body_ok() -> None:
    app = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/telemetry/frontend-error", json={"message": "boom"})
    assert resp.status_code == 204


async def test_frontend_error_missing_message_is_422() -> None:
    app = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/telemetry/frontend-error", json={"stack": "..."})
    assert resp.status_code == 422
