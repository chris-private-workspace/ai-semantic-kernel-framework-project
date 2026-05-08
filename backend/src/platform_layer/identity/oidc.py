"""
File: backend/src/platform_layer/identity/oidc.py
Purpose: WorkOS OIDC flow wrapper — initiate login + exchange callback + signout.
Category: 範疇 Platform Layer / Identity (Sprint 57.7 US-A2)
Scope: Phase 57 / Sprint 57.7 (IAM Foundation Tier 0 spike)
Owner: Platform Layer Identity team

Description:
    Hosted IAM vendor wrapper for WorkOS (chosen per US-A1 4-vendor matrix —
    see iam-vendor-matrix.md). Provides:

    1. initiate_login(redirect_uri) → vendor authorize URL + state for CSRF
       protection (caller stores state in httpOnly cookie / Redis;
       full PKCE code_verifier deferred Phase 58+ when high-security mode needed)
    2. exchange_callback(code, state, expected_state) → vendor SDK code
       exchange + extract user profile (caller does V2 user upsert)
    3. signout_url(return_to) → vendor logout redirect URL

    Path 1 per Day 0 D2 verify: V2 internal JWT stays HS256 via JWTManager;
    vendor SDK handles JWKS validation of WorkOS-issued tokens internally.
    NO direct JWKS fetching needed in V2 code.

    Day 3 (Sprint 57.7 — closes Day 2 carryover): replaced 3 placeholder
    methods with real `workos.AsyncWorkOSClient.user_management.*` calls.
    initiate_login stays sync (just URL string-builder; no network).
    exchange_callback is async (network call to WorkOS API).

Key Components:
    - WorkOSOIDCFlow: main flow class (initiate_login sync + exchange_callback
      async + signout_url sync)
    - OIDCConfigError: raised when workos_api_key blank (production safety)
    - OIDCStateError: raised on state mismatch (CSRF protection)
    - OIDCExchangeError: raised when vendor SDK rejects code exchange

Created: 2026-05-09 (Sprint 57.7 Day 1 PM)
Last Modified: 2026-05-10

Modification History (newest-first):
    - 2026-05-10: Sprint 57.7 Day 3 — replace 3 placeholder methods with real WorkOS SDK
    - 2026-05-09: Initial skeleton creation (Sprint 57.7 US-A2 Day 1 PM)

Related:
    - iam-vendor-matrix.md (Sprint 57.7 US-A1 vendor decision)
    - core/config/__init__.py (workos_api_key + workos_client_id + oidc_redirect_uri)
    - api/v1/auth.py (3 endpoints consume this flow)
    - .claude/rules/llm-provider-neutrality.md (workos is auth SDK; LLM SDK rule N/A)
"""

from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from core.config import get_settings

if TYPE_CHECKING:
    # Type-only imports prevent module load failure when WorkOS SDK is mocked
    # in unit tests. Runtime methods do lazy import inside the method body.
    pass

logger = logging.getLogger(__name__)


class OIDCConfigError(RuntimeError):
    """Raised when WorkOS configuration is missing (workos_api_key blank)."""


class OIDCStateError(ValueError):
    """Raised when callback state does not match initiate_login state (CSRF)."""


class OIDCExchangeError(RuntimeError):
    """Raised when WorkOS SDK rejects code exchange (auth / network / bad code)."""


@dataclass(frozen=True)
class OIDCProfile:
    """Subset of vendor profile used by V2 user upsert pathway."""

    external_id: str  # WorkOS user_id (subject) → users.external_id lookup
    email: str
    first_name: str | None
    last_name: str | None
    raw_id_token: str  # opaque vendor JWT (V2 does not decode; SDK validates)


