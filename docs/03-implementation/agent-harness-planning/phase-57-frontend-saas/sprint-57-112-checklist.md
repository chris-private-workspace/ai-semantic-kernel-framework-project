# Sprint 57.112 — Checklist (IAM Block C MFA, TOTP-only vertical: `users` + TOTP secret + `mfa_enabled`, a `TOTPService` (enroll→confirm→verify) mirroring the 57.86 `CredentialsService`, three `POST /api/v1/mfa/*` endpoints, and a password-login MFA-gate (`mfa_pending` challenge cookie → full `v2_jwt` after TOTP) — closes `AD-Auth-MFA-Backend-IAM-Block-C-Phase58` (TOTP leg); WebAuthn + recovery deferred)

[Plan](./sprint-57-112-plan.md)

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `b4790043`) — DONE, catalogued in progress.md D1-D11
- [x] **Prong 1 — path verify**: NEW files Glob-0 (`mfa.py` ×2 absent / `0029` head=0028 / `30-iam-mfa-spike.md` free); EDIT files Glob-1 present (`identity.py`/`auth.py`/`tenant_context.py`/`credentials.py`/`passwords.py`/`jwt.py`/FE mfa+password-login pages/`pyproject.toml`); migration `0029` free; design note `30` free
- [x] **Prong 2 — content verify**: D1 (EXEMPT exact-OR-prefix-with-slash → exact `/mfa/verify` exempts only verify; enroll stays protected; verify uses raw `get_db_session` + challenge cookie) · D2 (NO encryption utility → plaintext secret + deferred AD) · D3 (`credentials.py` mirror shape) · D7 (password-login gate point :492-496 + full-session block :496-528 → extract `_issue_full_session`) · D8 (`get_db_session` raw imported) · D9 (`append_audit` at endpoint) · D10 (`encode(extra={mfa_pending})` allowed + separate `v2_mfa_challenge` cookie) · D11 (`_cookie_kwargs` reusable) — all in progress.md
- [x] **Prong 3 — schema verify**: `users` has NO `totp_secret`/`mfa_enabled` (`identity.py:188-230`); `0027` add-column precedent (no RLS, inherits `users` RLS from 0009); `down_revision="0028"`; `server_default false` keeps existing rows valid
- [x] **Catalog drift** findings in progress.md Day 0 (D1-D11 + implications + plan §8 cross-ref)
- [x] **Go/no-go**: GO — every finding CONFIRMS the plan (D1 resolves §8 risk-1, no pivot); net scope shift < 20%

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-112-iam-mfa-totp` (from `main` `b4790043`)

---

## Day 1 — Backend: TOTP service + DB columns (US-1) ✅

### 1.1 Migration + ORM
- [x] **`requirements.txt`** (D12 — deps live here, NOT pyproject `dependencies=[]`): add `pyotp>=2.9,<3.0`; installs + smoke-tested (secret 32 chars, code 6-digit, `provisioning_uri` ok)
- [x] **`0029_user_mfa_totp.py`** (NEW): `op.add_column("users", totp_secret VARCHAR(64) NULL)` + `op.add_column("users", mfa_enabled BOOLEAN NOT NULL server_default false)`; `down_revision="0028_sidechain_sessions"`; downgrade drops both; file header
- [x] **`identity.py`**: `User` + `totp_secret: Mapped[str | None]` + `mfa_enabled: Mapped[bool]` (after `password_hash`, WHY comment — shared-secret can't be hashed; at-rest encryption deferred `AD-MFA-Secret-At-Rest-Encryption`); `Boolean` already imported (:51)
  - DoD: ✅ `alembic upgrade head` applied (0028→0029) + `downgrade -1` reverses + re-upgrade (roundtrip OK); existing rows valid via `server_default false`; mypy `src` 0 on the ORM edit

### 1.2 `TOTPService` (mirror `credentials.py`)
- [x] **`platform_layer/identity/mfa.py`** (NEW): `MFAError(status_code=400)` → `InvalidTOTPError(401, generic)` / `MFANotEnrolledError(400)` / `MFAAlreadyEnabledError(409)`; `EnrollResult` frozen dataclass; `TOTPService.enroll/confirm/verify` (stateless, module-level `_set_tenant` RLS, `pyotp` secret + `provisioning_uri`, `valid_window=1`); singleton `get_mfa_service`/`maybe_get_mfa_service`/`set_mfa_service`; file header + WHY. Audit deferred to endpoint layer (D9 — keeps service pure/testable like CredentialsService)
- [x] **Unit tests ADD (CI-safe) ×11** `tests/unit/platform_layer/identity/test_mfa_service.py`: enroll → secret + valid `otpauth://` + `mfa_enabled` false · enroll already-enabled → `MFAAlreadyEnabledError` · confirm valid → flips · confirm wrong → `InvalidTOTPError` · confirm no-enroll → `MFANotEnrolledError` · verify valid → User · verify wrong → generic 401 · verify not-enabled → generic 401 (no leak) · verify no-secret → generic 401 · `valid_window` prev-window code accepted (skew) · cross-tenant verify → `InvalidTOTPError` (id+tenant scope + RLS)
  - DoD: ✅ **11 passed**; mypy `src` 0 (mfa.py); black/isort/flake8 0

