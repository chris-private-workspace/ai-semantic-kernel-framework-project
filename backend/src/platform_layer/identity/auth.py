"""
File: backend/src/platform_layer/identity/auth.py
Purpose: FastAPI dependencies — get_current_tenant + get_current_user_id from
JWT-decoded request.state populated by TenantContextMiddleware.
Category: Platform layer / Identity (cross-cutting; multi-tenant 鐵律 3 dep)
Scope: Sprint 52.5 Day 1.2 (P0 #14 — replaces middleware/{tenant,auth}.py V1 stubs)
Owner: platform_layer/identity owner

Description:
    These deps are the *single canonical source* for tenant/user identity
    in V2. Every business endpoint MUST use them (or downstream wrappers
    like `get_db_session_with_tenant`) to ensure tenant_id is taken from
    the verified JWT, never from request bodies / query params / headers.

    `request.state.tenant_id` and `request.state.user_id` are populated
    by `TenantContextMiddleware` (Day 6.1 will rewrite that middleware
    to JWT-decode; Day 1.2 ships the deps + JWTManager so endpoints can
    declare `Depends(get_current_tenant)` immediately).

    Until Day 6.1 lands, callers will receive 401 because middleware
    still reads X-Tenant-Id (no user_id set). This is acceptable: the
    failing-fast behaviour is preferable to silent fallback to header
    spoofing — i.e. no production endpoint shall be wired up until the
    middleware change is in.

Key Components:
    - get_current_tenant(request) -> UUID
    - get_current_user_id(request) -> UUID

Created: 2026-05-01 (Sprint 52.5 Day 1.2)
Last Modified: 2026-05-01

Modification History:
    - 2026-05-10: Sprint 57.13 US-A3 — add require_tenant_match_or_platform_admin dep
    - 2026-05-09: Sprint 57.7 US-A3 — DB-backed RBAC hybrid path (closes Tier 0 #5)
    - 2026-05-04: Add require_approver_role RBAC dep + extract _require_role helper
        (Sprint 53.5 US-1 — approver / admin / manager)
    - 2026-05-04: Add require_audit_role RBAC dep (Sprint 53.5 US-5 — auditor / admin / compliance)
    - 2026-05-01: Initial creation (Sprint 52.5 Day 1.2) — replaces V1 stubs

Related:
    - platform_layer/identity/jwt.py — JWT decode (authoritative source)
    - platform_layer/middleware/tenant_context.py — populates request.state
    - .claude/rules/multi-tenant-data.md 鐵律 3 (every business endpoint)
    - claudedocs/5-status/V2-AUDIT-OPEN-ISSUES-20260501.md — issue #14
    - V1 stubs (to be removed Day 6): backend/src/middleware/{tenant,auth}.py
"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, Request, status

_AUTH_REQUIRED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Authentication required",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_tenant(request: Request) -> UUID:
    """Return UUID of the authenticated tenant.

    Reads `request.state.tenant_id` populated by TenantContextMiddleware
    after successful JWT decode. Raises 401 if absent — this should be
    impossible if middleware is installed before the routes; the explicit
    raise (rather than silent default) prevents endpoints from running
    against a missing tenant_id (which would mean RLS sees nothing AND
    rows could be inserted without tenant scope).
    """
    tenant_id = getattr(request.state, "tenant_id", None)
    if tenant_id is None:
        raise _AUTH_REQUIRED
    if not isinstance(tenant_id, UUID):
        # Defensive: middleware contract is to set a UUID. If it isn't,
        # something upstream is wrong; fail fast rather than coerce.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="tenant_id middleware contract violated",
        )
    return tenant_id


async def get_current_user_id(request: Request) -> UUID:
    """Return UUID of the authenticated user.

    Same shape as `get_current_tenant`, populated from JWT `sub` claim.
    """
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        raise _AUTH_REQUIRED
    if not isinstance(user_id, UUID):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="user_id middleware contract violated",
        )
    return user_id


# RBAC roles permitted to read audit_log (Sprint 53.5 US-5).
# Single-source: JWT 'roles' claim list[str].
_AUDIT_ROLES: frozenset[str] = frozenset({"auditor", "admin", "compliance"})

# RBAC roles permitted to view + decide on HITL approvals (Sprint 53.5 US-1).
# Auditors are intentionally NOT included — auditors review the chain after
# the fact; approval decisions belong to operators with authority over the
# tool action being requested.
_APPROVER_ROLES: frozenset[str] = frozenset({"approver", "admin", "manager"})

# RBAC roles permitted to invoke platform-admin endpoints (Sprint 56.2 US-4).
# Used by api/v1/admin/tenants.py for tenant lifecycle + onboarding endpoints.
# - "admin" = generic platform admin (existing convention from _AUDIT_ROLES /
#   _APPROVER_ROLES + tenant_health_check.py:196 ["admin", "tenant_admin"]).
# - "platform_admin" = explicit role code for SaaS-Stage-1 platform operators.
# Tenant-scoped admins (role "tenant_admin") are intentionally excluded —
# they cannot create / suspend / archive other tenants.
_ADMIN_PLATFORM_ROLES: frozenset[str] = frozenset({"admin", "platform_admin"})


async def require_audit_role(request: Request) -> UUID:
    """Authorize the caller for audit endpoints.

    Returns the authenticated user_id once role membership is verified.
    Raises 401 if no JWT context (middleware must run first); 403 if the
    JWT's roles claim does not intersect _AUDIT_ROLES.

    Used by GET /api/v1/audit/log and /api/v1/audit/verify-chain.
    """
    return await _require_role(request, _AUDIT_ROLES, role_label="Audit")


async def require_approver_role(request: Request) -> UUID:
    """Authorize the caller for HITL approval decision endpoints.

    Returns the authenticated user_id once role membership is verified.
    Used by GET /api/v1/governance/approvals and POST /api/v1/governance/approvals/{id}/decide.
    """
    return await _require_role(request, _APPROVER_ROLES, role_label="Approver")


async def require_admin_platform_role(request: Request) -> UUID:
    """Authorize the caller for SaaS platform-admin endpoints.

    Returns the authenticated user_id once role membership is verified.
    Used by api/v1/admin/tenants.py — POST /admin/tenants (create) /
    GET /admin/tenants/{id}/onboarding-status / POST /admin/tenants/{id}/onboarding/{step}.

    Sprint 56.2 US-4 — closes AD-AdminAuth-1: replaces 56.1 stub
    `require_admin_token` (X-Admin-Token header against env var) with real
    JWT-claim-based RBAC role check, mirroring `require_audit_role` /
    `require_approver_role` pattern (53.5).
    """
    return await _require_role(request, _ADMIN_PLATFORM_ROLES, role_label="Platform admin")


async def require_tenant_match_or_platform_admin(tenant_id: UUID, request: Request) -> UUID:
    """Authorize a `/{tenant_id}/...` endpoint: caller is a platform admin OR
    the path `tenant_id` equals the caller's own JWT tenant_id.

    Returns the authenticated user_id. Raises 401 (no JWT context) / 403
    (a non-platform-admin reaching for another tenant via the URL).

    Sprint 57.13 US-A3: closes the "any admin can change the URL to read
    another tenant's data" hole on `/api/v1/admin/tenants/{tenant_id}/...`
    read endpoints (GET tenant / cost-summary / sla-report). It also lets a
    regular user read their own tenant's data — those pages (cost-dashboard /
    sla-dashboard / tenant-settings) now derive tenant_id from the session
    (authStore.tenant.id), not a hand-typed URL param.
    """
    user_id = await get_current_user_id(request)
    roles = getattr(request.state, "roles", None)
    if not isinstance(roles, list):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="roles middleware contract violated",
        )
    if any(r in _ADMIN_PLATFORM_ROLES for r in roles):
        return user_id  # platform admin — any tenant
    caller_tenant = await get_current_tenant(request)
    if tenant_id != caller_tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="cross-tenant access denied (not a platform admin)",
        )
    return user_id


async def _require_role(request: Request, allowed: frozenset[str], *, role_label: str) -> UUID:
    """Shared role-check helper used by require_audit_role + require_approver_role.

    Sprint 57.7 US-A3 hybrid path:
    - Path 1 (legacy JWT-claim): fast, in-process — preserves existing
      53.5+ behavior + 100+ tests that mock request.state.roles
    - Path 2 (NEW DB-backed fallback): RBACManager queries roles + user_roles
      with per-tenant filter — closes Tier 0 #5 (per-tenant custom roles)

    Path 1 is checked first;Path 2 only fires if Path 1 doesn't grant.
    Full DB-only enforcement (drop Path 1) deferred to Phase 58+ per
    `20-iam-deep-dive.md` §4 Open Invariants.
    """
    user_id = await get_current_user_id(request)
    roles = getattr(request.state, "roles", None)
    if not isinstance(roles, list):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="roles middleware contract violated",
        )

    # Path 1: legacy JWT-claim check (preserves existing behavior + tests)
    if any(r in allowed for r in roles):
        return user_id

    # Path 2: NEW DB-backed fallback (Sprint 57.7 US-A3 — opt-in via Settings)
    # Default OFF — preserves 100+ existing tests that mock request.state.roles
    # via SimpleNamespace stubs (no tenant_id available;Path 2 would 401).
    # Production rollout flips Settings.rbac_db_backed_fallback=True after
    # user_roles table populated via migration script.
    from core.config import get_settings

    if get_settings().rbac_db_backed_fallback:
        from platform_layer.identity.rbac import RBACManager

        tenant_id = await get_current_tenant(request)
        if await RBACManager.has_role_code(
            user_id=user_id,
            tenant_id=tenant_id,
            allowed_codes=allowed,
        ):
            return user_id

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"{role_label} role required",
    )


__all__ = [
    "get_current_tenant",
    "get_current_user_id",
    "require_admin_platform_role",
    "require_audit_role",
    "require_approver_role",
    "require_tenant_match_or_platform_admin",
]
