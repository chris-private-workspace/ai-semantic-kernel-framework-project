# 30 — IAM Block C MFA (TOTP) Spike Design Note

**Purpose**: Capture the verified design of the TOTP-only MFA vertical shipped in Sprint 57.112 — the `TOTPService` + 3 endpoints + the password-login challenge-token gate — as extracted from the real implementation (not pre-written).
**Category / Scope**: platform_layer.identity (MFA) + api + frontend / Phase 57 / Sprint 57.112 (C-12 IAM Block C, TOTP leg)
**Created**: 2026-06-13
**Status**: Active (TOTP leg SHIPPED; WebAuthn + recovery deferred)

> **Modification History**
> - 2026-06-13: Initial creation (Sprint 57.112) — extracted from the shipped TOTP vertical (8-point gate self-checked in retrospective Q6)

> **Lineage**: 21-iam-invites-spike → 22-iam-credentials-spike → 23-iam-registration-spike → (57.105 RBAC-JWT wiring) → **this** (the MFA leg). Mirrors the 57.86 `CredentialsService` service+endpoint+migration pattern.

---

## 1. Spike Summary

**US-1 (TOTP service + columns)**: `users` gains `totp_secret` (base32) + `mfa_enabled`; `TOTPService.enroll/confirm/verify` mirrors `CredentialsService` (stateless, `_set_tenant` RLS, generic-error verify, singleton). **VERIFIED.**

**US-2 (endpoints + login gate)**: `POST /api/v1/mfa/{enroll,enroll/confirm,verify}`; password-login issues an `mfa_pending` challenge cookie (NO session) when `mfa_enabled`; `/mfa/verify` swaps a valid TOTP for a full `v2_jwt` session. **VERIFIED.**

**US-3 (drive-through)**: real UI + real backend + real Postgres — enroll (API) → confirm → password-login (`mfa_required`) → TOTP → authenticated `/chat-v2`; wrong code → inline error. **VERIFIED (ALL 3 legs PASS).**

**Verified scope (this spike)**: TOTP enroll/confirm/verify; the challenge-token login gate on the local-password path; the thin FE (`mfa_required` branch + un-stubbed `/auth/mfa`).

**Deferred boundary (NOT verified — §6)**: WebAuthn; recovery codes; the OIDC-callback MFA gate; TOTP-secret at-rest encryption; an enroll/setup UI; login lockout.

---

## 2. Decision Matrix

