# Sprint 57.112 Progress — IAM Block C MFA (TOTP-only vertical)

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-112-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-112-checklist.md)

---

## Day 0 — 2026-06-13 — Plan-vs-Repo Verify + Branch

### Three-prong Day-0 verify (against `main` HEAD `b4790043`)

**Prong 1 — path verify**
- NEW files Glob-0 (confirmed absent): `api/v1/mfa.py` (Glob 0), `platform_layer/identity/mfa.py` (not in the identity dir listing), `migrations/versions/0029_*.py` (head is `0028_sidechain_sessions.py`), `30-iam-mfa-spike.md` (design notes 20-29 all taken → 30 free).
- EDIT files Glob-1 (confirmed present): `identity.py`, `auth.py`, `tenant_context.py`, `credentials.py`, `passwords.py`, `jwt.py`, `frontend/src/pages/auth/mfa/index.tsx`, `frontend/src/pages/auth/password-login/index.tsx`, `pyproject.toml`.
- Migration head = `0028` → next free `0029`. Design note next free = `30`.

**Prong 2 — content verify** (the load-bearing greps)
- **D1 (CRITICAL — resolves plan §8 risk-1)**: `tenant_context.py:161-163` EXEMPT match is `path == prefix or path.startswith(prefix + "/")` (exact-OR-prefix-with-slash). → Adding the EXACT string `/api/v1/mfa/verify` exempts ONLY verify (+ any `/verify/...` subpath we don't have); `/api/v1/mfa/enroll` does NOT match → stays full-session protected. **Plan's primary approach holds; no in-endpoint-guard variant needed.** Consequence: verify is EXEMPT → middleware does NOT set `request.state.tenant_id` → verify MUST use raw `get_db_session` + decode the challenge cookie for tenant_id/user_id + let `TOTPService.verify` do its own `_set_tenant` (mirrors password-login, also EXEMPT, which uses raw `get_db_session` + `CredentialsService` self-manages RLS).
- **D2 (CRITICAL — confirms plaintext-storage decision)**: grep `EncryptedColumn|Fernet|cryptography\.|\.encrypt\(` across `backend/src` = **0 files**. No at-rest encryption utility is wired (the `.claude/rules/multi-tenant-data.md` `EncryptedColumn` mention is aspirational, not implemented). → TOTP secret stored as base32 plaintext in `users.totp_secret` + a documented deferred AD `AD-MFA-Secret-At-Rest-Encryption`. NOT a pretend-secure Potemkin; consistent with how the codebase stores other credentials columns (the column is the only at-rest exposure; the challenge token is signed, not the secret).
- **D3 — mirror target confirmed**: `credentials.py` — module-level `_set_tenant(db, tid)` = `SELECT set_config('app.tenant_id', :tid, true)` (:121-128); error hierarchy `CredentialsError(status_code=400, detail=...)` class-attrs + `__init__(detail=None)` → `InvalidCredentialsError(status_code=401)` (:55-70); stateless service; singleton `_service` + `get_/maybe_get_/set_credentials_service` + `__all__` (:133-164). `TOTPService` mirrors this byte-for-byte in shape.
- **D7 — password-login gate insertion point**: `auth.py:475-529`. `user = await service.authenticate(...)` succeeds at :490-492; the full-session block is :496-528 (tenant lookup :496 → `RBACManager.get_user_role_codes` :497-499 → `roles = sorted({"user", *role_codes})` :500 → `JWTManager().encode(sub, tenant_id, roles, extra={"email"})` :502-507 → `append_audit(...)` :508-517 → `AuthMeResponse(...).model_dump` :518-522 → `JSONResponse` + `set_cookie(_JWT_COOKIE, ..., max_age=jwt_expires_minutes*60)` :523-528). → MFA-gate `if user.mfa_enabled:` inserts BETWEEN :492 and :496; the :496-528 block is extracted to a shared `_issue_full_session(db, user, *, operation) -> JSONResponse` reused by the non-MFA password-login path + `/mfa/verify`.
- **D8 — `get_db_session` (raw) already imported** in `auth.py` (callback :243, dev-login :396, password-login :478). verify uses it; enroll/confirm (non-exempt) read `request.state.user_id`+`tenant_id` (the `me` pattern :359-361) + `get_db_session_with_tenant`.
- **D9 — `append_audit` signature** (`auth.py:508-517`): `append_audit(db, *, tenant_id, operation, resource_type, resource_id, operation_data, user_id, operation_result)`. MFA audit done at the ENDPOINT layer (mirror password_login; keeps `TOTPService` a pure, audit-free, unit-testable service like `CredentialsService`).
- **D10 — JWT challenge claim**: `JWTManager.encode(*, sub, tenant_id, roles=(), expires_minutes=None, extra=None)` (`jwt.py:133-170`); `_RESERVED_CLAIMS = {sub,tenant_id,roles,iat,exp}` (:112) → `extra={"mfa_pending": True}` is ALLOWED; `expires_minutes` override → the ~5-min challenge TTL; `decode` → `JWTClaims.extra` carries `mfa_pending` (:97). The challenge is a separate `v2_mfa_challenge` cookie; the middleware only treats `v2_jwt` (`JWT_COOKIE_NAME`, :107) as a session → a challenge holder reaches only the EXEMPT `/mfa/verify`.
- **D11 — `_cookie_kwargs(*, max_age)`** (`auth.py:93-104`, httpOnly + `cookie_secure` + SameSite=Lax) reused for the challenge cookie (`max_age = ttl_minutes*60`).

**Prong 3 — schema verify** (DB in scope)
- `users` ORM (`identity.py:188-230`): id/email/display_name/external_id/`password_hash`(String(255) nullable, :204)/status/preferences/created_at/updated_at; `UniqueConstraint(tenant_id,email)` (:223). **NO `totp_secret`/`mfa_enabled`** → 0029 adds them.
- Add-column precedent `0027_user_password_hash.py` (no new RLS — inherits `users`); `users` is already RLS-enabled (migration 0009). 0029 `down_revision="0028"`; `server_default false` keeps existing rows valid.

### Drift findings summary
| ID | Finding | Implication |
|----|---------|-------------|
| D1 | EXEMPT is exact-OR-prefix-with-slash | exact `/api/v1/mfa/verify` exempts only verify; verify uses raw `get_db_session` + challenge-cookie tenant — **plan §8 risk-1 RESOLVED, no pivot** |
| D2 | No at-rest encryption utility exists | TOTP secret = base32 plaintext + `AD-MFA-Secret-At-Rest-Encryption` deferred (confirms plan) |
| D3 | `credentials.py` pattern (errors/`_set_tenant`/singleton) | `TOTPService` mirrors exactly |
| D7 | password-login gate point + full-session block | insert `if mfa_enabled` at :492-496; extract `_issue_full_session` helper |
| D8 | `get_db_session` raw imported | verify=raw+challenge; enroll/confirm=request.state+tenant dep |
| D9 | `append_audit` at endpoint layer | `TOTPService` stays audit-free + unit-testable |
| D10 | `encode(extra=)` allows `mfa_pending`; separate `v2_mfa_challenge` cookie | challenge is non-session; only reaches EXEMPT verify |
| D11 | `_cookie_kwargs(max_age=)` reusable | challenge cookie shares the httpOnly/secure/SameSite attrs |

### Go/no-go
**GO** — net scope shift < 20%; every finding CONFIRMS the plan (D1 resolves the only open design risk; D2 confirms the storage decision; D3/D7/D8/D9/D10/D11 give exact mirror anchors). No loop.py / wire / codegen touched. Proceeding to Day 1.

### Branch
- `feature/sprint-57-112-iam-mfa-totp` from `main` `b4790043` ✅ created.

---

## Day 1 — 2026-06-13 — Backend: TOTP service + DB columns (US-1) ✅

**Drift D12** (Day-1, dep-file): `pyproject.toml` declares `dependencies = []` (runtime deps live in `requirements.txt` per its header comment) → `pyotp>=2.9,<3.0` added to `requirements.txt` (after the 57.86 bcrypt block), NOT pyproject. Plan §4 FCL item 9 adjusted. pyotp smoke-tested: `random_base32()` → 32-char secret (fits VARCHAR(64)), `TOTP.now()` → 6-digit, `provisioning_uri()` → `otpauth://totp/...`.

**Shipped**:
- `0029_user_mfa_totp.py` — `users.totp_secret VARCHAR(64) NULL` + `users.mfa_enabled BOOLEAN NOT NULL DEFAULT false`; `down_revision="0028_sidechain_sessions"`; no new RLS (inherits `users`, the 0027 precedent). `alembic upgrade head` (0028→0029) + `downgrade -1` + re-upgrade roundtrip all clean.
- `identity.py` — `User.totp_secret` + `User.mfa_enabled` after `password_hash` (WHY: shared-secret can't be hashed; at-rest encryption deferred). `Boolean` already imported.
- `platform_layer/identity/mfa.py` (NEW) — `TOTPService` mirrors `credentials.py`: `MFAError(400)` → `InvalidTOTPError(401, generic)`/`MFANotEnrolledError(400)`/`MFAAlreadyEnabledError(409)`; `EnrollResult` frozen; `enroll`/`confirm`/`verify` (stateless, module-level `_set_tenant`, `valid_window=1`); singleton trio. Audit at endpoint layer (D9).
- `tests/unit/platform_layer/identity/test_mfa_service.py` (NEW) — 11 tests, **11 passed**.

**Gates (Day-1 partial)**: mypy `src` 0 on mfa.py · black/isort/flake8 0 (mfa.py + migration + ORM + test) · migration roundtrip OK · 11/11 unit pass (real Postgres `db_session`, docker up 33h healthy).

**Actual ~3.0 hr** (est ~3.5; ahead — the credentials.py mirror was a clean template).

---

## Day 2 — 2026-06-13 — Backend: endpoints + login MFA-gate (US-2) ✅

**Shipped**:
- `api/v1/mfa.py` (NEW) — 3 endpoints. enroll/confirm read `request.state.user_id/tenant_id` (the `me` pattern) + `get_db_session_with_tenant`; verify uses raw `get_db_session` + `decode_mfa_challenge` (EXEMPT). webauthn → honest 400. verify success → `issue_session` (full v2_jwt) + clears challenge.
- `auth.py` — extracted shared `issue_session(db, user, *, operation)` (DRY: password-login non-MFA + `/mfa/verify`) + `_issue_mfa_challenge` + `decode_mfa_challenge` + `MFA_CHALLENGE_COOKIE="v2_mfa_challenge"`; password-login MFA-gate inserted between authenticate-success and the session block (D7); JWT import += `JWTAuthError, JWTClaims`.
- `tenant_context.py` — EXEMPT exact `/api/v1/mfa/verify` (D1: `path==prefix` exact-match → `/enroll` stays full-session protected).
- `core/config` — `mfa_issuer_name` + `mfa_challenge_ttl_minutes`. `api/main.py` — mount mfa_router.
- `tests/integration/api/test_mfa_endpoints.py` (NEW) — 9 tests incl. the full enroll→confirm→login→verify e2e. **9 passed**.

**Design note**: the challenge token is a separate `v2_mfa_challenge` cookie (`roles=[]`, `mfa_pending:true`); the middleware treats ONLY `v2_jwt` as a session → a half-authed user reaches only the EXEMPT `/mfa/verify`. Both EXEMPT (`get_db_session`) + non-EXEMPT (`get_db_session_with_tenant`) endpoints work: the EXEMPT verify self-sets RLS via `TOTPService.verify._set_tenant`, then `issue_session` runs under that context (the password-login precedent).

**Gates (Day-2 partial)**: mypy `src` 0 (mfa.py+auth.py) · black/isort/flake8 0 · 9/9 MFA integration pass · **87 passed** auth+identity regression (the `issue_session` extraction + JWT import change are clean — no break) · loop.py/wire/codegen UNTOUCHED.

**Actual ~3.5 hr** (est ~4.5; ahead — the password-login pattern + shared `issue_session` extraction made the gate + verify clean).
