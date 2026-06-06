# Sprint 57.86 — Checklist (C-12 IAM Block B/C: local credentials + password-login vertical spike)

**Plan**: `sprint-57-86-plan.md`
**Branch**: `feature/sprint-57-86-credentials-password-login` (from `main` `f61df966`)
**Closes**: `AD-Auth-Credentials-PasswordLogin-Phase58` (local-password leg of C-12 Block B/C). Register / MFA / lockout / strength-policy / recovery = follow-up slices (§9).

---

## Day 0 — Plan-vs-Repo Verify + Branch + Decisions

### 0.1 Day-0 verify (Explore two-pass three-prong + parent grep/read, main `f61df966`)
- [x] **Prong 1 (path)** — reusable infra confirmed: `jwt.py:103-237` (JWTManager HS256 encode), `auth.py:375-436` (dev-login JWT+cookie+AuthMeResponse template), `auth.py:81-126` (`_cookie_kwargs`/`AuthMeResponse`), `identity.py:116` (`Tenant.code String(64) unique`), `auth.py:251`/`:292` (tenant-by-code + roles `["user"]`), `tenant_context.py` EXEMPT_PATH_PREFIXES (per-subpath).
- [x] **Prong 2 (content)** — frontend wiring: `App.tsx:97-103`/`:38-45` (route + lazy), `pages/auth/dev/index.tsx:100-113` (POST→`bootstrap()`→`navigate(consumePostLoginRedirect())`), authStore.bootstrap→`fetchAuthMe()`; primitives `@/components/mockup-ui` + AuthShell, classes `.col/.input/.card` (reuse, no new CSS); i18n en/zh-TW `auth.json`; mockup `page-auth-extras.jsx` (AuthRegister/Invite/MFA) + `i18n.jsx`.
- [x] **Prong 3 (schema)** — `User` has NO credential column (`identity.py:187-225`); migration head `0026_invites` → next `0027` (exact down_revision read Day-1); `users` already RLS-enabled → no new policy.
- [x] **Drift findings** — D1 (no bcrypt dep + no password column → add both); D2 (57.85 accept drops password → wire it); D3 (dev-login uses query string → password-login uses JSON body); D4 (no lockout → carryover); D5 (bcrypt sync-blocking + 72-byte truncation → anyio offload + max_length=72).
- [x] **Design locked** (AskUserQuestion ×2, 2026-06-06): scope = **full slice + new login page** (+ mockup extension); tenant resolution = **tenant-code field** (`(tenant_code, email)`); hash = **bcrypt direct cost=12**. Defaults: `users.password_hash` nullable column (reuse RLS), endpoint EXEMPT, lockout deferred.
- [x] **go/no-go** — GO; Day-2-end cut-line (passwords+credentials+storage+tests); HTTP+frontend+mockup can carryover as `AD-PasswordLogin-Endpoint-Frontend-Wire` if Day-3 over-runs.

### 0.2 Branch + decisions
- [x] **Branch created** `feature/sprint-57-86-credentials-password-login` (from `main` `f61df966`)
- [x] **Decisions locked**: bcrypt cost=12 + anyio offload; `users.password_hash` nullable; `(tenant_code, email)` lookup; generic-401 for all failures + constant-time miss; JSON body (not query); JWT/cookie/AuthMeResponse mirror dev-login; new page + mockup `AuthPasswordLogin`; parent-direct (`agent_factor` 1.0).
- [x] **Day-0 commit** plan + checklist + progress.md Day 0 (`e57baa9d`)

---

## Day 1 — Schema + hashing util: bcrypt dep + `passwords.py` + `users.password_hash` + migration (US-1)

### 1.1 dependency + hashing util
- [x] **EDIT `backend/requirements.txt`** — added `bcrypt>=4.1,<5.0`; installed (bcrypt 4.3.0)
  - DoD: `python -c "import bcrypt"` OK ✅
- [x] **NEW `platform_layer/identity/passwords.py`** — `hash_password`/`verify_password` (bcrypt cost=12 + `anyio.to_thread.run_sync` offload; 72-byte truncate in both for deterministic version-independent behaviour; verify swallows malformed-hash `ValueError` → False). Pure (no DB).
  - DoD: mypy clean ✅

### 1.2 ORM + migration 0027
- [x] **EDIT `infrastructure/db/models/identity.py`** — `User.password_hash: Mapped[str | None] = mapped_column(String(255))` (nullable via Optional, no alias) + MHist
- [x] **Read `0026_invites.py` header** → `revision="0026_invites"` → `down_revision="0026_invites"`
- [x] **NEW `migrations/versions/0027_user_password_hash.py`** — `add_column`/`drop_column`; NO new RLS policy (inherits `users` RLS)
  - DoD: applied **both directions** on Docker DB (upgrade 0026→0027 → downgrade -1 → re-upgrade; `alembic current`=`0027_user_password_hash (head)`) ✅; `check_rls_policies` green ✅
