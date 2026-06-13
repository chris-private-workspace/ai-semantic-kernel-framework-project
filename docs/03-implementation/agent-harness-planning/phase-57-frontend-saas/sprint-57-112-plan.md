# Sprint 57.112 Plan — IAM Block C MFA (TOTP-only vertical): the local-password login path gains an app-level TOTP second factor — `users` gets a TOTP secret + an `mfa_enabled` flag, a new `TOTPService` (enroll → confirm → verify) mirrors the 57.86 `CredentialsService` pattern, three `POST /api/v1/mfa/*` endpoints, and a password-login MFA-gate (a short-lived `mfa_pending` challenge cookie replaces the full session JWT until the TOTP code is verified) — closing the MFA leg of the C-12 IAM epic and un-stubbing the already-shipped `/auth/mfa` frontend page

**Status**: Draft (pending user approval)
**Branch**: `feature/sprint-57-112-iam-mfa-totp`
**Base**: `main` HEAD `b4790043` (post-#286 merge)
**Slice**: IAM Block C MFA — the next C-12 leg after invites (57.85) + credentials/password-login (57.86) + registration (57.87) + RBAC-JWT wiring (57.105). Closes `AD-Auth-MFA-Backend-IAM-Block-C-Phase58` (next-phase-candidates §25). **TOTP-only** per user scope decision 2026-06-13 (AskUserQuestion: Option A — the complete TOTP vertical; WebAuthn + recovery codes are deferred to future C-12 spikes). The `/auth/mfa` frontend page already exists (Sprint 57.23) as a stub calling `POST /api/v1/mfa/verify`, which today returns 404 (no backend module). This sprint makes that endpoint real + adds the enrollment + login-gate it needs.
**Scope decisions**: (a) TOTP enroll + confirm + verify backend (a complete drivable vertical — a secret can be enrolled, activated, and used at login), NOT verify-only (verify-only with no enroll path = AP-4 Potemkin, rejected per the scope question). (b) The login MFA-gate is on the **local password-login path only** (57.86); the **OIDC callback gate is DEFERRED** (enterprise SSO typically enforces MFA at the IdP; gating the 302 redirect flow is a separate slice). (c) The MFA challenge uses a short-lived `mfa_pending` JWT (the existing `JWTManager.encode(extra=...)` seam) set as a SEPARATE `v2_mfa_challenge` cookie — NOT the full `v2_jwt` (which would be authz-effective) — so a half-authenticated user holds NO session until TOTP succeeds. (d) The frontend touch is thin: a `mfa_required` branch in the password-login handler + un-stub the `/auth/mfa` page (remove the demo banner, real error copy); enrollment has NO mockup UI → the enroll endpoints are driven via API for the drive-through, and an enroll/setup UI is a deferred FE slice. (e) WebAuthn stays the FE's "Simulate" stub (the `method="webauthn"` verify branch returns an honest 400 "not supported this slice") — NOT silently faked.

---

## 0. Background

The C-12 IAM epic has shipped four legs — invites (57.85), local credentials + password-login (57.86), self-service registration (57.87), and RBAC DB→JWT wiring (57.105). MFA is the remaining Block C leg. The `/auth/mfa` frontend (Sprint 57.23) shipped a TOTP 6-digit grid + a WebAuthn conic ring + a "Simulate" button + a visible demo banner ("MFA backend wire pending Phase 58+ IAM Block C — verify will return 501"); it calls `POST /api/v1/mfa/verify`, but no backend `mfa` module exists, so the call 404s today. This sprint builds the TOTP backend vertical that the FE already expects and wires the login-path gate that makes MFA actually enforced.

This is a **spike sprint** (new domain — MFA/TOTP has no prior code) → per `.claude/rules/sprint-workflow.md` §Step 5.5, Day 4 produces a design-note extract (`30-iam-mfa-spike.md`).

### Design decision (mirror the 57.86 credentials pattern; challenge-token gate; TOTP secret stored per the `password_hash` precedent; thin FE)

- **US-1 is "the TOTP service + its DB columns"**: `users` gains `totp_secret VARCHAR(64) NULL` (a base32 TOTP shared secret) + `mfa_enabled BOOLEAN NOT NULL DEFAULT false` (migration 0029, inherits the `users` RLS — no new table, no new policy, the `0027_user_password_hash` precedent). A NEW `platform_layer/identity/mfa.py::TOTPService` mirrors `CredentialsService` exactly: stateless class, a typed error hierarchy (`MFAError(400)` → `InvalidTOTPError(401, generic detail)` / `MFANotEnrolledError` / `MFAAlreadyEnabledError`), `_set_tenant(db, ...)` RLS before tenant-scoped queries, `append_audit` on state changes, and a module-level singleton (`get_mfa_service` / `maybe_get_mfa_service` / `set_mfa_service`). Three methods: `enroll` (generate secret + return the `otpauth://` provisioning URI; the secret is stored but `mfa_enabled` stays false until confirmed), `confirm` (verify the first code → flip `mfa_enabled=true`), `verify` (validate a code at login).
- **US-2 is "the endpoints + the login-gate"**: `api/v1/mfa.py` exposes `POST /api/v1/mfa/enroll` + `POST /api/v1/mfa/enroll/confirm` (both require a full session JWT — you enroll while logged in) + `POST /api/v1/mfa/verify` (the endpoint the FE already calls — challenge-gated, EXEMPT from the full-session middleware). The password-login handler (`auth.py`, 57.86) gains an MFA-gate: after the password verifies, if `user.mfa_enabled`, it issues a short-lived `mfa_pending` challenge JWT (`JWTManager.encode(..., roles=[], extra={"mfa_pending": True})`, ~5 min) as a `v2_mfa_challenge` cookie — and does NOT set `v2_jwt` — returning `{"mfa_required": true}`. `/mfa/verify` decodes the challenge cookie, checks `mfa_pending`, validates the TOTP via `TOTPService.verify`, and only then issues the FULL `v2_jwt` cookie (real roles via `RBACManager.get_user_role_codes`, the 57.105 pattern) + clears the challenge + returns `AuthMeResponse`.
- **The TOTP secret is stored as base32 text** (column `totp_secret`), mirroring how `password_hash` is a plain column — but UNLIKE a password (which is hashed because it is never recomputed), a TOTP secret is a SHARED secret that MUST be readable to compute codes, so it cannot be hashed. At-rest encryption (Fernet/app-key envelope) is the correct hardening but the codebase has no encryption-at-rest utility wired today (Day-0 confirms) → the spike stores base32 plaintext with a **documented deferred AD** (`AD-MFA-Secret-At-Rest-Encryption`), NOT a pretend-secure Potemkin. (Anti-enumeration is preserved differently: `verify` always returns one generic 401, and the user is already identified by the signed challenge token, so secret-column read is the only at-rest exposure.)
- **The challenge token is NOT authz-effective**: it carries `roles=[]` + `mfa_pending: true` and is in a SEPARATE cookie the tenant-context middleware does NOT treat as a session (only `v2_jwt` is the session cookie). A half-authenticated user can reach `/mfa/verify` (EXEMPT) and nothing else. The full `v2_jwt` is issued ONLY after TOTP succeeds.
- **Thin FE**: the password-login page gains a `mfa_required` branch (navigate to `/auth/mfa` instead of bootstrapping); the `/auth/mfa` page already calls `/mfa/verify` with `{method:"totp", code}` and navigates to `/auth/callback` on success → it needs only the demo banner removed + honest error copy (the cookie-based challenge flows automatically via `fetchWithAuth`). The WebAuthn tab's `method="webauthn"` path gets an honest 400 from the backend (not silently faked). Enrollment has NO mockup → enroll endpoints are API-driven for the drive-through; an enroll/setup UI is a deferred FE slice.
- **Rejected**: verify-only with no enroll (AP-4 Potemkin — no way to enroll); WebAuthn this slice (the FE conic-ring is Simulate-only — a real `navigator.credentials` ceremony + `py_webauthn` + a credential table is ~2× the surface, a separate spike); recovery codes + `/auth/mfa/recovery` (deferred Block C leg, `AD-Auth-MFA-Recovery-Page`); reusing the `v2_jwt` cookie for the challenge (it would be a partial session — security hole); OIDC-callback MFA-gate (the 302-redirect gate is a separate slice; SSO MFA is IdP-enforced); per-tenant MFA policy / enforce-MFA-org-wide (C3 Config 分層 territory); brute-force lockout on `/mfa/verify` (the existing `AD-Auth-PasswordLogin-Lockout` covers the login-attempt-throttle substrate — a shared follow-on).

### Ground truth (Day-0 head-start — 2 Explore recon agents + direct greps, file:line anchors on `main` HEAD `b4790043`; ALL re-verified in the formal Day-0 三-prong §checklist 0.1)

**DB / ORM (US-1):**
- **`users` ORM**: `infrastructure/db/models/identity.py:188-230` `class User(Base, TenantScopedMixin)`; columns id(:193)/email(:198)/display_name(:199)/external_id(:200)/`password_hash`(:204, `String(255)` nullable, the storage precedent)/status(:205)/preferences(:206)/created_at(:211)/updated_at(:216); `UniqueConstraint("tenant_id","email")` (:223). **NO mfa columns** → 0029 adds `totp_secret VARCHAR(64) NULL` + `mfa_enabled BOOLEAN NOT NULL DEFAULT false`.
- **Latest migration**: `migrations/versions/0028_sidechain_sessions.py` is the head → **0029** is next free. New-column precedent: `0027_user_password_hash.py` (`op.add_column("users", sa.Column("password_hash", sa.String(255), nullable=True))`, no new RLS — inherits the table). RLS two-policy + system-sentinel pattern (only if a NEW table — N/A here): `0026_invites.py:137-156`.
- **`TenantScopedMixin`** provides `tenant_id` + `idx_users_tenant`; `_set_tenant(db, str(tenant_id))` is the RLS-context helper used across the IAM services.

**Service + endpoint pattern (US-1 + US-2):**
- **`CredentialsService`** `platform_layer/identity/credentials.py` (~:54-164 per recon): error hierarchy `CredentialsError(status_code=400)` → `InvalidCredentialsError(401, generic detail)` (~:54-70); stateless `async def authenticate(db, *, tenant_code, email, raw) -> User` (~:80-118) — resolves tenant w/o RLS, `_set_tenant`, scoped `(tenant_id, email)` query, anti-enumeration `verify_password(raw, DUMMY_HASH)` on miss, single `InvalidCredentialsError()` for all failures; singleton `_service` + `get_credentials_service` / `maybe_get_credentials_service` / `set_credentials_service` (~:133-154). **Mirror this exactly for `TOTPService`.**
- **`passwords.py`** `platform_layer/identity/passwords.py` — `hash_password` / `verify_password` (bcrypt cost=12, `anyio.to_thread` offload, 72-byte guard) / `DUMMY_HASH`. (Not reused for TOTP — TOTP uses `pyotp` — but the same `platform_layer/identity/` home + module shape.)
- **`InvitesService` / `RegistrationService`** (`invites.py` / `registration.py`) — same stateless + `_set_tenant` + audit + singleton pattern; `RegistrationService` is the precedent for seeding a `Role` + `User` + WORM audit.
- **Auth endpoints** `api/v1/auth.py`: `router = APIRouter(prefix="/auth")` (:90); `_cookie_kwargs(*, max_age)` (:93-104, httpOnly + `cookie_secure` + SameSite=Lax); cookie names `_JWT_COOKIE = "v2_jwt"` (:114); `AuthMeUser/Tenant/Response` (:122-137); OIDC `_upsert_user_from_oidc` (:173+); `POST /auth/password-login` (~:475-529 per recon, `PasswordLoginRequest(tenant_code,email,password)` ~:467-472, EXEMPT, issues JWT via `RBACManager.get_user_role_codes` + `JWTManager().encode(roles=sorted({"user",*codes}), extra={...})` + `set_cookie(_JWT_COOKIE)` + `AuthMeResponse` body); `POST /auth/dev-login` (~:392-453); `GET /auth/callback` (~:236-330, OIDC, the DEFERRED gate site); `GET /auth/me` (~:346-380).
- **`JWTManager`** `platform_layer/identity/jwt.py:103-246`: `encode(*, sub, tenant_id, roles=(), expires_minutes=None, extra=None) -> str` (:133-170) — `extra` accepts non-reserved claims (`_RESERVED_CLAIMS = {sub,tenant_id,roles,iat,exp}` :112 → `mfa_pending` is allowed); `decode(token) -> JWTClaims` (:172-189) raising `JWTExpiredError`/`JWTInvalidError`; `JWTClaims.extra: dict` (:97) carries `mfa_pending`. `expires_minutes` override → the ~5-min challenge TTL.
- **Tenant-context middleware** `platform_layer/middleware/tenant_context.py` — `EXEMPT_PATH_PREFIXES` (the public-route allowlist password-login/dev-login/callback/register live on); `/api/v1/mfa/verify` MUST be added (challenge-gated, pre-session); `/api/v1/mfa/enroll*` must NOT (full-session required). `get_db_session` / `get_db_session_with_tenant` / `get_current_user` deps live here / in `auth.py`.
- **`RBACManager.get_user_role_codes(user_id, tenant_id, *, session)`** (`rbac.py`, 57.105) — the DB role→JWT claim source for the full `v2_jwt` issued post-TOTP.
- **`api/main.py`** — router mount site (`app.include_router(...)` for the v1 routers); `mfa` router added next to `auth` / `tenants` / `invites`.

**Frontend (thin — US-2):**
- **`/auth/mfa` page** `frontend/src/pages/auth/mfa/index.tsx` (~412 lines): TOTP 6-digit grid (submit ~:106 `POST /api/v1/mfa/verify {method:"totp", code}`) + WebAuthn conic ring + "Simulate" (~:127 `{method:"webauthn", simulated:true}`); on success navigates `/auth/callback` (~:115/:136); demo banner ("verify will return 501") + recovery link disabled. i18n `auth.json` `mfa.*` (~:105-123 en + zh-TW mirror) incl. `mfa.errorStubbed` / `mfa.demoBanner` (to be replaced with real error copy).
- **Password-login page** (57.86, `frontend/src/pages/auth/password-login/` per recon) — calls `POST /api/v1/auth/password-login`; on success `bootstrap()` + `consumePostLoginRedirect()`. Gains a `mfa_required` branch → navigate `/auth/mfa`.
- **`authService`** `frontend/src/features/auth/services/authService.ts` — `fetchWithAuth()` (cookie-carrying, the challenge flows automatically) + `setPostLoginRedirect`/`consumePostLoginRedirect` (~:68-76).
- **NO `/auth/mfa/recovery` route** (the recovery link is a `#recovery` anchor — deferred).

**Deps + baselines:**
- **`pyotp` NOT present** in `backend/pyproject.toml` / requirements (recon: no pyotp/webauthn/qrcode). Add `pyotp` (pure-python, stdlib-hmac TOTP — RFC 6238). `python-jose` (JWT) + `bcrypt` (57.86) already present.
- **Baselines (57.111 closeout)**: full pytest **2526+5skip** · wire count **24** (no new SSE event — MFA is REST, not loop-streamed) · FE Vitest **837** · mockup-fidelity **51** · mypy `src` **0/360**. Re-verify Day-0.
- **Design note next free = 30** (20-29 all taken: 20-iam-deep-dive + 20-subagent-child-loop, 21-23 IAM spikes, 24 multi-model, 25 verif-in-loop, 26 injection, 27 model-policy, 28 harness-policy, 29 handoff) → `30-iam-mfa-spike.md`. IAM design authority: `20-iam-deep-dive.md`.

### STALE / drift anchors to re-confirm in the formal Day-0 三-prong (§ checklist 0.1)

The exact `auth.py` password-login line range + its current JWT-issuance + cookie-set sequence (the gate inserts BEFORE the `set_cookie(v2_jwt)`) · the exact `EXEMPT_PATH_PREFIXES` declaration + whether it is prefix- or exact-match (so `/api/v1/mfa/verify` is exempt but `/api/v1/mfa/enroll` is not — if prefix-only on `/api/v1/mfa`, restructure or use an in-endpoint guard) · the `get_current_user` dependency shape (what it returns — `JWTClaims`? a `User`? — for the enroll endpoints) · whether an at-rest encryption utility exists (`EncryptedColumn` referenced in `.claude/rules/multi-tenant-data.md` — is it WIRED or aspirational? decides plaintext-vs-encrypted storage) · the `append_audit` signature + the WORM audit operation-name convention (`mfa_enrolled`/`mfa_confirmed`/`mfa_verified`) · the FE password-login success-handler exact location for the `mfa_required` branch + whether `fetchWithAuth` surfaces a 200-with-`mfa_required` vs needs a non-2xx · the `/auth/mfa` page's exact `POST /mfa/verify` call + how it reads the response (does it expect `AuthMeResponse`? a redirect? — align the verify response shape) · the `api/main.py` router-mount block + the `core/config` app-name/issuer for the `otpauth://` URI · `pyotp` import name + `TOTP.verify(code, valid_window=1)` API + `random_base32()` · baselines re-verify (pytest 2526+5skip / wire 24 / Vitest 837 / mockup 51 / mypy 0/360) · whether any existing auth/middleware test asserts `/api/v1/mfa` 404s (convert, never delete) · the migration `down_revision` head (= 0028) + the Alembic revision-id convention.

## 1. Sprint Goal

The local password-login path gains a real app-level TOTP second factor: a user can enroll an authenticator (the backend generates a base32 secret + an `otpauth://` URI, the user confirms with their first code to flip `mfa_enabled`), and thereafter password-login no longer issues a session directly — it issues a short-lived `mfa_pending` challenge, redirects to `/auth/mfa`, and the full `v2_jwt` session is granted ONLY after `POST /api/v1/mfa/verify` validates the TOTP code — all mirroring the 57.86 `CredentialsService` service+endpoint+migration pattern (a `TOTPService`, three `POST /api/v1/mfa/*` endpoints, migration 0029 on `users`), with a thin FE (a `mfa_required` branch + un-stubbing the existing `/auth/mfa` page), proven by a real drive-through (enroll a real user via the API + a `pyotp`-computed code, then drive the real UI: password-login → MFA challenge → TOTP → session). Closes `AD-Auth-MFA-Backend-IAM-Block-C-Phase58` (the TOTP leg; WebAuthn + recovery deferred).

## 2. User Stories

- **US-1**: 作為 platform，我希望 `users` 表加上 `totp_secret` + `mfa_enabled`（migration 0029，繼承 users RLS），並有一個 `TOTPService`（鏡像 57.86 `CredentialsService`：stateless + typed error 階層 + `_set_tenant` RLS + `append_audit` + singleton）提供 `enroll`（產生 base32 secret + `otpauth://` URI，存 secret 但 `mfa_enabled` 仍 false）/ `confirm`（驗第一個 code → `mfa_enabled=true`）/ `verify`（login 時驗 code，miss → 單一 generic 401），以便 TOTP 第二因子有完整的 enroll→confirm→verify 生命週期。
- **US-2**: 作為 platform，我希望 `api/v1/mfa.py` 暴露 `POST /api/v1/mfa/enroll` + `/enroll/confirm`（需 full session JWT）+ `POST /api/v1/mfa/verify`（challenge-gated、EXEMPT），且 password-login 在 `user.mfa_enabled` 時改發短命 `mfa_pending` challenge cookie（`v2_mfa_challenge`，roles=[]，不發 `v2_jwt`）並回 `{"mfa_required": true}`；`/mfa/verify` 驗 challenge + TOTP 後才發 full `v2_jwt`（real roles via `RBACManager.get_user_role_codes`）+ 清 challenge + 回 `AuthMeResponse`，以便 MFA 真正在 login 路徑被強制執行（半認證使用者持有零 session）。
- **US-3**: 作為 reviewer，我希望 drive-through 證明（真 UI :3007 + 真後端 + 真 DB，零 dev-login）：先用 enroll API（帶該 user 的 session JWT）+ `pyotp` 算出當下 code 完成 enroll→confirm（enroll UI 無 mockup → API 驅動，誠實），然後驅動真 UI 走完整 login：以該 user password-login → 後端回 `mfa_required` + 設 challenge cookie → FE 跳 `/auth/mfa` → 輸入 TOTP code → `/mfa/verify` → 發 full `v2_jwt` → `/auth/callback` → 登入成功（pages render real role）；錯誤 code → generic 401 顯示真實錯誤文案（非 stub 文案）。

## 3. Technical Specifications

### 3.0 Architecture (backend IAM vertical + thin FE; migration 0029 on `users`; NO new table / NO new SSE wire event / wire count 24 UNCHANGED; mirrors 57.86 credentials pattern)

```
infrastructure/db/migrations/versions/0029_user_mfa_totp.py (NEW): users + totp_secret VARCHAR(64) NULL + mfa_enabled BOOLEAN NOT NULL DEFAULT false (inherits users RLS — no new policy)
infrastructure/db/models/identity.py (EDIT): User + totp_secret + mfa_enabled mapped columns
platform_layer/identity/mfa.py (NEW): TOTPService (enroll/confirm/verify) + MFAError hierarchy + singleton — mirrors credentials.py
api/v1/mfa.py (NEW): POST /mfa/enroll (authed) + /mfa/enroll/confirm (authed) + /mfa/verify (challenge-gated, EXEMPT)
api/main.py (EDIT): mount the mfa router
api/v1/auth.py (EDIT): password-login MFA-gate (mfa_enabled → mfa_pending challenge cookie + {"mfa_required": true}, no v2_jwt); a shared _issue_session(...) helper if it de-dups the JWT+cookie+AuthMeResponse block
platform_layer/middleware/tenant_context.py (EDIT): EXEMPT /api/v1/mfa/verify (NOT /enroll)
core/config (EDIT if needed): MFA_ISSUER_NAME (otpauth label) + MFA_CHALLENGE_TTL_MINUTES (Day-0 pins settings vs module constants)
pyproject.toml (EDIT): + pyotp dependency
frontend/src/pages/auth/password-login/ (EDIT): mfa_required branch → navigate /auth/mfa
frontend/src/pages/auth/mfa/index.tsx (EDIT): remove demo banner; real error copy; webauthn → honest "not yet"
frontend/src/i18n/locales/{en,zh-TW}/auth.json (EDIT): mfa.* error/banner copy (symmetric keys)
wire schema / codegen / SSE events / compaction / loop.py: UNTOUCHED
```

### 3.1 TOTP service + DB columns (US-1)

- **Migration 0029** (`0029_user_mfa_totp.py`): `op.add_column("users", sa.Column("totp_secret", sa.String(64), nullable=True))` + `op.add_column("users", sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")))`; `down_revision="0028"`; downgrade drops both. No RLS policy (inherits `users` — the 0027 precedent). The `server_default` keeps existing rows valid.
- **ORM** (`identity.py`): `totp_secret: Mapped[str | None] = mapped_column(String(64))` + `mfa_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))` on `User`, placed after `password_hash` with a WHY comment (TOTP shared-secret, can't be hashed; at-rest encryption deferred — `AD-MFA-Secret-At-Rest-Encryption`).
- **`TOTPService`** (`mfa.py` NEW, mirror `credentials.py`): stateless; errors `MFAError(status_code=400)` → `InvalidTOTPError(401, "Invalid verification code")` / `MFANotEnrolledError(400)` / `MFAAlreadyEnabledError(409)`.
  - `async def enroll(db, *, user_id, tenant_id) -> EnrollResult`: `_set_tenant`; load user (scoped); if `mfa_enabled` → `MFAAlreadyEnabledError`; `secret = pyotp.random_base32()`; `user.totp_secret = secret`; build `otpauth_uri = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name=<MFA_ISSUER_NAME>)`; `append_audit(operation="mfa_enroll_started")`; return `EnrollResult(secret, otpauth_uri)` (frozen dataclass).
  - `async def confirm(db, *, user_id, tenant_id, code) -> None`: `_set_tenant`; load user; require `totp_secret` else `MFANotEnrolledError`; `pyotp.TOTP(secret).verify(code, valid_window=1)` else `InvalidTOTPError`; `user.mfa_enabled = True`; `append_audit(operation="mfa_enabled")`.
  - `async def verify(db, *, user_id, tenant_id, code) -> User`: `_set_tenant`; load user; require `mfa_enabled` + `totp_secret` else `InvalidTOTPError` (generic — no "not enrolled" leak at login); `TOTP.verify(code, valid_window=1)` else `InvalidTOTPError`; `append_audit(operation="mfa_verified")`; return user.
  - Singleton `get_mfa_service` / `maybe_get_mfa_service` / `set_mfa_service`.
- **`valid_window=1`** absorbs ±30 s clock skew (RFC 6238 standard tolerance). The secret is base32 (≤ 32 chars → fits `VARCHAR(64)`).

### 3.2 Endpoints + login MFA-gate (US-2)

- **`api/v1/mfa.py`** (NEW, `router = APIRouter(prefix="/mfa", tags=["mfa"])`):
  - `POST /mfa/enroll` (current-user dep, full session) → `TOTPService.enroll(db, user_id=<claims.sub>, tenant_id=<claims.tenant_id>)` → `EnrollResponse(secret, otpauth_uri)`. Errors map via `MFAError.status_code`.
  - `POST /mfa/enroll/confirm` (current-user dep) → body `{code}` → `TOTPService.confirm(...)` → `{"mfa_enabled": true}`.
  - `POST /mfa/verify` (EXEMPT, no session) → reads `v2_mfa_challenge` cookie → `JWTManager().decode` → require `extra["mfa_pending"] is True` (else 401) → body `{method, code}`; if `method == "webauthn"` → `400` honest "WebAuthn not supported in this release" (NOT faked); `method == "totp"` → `TOTPService.verify(db, user_id=<sub>, tenant_id=<tenant>, code=code)` → on success issue full `v2_jwt` (`RBACManager.get_user_role_codes` + `JWTManager().encode(roles=sorted({"user",*codes}), extra={email,...})` + `set_cookie(_JWT_COOKIE)`) + `response.delete_cookie("v2_mfa_challenge")` + return `AuthMeResponse`. The full-session issuance MIRRORS password-login's block (extract a shared `_issue_full_session(response, user, db) -> AuthMeResponse` helper in `auth.py` if it cleanly de-dups, else inline).
- **Password-login MFA-gate** (`auth.py`): after the password verifies + the user is loaded, branch on `user.mfa_enabled`:
  - `True` → `challenge = JWTManager().encode(sub=str(user.id), tenant_id=user.tenant_id, roles=[], expires_minutes=<MFA_CHALLENGE_TTL>, extra={"mfa_pending": True})`; `response.set_cookie("v2_mfa_challenge", challenge, **_cookie_kwargs(max_age=<ttl*60>))`; do NOT set `v2_jwt`; return `{"mfa_required": true}` (200). Audit `operation="password_login_mfa_challenge"`.
  - `False` → the existing full-session path (unchanged).
- **Middleware EXEMPT** (`tenant_context.py`): add `/api/v1/mfa/verify` to `EXEMPT_PATH_PREFIXES` (Day-0 confirms prefix vs exact; `/api/v1/mfa/enroll*` stays protected — if the allowlist is prefix-only on `/api/v1/mfa`, instead exempt the exact `/mfa/verify` or add an in-endpoint challenge guard so enroll is NOT inadvertently exposed).
- **Config**: `MFA_ISSUER_NAME` (default app name, the `otpauth://` issuer label) + `MFA_CHALLENGE_TTL_MINUTES` (default 5) — Day-0 pins `core/config.Settings` fields vs `mfa.py` module constants (mirror the 57.111 decision: internal tuning → module constants unless a tenant/env knob is needed; the issuer name is env-ish → likely `core/config`).

### 3.3 Frontend (thin — US-2) + drive-through enrollment (US-3)

- **Password-login page**: the success handler branches — if the response carries `mfa_required: true`, `navigate("/auth/mfa")` (preserve any `consumePostLoginRedirect` target across the hop); else the existing `bootstrap()` flow.
- **`/auth/mfa` page**: remove the demo banner; replace `mfa.errorStubbed` copy with a real invalid-code message; on a successful `/mfa/verify` (now returns `AuthMeResponse` + sets `v2_jwt`) keep the existing `navigate("/auth/callback")`. The WebAuthn tab's Simulate → surfaces the backend's honest 400 (or the tab is visibly marked "coming soon" per mockup-fidelity — Day-1 decides minimal honest treatment without inventing UI).
- **i18n** (`auth.json` en + zh-TW): update `mfa.*` strings (drop "501"/"stubbed"/demo-banner copy; add a real invalid-code message); keep en/zh-TW keys symmetric.
- **Drive-through enrollment** (US-3): the mockup has NO enroll/setup UI → the drive-through enrolls via the API: log in a test user (real password-login, pre-MFA), `POST /mfa/enroll` (carries the session cookie) → get the secret, compute the current code with `pyotp` in the dt script, `POST /mfa/enroll/confirm` → `mfa_enabled`. THEN the real-UI leg: log out, password-login as that user → `mfa_required` → `/auth/mfa` → enter the live TOTP → session. The enroll/setup UI is a deferred FE slice (`AD-MFA-Enroll-Setup-UI`).

### 3.4 What is explicitly NOT done

WebAuthn (the FE conic-ring is Simulate-only; real ceremony + `py_webauthn` + a `webauthn_credentials` table is a separate spike); recovery codes + `/auth/mfa/recovery` (`AD-Auth-MFA-Recovery-Page`); the OIDC-callback MFA-gate (SSO MFA is IdP-enforced; the 302 gate is a separate slice); per-tenant / org-wide enforce-MFA policy (C3 Config 分層); brute-force lockout on `/mfa/verify` (shared `AD-Auth-PasswordLogin-Lockout` substrate); TOTP-secret at-rest encryption (`AD-MFA-Secret-At-Rest-Encryption` — stored base32 plaintext this slice, documented); an enroll/setup UI (`AD-MFA-Enroll-Setup-UI` — no mockup); a new SSE wire event (MFA is REST, not loop-streamed — wire count 24 unchanged); QR-code image rendering (the `otpauth://` URI is returned; the FE/authenticator renders the QR — no server-side `qrcode` dep).

### 3.5 Validation (US-1..US-3)

Unit (backend, CI-safe): `TOTPService.enroll` generates a secret + valid `otpauth://` URI + leaves `mfa_enabled=false` · `confirm` flips the flag on a valid code / raises `InvalidTOTPError` on a bad code / `MFANotEnrolledError` with no secret / `MFAAlreadyEnabledError` when already on · `verify` passes a valid code / generic 401 on bad code / generic 401 when not enrolled (no leak) · `valid_window` skew tolerance · multi-tenant isolation (a tenant-A user's secret is invisible under tenant-B RLS — the Risk Class C autouse reset + an application-layer assertion if the test role is superuser). Endpoint (integration, TestClient): enroll requires a session (401 without) · verify is reachable with only the challenge cookie · verify rejects a missing/expired/non-`mfa_pending` challenge (401) · verify with a good code sets `v2_jwt` + returns `AuthMeResponse` + clears the challenge · `method="webauthn"` → 400 · password-login with `mfa_enabled` returns `{mfa_required:true}` + sets `v2_mfa_challenge` + does NOT set `v2_jwt` · password-login without MFA unchanged (regression). FE (Vitest): the password-login `mfa_required` branch navigates `/auth/mfa` · the mfa page submits the code + handles success/401. Gates: mypy strict 0 · run_all 10/10 (count 24; no codegen diff) · full pytest +N (0 del) vs 2526 · Vitest +N vs 837 · mockup-fidelity 51 holds (no oklch/CSS change — only banner removal + copy) · `loop.py` / wire / codegen UNTOUCHED.

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/infrastructure/db/migrations/versions/0029_user_mfa_totp.py` | NEW — add `users.totp_secret` + `users.mfa_enabled` (down_revision 0028; no new RLS — inherits users) |
| 2 | `backend/src/infrastructure/db/models/identity.py` | EDIT — `User` + `totp_secret` + `mfa_enabled` mapped columns (after `password_hash`, WHY comment) |
| 3 | `backend/src/platform_layer/identity/mfa.py` | NEW — `TOTPService` (enroll/confirm/verify) + `MFAError` hierarchy + `EnrollResult` + singleton (mirror `credentials.py`) |
| 4 | `backend/src/api/v1/mfa.py` | NEW — `POST /mfa/enroll` + `/enroll/confirm` (authed) + `/verify` (challenge-gated, EXEMPT); request/response Pydantic models |
| 5 | `backend/src/api/main.py` | EDIT — mount the `mfa` router |
| 6 | `backend/src/api/v1/auth.py` | EDIT — password-login MFA-gate (mfa_pending challenge cookie + `{"mfa_required":true}`); a shared `_issue_full_session` helper if it cleanly de-dups |
| 7 | `backend/src/platform_layer/middleware/tenant_context.py` | EDIT — EXEMPT `/api/v1/mfa/verify` (NOT `/enroll`) |
| 8 | `backend/src/core/config/__init__.py` | EDIT (Day-0 pins) — `MFA_ISSUER_NAME` + `MFA_CHALLENGE_TTL_MINUTES` (settings vs module constants) |
| 9 | `backend/pyproject.toml` | EDIT — add `pyotp` dependency |
| 10 | `frontend/src/pages/auth/password-login/index.tsx` (Day-0 confirms path) | EDIT — `mfa_required` branch → navigate `/auth/mfa` |
| 11 | `frontend/src/pages/auth/mfa/index.tsx` | EDIT — remove demo banner; real error copy; webauthn honest 400 surfacing |
| 12 | `frontend/src/i18n/locales/en/auth.json` + `zh-TW/auth.json` | EDIT — `mfa.*` copy (symmetric keys) |
| 13 | backend tests (NEW): `tests/unit/.../identity/test_mfa_service.py` + `tests/integration/api/test_mfa_endpoints.py` + password-login-gate regression (CONVERT any `/api/v1/mfa` 404 assertion) | NEW/CONVERT (0 deletions) |
| 14 | frontend tests (NEW): password-login `mfa_required` branch + mfa page submit (Vitest) | NEW |
| 15 | `docs/03-implementation/agent-harness-planning/30-iam-mfa-spike.md` | NEW — spike design note (8-point quality gate, §5.5) |
| 16 | `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md` | EDIT (if the MFA endpoints/challenge-token introduce a documented cross-category contract) |
| — | `loop.py` / wire schema / codegen artifacts / SSE events / compaction / a new DB table | **UNTOUCHED** |

## 5. Acceptance Criteria

1. `users` has `totp_secret` + `mfa_enabled` (migration 0029, inherits RLS, existing rows valid via `server_default`); `TOTPService` enroll→confirm→verify works (mirror 57.86 pattern: stateless + `_set_tenant` + typed errors + audit + singleton), `verify` returns a single generic 401 on any failure, multi-tenant isolation holds.
2. `POST /api/v1/mfa/{enroll,enroll/confirm,verify}` exist + mounted; enroll/confirm require a full session, verify is challenge-gated (EXEMPT, rejects missing/expired/non-`mfa_pending` challenge); a successful verify issues the full `v2_jwt` (real roles) + clears the challenge + returns `AuthMeResponse`; password-login with `mfa_enabled` returns `{mfa_required:true}` + sets ONLY the `v2_mfa_challenge` cookie (no `v2_jwt`); `method="webauthn"` → honest 400; non-MFA password-login unchanged.
3. Thin FE: the password-login page navigates to `/auth/mfa` on `mfa_required`; the `/auth/mfa` page submits the code, handles success (→ `/auth/callback`, real session) + 401 (real error copy, demo banner gone); en/zh-TW `mfa.*` keys symmetric.
4. Gates: mypy strict 0 · run_all 10/10 (count 24) · full pytest +N (0 del) vs 2526 · Vitest +N vs 837 · mockup-fidelity 51 holds.
5. Real drive-through PASS (zero dev-login): enroll a real user via the API (`/mfa/enroll` + a `pyotp`-computed code → `/mfa/enroll/confirm` → `mfa_enabled`), then the real-UI leg — password-login as that user → `mfa_required` → `/auth/mfa` → live TOTP code → full session → `/auth/callback` → pages render the real role; a wrong code → generic 401 + real error copy.
6. `AD-Auth-MFA-Backend-IAM-Block-C-Phase58` (TOTP leg) closed; spike design note 30 written (8-point gate); deferred ADs recorded (WebAuthn / recovery / OIDC-gate / at-rest-encryption / enroll-UI / lockout).

## 6. Deliverables

- [ ] US-1 TOTP service + migration 0029 + ORM columns + unit tests
- [ ] US-2 three `/api/v1/mfa/*` endpoints + password-login MFA-gate + middleware EXEMPT + integration tests + thin FE (password-login branch + un-stub mfa page + i18n) + Vitest
- [ ] US-3 drive-through PASS (API-enroll + real-UI login→challenge→TOTP→session; screenshots + observed-vs-intended)
- [ ] CHANGE-079 + spike design note 30 + closeout (retro Q1-Q7 + calibration + navigators + 17.md if contract changed + next-phase-candidates MFA-DONE + deferred ADs)

## 7. Workload Calibration

- Scope class **`iam-backend-spike` 0.65** (3rd data point — 57.87 registration ≈1.0 1st validation, 57.105 RBAC-JWT ≈0.95 2nd; per the matrix the row is "KEEP — proposed from 57.85/86 over-runs under medium-backend 0.80; 2 validations IN band"). This sprint is predominantly backend (service + endpoints + migration + login-gate) with a THIN FE (one branch + un-stub a page + i18n) → `iam-backend-spike` fits; the thin FE adds < ~15% and does not reclassify.
- **Agent-delegated: no** — parent-direct (the login-gate + challenge-token + RLS secret storage is security-sensitive auth code; a mistake is a real vuln, not a cosmetic miss); `agent_factor = 1.0`, 3-segment form.
- Bottom-up est ~14 hr (migration+ORM ~1 + `TOTPService` ~2.5 + endpoints ~2.5 + password-login gate + middleware ~2 + unit+integration tests ~2.5 + thin FE+i18n+Vitest ~1.5 + dt ~1 + design note 30 + closeout ~1) → class-calibrated commit ~9 hr (mult 0.65). Day 4 retro Q2 verifies (3rd `iam-backend-spike` data point; if ratio diverges > 30% flag for the matrix).

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| The middleware `EXEMPT_PATH_PREFIXES` is PREFIX-match on `/api/v1/mfa` → exempting verify accidentally exposes `/mfa/enroll` (a session-required endpoint becomes public) | Day-0 reads the exact match semantics; exempt the EXACT `/api/v1/mfa/verify` OR keep `/mfa` non-exempt and gate verify with an in-endpoint challenge-cookie guard (decode-or-401) — enroll MUST stay full-session |
| Reusing/contaminating the `v2_jwt` session cookie with the challenge → a half-authenticated session | Use a SEPARATE `v2_mfa_challenge` cookie with `roles=[]` + `mfa_pending:true`; the middleware only treats `v2_jwt` as a session; the full `v2_jwt` is set ONLY in `/mfa/verify` after TOTP |
| TOTP secret stored plaintext at rest (no encryption utility wired) | Document `AD-MFA-Secret-At-Rest-Encryption` (deferred); store base32 in `totp_secret`; note the column is the only at-rest exposure (the challenge token is signed, not the secret); a follow-on wraps it in Fernet/app-key if/when an encryption utility lands (Day-0 confirms none exists) |
| `pyotp` new dependency — supply-chain / version pin | pin `pyotp` to a current minor range in `pyproject.toml` (pure-python, stdlib hmac, RFC 6238 — small surface); Day-0 confirms it installs in the env |
| Clock skew → a valid code rejected | `TOTP.verify(code, valid_window=1)` (±30 s); a unit test pins the window |
| The candidate FE `/auth/mfa` page expects a response shape `/mfa/verify` doesn't return (it navigates to `/auth/callback` expecting a session) | Day-0 reads the page's exact response handling; `/mfa/verify` returns `AuthMeResponse` + sets `v2_jwt` so the existing navigate works; the demo banner removal is the only structural FE change |
| Existing tests assert `/api/v1/mfa` 404s (router didn't exist) | Day-0 greps the auth/middleware test suite; convert (Never-Delete), do not skip |
| Risk Class C — module-level singleton (`_mfa_service`) across TestClient event loops | autouse `reset_mfa_service` fixture (the 57.53/57.86 pattern); plus a `get_db_session` override covering the new MFA endpoints (Risk Class C reinforcement — a previously-DB-free path gaining a DB call) |
| Risk Class E — stale `--reload` backend masks the migration / new router at dt | clean no-reload restart + `Win32_Process` orphan sweep + startup probe + confirm `/api/v1/mfa/verify` is mounted (the 57.97/109/110 routine); run `alembic upgrade head` before the dt |
| password-login is EXEMPT + now branches → a regression in the non-MFA path | the integration suite keeps a non-MFA password-login green (regression) + a new MFA-gate case; the gate is a single `if user.mfa_enabled` branch BEFORE the existing issuance block |
| mockup-fidelity drift from touching the `/auth/mfa` page | only REMOVE the demo banner + swap copy (no oklch / no layout / no widget change); `check:mockup-fidelity` 51 must hold; computed-style unaffected |
| Multi-tenant: the test DB role is superuser → RLS-block untestable | the 57.85 D5 lesson — add an application-layer isolation assertion (a tenant-B `_set_tenant` cannot load a tenant-A user's `totp_secret`) alongside the RLS policy test |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- WebAuthn (real `navigator.credentials` ceremony + `py_webauthn` + a `webauthn_credentials` table + FE rework) — a separate C-12 spike.
- Recovery codes + `/auth/mfa/recovery` page (`AD-Auth-MFA-Recovery-Page`) — needs the recovery flow + (for email delivery) an email adapter that does not exist.
- OIDC-callback MFA-gate (SSO MFA is IdP-enforced; the 302-redirect gate is a separate slice).
- Per-tenant / org-wide enforce-MFA policy + a tenant MFA toggle (C3 Config 分層 territory).
- Brute-force lockout / rate-limit on `/mfa/verify` (the shared `AD-Auth-PasswordLogin-Lockout` Redis-counter substrate).
- TOTP-secret at-rest encryption (`AD-MFA-Secret-At-Rest-Encryption`) — stored base32 plaintext this slice, documented.
- An enroll/setup UI (`AD-MFA-Enroll-Setup-UI`) — no mockup exists; enroll is API-driven for the drive-through.
- Server-side QR-image rendering (the `otpauth://` URI is returned; the authenticator/FE renders the QR).
- The remaining `next-phase-candidates.md` map (Skills system, IAM Block B WorkOS SCIM/SAML, SOC 2 + SBOM, frontend mockup rebuild, non-Azure adapters).
