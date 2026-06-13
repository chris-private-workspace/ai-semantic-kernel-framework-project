"""
File: backend/src/api/v1/auth.py
Purpose: OIDC PKCE auth endpoints — login redirect + callback exchange + logout.
Category: api/v1 (Sprint 57.7 US-A2)
Scope: Phase 57 / Sprint 57.7 (IAM Foundation Tier 0 spike)

Description:
    OIDC hosted-login flow via WorkOS + the session-introspection endpoint:

    - GET  /api/v1/auth/login    — generate vendor authorize URL + 302 redirect
    - GET  /api/v1/auth/callback — exchange code + V2 user upsert + V2 JWT issue
                                   (cookie) + 302 to SPA /auth/callback?next=...
    - GET  /api/v1/auth/me       — current identity {user, tenant, roles} (401
                                   if no valid JWT — used by SPA authStore.bootstrap)
    - POST /api/v1/auth/dev-login — dev-only fake login (404 in prod); upserts a
                                   dev tenant+user, issues a JWT cookie, returns {user,tenant,roles}
    - POST /api/v1/auth/password-login — local-password sign-in (tenant_code +
                                   email + password → JWT cookie + {user,tenant,roles});
                                   single generic 401 on any failure (Sprint 57.86)
    - POST /api/v1/auth/logout   — vendor signout redirect + clear v2_jwt cookie

    State CSRF protection via httpOnly secure cookie set by /login + read by
    /callback. Tenant scoping via `tenant_code` query param at /login →
    cookie → /callback resolves to Tenant.id (Multi-tenant 鐵律 #1 explicit
    tenant_id; no "default" magic; missing tenant → 400).

    V2 internal JWT remains HS256 per Day 0 D2 verify (Path 1) — vendor SDK
    handles vendor JWT (RS256) validation internally. Callback issues V2
    HS256 JWT via JWTManager.encode() and returns to caller as cookie.

    Day 3 (Sprint 57.7 — closes Day 2 carryover): callback now does real
    DB user upsert via SQLAlchemy AsyncSession. First-time login INSERT;
    subsequent login UPDATE last activity. JWT carries real users.id +
    real tenants.id (no more placeholder UUIDs).

Created: 2026-05-09 (Sprint 57.7 Day 1 PM)
Last Modified: 2026-06-12

Modification History (newest-first):
    - 2026-06-12: Sprint 57.105 — callback + password-login roles claim DB-sourced at issue time
    - 2026-06-06: Sprint 57.86 — add POST /auth/password-login (local credentials; generic 401)
    - 2026-05-10: Sprint 57.13 US-A4 — add POST /auth/dev-login (dev-only fake login; 404 in prod)
    - 2026-05-10: Sprint 57.13 US-A1 — add GET /auth/me + /callback 302→SPA + Settings cookie attrs
    - 2026-05-10: Sprint 57.7 Day 3 — DB user upsert + real tenant resolution
    - 2026-05-09: Initial skeleton creation (Sprint 57.7 US-A2 Day 1 PM)

Related:
    - platform_layer/identity/oidc.py (WorkOSOIDCFlow consumer)
    - platform_layer/identity/jwt.py (JWTManager.encode for V2 JWT issue)
    - infrastructure/db/models/identity.py (User upsert via external_id)
    - infrastructure/db/session.py (get_db_session dependency)
    - api/main.py (router include)
    - iam-vendor-matrix.md (Sprint 57.7 US-A1 vendor decision)
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote_plus
from uuid import UUID as PyUUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from infrastructure.db.audit_helper import append_audit
from infrastructure.db.models.identity import Tenant, User
from infrastructure.db.session import get_db_session
from platform_layer.identity.credentials import (
    CredentialsError,
    CredentialsService,
    maybe_get_credentials_service,
)
from platform_layer.identity.jwt import JWTAuthError, JWTClaims, JWTManager
from platform_layer.identity.oidc import (
    OIDCConfigError,
    OIDCExchangeError,
    OIDCProfile,
    OIDCStateError,
    WorkOSOIDCFlow,
)
from platform_layer.identity.rbac import RBACManager
from platform_layer.middleware.tenant_context import get_db_session_with_tenant

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


def _cookie_kwargs(*, max_age: int) -> dict[str, Any]:
    """Shared httpOnly cookie attrs. Secure flag from Settings (False in dev).

    SameSite=Lax lets the cross-site vendor → /callback redirect deliver the
    cookie back; httpOnly blocks JS access (XSS mitigation).
    """
    return {
        "max_age": max_age,
        "httponly": True,
        "secure": get_settings().cookie_secure,
        "samesite": "lax",
    }


# ---- Cookie names + TTL --------------------------------------------------
# Why httpOnly secure cookie: prevents JS access (XSS mitigation) + browser
# auto-sends to /callback for state validation. SameSite=Lax allows the
# vendor redirect (cross-site) to deliver the cookie back.
_STATE_COOKIE = "oidc_state"
_REDIRECT_COOKIE = "oidc_redirect_to"
_TENANT_COOKIE = "oidc_tenant_code"
_JWT_COOKIE = "v2_jwt"
_STATE_TTL_SECONDS = 600  # 10 min
# MFA challenge cookie (Sprint 57.112): a short-lived mfa_pending JWT set by
# password-login when the user has MFA enabled — NOT a session (roles=[]); only
# the EXEMPT POST /api/v1/mfa/verify consumes it (decode_mfa_challenge) and, on a
# valid TOTP, swaps it for the real _JWT_COOKIE session. Public so api/v1/mfa.py
# can read + clear it.
MFA_CHALLENGE_COOKIE = "v2_mfa_challenge"


class LogoutResponse(BaseModel):
    redirect_to: str


class AuthMeUser(BaseModel):
    id: PyUUID
    email: str
    display_name: str | None = None


class AuthMeTenant(BaseModel):
    id: PyUUID
    name: str
    code: str


class AuthMeResponse(BaseModel):
    user: AuthMeUser
    tenant: AuthMeTenant
    roles: list[str]


@router.get("/login")
async def login(
    redirect_to: str = Query(default="/cost-dashboard"),
    tenant_code: str = Query(
        default="default",
        description="Tenant code for multi-tenant context. /callback looks up tenants.code "
        "to resolve tenants.id; missing tenant → 400.",
    ),
) -> RedirectResponse:
    """Initiate OIDC login — 302 redirect to vendor authorize URL.

    Sets oidc_state + oidc_redirect_to + oidc_tenant_code cookies so /callback
    can validate state (CSRF), know where to redirect post-login, and resolve
    which tenant the user belongs to (Multi-tenant 鐵律 #1).
    """
    try:
        flow = WorkOSOIDCFlow()
        authorize_url, state = flow.initiate_login()
    except OIDCConfigError as exc:
        logger.error("auth.login: WorkOS not configured", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    response = RedirectResponse(url=authorize_url, status_code=status.HTTP_302_FOUND)
    cookie_kwargs = _cookie_kwargs(max_age=_STATE_TTL_SECONDS)
    response.set_cookie(key=_STATE_COOKIE, value=state, **cookie_kwargs)
    response.set_cookie(key=_REDIRECT_COOKIE, value=redirect_to, **cookie_kwargs)
    response.set_cookie(key=_TENANT_COOKIE, value=tenant_code, **cookie_kwargs)
    return response


async def _upsert_user_from_oidc(
    *,
    profile: OIDCProfile,
    tenant_id: PyUUID,
    db: AsyncSession,
) -> User:
    """Look up V2 User by (tenant_id, external_id); INSERT if missing.

    Why tenant_id + external_id: external_id alone is NOT unique across
    tenants (same WorkOS user might belong to multiple V2 tenants in
    multi-IdP federation). Composite lookup preserves Multi-tenant 鐵律 #2.
    Per identity.py L188-196, users has UNIQUE (tenant_id, email) +
    Index(external_id) — composite (tenant_id, external_id) is the proper key.

    Caller commits the session.
    """
    stmt = select(User).where(
        User.tenant_id == tenant_id,
        User.external_id == profile.external_id,
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is not None:
        # Subsequent login — preserve identity but refresh display_name if
        # vendor profile changed. updated_at server_default is NOT auto-bumped
        # on UPDATE so we set it here when display_name diverges.
        new_display = _format_display_name(profile)
        if new_display and user.display_name != new_display:
            user.display_name = new_display
        return user

    # First-time login — INSERT. status defaults to "active" via column
    # default; preferences / created_at / updated_at via server_default.
    new_user = User(
        tenant_id=tenant_id,
        email=profile.email,
        display_name=_format_display_name(profile),
        external_id=profile.external_id,
    )
    db.add(new_user)
    # Flush to get server-generated UUID id without committing (caller
    # commits via get_db_session lifecycle).
    await db.flush()
    logger.info(
        "auth.callback: user upsert INSERT",
        extra={
            "external_id": profile.external_id,
            "tenant_id": str(tenant_id),
            "user_id": str(new_user.id),
        },
    )
    return new_user


def _format_display_name(profile: OIDCProfile) -> str | None:
    """Combine first_name + last_name, fall back to email local-part."""
    parts = [p for p in (profile.first_name, profile.last_name) if p]
    if parts:
        return " ".join(parts)
    return profile.email.split("@", 1)[0] if profile.email else None


@router.get("/callback")
async def callback(
    code: str = Query(...),
    state: str = Query(...),
    oidc_state: str | None = Cookie(default=None),
    oidc_redirect_to: str | None = Cookie(default=None),
    oidc_tenant_code: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db_session),
) -> RedirectResponse:
    """Exchange OIDC callback code → vendor profile → V2 user upsert + V2 JWT.

    Day 3 (Sprint 57.7 carryover): full DB user upsert via AsyncSession.
    JWT carries real users.id + real tenants.id (replaces Day 1 placeholder
    UUIDs that Multi-tenant 鐵律 made unusable for downstream observers).
    """
    if oidc_state is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="missing oidc_state cookie",
        )
    if oidc_tenant_code is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="missing oidc_tenant_code cookie — re-initiate login",
        )

    # Resolve tenant_code → tenants.id BEFORE vendor exchange (fail fast).
    tenant_stmt = select(Tenant).where(Tenant.code == oidc_tenant_code)
    tenant_result = await db.execute(tenant_stmt)
    tenant = tenant_result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"tenant '{oidc_tenant_code}' not found — provision tenant first",
        )

    try:
        flow = WorkOSOIDCFlow()
        profile = await flow.exchange_callback(
            code=code,
            state=state,
            expected_state=oidc_state,
        )
    except OIDCStateError as exc:
        logger.warning("auth.callback: state mismatch")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except OIDCConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except OIDCExchangeError as exc:
        # Vendor rejected code (expired / replayed / network). 400 not 401
        # because the user's IdP login itself succeeded — issue is on us.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    user = await _upsert_user_from_oidc(profile=profile, tenant_id=tenant.id, db=db)

    # Issue-time DB roles (Sprint 57.105): the JWT claim carries the user's real
    # grants ("user" baseline ∪ Role/UserRole codes) — admin gates read the claim.
    role_codes = await RBACManager.get_user_role_codes(
        user_id=user.id, tenant_id=tenant.id, session=db
    )
    jwt_manager = JWTManager()
    v2_jwt = jwt_manager.encode(
        sub=str(user.id),
        tenant_id=tenant.id,
        roles=sorted({"user", *role_codes}),
        extra={"email": profile.email, "external_id": profile.external_id},
    )

    settings = get_settings()
    next_path = oidc_redirect_to or "/cost-dashboard"
    # Redirect the browser back to the SPA's /auth/callback so it can run
    # authStore.bootstrap() (which reads the v2_jwt cookie via /auth/me) then
    # navigate to the originally-requested page (?next=). Sprint 57.13 US-A1:
    # previously redirected straight to next_path, which left the SPA with no
    # signal to refresh its auth state — manifested as "logged in but app says
    # anonymous" until a hard refresh.
    final_redirect = f"{settings.frontend_base_url}/auth/callback?next={quote_plus(next_path)}"
    response = RedirectResponse(
        url=final_redirect,
        status_code=status.HTTP_302_FOUND,
    )
    response.set_cookie(
        key=_JWT_COOKIE,
        value=v2_jwt,
        **_cookie_kwargs(max_age=settings.jwt_expires_minutes * 60),
    )
    # Clear ephemeral state cookies
    response.delete_cookie(_STATE_COOKIE)
    response.delete_cookie(_REDIRECT_COOKIE)
    response.delete_cookie(_TENANT_COOKIE)
    return response


@router.get("/me", response_model=AuthMeResponse)
async def me(
    request: Request,
    db: AsyncSession = Depends(get_db_session_with_tenant),
) -> AuthMeResponse:
    """Return the current authenticated identity (user + tenant + roles).

    Auth: requires a valid V2 JWT (Bearer header OR v2_jwt cookie) — the
    TenantContextMiddleware decodes it and populates `request.state.{tenant_id,
    user_id, roles}`. This path is NOT in EXEMPT_PATH_PREFIXES, so an absent /
    invalid / expired JWT surfaces as 401 from the middleware before this
    handler ever runs.

    DB session: get_db_session_with_tenant (SET LOCAL app.tenant_id) so the
    users-table RLS policy (migration 0009) lets the row through in prod —
    request.state.tenant_id is guaranteed set since this path isn't exempt.

    Sprint 57.13 US-A1: the SPA's authStore.bootstrap() calls this on app
    mount + after login to decide authenticated vs anonymous, and to render
    the user / tenant / roles in the shell + gate routes.
    """
    tenant_id: PyUUID = request.state.tenant_id
    user_id: PyUUID = request.state.user_id
    roles: list[str] = list(getattr(request.state, "roles", []))

    user = (
        await db.execute(select(User).where(User.id == user_id, User.tenant_id == tenant_id))
    ).scalar_one_or_none()
    tenant = (await db.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one_or_none()
    if user is None or tenant is None:
        # JWT was valid but the referenced rows are gone (user offboarded /
        # tenant archived). Treat as unauthenticated rather than 500.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="authenticated identity no longer exists",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )

    return AuthMeResponse(
        user=AuthMeUser(id=user.id, email=user.email, display_name=user.display_name),
        tenant=AuthMeTenant(id=tenant.id, name=tenant.display_name, code=tenant.code),
        roles=roles,
    )


# Dev fake-login roles — every page renders (user pages + admin pages +
# platform-admin pages) so local dev can exercise the whole app.
_DEV_LOGIN_ROLES: tuple[str, ...] = ("user", "admin", "platform_admin")


def _is_production() -> bool:
    return get_settings().env.lower() in ("production", "prod")


@router.post("/dev-login")
async def dev_login(
    tenant_code: str = Query("dev", description="Tenant code; auto-created if absent (dev only)."),
    email: str = Query("dev@local", description="Dev user email."),
    db: AsyncSession = Depends(get_db_session),
) -> JSONResponse:
    """Dev-only fake login — no WorkOS account required. Returns 404 in production.

    Sprint 57.13 US-A4: lets local development sign in to auth-gated pages.
    Resolves (or auto-creates) a dev Tenant by `tenant_code`, upserts a dev
    User (external_id=`dev:<email>`), issues a V2 JWT cookie with roles
    [user, admin, platform_admin] so every page renders, and returns
    {user, tenant, roles} JSON — the SPA sets authStore from the payload and
    navigates itself (no 302 chain). In production (Settings.env in
    {production, prod}) the route is invisible (404), so it's safe to ship.
    """
    if _is_production():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")

    tenant = (
        await db.execute(select(Tenant).where(Tenant.code == tenant_code))
    ).scalar_one_or_none()
    if tenant is None:
        tenant = Tenant(code=tenant_code, display_name=f"Dev Tenant ({tenant_code})")
        db.add(tenant)
        await db.flush()

    external_id = f"dev:{email}"
    user = (
        await db.execute(
            select(User).where(User.tenant_id == tenant.id, User.external_id == external_id)
        )
    ).scalar_one_or_none()
    if user is None:
        user = User(
            tenant_id=tenant.id,
            email=email,
            display_name=email.split("@", 1)[0],
            external_id=external_id,
        )
        db.add(user)
        await db.flush()

    settings = get_settings()
    v2_jwt = JWTManager().encode(
        sub=str(user.id),
        tenant_id=tenant.id,
        roles=list(_DEV_LOGIN_ROLES),
        extra={"email": email, "external_id": external_id},
    )
    body = AuthMeResponse(
        user=AuthMeUser(id=user.id, email=user.email, display_name=user.display_name),
        tenant=AuthMeTenant(id=tenant.id, name=tenant.display_name, code=tenant.code),
        roles=list(_DEV_LOGIN_ROLES),
    ).model_dump(mode="json")
    response = JSONResponse(content=body)
    response.set_cookie(
        key=_JWT_COOKIE,
        value=v2_jwt,
        **_cookie_kwargs(max_age=settings.jwt_expires_minutes * 60),
    )
    return response


# ---- Session issuance + MFA challenge (Sprint 57.112) --------------------
# Why: the full-session block (DB-sourced roles → V2 JWT cookie + AuthMeResponse)
# is now issued from TWO places — password-login's non-MFA path and POST
# /api/v1/mfa/verify after a TOTP passes. issue_session() is the single shared
# implementation (DRY; api/v1/mfa.py imports it). The MFA challenge helpers gate
# the login: when a user has MFA enabled, password-login issues a short-lived
# mfa_pending challenge (roles=[]) instead of a session, and /mfa/verify swaps it
# for the real session only after the second factor checks out.


async def issue_session(
    db: AsyncSession,
    user: User,
    *,
    operation: str,
    operation_data: dict[str, Any] | None = None,
) -> JSONResponse:
    """Issue a full V2 session: DB-sourced roles → v2_jwt cookie + AuthMeResponse body.

    Shared by POST /auth/password-login (non-MFA path) and POST /api/v1/mfa/verify
    (post-TOTP). The caller's db session must already carry the user's RLS tenant
    context (both call sites set it: CredentialsService.authenticate / TOTPService
    .verify run set_config('app.tenant_id', ...) before this runs). `operation` is
    the audit op name (password_login / mfa_verified).
    """
    tenant = (await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))).scalar_one()
    role_codes = await RBACManager.get_user_role_codes(
        user_id=user.id, tenant_id=user.tenant_id, session=db
    )
    roles = sorted({"user", *role_codes})
    settings = get_settings()
    v2_jwt = JWTManager().encode(
        sub=str(user.id),
        tenant_id=user.tenant_id,
        roles=roles,
        extra={"email": user.email},
    )
    await append_audit(
        db,
        tenant_id=user.tenant_id,
        operation=operation,
        resource_type="user",
        resource_id=str(user.id),
        operation_data=operation_data or {},
        user_id=user.id,
        operation_result="success",
    )
    body_out = AuthMeResponse(
        user=AuthMeUser(id=user.id, email=user.email, display_name=user.display_name),
        tenant=AuthMeTenant(id=tenant.id, name=tenant.display_name, code=tenant.code),
        roles=roles,
    ).model_dump(mode="json")
    response = JSONResponse(content=body_out)
    response.set_cookie(
        key=_JWT_COOKIE,
        value=v2_jwt,
        **_cookie_kwargs(max_age=settings.jwt_expires_minutes * 60),
    )
    return response


def _issue_mfa_challenge(user: User) -> JSONResponse:
    """Issue a short-lived mfa_pending challenge cookie (NOT a session); signal the SPA.

    roles=[] + extra={"mfa_pending": True} → the middleware never treats this as a
    session (only v2_jwt is the session cookie). Body {"mfa_required": true} tells
    the SPA to navigate to /auth/mfa. The full session is granted only by
    /api/v1/mfa/verify after the TOTP code checks out.
    """
    settings = get_settings()
    challenge = JWTManager().encode(
        sub=str(user.id),
        tenant_id=user.tenant_id,
        roles=[],
        expires_minutes=settings.mfa_challenge_ttl_minutes,
        extra={"mfa_pending": True},
    )
    response = JSONResponse(content={"mfa_required": True})
    response.set_cookie(
        key=MFA_CHALLENGE_COOKIE,
        value=challenge,
        **_cookie_kwargs(max_age=settings.mfa_challenge_ttl_minutes * 60),
    )
    return response


def decode_mfa_challenge(request: Request) -> JWTClaims:
    """Decode + validate the v2_mfa_challenge cookie → claims, or raise 401.

    Used by POST /api/v1/mfa/verify (EXEMPT, pre-session). Raises 401 if the cookie
    is absent / expired / invalid / not an mfa_pending challenge. The claims carry
    sub (user_id) + tenant_id — the verify endpoint scopes TOTPService.verify with them.
    """
    token = request.cookies.get(MFA_CHALLENGE_COOKIE)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="MFA challenge required"
        )
    try:
        claims = JWTManager().decode(token)
    except JWTAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="MFA challenge invalid or expired",
        ) from exc
    if claims.extra.get("mfa_pending") is not True:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="MFA challenge invalid"
        )
    return claims


# ---- Password-login (local credentials; Sprint 57.86) --------------------
# Why: invited users who set a local password (invite-accept) must be able to
# sign back in without SSO. Mirrors dev-login's JWT/cookie/AuthMeResponse SUCCESS
# shape, but is a real auth path: a JSON body (creds never in the query string),
# a real (tenant_code, email) lookup + bcrypt verify (CredentialsService), a
# SINGLE generic 401 for every failure (no enumeration). The roles claim is
# DB-sourced at issue time ("user" ∪ Role/UserRole codes — Sprint 57.105), like
# the OIDC callback. NOT production-gated (unlike dev-login). Rate-limit/lockout
# is a tracked carryover (AD-Auth-PasswordLogin-Lockout-Phase58).


class PasswordLoginRequest(BaseModel):
    """Local password-login body (JSON — creds never travel in the query string)."""

    tenant_code: str = Field(min_length=1, max_length=64)
    email: str = Field(min_length=3, max_length=256)
    password: str = Field(min_length=1, max_length=72)


@router.post("/password-login")
async def password_login(
    body: PasswordLoginRequest,
    db: AsyncSession = Depends(get_db_session),
) -> JSONResponse:
    """Authenticate (tenant_code, email, password) → V2 JWT cookie + {user,tenant,roles}.

    Exempt path (the caller has no JWT yet). EVERY failure — unknown tenant /
    email / SSO-only user / wrong password — returns a single generic 401 (no
    enumeration; CredentialsService flattens timing). On success: a V2 HS256 JWT
    cookie (same shape as dev-login) + AuthMeResponse JSON; the SPA sets authStore
    from the payload and navigates itself.
    """
    service = maybe_get_credentials_service() or CredentialsService()
    try:
        user = await service.authenticate(
            db, tenant_code=body.tenant_code, email=body.email, raw=body.password
        )
    except CredentialsError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    # MFA-gate (Sprint 57.112): a user with a TOTP second factor does NOT get a
    # session here — password-login issues a short-lived mfa_pending challenge and
    # the SPA continues to /auth/mfa; the full session is granted by /api/v1/mfa/
    # verify after the code checks out. authenticate() already set the RLS tenant
    # context on db, so user.mfa_enabled is the freshly-loaded value.
    if user.mfa_enabled:
        await append_audit(
            db,
            tenant_id=user.tenant_id,
            operation="password_login_mfa_challenge",
            resource_type="user",
            resource_id=str(user.id),
            operation_data={},
            user_id=user.id,
            operation_result="success",
        )
        return _issue_mfa_challenge(user)

    return await issue_session(db, user, operation="password_login")


@router.post("/logout")
async def logout(
    return_to: str = Query(default="/auth/login"),
) -> JSONResponse:
    """Vendor signout + clear V2 JWT cookie.

    Returns JSON with vendor logout URL so frontend can redirect browser
    (POST → 302 chain not ideal; let frontend handle redirect explicitly).
    """
    try:
        flow = WorkOSOIDCFlow()
        # Encode return_to for safety even if vendor SDK does it (defense in depth).
        # session_id=None → fallback static logout (we don't track vendor session id yet)
        signout_url = flow.signout_url(return_to=quote_plus(return_to))
    except OIDCConfigError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    body = LogoutResponse(redirect_to=signout_url).model_dump()
    response = JSONResponse(content=body)
    response.delete_cookie(_JWT_COOKIE)
    return response
