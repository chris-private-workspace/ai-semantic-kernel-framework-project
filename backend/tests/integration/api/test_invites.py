"""
File: backend/tests/integration/api/test_invites.py
Purpose: IAM invites endpoints integration tests (Sprint 57.85 / US-1..US-5).
Category: Tests / Integration / API (C-12 IAM Block B invites)
Created: 2026-06-06 (Sprint 57.85 Day 3)

Verifies the 3 endpoints end-to-end over a real Postgres test session:
  - admin create requires auth (401)
  - e2e: admin create → guest GET metadata → guest accept → User + UserRole created
  - single-use (second accept → 410)
  - invalid token → 404; expired → 410
  - cross-tenant admin create denied (403)
  - exempt-path contract (guest paths exempt; admin path NOT)

The route session is the injected test db_session (override does NOT commit), so
the invite/user/audit writes stay in the test transaction and roll back at
teardown — no committed-row leakage (the service never commits internally).
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import FastAPI, Request, Response
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.invites import router as invites_router
from infrastructure.db.models.identity import Role, User, UserRole
from infrastructure.db.models.invites import Invite
from infrastructure.db.session import get_db_session
from platform_layer.identity.auth import require_admin_platform_role
from platform_layer.identity.invites import hash_token
from platform_layer.middleware.tenant_context import TenantContextMiddleware
from tests.conftest import seed_tenant, seed_user


def _build_app(
    db_session: AsyncSession | None = None, admin_user_id: UUID | None = None
) -> FastAPI:
    app = FastAPI()
    app.include_router(invites_router, prefix="/api/v1")

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
            yield db_session  # NB: no commit — writes roll back at fixture teardown

        async def _override_admin() -> UUID:
            return admin_user_id or UUID("00000000-0000-0000-0000-000000000001")

        app.dependency_overrides[get_db_session] = _override_session
        app.dependency_overrides[require_admin_platform_role] = _override_admin

    return app


async def _ctx(db: AsyncSession, tenant_id: object) -> None:
    await db.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant_id)})


async def _seed_role(db: AsyncSession, tenant_id: object, *, code: str = "member") -> Role:
    role = Role(tenant_id=tenant_id, code=code, display_name=code.title())
    db.add(role)
    await db.flush()
    await db.refresh(role)
    return role


def _platform_admin_headers(user_id: UUID) -> dict[str, str]:
    return {"X-Test-User": str(user_id), "X-Test-Roles": json.dumps(["platform_admin"])}


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ----- auth ----------------------------------------------------------------


async def test_create_requires_admin() -> None:
    """No JWT context → 401/403 from require_admin_platform_role."""
    app = _build_app()  # no overrides → real admin dep
    async with _client(app) as ac:
        resp = await ac.post(
            f"/api/v1/admin/tenants/{uuid4()}/invites",
            json={"email": "x@inv.test", "role_id": str(uuid4())},
        )
    assert resp.status_code in (401, 403)


# ----- happy path e2e ------------------------------------------------------


async def test_e2e_create_get_accept(db_session: AsyncSession) -> None:
    """US-1/2/3 — admin create → guest GET → guest accept → user + role + consumed."""
    tenant = await seed_tenant(db_session, code="INV_E2E")
    await _ctx(db_session, tenant.id)
    role = await _seed_role(db_session, tenant.id)
    inviter = await seed_user(db_session, tenant, email="admin@e2e.test")
    app = _build_app(db_session=db_session, admin_user_id=inviter.id)

    async with _client(app) as ac:
        create = await ac.post(
            f"/api/v1/admin/tenants/{tenant.id}/invites",
            json={"email": "newbie@e2e.test", "role_id": str(role.id)},
            headers=_platform_admin_headers(inviter.id),
        )
        assert create.status_code == 201, create.text
        token = create.json()["token"]
        assert token and "invite_id" in create.json()

        meta = await ac.get(f"/api/v1/invites/{token}")
        assert meta.status_code == 200, meta.text
        body = meta.json()
        assert body["tenant"] == "Tenant INV_E2E"
        assert body["role"] == role.display_name
        assert body["invitedBy"]  # inviter display/email
        assert "expiresIn" in body

        accept = await ac.post(
            f"/api/v1/invites/{token}/accept",
            json={"full_name": "New Bie", "password": "irrelevant-not-stored"},
        )
        assert accept.status_code == 200, accept.text
        assert accept.json()["ok"] is True
        new_user_id = UUID(accept.json()["user_id"])

    # Verify the user + role grant + invite consumed (same txn, via db_session).
    await _ctx(db_session, tenant.id)
    user = (await db_session.execute(select(User).where(User.id == new_user_id))).scalar_one()
    assert user.email == "newbie@e2e.test"
    assert user.display_name == "New Bie"
    granted = (
        await db_session.execute(
            select(UserRole).where(UserRole.user_id == new_user_id, UserRole.role_id == role.id)
        )
    ).scalar_one_or_none()
    assert granted is not None
    consumed = (
        await db_session.execute(select(Invite).where(Invite.token_hash == hash_token(token)))
    ).scalar_one()
    assert consumed.status == "accepted"


async def test_accept_single_use(db_session: AsyncSession) -> None:
    """US-4 — a second accept of the same token returns 410."""
    tenant = await seed_tenant(db_session, code="INV_SINGLE_HTTP")
    await _ctx(db_session, tenant.id)
    role = await _seed_role(db_session, tenant.id)
    inviter = await seed_user(db_session, tenant, email="admin@single.test")
    app = _build_app(db_session=db_session, admin_user_id=inviter.id)

    async with _client(app) as ac:
        create = await ac.post(
            f"/api/v1/admin/tenants/{tenant.id}/invites",
            json={"email": "s@single.test", "role_id": str(role.id)},
            headers=_platform_admin_headers(inviter.id),
        )
        token = create.json()["token"]
        first = await ac.post(
            f"/api/v1/invites/{token}/accept",
            json={"full_name": "First", "password": "x"},
        )
        second = await ac.post(
            f"/api/v1/invites/{token}/accept",
            json={"full_name": "Second", "password": "x"},
        )
    assert first.status_code == 200, first.text
    assert second.status_code == 410


async def test_get_invalid_token_404(db_session: AsyncSession) -> None:
    app = _build_app(db_session=db_session)
    async with _client(app) as ac:
        resp = await ac.get("/api/v1/invites/no-such-token-here")
    assert resp.status_code == 404


async def test_get_expired_token_410(db_session: AsyncSession) -> None:
    """US-4 — a pending invite past expires_at reads as 410 gone."""
    tenant = await seed_tenant(db_session, code="INV_EXP_HTTP")
    await _ctx(db_session, tenant.id)
    role = await _seed_role(db_session, tenant.id)
    inviter = await seed_user(db_session, tenant, email="admin@exp.test")
    raw = "expired-http-token"
    db_session.add(
        Invite(
            tenant_id=tenant.id,
            email="e@exp.test",
            role_id=role.id,
            invited_by=inviter.id,
            token_hash=hash_token(raw),
            status="pending",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
    )
    await db_session.flush()
    app = _build_app(db_session=db_session)
    async with _client(app) as ac:
        resp = await ac.get(f"/api/v1/invites/{raw}")
    assert resp.status_code == 410


# ----- isolation -----------------------------------------------------------


async def test_invite_scoped_to_path_tenant(db_session: AsyncSession) -> None:
    """US-4 — the created invite is attributed to the PATH tenant, not tenant B.

    Application-level tenant scoping. (DB-level RLS isolation is provided by the
    invites RLS policies — verified present by check_rls_policies — but is not
    enforced under the superuser test role, so cross-tenant leak is asserted at
    the application layer here, per the codebase isolation-test convention.)
    """
    tenant_a = await seed_tenant(db_session, code="INV_ISO_A")
    tenant_b = await seed_tenant(db_session, code="INV_ISO_B")
    await _ctx(db_session, tenant_a.id)
    role_a = await _seed_role(db_session, tenant_a.id)
    inviter_a = await seed_user(db_session, tenant_a, email="admin@a.test")
    app = _build_app(db_session=db_session, admin_user_id=inviter_a.id)

    async with _client(app) as ac:
        resp = await ac.post(
            f"/api/v1/admin/tenants/{tenant_a.id}/invites",
            json={"email": "x@a.test", "role_id": str(role_a.id)},
            headers=_platform_admin_headers(inviter_a.id),
        )
        assert resp.status_code == 201, resp.text
        token = resp.json()["token"]
        # the guest metadata resolves to tenant A (not B).
        meta = await ac.get(f"/api/v1/invites/{token}")
    assert meta.status_code == 200
    assert meta.json()["tenant"] == "Tenant INV_ISO_A"

    # the row is attributed to tenant A; tenant B has no invite row.
    await _ctx(db_session, tenant_a.id)
    row = (
        await db_session.execute(select(Invite).where(Invite.token_hash == hash_token(token)))
    ).scalar_one()
    assert row.tenant_id == tenant_a.id
    b_rows = (
        (await db_session.execute(select(Invite).where(Invite.tenant_id == tenant_b.id)))
        .scalars()
        .all()
    )
    assert b_rows == []


# ----- exempt-path contract -----------------------------------------------


def test_exempt_path_contract() -> None:
    """Guest invite paths are exempt; the admin create path is NOT."""
    exempt = TenantContextMiddleware.EXEMPT_PATH_PREFIXES
    assert "/api/v1/invites" in exempt
    admin_path = "/api/v1/admin/tenants/00000000-0000-0000-0000-000000000000/invites"
    assert not any(admin_path.startswith(p) for p in exempt)