---

## Day 2 — Backend: endpoints + login MFA-gate (US-2) ✅

### 2.1 MFA endpoints + router mount
- [x] **`api/v1/mfa.py`** (NEW, `prefix="/mfa"`): `POST /enroll` (`request.state` user/tenant + tenant DB dep) → `EnrollResponse(secret, otpauth_uri)` · `POST /enroll/confirm` (`{code}`) → `{mfa_enabled:true}` · `POST /verify` (EXEMPT, raw DB + `decode_mfa_challenge`) — `webauthn` → honest 400 / `totp` → `TOTPService.verify` → `issue_session` (full `v2_jwt`) + `delete_cookie(MFA_CHALLENGE_COOKIE)` + `AuthMeResponse`; Pydantic models; `MFAError.status_code` map; audit at endpoint (enroll/confirm) / via `issue_session` (verify); file header
- [x] **`api/main.py`**: mounted `mfa_router` (next to `auth`); MHist 1-line
- [x] **`core/config`**: `mfa_issuer_name="IPA Platform"` + `mfa_challenge_ttl_minutes=5`; MHist 1-line

### 2.2 Password-login MFA-gate + middleware EXEMPT
- [x] **`auth.py`**: extracted shared `issue_session(db, user, *, operation)` (DRY — used by password-login non-MFA + `/mfa/verify`) + `_issue_mfa_challenge(user)` + `decode_mfa_challenge(request)` + `MFA_CHALLENGE_COOKIE`; password-login branches `if user.mfa_enabled` → challenge cookie + `{"mfa_required":true}` + audit `password_login_mfa_challenge`, else `issue_session`; JWT import += `JWTAuthError, JWTClaims`
- [x] **`tenant_context.py`**: EXEMPT exact `/api/v1/mfa/verify` (D1 — `path==prefix` match → `/enroll` stays protected); MHist 1-line
- [x] **Integration tests ADD ×9** `tests/integration/api/test_mfa_endpoints.py`: full flow enroll→confirm→login(mfa_required)→verify→session · password-login `mfa_enabled` → `{mfa_required:true}` + challenge set + NO `v2_jwt` · non-MFA login unchanged (regression) · verify no-challenge → 401 · verify non-`mfa_pending` challenge → 401 · verify wrong code → 401 · `webauthn` → 400 · enroll already-enabled → 409 · EXEMPT contract (`/mfa/verify` in, `/mfa/enroll` not). Both `get_db_session` + `get_db_session_with_tenant` overridden to test session; TOTPService stateless (no reset fixture, mirrors CredentialsService)
  - DoD: ✅ **9 passed**; **87 passed** auth+identity regression (password-login refactor clean); mypy `src` 0 (mfa.py+auth.py); black/isort/flake8 0; loop.py/wire/codegen UNTOUCHED

---

## Day 3 — Thin FE + full gates + drive-through (US-3) + CHANGE-079