- [x] **black + isort + flake8 + mypy src/** — clean (mypy 0/341; flake8 0; run_all 10/10)

---

## Day 2 — Service: CredentialsService + wire invite-accept + tests (US-1/US-2/US-3) — SAFE CUT-LINE

> Day 2 = new credentials module + invite-accept wiring + service/unit tests, ZERO HTTP/frontend/mockup. The credential lifecycle is proven at the service/DB layer BEFORE Day-3 wires the endpoint + page.

### 2.1 CredentialsService
- [ ] **NEW `platform_layer/identity/credentials.py`** — `CredentialsService`:
  - `set_password(db, *, user, raw)` — `user.password_hash = await hash_password(raw)` (caller's txn)
  - `authenticate(db, *, tenant_code, email, raw) -> User` — tenant-by-code (None→err); user by `(tenant_id, email)` under `set_config('app.tenant_id', tenant.id, true)` (None→err); `password_hash is None`→err; `verify_password` False→err; return user. **All failures = `InvalidCredentialsError`**; constant-time miss (dummy verify when absent).
  - Typed errors `CredentialsError` base + `InvalidCredentialsError`; lenient singleton `set_/get_/maybe_get_credentials_service` (endpoint uses `maybe_get… or CredentialsService()` — no lifespan wiring → no leak)
  - DoD: mypy clean; authenticate raises one error type for all miss modes

### 2.2 wire invite-accept password storage
- [ ] **EDIT `platform_layer/identity/invites.py`** — `accept(..., password: str | None = None)`; if provided → `await CredentialsService().set_password(db, user=user, raw=password)` (same txn); keep `password=None` working
- [ ] **EDIT `api/v1/invites.py`** — pass `password=body.password` to `accept`; `InviteAcceptRequest.password` add `max_length=72`; docstring "accepted-not-stored" → "hashed + stored"
  - DoD: existing `test_invites.py` stays green; accept with password persists a hash

### 2.3 unit/service tests + gate (SAFE CUT-LINE)
- [ ] **NEW `tests/unit/platform_layer/identity/test_passwords.py`** (~4) — hash≠raw / verify true / wrong false / bcrypt `$2b$12$` format + 72-char password verifies
- [ ] **NEW `tests/unit/platform_layer/identity/test_credentials_service.py`** (db_session, ~6) — set_password persists; authenticate success / wrong-password / unknown-email / no-hash-user / unknown-tenant all → `InvalidCredentialsError`
- [ ] **Extend `tests/integration/api/test_invites.py`** (in-place — 57.78 lesson) — accept stores `password_hash` (1-2)
- [ ] **black + isort + flake8 + mypy src/ + pytest** — clean; new tests green; full suite green
- [ ] **Cut-line checkpoint** — credentials provable at service/DB layer; OIDC path untouched; nothing HTTP/UI-wired yet

---

## Day 3 — Endpoint + exempt path + frontend page + mockup (US-2/US-3/US-4)

### 3.1 password-login endpoint
- [ ] **EDIT `api/v1/auth.py`** — `PasswordLoginRequest(tenant_code≤64, email≤256, password≤72)` + `POST /password-login`: `CredentialsService.authenticate` → on err `HTTPException(401, "Invalid credentials")` (generic) → on success `JWTManager().encode(sub,tenant_id,roles=["user"],extra={email})` + `JSONResponse(AuthMeResponse)` + `set_cookie(_JWT_COOKIE, **_cookie_kwargs(...))` (mirror dev-login `:419-436`); `append_audit("password_login")` best-effort on success
  - DoD: 200+cookie / 401 generic ✓
- [ ] **EDIT `platform_layer/middleware/tenant_context.py`** — add `/api/v1/auth/password-login` to `EXEMPT_PATH_PREFIXES`
  - DoD: exempt-path test (reachable w/o JWT) + non-exempt admin path still 401

### 3.2 integration tests (HTTP e2e)
- [ ] **NEW `tests/integration/api/test_password_login.py`** (`_build_app`, ~7) — seed-user-w/-password → 200 + `v2_jwt` cookie + AuthMeResponse + `/me` works; wrong-pw 401 / no-hash-user 401 / unknown-tenant 401 (all generic); **2-tenant isolation** (same email A+B); exempt-path; audit on success
  - DoD: 7/7 green; generic-401 identical status+body across modes

### 3.3 frontend page + route + i18n
- [ ] **NEW `frontend/src/pages/auth/password-login/index.tsx`** — AuthShell+Card + 3 Field (tenant code/email/password) + Button; submit `fetchWithAuth(POST JSON {tenant_code,email,password})` → ok `await bootstrap()`+`navigate(consumePostLoginRedirect(),{replace:true})` → !ok generic error (reuse DangerNote-style alert); footer link `/auth/login`. Reuse `.col`/`.input` (no new CSS / no new oklch)
- [ ] **EDIT `frontend/src/App.tsx`** — lazy `PasswordLoginPage` + `<Route path="/auth/password-login" .../>` (production, not dev-gated)
- [ ] **EDIT `frontend/src/i18n/locales/{en,zh-TW}/auth.json`** — `passwordLogin.*` (title/subtitle/tenantCode/email/password/submit/submitting/error/foot); zh-TW 繁中

### 3.4 mockup sync (fidelity honest)
- [ ] **EDIT `reference/design-mockups/page-auth-extras.jsx`** — `AuthPasswordLogin` component (mirror AuthInvite/AuthRegister; AuthShell+Card+3 fields+button)
- [ ] **EDIT `reference/design-mockups/i18n.jsx`** — `passwordLogin.*` copy
  - DoD: `diff styles.css styles-mockup.css` empty; `check:mockup-fidelity` oklch baseline unchanged (delta 0)

### 3.5 frontend test + gate
- [ ] **NEW `frontend/tests/unit/pages/auth/password-login.test.tsx`** (~4) — renders 3 fields / submit 200→bootstrap+navigate / submit 401→generic error no-navigate / empty-field guard
  - DoD: green; full Vitest green; lint(no `--silent`)+build+mockup-fidelity green

### 3.6 test-isolation (Risk Class C)
- [ ] **conftest singleton reset** — assess: CredentialsService uses lenient `maybe_get… or CredentialsService()` (no lifespan singleton → no leak, same as 57.85); confirm full suite no event-loop leak (likely N/A)

---

## Day 4 — Full sweep + design note + Closeout

### 4.1 Full sweep
- [ ] **Backend gates** — black/isort/flake8 0 + `mypy src/` 0 + `pytest` green + `run_all.py` 10/10 (`check_rls_policies`)
- [ ] **Frontend gates** — `npm run lint` (NO `--silent`) + `npm run build` + `npm run test` + `npm run check:mockup-fidelity` (oklch baseline unchanged)
- [ ] **Read all changed code** — final pass (passwords, credentials, migration, invite-accept wire, endpoint, exempt path, frontend page, mockup)
- [ ] **real-Azure smoke?** — N/A (no LLM in credentials path; e2e proven by unit+integration+frontend tests)

### 4.2 design note (SPIKE — §Step 5.5 mandatory)
- [ ] **NEW `docs/03-implementation/agent-harness-planning/22-iam-credentials-spike.md`** — extracted from shipped impl; 8-point gate all ✓ (self-check in retrospective)
- [ ] **17.md assess** — N/A vs add (likely N/A — identity not a registered 11+1 surface; same call as 57.84/57.85). Contract lives in design note + docstrings + CHANGE-053.

### 4.3 Closeout docs
- [ ] **CHANGE-053** in `claudedocs/4-changes/feature-changes/`
- [ ] **progress.md** Day 0-4 + **retrospective.md** Q1-Q7 (bcrypt offload + generic-401/enumeration + new-page mockup extension + design-note 8-point gate)
- [ ] **Checklist** all `[x]`/`[→]` (no deletions)
- [ ] **Calibration** record (medium-backend 0.80; agent_factor 1.0 parent-direct; ratio — **2nd greenfield-IAM data point**; if > 1.0 again → propose `iam-backend-spike` ~0.55-0.65)
- [ ] **AD status**: `AD-Auth-Credentials-PasswordLogin-Phase58` CLOSED; NEW `AD-Auth-PasswordLogin-Lockout-Phase58` + register/MFA/recovery/strength/login-link carryovers → next-phase-candidates.md
- [ ] **MEMORY subfile + pointer** + **CLAUDE.md lean** (Current Sprint + Last Updated)
- [ ] **Design note?** — YES (spike sprint — new IAM credentials domain; 8-point gate per §Step 5.5)

### 4.4 Ship
- [ ] **Commit mapping** Day-0 / Day-1 schema / Day-2 service+wire+tests / Day-3 endpoint+frontend+mockup / Day-4 closeout
- [ ] **Push + PR** (user-gated — explicit authorization required)
