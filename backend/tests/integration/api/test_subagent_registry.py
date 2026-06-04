"""
File: backend/tests/integration/api/test_subagent_registry.py
Purpose: Integration tests for GET /api/v1/subagents (Sprint 57.78 — agent_catalog registry).
Category: Tests / Integration / API
Scope: Phase 57 / Sprint 57.78 (re-point from 57.19 stub)

Description:
    Sprint 57.78 re-pointed GET /subagents from the never-persisted "runtime
    invocations" stub (57.19 US-B4, returning empty + not_implemented_reason)
    to the real per-tenant agent_catalog registry view. These tests replace the
    prior stub-contract tests (not_implemented_reason / next_cursor / mode
    Literal 422) — that contract is gone, superseded by the catalog shape.

    Mounts the subagents router on a minimal FastAPI app and overrides identity
    deps with a synthetic tenant + RLS session (mirrors test_memory_matrix.py).
    Verifies the agent_catalog registry view:

    - Happy path: seeded agent_catalog rows map to the registry shape
      (key/name/model/allowed_modes/status/system_prompt/budget/tools)
    - gapped contains the 5 usage metrics (no runtime source)
    - budget/tools parse from meta_data; empty meta_data → budget None + tools []
    - Cross-tenant isolation: tenant B's rows are NOT visible to tenant A
    - Deps: unauthenticated (get_current_tenant raises 401) → 401

Created: 2026-05-17 (Sprint 57.19 Day 2 / US-B4)
Last Modified: 2026-06-04

Modification History (newest-first):
    - 2026-06-04: Sprint 57.78 — rewrite for agent_catalog registry re-point (was stub)
    - 2026-05-17: Initial creation (Sprint 57.19 Day 2 / US-B4)

Related:
    - api/v1/subagents.py (list_subagents)
    - infrastructure/db/models/agent_catalog.py (AgentCatalog ORM)
    - tests/integration/api/test_memory_matrix.py (fixture/RLS pattern reuse)
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID

import pytest
from fastapi import FastAPI, HTTPException, status
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.subagents import USAGE_GAPPED
from api.v1.subagents import router as subagents_router
from infrastructure.db.models import Tenant
from infrastructure.db.models.agent_catalog import AgentCatalog
from platform_layer.identity.auth import get_current_tenant
from platform_layer.middleware.tenant_context import get_db_session_with_tenant
from tests.conftest import seed_tenant

pytestmark = pytest.mark.asyncio


async def _seed_agent(
    db: AsyncSession,
    *,
    tenant: Tenant,
    key: str,
    name: str = "Agent",
    model: str | None = None,
    allowed_modes: list[str] | None = None,
    status_: str = "live",
    system_prompt: str = "You are an agent.",
    meta_data: dict[str, Any] | None = None,
) -> AgentCatalog:
    agent = AgentCatalog(
        tenant_id=tenant.id,
        key=key,
        name=name,
        model=model,
        allowed_modes=allowed_modes if allowed_modes is not None else ["handoff"],
        status=status_,
        system_prompt=system_prompt,
    )
    if meta_data is not None:
        agent.meta_data = meta_data
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return agent


def _build_app(
    *,
    db_session: AsyncSession,
    tenant_id: UUID | None,
) -> FastAPI:
    app = FastAPI()
    app.include_router(subagents_router, prefix="/api/v1")

    async def _override_tenant() -> UUID:
        if tenant_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
        return tenant_id

    async def _override_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_current_tenant] = _override_tenant
    app.dependency_overrides[get_db_session_with_tenant] = _override_db
    return app


async def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _by_key(body: dict, key: str) -> dict | None:
    for item in body["items"]:
        if item["key"] == key:
            return item
    return None


# ---------------------------------------------------------------------------
# Happy path — registry shape mapping
# ---------------------------------------------------------------------------


async def test_subagents_returns_catalog_rows(db_session: AsyncSession) -> None:
    """Seeded agent_catalog rows map to the registry shape."""
    tenant = await seed_tenant(db_session, code="SA_HAPPY")
    await _seed_agent(
        db_session,
        tenant=tenant,
        key="researcher",
        name="Researcher",
        model="gpt-4o",
        allowed_modes=["handoff", "as_tool"],
        status_="live",
        system_prompt="Research things.",
    )
    await _seed_agent(
        db_session,
        tenant=tenant,
        key="reviewer",
        name="Reviewer",
        allowed_modes=["handoff"],
        status_="staging",
    )

    app = _build_app(db_session=db_session, tenant_id=tenant.id)
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/subagents")
    assert resp.status_code == 200
    body = resp.json()

    assert {i["key"] for i in body["items"]} == {"researcher", "reviewer"}

    researcher = _by_key(body, "researcher")
    assert researcher is not None
    assert researcher["name"] == "Researcher"
    assert researcher["model"] == "gpt-4o"
    assert researcher["allowed_modes"] == ["handoff", "as_tool"]
    assert researcher["status"] == "live"
    assert researcher["system_prompt"] == "Research things."

    reviewer = _by_key(body, "reviewer")
    assert reviewer is not None
    assert reviewer["model"] is None  # nullable model → None
    assert reviewer["status"] == "staging"


async def test_subagents_gapped_usage_metrics(db_session: AsyncSession) -> None:
    """gapped reports the 5 usage metrics that have no runtime source."""
    tenant = await seed_tenant(db_session, code="SA_GAP")
    app = _build_app(db_session=db_session, tenant_id=tenant.id)
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/subagents")
    assert resp.status_code == 200
    body = resp.json()
    assert body["gapped"] == USAGE_GAPPED
    assert body["gapped"] == [
        "calls_24h",
        "p95_latency",
        "success_rate",
        "avg_tokens",
        "top_orchestrator",
    ]


# ---------------------------------------------------------------------------
# meta_data → budget / tools mapping
# ---------------------------------------------------------------------------


async def test_subagents_budget_tools_from_meta_data(db_session: AsyncSession) -> None:
    """budget/tools parse from meta_data when present."""
    tenant = await seed_tenant(db_session, code="SA_META")
    await _seed_agent(
        db_session,
        tenant=tenant,
        key="planner",
        meta_data={"budget": {"max_tokens": 10000}, "tools": ["log.tail"]},
    )
    app = _build_app(db_session=db_session, tenant_id=tenant.id)
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/subagents")
    assert resp.status_code == 200
    item = _by_key(resp.json(), "planner")
    assert item is not None
    assert item["budget"] == {"max_tokens": 10000}
    assert item["budget"]["max_tokens"] == 10000
    assert item["tools"] == ["log.tail"]


async def test_subagents_empty_meta_data_safe_defaults(db_session: AsyncSession) -> None:
    """Empty meta_data → budget None + tools []."""
    tenant = await seed_tenant(db_session, code="SA_EMPTY_META")
    await _seed_agent(db_session, tenant=tenant, key="bare", meta_data={})
    app = _build_app(db_session=db_session, tenant_id=tenant.id)
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/subagents")
    assert resp.status_code == 200
    item = _by_key(resp.json(), "bare")
    assert item is not None
    assert item["budget"] is None
    assert item["tools"] == []


# ---------------------------------------------------------------------------
# Cross-tenant isolation (multi-tenant-data.md 鐵律)
# ---------------------------------------------------------------------------


async def test_subagents_cross_tenant_isolation(db_session: AsyncSession) -> None:
    """Tenant A's registry EXCLUDES tenant B's agent_catalog rows."""
    tenant_a = await seed_tenant(db_session, code="SA_ISO_A")
    tenant_b = await seed_tenant(db_session, code="SA_ISO_B")
    await _seed_agent(db_session, tenant=tenant_a, key="a_only")
    await _seed_agent(db_session, tenant=tenant_b, key="b_only_1")
    await _seed_agent(db_session, tenant=tenant_b, key="b_only_2")

    app_a = _build_app(db_session=db_session, tenant_id=tenant_a.id)
    async with await _client(app_a) as ac:
        resp = await ac.get("/api/v1/subagents")
    assert resp.status_code == 200
    keys = {i["key"] for i in resp.json()["items"]}
    assert keys == {"a_only"}
    assert "b_only_1" not in keys
    assert "b_only_2" not in keys


async def test_subagents_empty_tenant(db_session: AsyncSession) -> None:
    """A tenant with no catalog rows → empty items + gapped still reported."""
    tenant = await seed_tenant(db_session, code="SA_NONE")
    app = _build_app(db_session=db_session, tenant_id=tenant.id)
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/subagents")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["gapped"] == USAGE_GAPPED


# ---------------------------------------------------------------------------
# Deps — unauthenticated
# ---------------------------------------------------------------------------


async def test_subagents_unauthenticated_401(db_session: AsyncSession) -> None:
    """No tenant context (get_current_tenant raises) → 401."""
    app = _build_app(db_session=db_session, tenant_id=None)
    async with await _client(app) as ac:
        resp = await ac.get("/api/v1/subagents")
    assert resp.status_code == 401