### 3.1 Thin FE (password-login branch + un-stub mfa page + i18n)
- [ ] **password-login page**: `mfa_required` branch → `navigate("/auth/mfa")` (preserve redirect target); else existing bootstrap
- [ ] **`/auth/mfa/index.tsx`**: remove demo banner; real invalid-code copy; webauthn Simulate surfaces the honest 400 (or visibly "coming soon" per mockup — no invented UI); keep success `navigate("/auth/callback")`
- [ ] **`auth.json` en + zh-TW**: update `mfa.*` (drop 501/stubbed/demo copy; real invalid-code message); symmetric keys
- [ ] **Vitest ADD**: password-login `mfa_required` → navigate `/auth/mfa` · mfa page submit code → success/401 handling
  - DoD: `npm run lint` (NO `--silent`) + `npm run build` clean; Vitest +N vs 837; `npm run check:mockup-fidelity` **51 holds** (banner removal + copy only — no oklch/layout change)

### 3.2 Full gate sweep
- [ ] mypy `src` 0 · black/isort/flake8 0 (full `flake8 src/ tests/` CI-identical — re-run after MHist/header edits; 57.111 CI-escape lesson) · run_all 10/10 (count 24; no codegen diff; `check_llm_sdk_leak` + `check_event_schema_sync` green) · full pytest +N (0 del) vs 2526+5skip · Vitest +N vs 837 · mockup-fidelity 51 · `loop.py`/wire diff empty

### 3.3 Drive-through (US-3 — real UI :3007 + fresh single-process backend + real DB; zero dev-login; Risk Class E clean restart + `alembic upgrade head`)
- [ ] **Enroll leg (API-driven — no mockup enroll UI)**: real password-login a test user (pre-MFA) → `POST /mfa/enroll` (session cookie) → secret → `pyotp` compute current code → `POST /mfa/enroll/confirm` → `mfa_enabled=true` (DB-verified)
- [ ] **Login leg (real UI)**: log out → password-login as that user → backend `{mfa_required:true}` + `v2_mfa_challenge` set (no `v2_jwt`) → FE navigates `/auth/mfa` → enter the LIVE TOTP code → `/mfa/verify` → full `v2_jwt` set → `/auth/callback` → pages render the real role; a WRONG code → generic 401 + real error copy (banner gone)
- [ ] Screenshots + observed-vs-intended in progress.md (`artifacts/`); confirm no dead control / no fixture masquerade
  - DoD: full login→challenge→TOTP→session drivable end-to-end on real UI + real backend + real DB; wrong-code path shows real 401 copy

### 3.4 CHANGE-079
- [ ] `claudedocs/4-changes/feature-changes/CHANGE-079-iam-mfa-totp.md` (1-page)

---

## Day 4 — Closeout

### 4.1 Closeout
- [ ] retrospective.md Q1-Q7 + calibration (`iam-backend-spike` 0.65 3rd data point — record ratio vs 57.87/57.105; agent-delegated: no) + progress.md final
- [ ] **Spike design note `30-iam-mfa-spike.md`** (§5.5) — 8-point quality gate (section-header per US / file:line per claim / decision matrix — challenge-token vs body-id, plaintext-vs-encrypted secret / verification command / test fixture / open-invariant boundary / rollback path / 17.md cross-ref); record verified ratio in retro Q6
- [ ] Navigators: CLAUDE.md Current-Sprint row + Last-Updated; MEMORY.md quality pointer + memory subfile `project_phase57_112_iam_mfa_totp.md`; next-phase-candidates 57.112 carryover block (`AD-Auth-MFA-Backend-IAM-Block-C-Phase58` CLOSED TOTP leg + NEW deferred ADs: `AD-MFA-Secret-At-Rest-Encryption` / `AD-MFA-Enroll-Setup-UI` / WebAuthn + recovery + OIDC-gate remaining); sprint-workflow matrix `iam-backend-spike` 3rd data point; 17.md if a contract changed
- [ ] **Anti-pattern self-check** (esp. AP-4 Potemkin — verify enroll→confirm→verify is a REAL drivable vertical, not a verify-only stub; AP-2 — no dead control / honest webauthn 400)
- [ ] PR (push + open on user authorization)
