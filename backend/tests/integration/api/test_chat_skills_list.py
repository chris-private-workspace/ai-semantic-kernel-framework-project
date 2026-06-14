"""
File: backend/tests/integration/api/test_chat_skills_list.py
Purpose: Integration tests — GET /api/v1/chat/skills (Sprint 57.115 slash-command picker list).
Category: Tests / Integration / API (Skills System slash-command)
Scope: Sprint 57.115 / US-2

The non-admin, tenant-scoped picker list: returns the tenant's effective skills
(bundled + the tenant_skills overlay) as name + description ONLY — the full
instructions body NEVER reaches this list endpoint (it loads on force-load /
read_skill). 401 without a tenant; isolated per tenant.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.chat.router import router as chat_router
from infrastructure.db.session import get_db_session
from platform_layer.identity import get_current_tenant
from platform_layer.skills import reset_skill_registry_cache
from platform_layer.skills.service import tenant_skill_service
from tests.conftest import seed_tenant

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def _reset_skill_cache() -> object:
    # Risk Class C: the resolver's TTL cache is a module singleton; clear it
    # around each test so a prior tenant's registry never bleeds across.
    reset_skill_registry_cache()
    yield
    reset_skill_registry_cache()


def _build_app(db_session: AsyncSession, *, tenant_id: UUID | None) -> FastAPI:
    app = FastAPI()
    # The chat router already carries an internal "/chat" prefix → mount at /api/v1
    # so the effective path is /api/v1/chat/skills (matches the real app mount).
    app.include_router(chat_router, prefix="/api/v1")

    async def _override_session() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db_session] = _override_session
    if tenant_id is not None:
        app.dependency_overrides[get_current_tenant] = lambda: tenant_id
    return app


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


async def test_list_skills_returns_bundled_for_plain_tenant(db_session: AsyncSession) -> None:
    tenant = await seed_tenant(db_session, code="SK_LIST_PLAIN")
    async with _client(_build_app(db_session, tenant_id=tenant.id)) as client:
        resp = await client.get("/api/v1/chat/skills")
    assert resp.status_code == 200
    names = {s["name"] for s in resp.json()["skills"]}
    assert "code-review" in names
    assert "summarize" in names


async def test_list_skills_includes_tenant_overlay(db_session: AsyncSession) -> None:
    tenant = await seed_tenant(db_session, code="SK_LIST_OVL")
    await tenant_skill_service.create(
        db_session,
        tenant_id=tenant.id,
        name="release-notes",
        description="Turn commits into a release note",
        instructions="Heading / Highlights",
    )
    async with _client(_build_app(db_session, tenant_id=tenant.id)) as client:
        resp = await client.get("/api/v1/chat/skills")
    names = {s["name"] for s in resp.json()["skills"]}
    assert "release-notes" in names  # the tenant overlay
    assert "code-review" in names  # bundled still present


async def test_list_skills_no_instructions_field(db_session: AsyncSession) -> None:
    tenant = await seed_tenant(db_session, code="SK_LIST_NOINSTR")
    await tenant_skill_service.create(
        db_session,
        tenant_id=tenant.id,
        name="release-notes",
        description="d",
        instructions="SECRET-INSTRUCTION-BODY",
    )
    async with _client(_build_app(db_session, tenant_id=tenant.id)) as client:
        resp = await client.get("/api/v1/chat/skills")
    items = resp.json()["skills"]
    assert all("instructions" not in item for item in items)
    # The body must never leak to a non-admin list endpoint.
    assert "SECRET-INSTRUCTION-BODY" not in resp.text


async def test_list_skills_tenant_scoped(db_session: AsyncSession) -> None:
    tenant_a = await seed_tenant(db_session, code="SK_LIST_A")
    tenant_b = await seed_tenant(db_session, code="SK_LIST_B")
    await tenant_skill_service.create(
        db_session,
        tenant_id=tenant_a.id,
        name="a-only-skill",
        description="d",
        instructions="b",
    )
    async with _client(_build_app(db_session, tenant_id=tenant_b.id)) as client:
        resp = await client.get("/api/v1/chat/skills")
    names = {s["name"] for s in resp.json()["skills"]}
    assert "a-only-skill" not in names  # B never sees A's overlay


async def test_list_skills_unauthed_401(db_session: AsyncSession) -> None:
    # No tenant override → the real get_current_tenant runs → no request.state →
    # 401 (the standard chat auth gate; the picker is non-admin but still authed).
    async with _client(_build_app(db_session, tenant_id=None)) as client:
        resp = await client.get("/api/v1/chat/skills")
    assert resp.status_code == 401