| Decision | Options | Chosen | Why |
|----------|---------|--------|-----|
| **How does `/mfa/verify` identify the user pre-session?** | (a) short-lived signed `mfa_pending` JWT in a separate cookie · (b) user_id+tenant in the request body | **(a)** challenge cookie | The body is client-controlled (forgeable → verify any user's MFA). A signed JWT (`extra={"mfa_pending":True}`, `roles=[]`, ~5min) is tamper-proof + carries sub/tenant; the middleware treats ONLY `v2_jwt` as a session so the challenge reaches only the EXEMPT verify. |
| **Challenge cookie name** | reuse `v2_jwt` · separate `v2_mfa_challenge` | **separate** | Reusing `v2_jwt` would be a partial session (the middleware would authorize it for every route). A separate cookie holds zero session authority. |
| **TOTP secret at rest** | plaintext base32 · encrypted (Fernet/app-key) | **plaintext (documented deferred)** | A TOTP secret is a SHARED secret that must be readable to recompute codes (unlike a password it cannot be hashed). Day-0 grep confirmed NO encryption utility is wired (`EncryptedColumn` is aspirational). Building key-management infra exceeds a thin spike → `AD-MFA-Secret-At-Rest-Encryption`, the column documented as the only at-rest exposure (the challenge token is signed, not the secret). |
| **Which login paths gate?** | password-login only · + OIDC callback | **password-login only** | The local-password path is fully under our control; the OIDC 302-redirect gate is a separate slice + SSO MFA is typically IdP-enforced. |
| **Audit layer** | inside `TOTPService` · at the endpoint | **endpoint** | Keeps `TOTPService` a pure, audit-free, unit-testable service (the `CredentialsService` precedent); `issue_session` emits the `mfa_verified` row. |

---

## 3. Verified Invariants (file:line + how verified)

| # | Invariant | Anchor | Verification |
|---|-----------|--------|--------------|
| 1 | `users` has `totp_secret VARCHAR(64) NULL` + `mfa_enabled BOOLEAN NOT NULL DEFAULT false`; inherits `users` RLS | migration `0029_user_mfa_totp.py` · ORM `identity.py:205-217` | `alembic upgrade head` (0028→0029) + `downgrade -1` + re-upgrade roundtrip clean; `check_rls_policies` green |
| 2 | `TOTPService` mirrors `CredentialsService`: stateless, module-level `_set_tenant`, generic `InvalidTOTPError(401)` on every login miss, singleton | `platform_layer/identity/mfa.py` | `pytest tests/unit/platform_layer/identity/test_mfa_service.py` (11 pass) |
| 3 | `/mfa/verify` is EXEMPT + challenge-gated; `/mfa/enroll` is NOT (full session) | `tenant_context.py` EXEMPT exact `/api/v1/mfa/verify`; live probe verify→401 "MFA challenge required" / enroll→401 "Authorization Bearer token required" | `pytest tests/integration/api/test_mfa_endpoints.py::test_mfa_exempt_contract` + the drive-through routing probe |
| 4 | password-login `mfa_enabled` → `{mfa_required:true}` + `v2_mfa_challenge` cookie + NO `v2_jwt`; a valid TOTP → full `v2_jwt` via the shared `issue_session` | `auth.py` (`issue_session` / `_issue_mfa_challenge` / password-login branch) + `mfa.py::verify` | `pytest tests/integration/api/test_mfa_endpoints.py` (9 pass incl. full e2e) + drive-through Leg B |
| 5 | The challenge is non-authoritative (`roles=[]`, `mfa_pending:true`); only `v2_jwt` is a session | `auth.py:_issue_mfa_challenge` + `tenant_context.py:JWT_COOKIE_NAME="v2_jwt"` | the middleware reads only `v2_jwt`; a challenge holder 401s on every non-exempt route |
| 6 | Wire count 24 unchanged (MFA is REST, no SSE event); loop.py untouched | `run_all.py check_event_schema_sync` | run_all 10/10 |
| 7 | FE: a wrong-code 401 surfaces inline (NOT an SSO bounce) | `mfa/index.tsx` `fetchWithAuth(..., {redirectOn401:false})` | drive-through Leg C (re-driven after the D13 fix) |

**Full gate**: mypy `src` 0/363 · black/isort/flake8 0 (full `src tests`) · run_all 10/10 · full pytest 2546+5skip (+20, 0 del) · Vitest 840 (+3) · mockup-fidelity 51 · build ✓.

**Test fixtures**: `tests/unit/platform_layer/identity/test_mfa_service.py` (real Postgres `db_session`, pyotp-computed codes) + `tests/integration/api/test_mfa_endpoints.py` (httpx ASGITransport, `get_db_session` + `get_db_session_with_tenant` both overridden to the test session). No real-LLM (MFA is auth).

---

## 4. Cross-Category Contracts (17.md)

MFA is an api + platform_layer.identity surface — not an 11+1 harness category, so no new harness ABC. The challenge-token contract (`v2_mfa_challenge` cookie carrying `mfa_pending`; `auth.issue_session` shared by password-login + `/mfa/verify`) is identity-internal. Consistent with prior IAM spikes (21/22/23), which likewise did not add a 17.md row (identity is platform infrastructure, not a cross-category interface). **No 17.md change.**

---

## 5. Open Invariants (deferred — NOT verified this spike)

- **`AD-MFA-Secret-At-Rest-Encryption`** — `totp_secret` is base32 plaintext; encrypt at rest (Fernet/app-key) once an encryption utility exists.
- **WebAuthn** — the FE conic-ring is Simulate-only; a real `navigator.credentials` ceremony + `py_webauthn` + a `webauthn_credentials` table is a separate spike (the `/mfa/verify` `method="webauthn"` path returns an honest 400 today).
- **`AD-Auth-MFA-Recovery-Page`** — recovery codes + `/auth/mfa/recovery` (needs the recovery flow + email adapter).
- **OIDC-callback MFA gate** — SSO MFA is IdP-enforced; the 302-redirect gate is a separate slice.
- **`AD-MFA-Enroll-Setup-UI`** — no enroll/setup mockup exists; enroll is API-driven for the drive-through.
- **Login lockout** — brute-force throttle on `/mfa/verify` (the shared `AD-Auth-PasswordLogin-Lockout` Redis substrate).
- **Per-tenant / org-wide enforce-MFA policy** — C3 Config 分層 territory.

---

## 6. Rollback

- **Feature gate**: there is no env kill-switch (MFA is per-user via `users.mfa_enabled`); to disable for a user, set `mfa_enabled=false` (admin / DB). No tenant has MFA on by default (the column defaults false), so the change is inert until a user enrolls.
- **Full revert**: revert the 3 sprint commits (`f29ba434` Day 1 / `ca0694f2` Day 2 / `e7ef0d29` Day 3) + `alembic downgrade -1` (drops the 2 columns; downgrade tested). The FE falls back to the demo-banner stub (git history). ~1 hr.
- **Risk surface**: the `auth.py` `issue_session` extraction is behavior-preserving (87 auth/identity regression green); the password-login MFA-gate is a single `if user.mfa_enabled` branch BEFORE the existing issuance.

---

## 7. References

- `sprint-57-112-plan.md` / `sprint-57-112-checklist.md` — the sprint contract
- `claudedocs/4-changes/feature-changes/CHANGE-079-iam-mfa-totp.md` — the change record (incl. the D13 drive-through find)
- `22-iam-credentials-spike.md` — the `CredentialsService` pattern this mirrors
- `backend/src/platform_layer/identity/mfa.py` + `api/v1/mfa.py` + `api/v1/auth.py` — the implementation
- `.claude/rules/multi-tenant-data.md` — the tenant-context-per-query 鐵律
- `memory/feedback_drive_through_over_paper_metrics.md` — the Drive-Through-Acceptance hard constraint the D13 find validates
