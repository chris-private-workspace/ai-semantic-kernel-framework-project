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

## Day 3 — Thin FE + full gates + drive-through (US-3) + CHANGE-079 ✅

### 3.1 Thin FE (password-login branch + un-stub mfa page + i18n)
- [x] **password-login page**: `mfa_required` branch → `navigate("/auth/mfa")` (redirect preserved); else existing bootstrap
- [x] **`/auth/mfa/index.tsx`**: removed demo banner; `errorInvalid` copy; webauthn Simulate → honest 400 `webauthnUnavailable`; recovery link stays honestly disabled; **+ `redirectOn401:false` on both verify calls (D13 drive-through fix)**
- [x] **`auth.json` en + zh-TW**: dropped `demoBanner`/`errorStubbed`, added `errorInvalid`/`webauthnUnavailable`; symmetric keys
- [x] **Vitest**: password-login +1 (`mfa_required` → `/auth/mfa`) · mfa.test.tsx 7→9 (converted demo-banner + webauthn-200 → no-banner + webauthn-400; +TOTP verify 200/401)
  - DoD: ✅ `npm run lint` (no `--silent`) + `npm run build` clean; Vitest **840** (+3); `check:mockup-fidelity` **51 holds** (banner used `hitl-card` class, no oklch)

### 3.2 Full gate sweep
- [x] mypy `src` **0/363** · black/isort/flake8 **0** (full `src tests` CI-identical) · run_all **10/10** (count 24; `check_rls_policies`+`check_event_schema_sync`+`check_ap4_frontend_placeholder` green) · full pytest **2546+5skip** (+20, 0 del) · Vitest **840** (+3) · mockup-fidelity **51** · loop.py/wire diff empty

### 3.3 Drive-through (US-3 — real UI :3007 + fresh single-process backend PID 25896 + real Postgres; zero dev-login; Risk Class E clean restart)
- [x] **Live routing probe**: `/mfa/verify` no-cookie → 401 "MFA challenge required" (EXEMPT+gated); `/mfa/enroll` no-auth → 401 "Authorization Bearer token required" (non-exempt) → D1 proven in prod
- [x] **Enroll leg (API-driven — no mockup enroll UI)**: real `/mfa/enroll` → secret + otpauth URI → pyotp code → `/mfa/enroll/confirm` → `mfa_enabled=true`
- [x] **Login leg (real UI)**: password-login (`mfa-dt`/`mfauser@dt.test`) → `{mfa_required}` + challenge (no v2_jwt) → `/auth/mfa` → live TOTP → full `v2_jwt` → `/auth/callback` → authenticated `/chat-v2` (header "acme-prod · user"); **wrong code `000000` → inline "That code didn't match…" + stays (after D13 fix)**
- [x] Screenshots `artifacts/dt57112-{1,4,5}-*.png` + observed-vs-intended in progress.md; no dead control / no fixture masquerade
  - DoD: ✅ full login→challenge→TOTP→session drivable e2e on real UI+backend+DB; wrong-code shows real error
- [x] **D13 drive-through find FIXED**: MFA verify `fetchWithAuth` lacked `{redirectOn401:false}` → wrong-code 401 bounced to SSO; fixed + re-driven (gate-green ≠ usable — Drive-Through-Acceptance proof)

### 3.4 CHANGE-079
- [x] `claudedocs/4-changes/feature-changes/CHANGE-079-iam-mfa-totp.md` (1-page, incl. the D13 drive-through find)

---

## Day 4 — Closeout

### 4.1 Closeout
- [ ] retrospective.md Q1-Q7 + calibration (`iam-backend-spike` 0.65 3rd data point — record ratio vs 57.87/57.105; agent-delegated: no) + progress.md final
- [ ] **Spike design note `30-iam-mfa-spike.md`** (§5.5) — 8-point quality gate (section-header per US / file:line per claim / decision matrix — challenge-token vs body-id, plaintext-vs-encrypted secret / verification command / test fixture / open-invariant boundary / rollback path / 17.md cross-ref); record verified ratio in retro Q6
- [ ] Navigators: CLAUDE.md Current-Sprint row + Last-Updated; MEMORY.md quality pointer + memory subfile `project_phase57_112_iam_mfa_totp.md`; next-phase-candidates 57.112 carryover block (`AD-Auth-MFA-Backend-IAM-Block-C-Phase58` CLOSED TOTP leg + NEW deferred ADs: `AD-MFA-Secret-At-Rest-Encryption` / `AD-MFA-Enroll-Setup-UI` / WebAuthn + recovery + OIDC-gate remaining); sprint-workflow matrix `iam-backend-spike` 3rd data point; 17.md if a contract changed
- [ ] **Anti-pattern self-check** (esp. AP-4 Potemkin — verify enroll→confirm→verify is a REAL drivable vertical, not a verify-only stub; AP-2 — no dead control / honest webauthn 400)
- [ ] PR (push + open on user authorization)
