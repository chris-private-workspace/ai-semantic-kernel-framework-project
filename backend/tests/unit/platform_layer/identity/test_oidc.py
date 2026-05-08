"""
File: backend/tests/unit/platform_layer/identity/test_oidc.py
Purpose: Unit tests for Sprint 57.7 US-A2 WorkOSOIDCFlow + auth.py callback upsert.
Category: Tests / Platform / Identity (Sprint 57.7 US-A2)
Scope: Phase 57 / Sprint 57.7 Day 3 (Day 2 carryover closure)

Description:
    6 unit tests covering both oidc.py + auth.py with mocked WorkOS SDK +
    mocked AsyncSession (no real network / no real DB):

    1. initiate_login returns (authorize_url, state) when configured
    2. exchange_callback raises OIDCStateError on state mismatch (CSRF)
    3. exchange_callback returns OIDCProfile on vendor SDK success
    4. callback endpoint returns 400 when oidc_tenant_code cookie missing
    5. callback endpoint returns 400 when tenant_code resolves to no Tenant
    6. _upsert_user_from_oidc INSERTs new User on first-time external_id miss

    Tests mock WorkOS client construction (_make_sync_client / _make_async_client)
    and avoid loading real workos package. AsyncSession mocked via AsyncMock for
    database tests.

Created: 2026-05-10 (Sprint 57.7 Day 3)
Last Modified: 2026-05-10

Modification History:
    - 2026-05-10: Initial creation (Sprint 57.7 Day 3 Day 2 carryover closure)

Related:
    - platform_layer/identity/oidc.py (system under test)
    - api/v1/auth.py (system under test)
    - infrastructure/db/models/identity.py (User + Tenant ORM)
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from api.v1.auth import _upsert_user_from_oidc, callback
from infrastructure.db.models.identity import User
from platform_layer.identity.oidc import (
    OIDCExchangeError,
    OIDCProfile,
    OIDCStateError,
    WorkOSOIDCFlow,
)

# =====================================================================
# WorkOSOIDCFlow direct tests (mock SDK)
# =====================================================================


@pytest.fixture
def configured_flow() -> WorkOSOIDCFlow:
    """Build a flow with stub config so _require_configured passes."""
    flow = WorkOSOIDCFlow()
    flow._api_key = "sk_test_xxx"
    flow._client_id = "client_xxx"
    flow._default_redirect_uri = "http://localhost:3005/auth/callback"
    return flow


class TestWorkOSOIDCFlow:
    def test_initiate_login_returns_url_and_state(self, configured_flow: WorkOSOIDCFlow) -> None:
        """1. initiate_login returns vendor URL + 32-byte+ state, when configured."""
        fake_client = MagicMock()
        fake_client.user_management.get_authorization_url.return_value = (
            "https://api.workos.com/user_management/authorize?state=xyz"
        )
        with patch.object(WorkOSOIDCFlow, "_make_sync_client", return_value=fake_client):
            url, state = configured_flow.initiate_login()

        assert url.startswith("https://api.workos.com/")
        assert len(state) >= 32  # secrets.token_urlsafe(32) → 43 chars
        # Verify SDK called with our state + redirect_uri
        call_kwargs = fake_client.user_management.get_authorization_url.call_args.kwargs
        assert call_kwargs["state"] == state
        assert call_kwargs["redirect_uri"] == "http://localhost:3005/auth/callback"
        assert call_kwargs["provider"] == "authkit"

    @pytest.mark.asyncio
    async def test_exchange_callback_state_mismatch_raises(
        self, configured_flow: WorkOSOIDCFlow
    ) -> None:
        """2. exchange_callback raises OIDCStateError on CSRF state mismatch."""
        with pytest.raises(OIDCStateError, match="state mismatch"):
            await configured_flow.exchange_callback(
                code="some_code",
                state="from_callback",
                expected_state="from_cookie_DIFFERENT",
            )

    @pytest.mark.asyncio
    async def test_exchange_callback_returns_profile_on_success(
        self, configured_flow: WorkOSOIDCFlow
    ) -> None:
        """3. exchange_callback returns OIDCProfile when vendor SDK succeeds."""
        # AuthenticateResponse stub — has .user (with .id/.email/.first_name/.last_name)
        # + .access_token
        fake_user = SimpleNamespace(
            id="user_workos_abc",
            email="alice@example.com",
            first_name="Alice",
            last_name="Smith",
        )
        fake_response = SimpleNamespace(user=fake_user, access_token="tok_xxx")

        fake_async_client = MagicMock()
        fake_async_client.user_management.authenticate_with_code = AsyncMock(
            return_value=fake_response
        )

        with patch.object(WorkOSOIDCFlow, "_make_async_client", return_value=fake_async_client):
            same_state = "abc123"
            profile = await configured_flow.exchange_callback(
                code="auth_code", state=same_state, expected_state=same_state
            )

        assert isinstance(profile, OIDCProfile)
        assert profile.external_id == "user_workos_abc"
        assert profile.email == "alice@example.com"
        assert profile.first_name == "Alice"
        assert profile.last_name == "Smith"
        assert profile.raw_id_token == "tok_xxx"


# =====================================================================
# auth.py endpoint + helper tests (mock DB AsyncSession)
# =====================================================================


class TestAuthCallbackEndpoint:
    @pytest.mark.asyncio
    async def test_callback_missing_tenant_cookie_returns_400(self) -> None:
        """4. callback raises 400 when oidc_tenant_code cookie absent."""
        from fastapi import HTTPException

        mock_db = AsyncMock()
        with pytest.raises(HTTPException) as exc_info:
            await callback(
                code="x",
                state="y",
                oidc_state="y",
                oidc_redirect_to="/dest",
                oidc_tenant_code=None,  # the failure trigger
                db=mock_db,
            )
        assert exc_info.value.status_code == 400
        assert "tenant_code" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_callback_unknown_tenant_returns_400(self) -> None:
        """5. callback raises 400 when tenant_code resolves to no Tenant row."""
        from fastapi import HTTPException

        # AsyncSession.execute returns a result; .scalar_one_or_none returns None
        # for tenant lookup miss
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await callback(
                code="x",
                state="y",
                oidc_state="y",
                oidc_redirect_to="/dest",
                oidc_tenant_code="nonexistent_tenant",
                db=mock_db,
            )
        assert exc_info.value.status_code == 400
        assert "nonexistent_tenant" in exc_info.value.detail
        assert "not found" in exc_info.value.detail


class TestUserUpsert:
    @pytest.mark.asyncio
    async def test_upsert_inserts_on_first_login(self) -> None:
        """6. _upsert_user_from_oidc INSERTs new User when external_id miss."""
        # Lookup misses
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = MagicMock()  # add is sync on AsyncSession
        mock_db.flush = AsyncMock()

        tenant_id = uuid4()
        profile = OIDCProfile(
            external_id="user_workos_new",
            email="bob@acme.com",
            first_name="Bob",
            last_name="Doe",
            raw_id_token="tok",
        )

        new_user = await _upsert_user_from_oidc(profile=profile, tenant_id=tenant_id, db=mock_db)

        assert isinstance(new_user, User)
        assert new_user.email == "bob@acme.com"
        assert new_user.external_id == "user_workos_new"
        assert new_user.tenant_id == tenant_id
        assert new_user.display_name == "Bob Doe"
        # Verify session.add + flush called (INSERT path)
        mock_db.add.assert_called_once_with(new_user)
        mock_db.flush.assert_awaited_once()


# =====================================================================
# Bonus: OIDCExchangeError mapping (sanity check)
# =====================================================================


class TestExchangeErrorMapping:
    @pytest.mark.asyncio
    async def test_exchange_callback_wraps_vendor_exception(
        self, configured_flow: WorkOSOIDCFlow
    ) -> None:
        """7 (BONUS, beyond +6 plan target): vendor exception → OIDCExchangeError."""

        class FakeVendorError(Exception):
            pass

        fake_async_client = MagicMock()
        fake_async_client.user_management.authenticate_with_code = AsyncMock(
            side_effect=FakeVendorError("invalid code")
        )

        with patch.object(WorkOSOIDCFlow, "_make_async_client", return_value=fake_async_client):
            same_state = "abc"
            with pytest.raises(OIDCExchangeError, match="WorkOS code exchange failed"):
                await configured_flow.exchange_callback(
                    code="bad", state=same_state, expected_state=same_state
                )
