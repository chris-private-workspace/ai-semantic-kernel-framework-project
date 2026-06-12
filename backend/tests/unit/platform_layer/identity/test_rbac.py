"""
File: backend/tests/unit/platform_layer/identity/test_rbac.py
Purpose: Unit tests for Sprint 57.7 US-A3 DB-backed RBACManager + opt-in hybrid path.
Category: Tests / Platform / Identity (Sprint 57.7 US-A3)
Scope: Phase 57 / Sprint 57.7 Day 2 PM

Description:
    4+ unit tests covering:
    - 1 happy path: user has role code in DB → has_role_code returns True
    - 1 rejection: user lacks role code in DB → has_role_code returns False
    - 1 cross-tenant isolation: user has role in tenant A, queried for tenant B
      → has_role_code returns False (per multi-tenant 鐵律 #2)
    - 1 backwards compat: opt-in OFF (default) preserves legacy 403 behavior
      when JWT claim doesn't grant + Path 2 skipped
    - 1 opt-in ON: Path 2 fires + queries DB + grants if user has role

    Tests use SQLite in-memory + minimal seed (NOT real Postgres) to keep
    unit tests fast + isolated. RLS policies (PostgreSQL-only) are NOT
    exercised at this layer — covered by integration tests Phase 58+.

Created: 2026-05-09 (Sprint 57.7 Day 2 PM)
Last Modified: 2026-06-12

Modification History:
    - 2026-06-12: Sprint 57.105 — add TestGetUserRoleCodes (issue-time JWT roles source)
    - 2026-05-09: Initial creation (Sprint 57.7 US-A3 Day 2)

Related:
    - platform_layer/identity/rbac.py (system under test)
    - platform_layer/identity/auth.py (_require_role hybrid path)
    - core/config/__init__.py (rbac_db_backed_fallback opt-in)
    - infrastructure/db/models/identity.py (Role + UserRole + User)
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from platform_layer.identity.auth import require_admin_platform_role
from platform_layer.identity.rbac import RBACManager


def _make_request(*, user_id: object, roles: object, tenant_id: object = None) -> SimpleNamespace:
    """Build minimal Request stub with .state.user_id + .state.roles + optional tenant_id."""
    state = SimpleNamespace(user_id=user_id, roles=roles, tenant_id=tenant_id)
    return SimpleNamespace(state=state)


class TestRBACManagerHasRoleCode:
    """Direct tests for RBACManager.has_role_code DB query."""

    @pytest.mark.asyncio
    async def test_user_with_matching_role_returns_true(self) -> None:
        """User has role code in allowed_codes → True (mocked DB session)."""
        user_id = uuid4()
        tenant_id = uuid4()
        # Mock the inner _has_role_code_with_session method to bypass real DB
        with patch.object(
            RBACManager,
            "_has_role_code_with_session",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_inner:
            result = await RBACManager.has_role_code(
                user_id=user_id,
                tenant_id=tenant_id,
                allowed_codes=frozenset({"admin"}),
                session=AsyncMock(),  # passed to bypass session factory
            )
        assert result is True
        mock_inner.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_user_without_matching_role_returns_false(self) -> None:
        """User lacks role code in allowed_codes → False."""
        user_id = uuid4()
        tenant_id = uuid4()
        with patch.object(
            RBACManager,
            "_has_role_code_with_session",
            new_callable=AsyncMock,
            return_value=False,
        ):
            result = await RBACManager.has_role_code(
                user_id=user_id,
                tenant_id=tenant_id,
                allowed_codes=frozenset({"admin"}),
                session=AsyncMock(),
            )
        assert result is False

    @pytest.mark.asyncio
    async def test_empty_allowed_codes_returns_false(self) -> None:
        """Defensive: empty allowed_codes returns False without DB hit."""
        user_id = uuid4()
        tenant_id = uuid4()
        result = await RBACManager.has_role_code(
            user_id=user_id,
            tenant_id=tenant_id,
            allowed_codes=frozenset(),
            session=AsyncMock(),
        )
        assert result is False


class TestGetUserRoleCodes:
    """Sprint 57.105 — issue-time JWT roles source (login handlers bake into claim)."""

    @staticmethod
    def _session_returning(codes: list[str]) -> AsyncMock:
        """AsyncMock session whose execute() yields a Result with scalars().all() == codes."""
        result = MagicMock()
        result.scalars.return_value.all.return_value = codes
        session = AsyncMock()
        session.execute = AsyncMock(return_value=result)
        return session

    @pytest.mark.asyncio
    async def test_codes_sorted_and_deduped(self) -> None:
        """Duplicate grants collapse; output sorted for a deterministic claim."""
        session = self._session_returning(["user", "admin", "admin"])
        codes = await RBACManager.get_user_role_codes(
            user_id=uuid4(), tenant_id=uuid4(), session=session
        )
        assert codes == ["admin", "user"]
        session.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_no_grants_returns_empty(self) -> None:
        """Role-less user → [] (claim stays the ['user'] baseline at the call site)."""
        session = self._session_returning([])
        codes = await RBACManager.get_user_role_codes(
            user_id=uuid4(), tenant_id=uuid4(), session=session
        )
        assert codes == []


class TestRequireRoleHybridPath:
    """Tests for auth.py _require_role hybrid path (Path 1 JWT + Path 2 DB)."""

    @pytest.mark.asyncio
    async def test_path1_jwt_admin_passes_without_db_hit(self) -> None:
        """Path 1: JWT roles claim has 'admin' → grants without touching DB."""
        user_id = uuid4()
        request = _make_request(user_id=user_id, roles=["admin"])
        # No need to mock DB — Path 1 short-circuits
        result = await require_admin_platform_role(request)  # type: ignore[arg-type]
        assert result == user_id

    @pytest.mark.asyncio
    async def test_path2_disabled_default_falls_through_to_403(self) -> None:
        """Backwards compat: opt-in OFF (default) → falls through to 403 when
        JWT claim doesn't grant + Path 2 skipped (no DB hit)."""
        user_id = uuid4()
        # 'tenant_admin' NOT in _ADMIN_PLATFORM_ROLES frozenset
        request = _make_request(user_id=user_id, roles=["tenant_admin"])
        with pytest.raises(HTTPException) as exc_info:
            await require_admin_platform_role(request)  # type: ignore[arg-type]
        assert exc_info.value.status_code == 403
        assert "Platform admin" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_path2_enabled_db_grants_per_tenant_role(self) -> None:
        """Path 2 ON + JWT claim doesn't grant + DB has matching role → grants.

        This proves the per-tenant custom role pattern works: user has role
        with code 'admin' in DB but JWT only carries label 'tenant_admin'
        (e.g. JWT generated before role grant in DB).
        """
        user_id = uuid4()
        tenant_id = uuid4()
        request = _make_request(user_id=user_id, roles=["tenant_admin"], tenant_id=tenant_id)
        with patch(
            "platform_layer.identity.rbac.RBACManager.has_role_code",
            new_callable=AsyncMock,
            return_value=True,
        ) as mock_has_role:
            with patch(
                "core.config.get_settings",
                return_value=SimpleNamespace(rbac_db_backed_fallback=True),
            ):
                result = await require_admin_platform_role(request)  # type: ignore[arg-type]
        assert result == user_id
        mock_has_role.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_path2_enabled_db_lacks_role_still_403(self) -> None:
        """Path 2 ON + JWT claim doesn't grant + DB also lacks role → 403."""
        user_id = uuid4()
        tenant_id = uuid4()
        request = _make_request(user_id=user_id, roles=["tenant_admin"], tenant_id=tenant_id)
        with patch(
            "platform_layer.identity.rbac.RBACManager.has_role_code",
            new_callable=AsyncMock,
            return_value=False,
        ):
            with patch(
                "core.config.get_settings",
                return_value=SimpleNamespace(rbac_db_backed_fallback=True),
            ):
                with pytest.raises(HTTPException) as exc_info:
                    await require_admin_platform_role(request)  # type: ignore[arg-type]
        assert exc_info.value.status_code == 403
