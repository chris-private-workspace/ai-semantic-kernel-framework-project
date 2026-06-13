"""
File: backend/src/api/v1/mfa.py
Purpose: TOTP MFA endpoints — enroll / confirm / verify (C-12 IAM Block C MFA).
Category: api (HTTP boundary) / Identity
Scope: Sprint 57.112 / US-2

Description:
    Three endpoints behind the /api/v1/mfa prefix:
      - POST /mfa/enroll          (full session) → generate + store a TOTP secret,
        return the otpauth:// URI the authenticator app scans. mfa_enabled stays
        false until confirmed.
      - POST /mfa/enroll/confirm  (full session) → verify the first code → activate.
      - POST /mfa/verify          (EXEMPT, challenge-gated) → the endpoint the
        /auth/mfa page calls during login. Reads the short-lived mfa_pending
        challenge cookie (set by password-login), validates the TOTP, and swaps it
        for a full v2_jwt session (via the shared auth.issue_session).

    enroll/confirm require a full session (you enroll while logged in) — they read
    request.state.{user_id,tenant_id} (middleware-populated) + use the tenant DB
    dep. verify is EXEMPT (the caller has no session yet) — it uses the raw DB
    session + decodes the challenge cookie for (user_id, tenant_id); TOTPService
    .verify sets the RLS context itself. Audit is recorded here at the endpoint
    layer (TOTPService stays a pure service).

    WebAuthn is NOT supported in this release (the FE conic-ring is a Simulate
    stub): method="webauthn" returns an honest 400 rather than a faked success.

Key Components:
    - EnrollResponse / ConfirmRequest / ConfirmResponse / VerifyRequest (Pydantic)
    - enroll / enroll_confirm / verify (the 3 routes)

Created: 2026-06-13 (Sprint 57.112)
Last Modified: 2026-06-13

Modification History (newest-first):
    - 2026-06-13: Initial creation (Sprint 57.112 / US-2) — TOTP enroll/confirm/verify

Related:
    - platform_layer/identity/mfa.py — TOTPService (the service these wrap)
    - api/v1/auth.py — issue_session / decode_mfa_challenge / MFA_CHALLENGE_COOKIE
    - platform_layer/middleware/tenant_context.py — /api/v1/mfa/verify EXEMPT entry
    - api/main.py — router mount
    - sprint-57-112-plan.md §3.2
"""

from __future__ import annotations

from uuid import UUID as PyUUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.v1.auth import MFA_CHALLENGE_COOKIE, decode_mfa_challenge, issue_session
from core.config import get_settings
from infrastructure.db.audit_helper import append_audit
from infrastructure.db.session import get_db_session
from platform_layer.identity.mfa import MFAError, TOTPService, maybe_get_mfa_service
from platform_layer.middleware.tenant_context import get_db_session_with_tenant

router = APIRouter(prefix="/mfa", tags=["mfa"])


class EnrollResponse(BaseModel):
    """The base32 secret + provisioning URI (the user keys it into / scans it with
    an authenticator app)."""

    secret: str
    otpauth_uri: str


class ConfirmRequest(BaseModel):
    code: str = Field(min_length=4, max_length=12)


class ConfirmResponse(BaseModel):
    mfa_enabled: bool


class VerifyRequest(BaseModel):
    """The /auth/mfa page posts {method:"totp", code} or {method:"webauthn", simulated}."""

    method: str = Field(min_length=1, max_length=32)
    code: str = Field(default="", max_length=12)
    simulated: bool = False


def _service() -> TOTPService:
    """Singleton if wired (tests), else a fresh stateless instance (mirrors password-login)."""
    return maybe_get_mfa_service() or TOTPService()


@router.post("/enroll", response_model=EnrollResponse)
async def enroll(
    request: Request,
    db: AsyncSession = Depends(get_db_session_with_tenant),
) -> EnrollResponse:
    """Generate + store a TOTP secret for the logged-in user; return the otpauth URI.

    Requires a full session (NON-exempt): the user is identified by the JWT the
    middleware decoded into request.state. 409 if MFA is already enabled.
    """
    user_id: PyUUID = request.state.user_id
    tenant_id: PyUUID = request.state.tenant_id
    try:
        result = await _service().enroll(
            db,
            user_id=user_id,
            tenant_id=tenant_id,
            issuer_name=get_settings().mfa_issuer_name,
        )
    except MFAError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    await append_audit(
        db,
        tenant_id=tenant_id,
        operation="mfa_enroll_started",
        resource_type="user",
        resource_id=str(user_id),
        operation_data={},
        user_id=user_id,
        operation_result="success",
    )
    return EnrollResponse(secret=result.secret, otpauth_uri=result.otpauth_uri)


@router.post("/enroll/confirm", response_model=ConfirmResponse)
async def enroll_confirm(
    body: ConfirmRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session_with_tenant),
) -> ConfirmResponse:
    """Verify the user's first code → flip mfa_enabled true (activation). Full session."""
    user_id: PyUUID = request.state.user_id
    tenant_id: PyUUID = request.state.tenant_id
    try:
        await _service().confirm(db, user_id=user_id, tenant_id=tenant_id, code=body.code)
    except MFAError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
    await append_audit(
        db,
        tenant_id=tenant_id,
        operation="mfa_enabled",
        resource_type="user",
        resource_id=str(user_id),
        operation_data={},
        user_id=user_id,
        operation_result="success",
    )
    return ConfirmResponse(mfa_enabled=True)


@router.post("/verify")
async def verify(
    body: VerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> JSONResponse:
    """Validate the TOTP against the mfa_pending challenge → issue the full session.

    EXEMPT (the caller has only the short-lived challenge cookie, not a session).
    Decodes the challenge for (user_id, tenant_id), validates the code, then swaps
    the challenge for a real v2_jwt session (auth.issue_session) and clears the
    challenge cookie. WebAuthn is not supported this release → honest 400.
    """
    claims = decode_mfa_challenge(request)  # 401 if absent / expired / not mfa_pending
    user_id = PyUUID(claims.sub)
    tenant_id = claims.tenant_id

    if body.method == "webauthn":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="WebAuthn is not supported yet — use an authenticator app (TOTP).",
        )
    if body.method != "totp":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported MFA method: {body.method}",
        )

    try:
        user = await _service().verify(db, user_id=user_id, tenant_id=tenant_id, code=body.code)
    except MFAError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    # Issue the full session (DB-sourced roles → v2_jwt, ONE "mfa_verified" audit
    # row under the RLS context TOTPService.verify just set) + clear the challenge.
    response = await issue_session(db, user, operation="mfa_verified")
    response.delete_cookie(MFA_CHALLENGE_COOKIE)
    return response