class WorkOSOIDCFlow:
    """OIDC hosted login flow via WorkOS user_management API.

    Day 3 production usage:

        flow = WorkOSOIDCFlow()
        authorize_url, state = flow.initiate_login(redirect_uri="...")
        # browser → WorkOS hosted login → IdP → callback
        profile = await flow.exchange_callback(
            code=..., state=..., expected_state=cookie_value
        )
        # caller upserts users row via profile.external_id + profile.email
    """

    def __init__(self) -> None:
        s = get_settings()
        self._api_key = s.workos_api_key
        self._client_id = s.workos_client_id
        self._default_redirect_uri = s.oidc_redirect_uri

    def _require_configured(self) -> None:
        """Raise OIDCConfigError if WorkOS not configured."""
        if not self._api_key or not self._client_id:
            raise OIDCConfigError(
                "WorkOS not configured: set WORKOS_API_KEY + WORKOS_CLIENT_ID env vars"
            )

    def _make_async_client(self) -> Any:
        """Construct AsyncWorkOSClient lazily.

        Why lazy: keeps top-level module import cheap when running unit tests
        that monkey-patch this method to inject AsyncMock client.
        """
        from workos import AsyncWorkOSClient

        return AsyncWorkOSClient(api_key=self._api_key, client_id=self._client_id)

    def _make_sync_client(self) -> Any:
        """Construct sync WorkOSClient for URL builders (no network call)."""
        from workos import WorkOSClient

        return WorkOSClient(api_key=self._api_key, client_id=self._client_id)

    def initiate_login(self, *, redirect_uri: str | None = None) -> tuple[str, str]:
        """Generate vendor authorize URL + state for CSRF protection.

        WorkOS get_authorization_url is sync (just URL builder; no network).
        Caller stores returned state in httpOnly cookie for callback validation.

        Args:
            redirect_uri: Override default oidc_redirect_uri Setting.

        Returns:
            Tuple of (authorize_url, state).

        Raises:
            OIDCConfigError: WorkOS not configured.
        """
        self._require_configured()
        state = secrets.token_urlsafe(32)
        target_redirect = redirect_uri or self._default_redirect_uri

        client = self._make_sync_client()
        # provider="authkit" routes to WorkOS AuthKit hosted login UX (default).
        # state passed through; caller validates equality on callback.
        authorize_url: str = client.user_management.get_authorization_url(
            redirect_uri=target_redirect,
            state=state,
            provider="authkit",
        )
        logger.info(
            "oidc.initiate_login",
            extra={"redirect_uri": target_redirect, "state_len": len(state)},
        )
        return authorize_url, state

    async def exchange_callback(self, *, code: str, state: str, expected_state: str) -> OIDCProfile:
        """Exchange authorization code for vendor profile.

        Async because WorkOS authenticate_with_code makes a network call.

        Args:
            code: Authorization code from vendor callback query param.
            state: State value returned by vendor callback.
            expected_state: State previously stored at initiate_login (caller
                retrieves from session/cookie/Redis).

        Returns:
            OIDCProfile with external_id (WorkOS user_id), email, name,
            raw_id_token.

        Raises:
            OIDCConfigError: WorkOS not configured.
            OIDCStateError: state mismatch (CSRF / replay).
            OIDCExchangeError: WorkOS SDK rejected code (auth / network failure).
        """
        self._require_configured()
        # Constant-time-ish CSRF check: secrets.compare_digest avoids timing
        # leak even though state values are short and random.
        if not secrets.compare_digest(state, expected_state):
            raise OIDCStateError("state mismatch — possible CSRF or replay attack")

        client = self._make_async_client()
        try:
            # WorkOS AuthenticateResponse — has .user (User) + .access_token + ...
            auth_response = await client.user_management.authenticate_with_code(code=code)
        except Exception as exc:  # noqa: BLE001 — vendor exception classes vary; map to ours
            logger.warning("oidc.exchange_callback failed", exc_info=True)
            raise OIDCExchangeError(f"WorkOS code exchange failed: {exc}") from exc

        user = auth_response.user
        access_token = getattr(auth_response, "access_token", "") or ""
        logger.info(
            "oidc.exchange_callback ok",
            extra={"workos_user_id": user.id, "email_domain": user.email.split("@")[-1]},
        )
        return OIDCProfile(
            external_id=user.id,
            email=user.email,
            first_name=getattr(user, "first_name", None),
            last_name=getattr(user, "last_name", None),
            raw_id_token=access_token,
        )

    def signout_url(self, *, return_to: str, session_id: str | None = None) -> str:
        """Vendor signout URL — caller redirects browser to this URL.

        WorkOS get_logout_url requires session_id (vendor session, NOT V2
        session UUID). When V2 doesn't track vendor session_id (e.g. HS256
        JWT-only flow), callers may pass None and we fall back to a static
        AuthKit logout entry that respects return_to.

        Args:
            return_to: URL to redirect to after vendor logout.
            session_id: Optional vendor session id from authenticate_with_code
                response (auth_response.organization_id or similar future field).

        Returns:
            Vendor logout URL.

        Raises:
            OIDCConfigError: WorkOS not configured.
        """
        self._require_configured()

        if session_id:
            client = self._make_sync_client()
            url: str = client.user_management.get_logout_url(
                session_id=session_id,
                return_to=return_to,
            )
            return url

        # Fallback: V2 doesn't have vendor session_id (e.g. cookie expired,
        # JWT-only path). Use AuthKit static logout entry.
        # Caller still gets a usable redirect; vendor side just clears its
        # OIDC session if any.
        return f"https://api.workos.com/user_management/logout?return_to={return_to}"


__all__ = [
    "WorkOSOIDCFlow",
    "OIDCProfile",
    "OIDCConfigError",
    "OIDCStateError",
    "OIDCExchangeError",
]
