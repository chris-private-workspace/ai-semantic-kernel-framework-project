"""
File: backend/src/platform_layer/identity/rbac.py
Purpose: DB-backed RBAC manager — replaces auth.py 3 hardcoded frozenset role checks.
Category: Platform layer / Identity (Sprint 57.7 US-A3)
Scope: Phase 57 / Sprint 57.7 (IAM Foundation Tier 0 spike)

Description:
    Per-tenant role lookup via SQL JOIN on roles + user_roles tables. Closes
    gap-analysis §1.2 Tier 0 #5 RED finding (auth.py L101/107/116 hardcoded
    frozenset RBAC). After this sprint, tenants CAN define custom role codes
    (e.g. "data_steward", "tenant_a_reviewer") and have them participate in
    permission checks per-tenant — no more global hardcoded role list.

    Sprint 57.7 spike scope: Day 2 ships RBACManager + auth.py hybrid path
    (legacy JWT-claim path preserved for backwards compat;DB-backed fallback
    added for per-tenant custom roles). Full DB-only enforcement migration
    deferred to Phase 58+ follow-up sprint per `20-iam-deep-dive.md` §4
    Open Invariants.

    Pure DB-backed approach considered + rejected for Sprint 57.7 due to
    risk of breaking 100+ existing tests that mock `request.state.roles`
    (frozenset path). Hybrid path lets spike ship without test churn while
    proving architecture works.

Key Components:
    - RBACManager: stateless class with 3 async static methods
        - has_role_code() — checks user has any role with code in allowed_codes
        - get_user_role_codes() — all role codes for a user in a tenant (JWT issue-time source)
        - has_permission() — Day 2 stub for future role_permissions wire (Phase 58+)

Created: 2026-05-09 (Sprint 57.7 Day 2 PM)
Last Modified: 2026-06-12

Modification History (newest-first):
    - 2026-06-12: Sprint 57.105 — add get_user_role_codes (issue-time JWT roles source)
    - 2026-05-09: Initial creation (Sprint 57.7 US-A3 Day 2 PM) — DB-backed RBAC

Related:
    - platform_layer/identity/auth.py (consumer — _require_role hybrid path)
    - infrastructure/db/models/identity.py (Role + UserRole + RolePermission)
    - infrastructure/db/session.py (get_db_session FastAPI dep)
    - 09-db-schema-design.md §RBAC tables (L150-189)
    - .claude/rules/multi-tenant-data.md 鐵律 #2 (per-tenant filter)
    - claudedocs/1-planning/enterprise-saas-gap-analysis-20260508.md §1.2 Tier 0 #5
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select

from infrastructure.db.engine import get_session_factory
from infrastructure.db.models.identity import Role, UserRole

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class RBACManager:
    """Stateless DB-backed RBAC checker. Per `20-iam-deep-dive.md` §2.4."""

    @staticmethod
    async def has_role_code(
        *,
        user_id: UUID,
        tenant_id: UUID,
        allowed_codes: frozenset[str],
        session: AsyncSession | None = None,
    ) -> bool:
        """Return True if user has any role whose code is in allowed_codes
        within the given tenant.

        Per `multi-tenant-data.md` 鐵律 #2: query MUST filter by tenant_id
        even though RLS policy provides defense in depth.

        Args:
            user_id: User to check.
            tenant_id: Tenant scope (per-tenant role isolation).
            allowed_codes: Set of role codes to match (e.g. {"admin", "auditor"}).
            session: Optional AsyncSession;if None, opens new session via
                get_session_factory (so callers in dependency chains that
                don't have a session don't need to plumb one).

        Returns:
            True if user has any role with code in allowed_codes for this
            tenant, False otherwise.

        Performance note (Phase 58+ optimization candidate):
            Each call opens a new session + executes 1 query. For high-RPS
            endpoints consider caching role membership in Redis with TTL,
            invalidate on user_roles INSERT/DELETE.
        """
        if session is not None:
            return await RBACManager._has_role_code_with_session(
                session=session,
                user_id=user_id,
                tenant_id=tenant_id,
                allowed_codes=allowed_codes,
            )

        # Open own session — for callers in FastAPI dep chain w/o passed session
        factory = get_session_factory()
        async with factory() as own_session:
            return await RBACManager._has_role_code_with_session(
                session=own_session,
                user_id=user_id,
                tenant_id=tenant_id,
                allowed_codes=allowed_codes,
            )

    @staticmethod
    async def _has_role_code_with_session(
        *,
        session: AsyncSession,
        user_id: UUID,
        tenant_id: UUID,
        allowed_codes: frozenset[str],
    ) -> bool:
        """Inner SQL JOIN executor — per TS-3 in sprint-57-7-plan.md."""
        if not allowed_codes:
            # Defensive: empty allowed set means no role grants access
            return False
        stmt = (
            select(Role.id)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(
                (UserRole.user_id == user_id)
                & (Role.tenant_id == tenant_id)
                & (Role.code.in_(allowed_codes))
            )
            .limit(1)
        )
        result = await session.execute(stmt)
        return result.first() is not None

    @staticmethod
    async def get_user_role_codes(
        *,
        user_id: UUID,
        tenant_id: UUID,
        session: AsyncSession,
    ) -> list[str]:
        """Return ALL role codes granted to the user within the tenant (sorted, deduped).

        JWT issue-time source (Sprint 57.105): the login handlers (OIDC callback +
        password-login) call this once per login and bake the result into the JWT
        `roles` claim — making DB role grants (registration founding admin 57.87,
        invite-accept 57.85) authz-effective on real sessions.

        Per `multi-tenant-data.md` 鐵律 #2: filtered by tenant_id via Role
        (UserRole has no tenant column — the JOIN provides the scope).

        Args:
            user_id: User whose grants to read.
            tenant_id: Tenant scope (per-tenant role isolation).
            session: Caller's AsyncSession (REQUIRED — login handlers pass the
                request session; this path never opens its own).

        Returns:
            Sorted unique role codes; empty list when the user has no grants.
        """
        stmt = (
            select(Role.code)
            .join(UserRole, UserRole.role_id == Role.id)
            .where((UserRole.user_id == user_id) & (Role.tenant_id == tenant_id))
        )
        result = await session.execute(stmt)
        return sorted(set(result.scalars().all()))

    @staticmethod
    async def has_permission(
        *,
        user_id: UUID,
        tenant_id: UUID,
        action: str,
        resource_type: str,
    ) -> bool:
        """Permission check via role_permissions JOIN — Phase 58+ stub.

        Day 2 spike returns False (deny by default) — full implementation
        deferred to Phase 58+ when first endpoint requires fine-grained
        permission check (current spike uses role-code checks via
        has_role_code which is sufficient for SaaS B2B baseline).

        Args:
            user_id: User to check.
            tenant_id: Tenant scope.
            action: Action verb (e.g. "read", "write", "decide").
            resource_type: Resource type (e.g. "approval", "tenant").

        Returns:
            False (Day 2 stub). Phase 58+ wires real role_permissions JOIN
            per TS-3 in plan + adds caller endpoints.
        """
        logger.debug(
            "RBACManager.has_permission stub called (Phase 58+ wire)",
            extra={
                "user_id": str(user_id),
                "tenant_id": str(tenant_id),
                "action": action,
                "resource_type": resource_type,
            },
        )
        return False


__all__ = ["RBACManager"]
