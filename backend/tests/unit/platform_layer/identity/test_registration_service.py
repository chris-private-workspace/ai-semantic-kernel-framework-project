"""
File: backend/tests/unit/platform_layer/identity/test_registration_service.py
Purpose: RegistrationService unit tests (Sprint 57.87 / US-1..US-3 + US-5).
Category: Tests / Unit (platform_layer.identity — C-12 IAM Block B registration)
Created: 2026-06-06 (Sprint 57.87 Day 2)

Covers the service against the real docker-compose Postgres (db_session, rolled
back at teardown): register creates the tenant (ACTIVE / plan ENTERPRISE /
requested_plan+company_size in meta_data) + seeds the "admin" Role + the founding
User + the admin UserRole + a tenant_registered audit row; duplicate-slug guard;
the OIDC-first user has no password; and 2-tenant RLS isolation.

The HTTP layer (public exempt POST /tenants/register + 409/422) is covered in
tests/integration/api/test_tenant_register.py.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models.audit import AuditLog
from infrastructure.db.models.identity import (
    Role,
    TenantPlan,
    TenantState,
    User,
    UserRole,
)
from platform_layer.identity.registration import (
    FOUNDING_ADMIN_ROLE_CODE,
    RegistrationService,
    TenantSlugTakenError,
)

# asyncio_mode=auto (pyproject) auto-detects async tests.


async def _register(db: AsyncSession, *, slug: str, email: str = "founder@reg.test"):
    return await RegistrationService().register(
        db,
        email=email,
        full_name="Founder One",
        company_name=f"Company {slug}",
        tenant_slug=slug,
        region="global",
        requested_plan="pro",
        company_size="11-50",
    )


# ----- happy path ---------------------------------------------------------


async def test_register_creates_tenant_admin_role_user_and_audit(db_session: AsyncSession) -> None:
    """US-1/US-2/US-3 — register creates tenant + admin role + user + userrole + audit."""
    result = await _register(db_session, slug="reg-acme-1")
    tenant, user = result.tenant, result.user

    # tenant created
    assert tenant.code == "reg-acme-1"
    assert tenant.display_name == "Company reg-acme-1"

    # admin role seeded in the new tenant (queryable under its RLS context)
    role = (
        await db_session.execute(
            select(Role).where(Role.tenant_id == tenant.id, Role.code == FOUNDING_ADMIN_ROLE_CODE)
        )
    ).scalar_one_or_none()
    assert role is not None
    assert role.display_name == "Admin"

    # founding user
    assert user.email == "founder@reg.test"
    assert user.display_name == "Founder One"
    assert user.status == "active"
    assert user.tenant_id == tenant.id

    # admin role granted to the founding user
    granted = (
        await db_session.execute(
            select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id)
        )
    ).scalar_one_or_none()
    assert granted is not None

    # tenant_registered audit row
    audit = (
        (await db_session.execute(select(AuditLog).where(AuditLog.resource_id == str(tenant.id))))
        .scalars()
        .all()
    )
    assert any(a.operation == "tenant_registered" for a in audit)


async def test_register_tenant_is_active_plan_enterprise_meta(db_session: AsyncSession) -> None:
    """US-1/D2 — tenant is ACTIVE immediately; plan ENTERPRISE; requested_plan+size in meta_data."""
    result = await _register(db_session, slug="reg-active-1")
    tenant = result.tenant
    assert tenant.state == TenantState.ACTIVE
    assert tenant.plan == TenantPlan.ENTERPRISE
    assert tenant.meta_data.get("requested_plan") == "pro"
    assert tenant.meta_data.get("company_size") == "11-50"


# ----- guards -------------------------------------------------------------


async def test_register_duplicate_slug_raises(db_session: AsyncSession) -> None:
    """US-3 — a second registration with the same slug → TenantSlugTakenError (409)."""
    await _register(db_session, slug="reg-dup-1", email="first@reg.test")
    with pytest.raises(TenantSlugTakenError):
        await _register(db_session, slug="reg-dup-1", email="second@reg.test")


async def test_register_concurrent_slug_race_maps_integrityerror_to_409() -> None:
    """FIX-030 — the concurrent same-slug race surfaces as a clean 409, not a 500.

    Two racing signups can both pass the step-1 pre-check (neither sees the other's
    uncommitted row) and then collide on the unique `tenants.code` constraint at the
    INSERT. The DB prevents the duplicate; the service must map that IntegrityError
    to TenantSlugTakenError (409) rather than letting it bubble as a raw 500. Driven
    with a mock session (the pre-check returns None → race window; the tenant flush
    raises IntegrityError) so the mapping is covered deterministically without real
    concurrency.
    """
    db = MagicMock(spec=AsyncSession)
    precheck = MagicMock()
    precheck.scalar_one_or_none.return_value = None  # step-1 sees no existing slug
    db.execute = AsyncMock(return_value=precheck)
    db.add = MagicMock()
    db.flush = AsyncMock(side_effect=IntegrityError("INSERT tenants", {}, Exception("dup code")))

    with pytest.raises(TenantSlugTakenError):
        await RegistrationService().register(
            db,
            email="race@reg.test",
            full_name="Race Founder",
            company_name="Race Co",
            tenant_slug="race-slug",
            region="global",
            requested_plan="pro",
        )


async def test_register_user_has_no_password(db_session: AsyncSession) -> None:
    """OIDC-first — the founding user gets no local password at registration."""
    result = await _register(db_session, slug="reg-nopw-1")
    assert result.user.password_hash is None


# ----- isolation ----------------------------------------------------------


async def test_register_two_tenants_isolated(db_session: AsyncSession) -> None:
    """US-3 — two registrations are scoped to their own tenant (no cross-leak).

    Isolation is asserted at the application layer (WHERE tenant_id == …). The
    test DB role is a superuser that bypasses RLS FORCE (57.85 D5 lesson), so a
    raw SELECT can't prove the policy here; the production non-superuser role
    enforces it. The invariant under test: register scopes each user/role to its
    own tenant_id.
    """
    a = await _register(db_session, slug="reg-iso-a", email="a@reg.test")
    b = await _register(db_session, slug="reg-iso-b", email="b@reg.test")
    assert a.tenant.id != b.tenant.id

    a_users = (
        (await db_session.execute(select(User.email).where(User.tenant_id == a.tenant.id)))
        .scalars()
        .all()
    )
    assert a_users == ["a@reg.test"]
    b_users = (
        (await db_session.execute(select(User.email).where(User.tenant_id == b.tenant.id)))
        .scalars()
        .all()
    )
    assert b_users == ["b@reg.test"]
    # the seeded admin role is likewise scoped to its own tenant
    a_roles = (
        (await db_session.execute(select(Role.id).where(Role.tenant_id == a.tenant.id)))
        .scalars()
        .all()
    )
    assert len(a_roles) == 1


async def test_register_seeds_exactly_one_admin_role(db_session: AsyncSession) -> None:
    """US-2 — exactly one 'admin' role is seeded in the new tenant."""
    result = await _register(db_session, slug="reg-role-1")
    roles = (
        (await db_session.execute(select(Role).where(Role.tenant_id == result.tenant.id)))
        .scalars()
        .all()
    )
    assert len(roles) == 1
    assert roles[0].code == FOUNDING_ADMIN_ROLE_CODE
