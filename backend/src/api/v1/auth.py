"""
File: backend/src/api/v1/auth.py
Purpose: OIDC PKCE auth endpoints — login redirect + callback exchange + logout.
Category: api/v1 (Sprint 57.7 US-A2)
Scope: Phase 57 / Sprint 57.7 (IAM Foundation Tier 0 spike)

Description:
    Three endpoints implementing OIDC hosted-login flow via WorkOS:

    - GET /api/v1/auth/login    — generate vendor authorize URL + 302 redirect
    - GET /api/v1/auth/callback — exchange code + V2 user upsert + V2 JWT issue
    - POST /api/v1/auth/logout  — vendor signout redirect

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
Last Modified: 2026-05-10

Modification History (newest-first):
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

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.models.identity import Tenant, User
from infrastructure.db.session import get_db_session
from platform_layer.identity.jwt import JWTManager
from platform_layer.identity.oidc import (
    OIDCConfigError,
    OIDCExchangeError,
    OIDCProfile,
    OIDCStateError,
    WorkOSOIDCFlow,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


# ---- Cookie names + TTL --------------------------------------------------
# Why httpOnly secure cookie: prevents JS access (XSS mitigation) + browser
# auto-sends to /callback for state validation. SameSite=Lax allows the
# vendor redirect (cross-site) to deliver the cookie back.
_STATE_COOKIE = "oidc_state"
_REDIRECT_COOKIE = "oidc_redirect_to"
_TENANT_COOKIE = "oidc_tenant_code"
_JWT_COOKIE = "v2_jwt"
_STATE_TTL_SECONDS = 600  # 10 min


class LogoutResponse(BaseModel):
    redirect_to: str


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
    cookie_kwargs: dict[str, Any] = {
        "max_age": _STATE_TTL_SECONDS,
        "httponly": True,
        "secure": False,  # Phase 58+: True in prod (set via Settings.cookie_secure)
        "samesite": "lax",
    }
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

    jwt_manager = JWTManager()
    v2_jwt = jwt_manager.encode(
        sub=str(user.id),
        tenant_id=tenant.id,
        roles=["user"],  # RBAC actual roles loaded per-request via RBACManager
        extra={"email": profile.email, "external_id": profile.external_id},
    )

    final_redirect = oidc_redirect_to or "/cost-dashboard"
    response = RedirectResponse(
        url=final_redirect,
        status_code=status.HTTP_302_FOUND,
    )
    response.set_cookie(
        key=_JWT_COOKIE,
        value=v2_jwt,
        max_age=3600,  # 1 hour matches jwt_expires_minutes default
        httponly=True,
        secure=False,
        samesite="lax",
    )
    # Clear ephemeral state cookies
    response.delete_cookie(_STATE_COOKIE)
    response.delete_cookie(_REDIRECT_COOKIE)
    response.delete_cookie(_TENANT_COOKIE)
    return response


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
