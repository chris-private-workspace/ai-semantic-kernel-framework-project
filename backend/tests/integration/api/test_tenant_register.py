"""
File: backend/tests/integration/api/test_tenant_register.py
Purpose: Self-service tenant registration endpoint integration tests (Sprint 57.87).
Category: Tests / Integration / API (C-12 IAM Block B registration)
Created: 2026-06-06 (Sprint 57.87 Day 3)

Verifies POST /tenants/register end-to-end over a real Postgres test session:
  - 201 + response shape; tenant ACTIVE + admin role + user + userrole + audit row
  - duplicate slug → 409 (generic); invalid slug pattern → 422
  - the created tenant is resolvable by code (OIDC /auth/callback unblocked)
  - 2-tenant isolation (app-layer, per the superuser-test-role convention)
  - exempt-path contract (register exempt; admin tenant CRUD NOT)

The route session is the injected test db_session (override does NOT commit), so
the tenant/user/role/audit writes stay in the test transaction and roll back at
teardown (the service never commits internally).
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.tenants import router as tenants_router
from infrastructure.db.models.audit import AuditLog
from infrastructure.db.models.identity import Role, Tenant, TenantState, User, UserRole
from infrastructure.db.session import get_db_session
from platform_layer.middleware.tenant_context import TenantContextMiddleware


def _build_app(db_session: AsyncSession | None = None) -> FastAPI:
    app = FastAPI()
    app.include_router(tenants_router, prefix="/api/v1")
    if db_session is not None:

        async def _override_session() -> AsyncIterator[AsyncSession]:
            yield db_session  # NB: no commit — writes roll back at fixture teardown

        app.dependency_overrides[get_db_session] = _override_session
    return app


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def _body(slug: str, *, email: str = "founder@reg.test") -> dict[str, str]:
    return {
        "email": email,
        "full_name": "Founder One",
        "company_name": f"Company {slug}",
        "tenant_slug": slug,
        "region": "global",
        "plan": "pro",
        "size": "11-50",
    }


# ----- happy path e2e ------------------------------------------------------


async def test_register_creates_tenant_admin_and_audit(db_session: AsyncSession) -> None:
    """US-1/2/3 — 201 + tenant ACTIVE + admin role + user + userrole + audit."""
    app = _build_app(db_session=db_session)
    async with _client(app) as ac:
        resp = await ac.post("/api/v1/tenants/register", json=_body("reg-http-1"))
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["tenant"]["code"] == "reg-http-1"
    assert body["tenant"]["state"] == "active"
    assert body["user"]["email"] == "founder@reg.test"
    tenant_id = body["tenant"]["id"]
    user_id = body["user"]["id"]

    role = (
        await db_session.execute(
            select(Role).where(Role.tenant_id == tenant_id, Role.code == "admin")
        )
    ).scalar_one_or_none()
    assert role is not None
    granted = (
        await db_session.execute(
            select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role.id)
        )
    ).scalar_one_or_none()
    assert granted is not None
    audit = (
        (await db_session.execute(select(AuditLog).where(AuditLog.resource_id == tenant_id)))
        .scalars()
        .all()
    )
    assert any(a.operation == "tenant_registered" for a in audit)


async def test_register_tenant_is_active_in_db(db_session: AsyncSession) -> None:
    """US-1 — the persisted tenant is ACTIVE (resolvable by code → OIDC unblocked)."""
    app = _build_app(db_session=db_session)
    async with _client(app) as ac:
        resp = await ac.post("/api/v1/tenants/register", json=_body("reg-http-active"))
    assert resp.status_code == 201, resp.text
    tenant = (
        await db_session.execute(select(Tenant).where(Tenant.code == "reg-http-active"))
    ).scalar_one()
    assert tenant.state == TenantState.ACTIVE
    assert tenant.meta_data.get("requested_plan") == "pro"


# ----- guards --------------------------------------------------------------


async def test_register_duplicate_slug_409(db_session: AsyncSession) -> None:
    """US-3 — a second registration with the same slug → generic 409."""
    app = _build_app(db_session=db_session)
    async with _client(app) as ac:
        first = await ac.post("/api/v1/tenants/register", json=_body("reg-http-dup"))
        second = await ac.post(
            "/api/v1/tenants/register", json=_body("reg-http-dup", email="second@reg.test")
        )
    assert first.status_code == 201, first.text
    assert second.status_code == 409


async def test_register_invalid_slug_422(db_session: AsyncSession) -> None:
    """US-3 — an invalid slug pattern is rejected by request validation (422)."""
    app = _build_app(db_session=db_session)
    async with _client(app) as ac:
        resp = await ac.post("/api/v1/tenants/register", json=_body("Bad Slug!"))
    assert resp.status_code == 422


# ----- isolation -----------------------------------------------------------


async def test_register_two_tenants_isolated(db_session: AsyncSession) -> None:
    """US-3 — two registrations attribute users to their own tenant (app-layer).

    DB-level RLS isolation is provided by the users/roles policies (present per
    check_rls_policies) but not enforced under the superuser test role, so the
    cross-tenant non-leak is asserted at the application layer (WHERE tenant_id),
    per the codebase isolation-test convention (57.85).
    """
    app = _build_app(db_session=db_session)
    async with _client(app) as ac:
        a = await ac.post(
            "/api/v1/tenants/register", json=_body("reg-iso-http-a", email="a@r.test")
        )
        b = await ac.post(
            "/api/v1/tenants/register", json=_body("reg-iso-http-b", email="b@r.test")
        )
    assert a.status_code == 201 and b.status_code == 201
    a_tid = a.json()["tenant"]["id"]
    b_tid = b.json()["tenant"]["id"]
    assert a_tid != b_tid

    a_users = (
        (await db_session.execute(select(User.email).where(User.tenant_id == a_tid)))
        .scalars()
        .all()
    )
    assert a_users == ["a@r.test"]
    b_users = (
        (await db_session.execute(select(User.email).where(User.tenant_id == b_tid)))
        .scalars()
        .all()
    )
    assert b_users == ["b@r.test"]


# ----- exempt-path contract ------------------------------------------------


def test_exempt_path_contract() -> None:
    """The register path is exempt; admin tenant CRUD is NOT."""
    exempt = TenantContextMiddleware.EXEMPT_PATH_PREFIXES
    assert "/api/v1/tenants/register" in exempt
    admin_path = "/api/v1/admin/tenants/00000000-0000-0000-0000-000000000000"
    assert not any(admin_path.startswith(p) for p in exempt)
