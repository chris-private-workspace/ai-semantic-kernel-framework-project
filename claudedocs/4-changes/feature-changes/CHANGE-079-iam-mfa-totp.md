# CHANGE-079: IAM Block C MFA — TOTP-only vertical

**Date**: 2026-06-13
**Sprint**: 57.112
**Scope**: platform_layer.identity (MFA) + api (mfa endpoints + auth gate) + frontend (auth pages) — C-12 IAM Block C

## Problem / Goal

The C-12 IAM epic had shipped invites (57.85) + credentials/password-login (57.86) + registration (57.87) + RBAC-JWT wiring (57.105), but MFA was still a frontend stub: `/auth/mfa` (Sprint 57.23) rendered a TOTP grid + a demo banner and called `POST /api/v1/mfa/verify`, which **404'd** (no backend module). Close the TOTP leg of `AD-Auth-MFA-Backend-IAM-Block-C-Phase58`: a real app-level TOTP second factor on the local-password login path.

## Solution

A complete TOTP vertical (enroll → confirm → verify) mirroring the 57.86 `CredentialsService` pattern.

**Backend**
- **Migration 0029** (`0029_user_mfa_totp.py`): `users.totp_secret VARCHAR(64) NULL` (base32 secret) + `users.mfa_enabled BOOLEAN NOT NULL DEFAULT false`. No new RLS (inherits `users`, the 0027 precedent).
- **`platform_layer/identity/mfa.py`** — `TOTPService` (stateless, module-level `_set_tenant` RLS, singleton): `enroll` (generate base32 secret + `otpauth://` URI, `mfa_enabled` stays false), `confirm` (verify first code → `mfa_enabled=true`), `verify` (validate at login; every miss → one generic `InvalidTOTPError` 401). `pyotp` (RFC 6238, `valid_window=1` for ±30s skew). Error hierarchy `MFAError(400)` → `InvalidTOTPError(401)` / `MFANotEnrolledError(400)` / `MFAAlreadyEnabledError(409)`.
- **`api/v1/mfa.py`** — `POST /api/v1/mfa/{enroll,enroll/confirm,verify}`. enroll/confirm require a full session; **verify is EXEMPT + challenge-gated** (`decode_mfa_challenge`). A valid TOTP swaps the challenge for a full `v2_jwt` session via the shared `auth.issue_session`.
- **`api/v1/auth.py`** — extracted `issue_session(db, user, *, operation)` (DRY: password-login non-MFA + `/mfa/verify`). Password-login now branches: `mfa_enabled` → a short-lived `mfa_pending` challenge cookie (`v2_mfa_challenge`, `roles=[]`) + `{"mfa_required":true}` (NO session) — else `issue_session`. `decode_mfa_challenge` + `_issue_mfa_challenge` + `MFA_CHALLENGE_COOKIE`.
- **`tenant_context.py`** — EXEMPT the EXACT `/api/v1/mfa/verify` (the dispatch is `path == prefix`, so `/mfa/enroll` stays full-session protected). **`core/config`** — `mfa_issuer_name` + `mfa_challenge_ttl_minutes`. **`api/main.py`** — mount the router. **`requirements.txt`** — `pyotp>=2.9,<3.0`.

**Frontend (thin)**
- Password-login page: a `mfa_required` branch → `navigate("/auth/mfa")` (the stashed redirect is preserved for `/auth/callback` after verify).
- `/auth/mfa` page: removed the demo banner (backend is real); real `errorInvalid` copy; WebAuthn Simulate surfaces the backend's honest 400 (`webauthnUnavailable`) — not a faked success; recovery link stays honestly disabled (deferred).
- i18n en + zh-TW `mfa.*` (symmetric keys).

## Design decisions

- **Challenge token** is a SEPARATE `v2_mfa_challenge` cookie (`roles=[]` + `mfa_pending:true`); the middleware treats ONLY `v2_jwt` as a session → a half-authenticated user reaches only the EXEMPT `/mfa/verify`. The full session is issued only after the TOTP checks out.
- **TOTP secret stored base32 plaintext** — a TOTP secret is a SHARED secret that must be readable to recompute codes (unlike a password it cannot be hashed). No at-rest encryption utility is wired in the codebase (Day-0 grep confirmed) → deferred `AD-MFA-Secret-At-Rest-Encryption`, documented (not a pretend-secure Potemkin).
- **Scope** (user decision 2026-06-13): TOTP-only. WebAuthn + recovery codes + the OIDC-callback gate + an enroll/setup UI are deferred slices.

## Verification

- Unit: `tests/unit/platform_layer/identity/test_mfa_service.py` (11). Integration: `tests/integration/api/test_mfa_endpoints.py` (9, incl. the full enroll→confirm→login→verify e2e). FE: `mfa.test.tsx` (9) + `password-login.test.tsx` (5).
- Gates: mypy `src` 0/363 · black/isort/flake8 0 (full `src tests`) · run_all 10/10 (wire count 24 unchanged) · full pytest **2546 passed + 5 skipped** (+20, 0 del) · Vitest **840** (+3) · mockup-fidelity 51 · build ✓.
- **Drive-through (real UI :3007 + fresh backend PID 25896 + real Postgres; zero dev-login)** — ALL 3 legs PASS:
  - **Leg A (enroll, API-driven — no enroll UI by design)**: real `POST /mfa/enroll` → secret `5PONG…M7CT` + `otpauth://` URI; `POST /mfa/enroll/confirm` (pyotp code) → `mfa_enabled=true`.
  - **Leg B (login success, real UI)**: password-login (`mfa-dt` / `mfauser@dt.test`) → `{mfa_required}` → `/auth/mfa` → live TOTP `471919` → full `v2_jwt` → `/auth/callback` → authenticated `/chat-v2` (header "acme-prod · user"). Screenshots `artifacts/dt57112-{1,4}-*.png`.
  - **Leg C (wrong code)**: `000000` → inline "That code didn't match…" error, stays on `/auth/mfa`. `artifacts/dt57112-5-wrong-code-error.png`.

## Drive-through find (fixed same sprint)

The first wrong-code attempt **bounced to `/auth/login` (SSO)** instead of showing the inline error: the MFA page's `fetchWithAuth("/api/v1/mfa/verify", …)` omitted `{ redirectOn401: false }`, so `fetchWithAuth` treated the wrong-code 401 as a session expiry (`handleAuthExpired` → SSO redirect). The Vitest mocks `global.fetch` directly + jsdom no-ops `window.location`, so the unit tests passed — **only the real drive-through surfaced it**. Fixed: both `/mfa/verify` calls now pass `{ redirectOn401: false }` (the password-login page already did). Re-driven → wrong code stays on the page with the real error. (A textbook case for the Drive-Through Acceptance hard constraint.)

## Impact

Backend (new module + migration + 6 edits) + thin FE (2 pages + i18n). No loop.py / wire schema / codegen / new SSE event. Closes the TOTP leg of `AD-Auth-MFA-Backend-IAM-Block-C-Phase58`. Deferred: WebAuthn, recovery codes, OIDC-callback gate, secret at-rest encryption, enroll UI, login lockout.
