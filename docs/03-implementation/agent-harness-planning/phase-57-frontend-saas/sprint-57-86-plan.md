# Sprint 57.86 Plan — C-12 IAM Block B/C: local credentials + password-login vertical spike (store invite password + `POST /auth/password-login` + new login page) (closes AD-Auth-Credentials-PasswordLogin-Phase58)

**Branch**: `feature/sprint-57-86-credentials-password-login` (from `main` `f61df966`)
**Closes**: `AD-Auth-Credentials-PasswordLogin-Phase58` — the **local-password credentials leg** of C-12 IAM Block B/C. This is the SECOND vertical spike of C-12 (after 57.85 invites; per the thin-spike discipline: minimal self-contained slice → retrospective → extract design note; **NOT** a full Block B/C plan). Self-service tenant registration (`AD-Auth-Register-Backend-IAM-Block-B-Phase58`) + MFA (`AD-Auth-MFA-Backend-IAM-Block-C-Phase58`) + invite-email delivery + password-strength/lockout policy remain explicit out-of-scope follow-up slices (rolling — not pre-written).

---

## 0. Background

57.85 stood up the `invites` vertical slice (admin create → guest accept → User + role + audit). The accept endpoint accepts `{full_name, password}` (the shipped frontend contract) but the `password` is **accepted-but-not-stored** — there is no local-credential store (auth is OIDC/WorkOS + dev-login only). User split this credential leg to 57.86 (rolling). User picked 57.86 (2026-06-06) to continue "process all" of the C-area gaps.

**The critical fork (resolved Day-0 via AskUserQuestion)**: password-login has **no UI consumer in the mockup** — the login mockup is OIDC-only (no password field) and there is no password-login screen anywhere in `reference/design-mockups/`; the invite page has a password field but nothing logs in with it afterward. Storing a password with no verifier, a verifier with no UI, or inventing a mockup-absent login page each violates a platform hard constraint (約束 2 主流量驗證 / AP-4 Potemkin / Mockup-Fidelity). **User decision (2026-06-06)**: **full vertical slice + a new login page** — wire the invite-accept password into a real hash, add `POST /api/v1/auth/password-login`, build a NEW `/auth/password-login` frontend page (from the existing AuthShell + mockup-ui primitives, reusing existing CSS classes — zero new CSS), and **add a matching mockup component** so the canonical visual source-of-truth stays honest (deliberate, user-approved mockup extension — NOT a fidelity violation). Tenant resolution = **tenant-code field** (`(tenant_code, email)` lookup; email is per-tenant unique). Hash = **bcrypt direct, cost=12**.

**Day-0 ground-truth (Explore two-pass three-prong + parent grep/read, main `f61df966`)**:
- **Reusable infra (do NOT rebuild)**: `JWTManager().encode(sub, tenant_id, roles, extra)` HS256 (`platform_layer/identity/jwt.py:103-237`); `Tenant.code String(64) unique` (`infrastructure/db/models/identity.py:116`); dev-login is the mirrorable JWT+cookie+response template (`api/v1/auth.py:375-436` — `_JWT_COOKIE='v2_jwt'`, `_cookie_kwargs` httponly/secure=`settings.cookie_secure`/samesite=lax `:81-92`, returns `AuthMeResponse` `:110-126`); OIDC callback resolves tenant by `select(Tenant).where(Tenant.code==...)` (`:251`) + roles `["user"]` (`:292`); EXEMPT_PATH_PREFIXES per-subpath (`middleware/tenant_context.py` — `/api/v1/auth/login`,`/callback`,`/dev-login`,`/logout`,`/api/v1/invites`); frontend route block `App.tsx:97-103` + lazy `:38-45`; dev page flow `fetchWithAuth(POST)` → `await bootstrap()` → `navigate(consumePostLoginRedirect())` (`pages/auth/dev/index.tsx:100-113`); `authStore.bootstrap` → `fetchAuthMe()` GET `/me`; primitives `@/components/mockup-ui` (Card/Field/Button/Icon) + AuthShell, classes `.col/.row/.input/.card/.hr` (reuse — no new CSS); i18n en/zh-TW `auth.json` (top-level `login.*/invite.*/dev.*/mfa.*`); mockup `reference/design-mockups/page-auth-extras.jsx` (AuthRegister/AuthInvite/AuthMFA pattern) + `i18n.jsx`.
- **0 password/credential columns** on `User` (`identity.py:187-225`) → must add. **No bcrypt/passlib/argon2 dependency** → must add bcrypt. **Drift D1.**
- **57.85 `InvitesService.accept` has NO `password` param** (`invites.py:248-311`); the accept endpoint drops `body.password` (`api/v1/invites.py:181-192`). This sprint wires it. **Drift D2.**
- **dev-login passes creds as QUERY string** (`?tenant_code=&email=`); password MUST NOT follow that pattern (query strings are logged) → password-login uses a **JSON body**. **Drift D3.**
- **No rate-limit/lockout on auth** → brute-force throttle is a tracked carryover (NOT built this spike). **Drift D4 / Risk #5.**
- **bcrypt is sync/CPU-bound + truncates at 72 bytes** → offload via `anyio.to_thread.run_sync`; enforce `max_length=72` on password fields. **Drift D5 / Risk #4.**
- **Migration head = `0026_invites`** → next = `0027`. Exact `down_revision` confirmed Day-1 by reading the `0026` header.

---

## 1. Sprint Goal

Stand up the **local-credentials vertical slice** of IAM Block B/C end-to-end: add a bcrypt password-hash store on `users`, wire the 57.85 invite-accept `password` into a real hash (closing the accepted-not-stored gap), add a `POST /api/v1/auth/password-login` endpoint that authenticates `(tenant_code, email, password)` and issues the same JWT/cookie/response as dev-login (generic 401 on any failure — no enumeration), and build a NEW mockup-consistent `/auth/password-login` frontend page (+ a matching mockup component) that is the real main-flow consumer — so an invited user who set a password can sign back in with email + password, without regressing the OIDC path and without inventing a fidelity-violating UI.

## 2. User Stories

- **US-1**: As an invited user, I want the password I set on the invite-accept page to actually be stored (hashed), so it is not silently discarded. (wire `InvitesService.accept` → bcrypt hash → `users.password_hash`)
- **US-2**: As a returning user, I want to sign in with my tenant code + email + password and receive a session, so I can access the app without SSO. (`POST /auth/password-login` → JWT cookie + `AuthMeResponse`)
- **US-3**: As a security owner, I want password-login to fail with a single generic 401 for every failure mode (unknown tenant / unknown email / OIDC-only user with no password / wrong password), so the endpoint cannot be used to enumerate tenants or users. (generic-error contract + tests)
- **US-4**: As a user, I want a real `/auth/password-login` page (mockup-consistent) that posts my credentials over a JSON body and lands me in the app, so the feature has a genuine main-flow UI consumer (not a Potemkin). (new frontend page + route + mockup component + i18n)
- **US-5**: As a maintainer, I want unit + integration + frontend tests pinning the hash round-trip, the set-then-authenticate lifecycle, the generic-401 contract, 2-tenant isolation, and the page submit/error flow, so the slice is a verifiable real e2e.

## 3. Technical Specifications

### 3.0 Architecture

Two new files in `platform_layer/identity/` (the existing Identity range, alongside `jwt.py`/`auth.py`/`invites.py`): `passwords.py` (pure bcrypt hash/verify util, no DB) + `credentials.py` (`CredentialsService` — DB-touching set/authenticate). The `password_hash` lives as a nullable column on the existing `users` table (lean monolithic identity convention; `users` is already RLS-enabled so NO new policy is needed). The password-login HTTP surface is co-located in the existing `api/v1/auth.py` (next to login/callback/dev-login/logout), EXEMPT from the tenant middleware (pre-JWT). The new frontend page mirrors the dev-login page structure (POST → `bootstrap()` → redirect) but with real credentials over a JSON body. LLM neutrality: N/A. Multi-tenant: password-login resolves the tenant by `Tenant.code` then the user by `(tenant_id, email)`; the JWT carries `tenant_id` exactly as dev-login/OIDC.

**Security divergences from dev-login (deliberate)**: dev-login is a dev-only fixture (no creds, query-string params, auto-creates the tenant, grants all roles). password-login is a real auth path: (a) credentials in a **JSON body** (never query string); (b) **no tenant auto-create** (unknown code → generic 401); (c) **real user lookup + bcrypt verify** (not an upsert); (d) roles `["user"]` (not all-roles); (e) **single generic 401** for all failure modes (no "user not found" vs "wrong password" distinction). password-login mirrors dev-login ONLY for the JWT-encode + cookie-set + `AuthMeResponse` success shape.

### 3.1 `users.password_hash` + migration `0027` (US-1/US-2) — schema

- EDIT `infrastructure/db/models/identity.py` `User`: add `password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)` (nullable — OIDC-only users have none). No alias (direct column name; `users` has no alias pattern, unlike `tenants.meta_data`→`"metadata"`).
- NEW `infrastructure/db/migrations/versions/0027_user_password_hash.py` (`down_revision` = `0026_invites` revision id, confirmed Day-1 by reading the `0026` header): `op.add_column("users", sa.Column("password_hash", sa.String(255), nullable=True))` + `downgrade` `op.drop_column`. **No new RLS policy** (the `password_hash` column inherits the existing `users` per-tenant RLS — confirm `check_rls_policies` stays green; it checks table-level ENABLE + policy presence, already satisfied for `users`). Apply both directions on Docker DB.

### 3.2 `passwords.py` util + `CredentialsService` (US-1/US-2/US-3) — NEW

- NEW `platform_layer/identity/passwords.py`: `async def hash_password(raw: str) -> str` + `async def verify_password(raw: str, hashed: str) -> bool`, each wrapping the sync `bcrypt.hashpw`/`bcrypt.checkpw` in `await anyio.to_thread.run_sync(...)` (offload the CPU-bound/blocking call off the event loop). cost=12 (`bcrypt.gensalt(rounds=12)`). UTF-8 encode; the API layer enforces `max_length=72` so bcrypt's 72-byte truncation never silently bites. Pure (no DB) → trivially unit-testable.
- NEW `platform_layer/identity/credentials.py` `CredentialsService`:
  - `async def set_password(self, db, *, user, raw) -> None`: `user.password_hash = await hash_password(raw)` (mutate the passed ORM user in the caller's txn). Used by invite-accept (US-1).
  - `async def authenticate(self, db, *, tenant_code, email, raw) -> User`: resolve `Tenant` by `code` (None → raise `InvalidCredentialsError`); resolve `User` by `(tenant_id, email)` under `set_config('app.tenant_id', tenant.id, true)` (None → `InvalidCredentialsError`); if `user.password_hash is None` → `InvalidCredentialsError` (OIDC-only user); `await verify_password(raw, user.password_hash)` False → `InvalidCredentialsError`; return user. **Every failure raises the SAME error type** (the endpoint maps it to a single generic 401) — no enumeration. Optional constant-time miss: when the user/hash is absent, still run one `verify_password` against a dummy hash to flatten timing (decided Day-2; cheap, documented).
  - Typed errors co-located: `CredentialsError` base + `InvalidCredentialsError`. Module-level **lenient singleton** (`set_/get_/maybe_get_credentials_service`; endpoint uses `maybe_get_credentials_service() or CredentialsService()` — NO lifespan wiring → no leak, mirrors 57.85 invites; deliberately avoids the 57.84 Day-3 singleton-leak class).

### 3.3 Wire invite-accept password storage (US-1) — EDIT

- EDIT `platform_layer/identity/invites.py` `InvitesService.accept`: add `password: str | None = None` param; after creating the User + before/with the audit, if `password` provided → `await CredentialsService().set_password(db, user=user, raw=password)` (same txn). (Keep the method working with `password=None` so existing service callers/tests don't break.)
- EDIT `api/v1/invites.py` accept endpoint: pass `password=body.password` to `accept(...)`; add `max_length=72` to `InviteAcceptRequest.password`. The endpoint contract + frontend payload are unchanged (the field was already sent). Update the docstring (was "accepted but not stored" → "hashed + stored").

### 3.4 `POST /api/v1/auth/password-login` endpoint (US-2/US-3) — EDIT `api/v1/auth.py`

- NEW request model `PasswordLoginRequest(BaseModel)`: `tenant_code: str (min 1, max 64)`, `email: EmailStr | str (min 1, max 256)`, `password: str (min 1, max 72)`.
- NEW `@router.post("/password-login")` (EXEMPT — pre-JWT): body → `CredentialsService.authenticate(db, tenant_code=…, email=…, raw=…)`; on `InvalidCredentialsError` → `HTTPException(401, "Invalid credentials")` (single generic message); on success → resolve roles (`["user"]` baseline, matching OIDC callback) → `JWTManager().encode(sub=str(user.id), tenant_id=user.tenant_id, roles=roles, extra={"email": user.email})` → `JSONResponse(AuthMeResponse(...).model_dump(mode="json"))` + `response.set_cookie(_JWT_COOKIE, jwt, **_cookie_kwargs(max_age=...))` (mirror dev-login `:419-436`). Audit: `append_audit(user.tenant_id, "password_login", {...})` best-effort (success only; failures are intentionally not user-attributable — log generically).
- EDIT `platform_layer/middleware/tenant_context.py`: add `/api/v1/auth/password-login` to `EXEMPT_PATH_PREFIXES` (the user has no JWT yet). A test asserts the prefix is present + that non-exempt admin paths are unaffected.

### 3.5 Frontend `/auth/password-login` page + route + i18n (US-4) — NEW + EDIT

- NEW `frontend/src/pages/auth/password-login/index.tsx`: `AuthShell` + `Card` + 3 `Field`s (tenant code / email / password) + primary `Button`; reuse classes `.col`/`.input` (zero new CSS). Submit → `fetchWithAuth("/api/v1/auth/password-login", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({tenant_code, email, password})})`; on `res.ok` → `await bootstrap()` → `navigate(consumePostLoginRedirect(), {replace:true})` (mirror dev page); on `!res.ok` → generic error surface (reuse the invite page's `DangerNote`-style inline alert; no new widget). Footer link back to `/auth/login` (OIDC) like the invite page footer.
- EDIT `frontend/src/App.tsx`: lazy import `PasswordLoginPage` + `<Route path="/auth/password-login" element={<PasswordLoginPage />} />` (production route — NOT dev-gated, unlike `/auth/dev`).
- EDIT `frontend/src/i18n/locales/{en,zh-TW}/auth.json`: add `passwordLogin.*` namespace (title/subtitle/tenantCode/email/password/submit/submitting/error/foot). zh-TW translated (繁中, per locale-file-is-translated rule).

### 3.6 Mockup sync (US-4) — EDIT `reference/design-mockups/`

- EDIT `reference/design-mockups/page-auth-extras.jsx`: add an `AuthPasswordLogin` component mirroring `AuthInvite`/`AuthRegister` (AuthShell + Card + 3 fields + button; same inline-style/class vocabulary). This is the deliberate, user-approved extension of the canonical source so the production page has a real mockup parent (fidelity stays honest).
- EDIT `reference/design-mockups/i18n.jsx`: add the matching `passwordLogin.*` copy.
- `styles-mockup.css` UNCHANGED (reuse existing classes) → `diff reference/design-mockups/styles.css frontend/src/styles-mockup.css` stays empty; `check:mockup-fidelity` oklch baseline **unchanged** (delta 0). The new page is built from the same primitives as its mockup → parity by construction.

### 3.7 Tests (US-5)

- Unit `tests/unit/platform_layer/identity/test_passwords.py` (~4): hash≠raw / verify round-trip true / wrong password false / hash is bcrypt-format (`$2b$12$…`) + idempotent-verify across two hashes of same pw (salts differ).
- Unit `tests/unit/platform_layer/identity/test_credentials_service.py` (db_session, ~6): set_password persists hash; authenticate success returns user; wrong password → `InvalidCredentialsError`; unknown email → same error; OIDC-only user (no hash) → same error; unknown tenant_code → same error.
- Integration `tests/integration/api/test_password_login.py` (`_build_app` + committed/seed, ~7): e2e seed user w/ password (or invite-accept w/ password) → `POST /password-login` 200 + `v2_jwt` cookie set + `AuthMeResponse` shape; wrong password → 401 generic; OIDC-only user → 401 generic; unknown tenant → 401 generic; **2-tenant isolation** (same email in tenant A + B with different passwords → each only authenticates with its own); exempt-path contract (password-login reachable w/o JWT); audit row on success.
- Extend `tests/integration/api/test_invites.py` (or unit, in-place — Sprint 57.78 lesson): assert invite-accept now stores `password_hash` (1-2 tests).
- Frontend `frontend/tests/unit/pages/auth/password-login.test.tsx` (Vitest, ~4): renders 3 fields; submit 200 → `bootstrap`+navigate; submit 401 → generic error, no navigate; empty-field guard (button disabled / no fetch).

### 3.8 Lint / validation

`black + isort + flake8 + mypy src/` 0 + `run_all.py` 10/10 (esp. `check_rls_policies` — `users` already covered; confirm no regression). Frontend `npm run lint` (NO `--silent`) + `npm run build` + `npm run test` + `npm run check:mockup-fidelity`. Full format chain pre-commit. (No `check_llm_sdk_leak` concern — no LLM.)

## 4. File Change List

**Code — NEW (4)**:
1. `backend/src/platform_layer/identity/passwords.py` — bcrypt `hash_password`/`verify_password` (anyio threadpool, cost=12)
2. `backend/src/platform_layer/identity/credentials.py` — `CredentialsService` (set_password/authenticate) + typed errors + lenient singleton
3. `backend/src/infrastructure/db/migrations/versions/0027_user_password_hash.py` — ALTER users ADD password_hash
4. `frontend/src/pages/auth/password-login/index.tsx` — NEW page

**Code — EDIT (6)**:
5. `backend/requirements.txt` — add `bcrypt` (pin a current major)
6. `backend/src/infrastructure/db/models/identity.py` — `User.password_hash` column
7. `backend/src/platform_layer/identity/invites.py` — `accept(..., password=None)` → hash+store
8. `backend/src/api/v1/invites.py` — pass `body.password`; `password` `max_length=72`; docstring
9. `backend/src/api/v1/auth.py` — `PasswordLoginRequest` + `POST /password-login` endpoint
10. `backend/src/platform_layer/middleware/tenant_context.py` — exempt `/api/v1/auth/password-login`

**Frontend — EDIT (3)**:
11. `frontend/src/App.tsx` — lazy import + route
12. `frontend/src/i18n/locales/en/auth.json` — `passwordLogin.*`
13. `frontend/src/i18n/locales/zh-TW/auth.json` — `passwordLogin.*` (繁中)

**Mockup — EDIT (2)**:
14. `reference/design-mockups/page-auth-extras.jsx` — `AuthPasswordLogin` component
15. `reference/design-mockups/i18n.jsx` — `passwordLogin.*` copy

**Tests (4 NEW + 1 extend)**:
16. `backend/tests/unit/platform_layer/identity/test_passwords.py`
17. `backend/tests/unit/platform_layer/identity/test_credentials_service.py`
18. `backend/tests/integration/api/test_password_login.py`
19. `frontend/tests/unit/pages/auth/password-login.test.tsx`
20. extend `backend/tests/integration/api/test_invites.py` (accept stores hash)

**Docs (3)**:
21. `docs/03-implementation/agent-harness-planning/22-iam-credentials-spike.md` — **design note extract** (spike sprint; 8-point quality gate per §Step 5.5)
22. `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md` — assess Day-4 (likely N/A platform_layer-internal, same call as 57.84/57.85)
23. `claudedocs/4-changes/feature-changes/CHANGE-053-iam-credentials-password-login.md`

## 5. Acceptance Criteria

1. `users.password_hash` column exists (migration `0027` applies on the `0026` head, both directions); `check_rls_policies` green (no new policy needed — inherits `users` RLS).
2. `bcrypt` is a dependency; `hash_password`/`verify_password` round-trip (offloaded via anyio); password fields capped at 72 bytes.
3. invite-accept now stores `password_hash` (the 57.85 accepted-not-stored gap is closed); `accept(password=None)` still works for existing callers.
4. `POST /auth/password-login` authenticates `(tenant_code, email, password)` → issues the `v2_jwt` cookie + `AuthMeResponse`; a follow-up `/auth/me` succeeds.
5. **Every** failure mode (unknown tenant / unknown email / no-password user / wrong password) returns a **single generic 401** (no enumeration); covered by tests.
6. 2-tenant isolation holds (same email in two tenants authenticates only with its own tenant_code + password).
7. NEW `/auth/password-login` page renders (3 fields), posts a JSON body, bootstraps + redirects on 200, shows a generic error on 401; the mockup has a matching `AuthPasswordLogin` component; `check:mockup-fidelity` baseline unchanged (oklch delta 0; styles-mockup.css diff empty).
8. `mypy src/` 0; full backend pytest green; frontend lint(no `--silent`)/build/test/mockup-fidelity green; `run_all.py` 10/10.

## 6. Deliverables

- [ ] US-1: `users.password_hash` + migration `0027` + `passwords.py` + invite-accept wires hash-store
- [ ] US-2: `CredentialsService.authenticate` + `POST /auth/password-login` (JWT/cookie/AuthMeResponse mirror) + exempt path
- [ ] US-3: generic-401 contract (all failure modes one error) + constant-time miss + tests
- [ ] US-4: NEW frontend page + route + i18n + mockup `AuthPasswordLogin` component (fidelity honest)
- [ ] US-5: unit (passwords + credentials) + integration (password-login e2e + isolation + accept-stores-hash) + frontend tests
- [ ] Closeout: **design note `22-iam-credentials-spike.md` (8-point gate)** + CHANGE-053 + 17.md assess + progress + retrospective + checklist + MEMORY + CLAUDE lean + next-phase-candidates (defer register/MFA/email/lockout/strength)

## 7. Workload Calibration

- **Agent-delegated: no** (parent-direct — security-sensitive: bcrypt offload + 72-byte guard, generic-401/enumeration avoidance, auth endpoint + cookie/JWT, multi-tenant credential isolation are judgment-sensitive; consistent with the security-sensitive billing + 57.85 IAM sprints all parent-direct). `agent_factor` 1.0 → 3-segment form.
- Scope class: **`medium-backend` 0.80** (backend dominates: passwords + credentials + endpoint + migration + storage wiring + tests; the frontend new page + mockup is the larger-than-usual frontend portion but still secondary). **Greenfield-IAM caveat (2nd data point)**: 57.85 (greenfield-IAM medium-backend) ran **~1.25 over**; 57.85 plan flagged "if 57.86 confirms → propose `iam-backend-spike` class". This sprint is that 2nd data point — expect another over-run; record the ratio in Day-4 retro Q2 and, if it again lands > 1.0, **propose `iam-backend-spike` (~0.55-0.65)** in the retro (do NOT pre-create the class).
- Bottom-up est ~10.5 hr (bcrypt dep + passwords.py ~0.5 / migration 0027 + ORM ~0.5 / CredentialsService set+authenticate+errors+singleton ~1.5 / wire invite-accept ~0.5 / password-login endpoint + request model + exempt ~1.5 / frontend page + route + i18n ~1.5 / mockup AuthPasswordLogin + i18n ~1 / tests unit+integration+frontend+accept-store ~3) → class-calibrated commit ~8.4 hr (`medium-backend` 0.80).
- **Size caveat (honest)**: ~1.5-2× a small sprint (≈ 57.85); a new security domain + a new public auth endpoint + a new frontend page + a mockup extension. The Day structure carries the safety: **Day-2-end is a safe cut-line** (passwords + credentials + invite-accept storage + service/unit tests green = the credential capability is provable at the service/DB layer before any HTTP/frontend wiring). If the Day-3 endpoint + frontend page + mockup over-runs, ship Day-1-2 (storage + service + tests) and carryover the HTTP + frontend + mockup as `AD-PasswordLogin-Endpoint-Frontend-Wire` (clean split; lifecycle core is the learning). Noted §8 Risk #2.

## 8. Dependencies & Risks

| # | Risk | Mitigation |
|---|------|-----------|
| 1 | password-login enables user/tenant enumeration via distinct error messages/timing | Single generic 401 for ALL failure modes (unknown tenant/email/no-password/wrong-password); constant-time miss (run one dummy `verify_password` when user/hash absent); tests assert identical status+body across modes. |
| 2 | Spike is ~1.5-2× a small sprint + new public auth endpoint + new page + mockup | Day-2-end cut-line (storage + service + tests, nothing HTTP/UI-wired) = safe partial ship; endpoint + frontend + mockup carryover as `AD-PasswordLogin-Endpoint-Frontend-Wire`. Not a failure — credential core is the learning. |
| 3 | New page added that the login mockup doesn't have (Mockup-Fidelity hard constraint) | User-approved deliberate mockup EXTENSION: add `AuthPasswordLogin` to `page-auth-extras.jsx` + i18n.jsx so the production page has a real mockup parent; reuse existing CSS classes (styles-mockup.css diff empty); `check:mockup-fidelity` oklch delta 0. NOT a translation/HSL drift — same primitives both sides. |
| 4 | bcrypt blocks the event loop + truncates at 72 bytes (Drift D5) | `await anyio.to_thread.run_sync(...)` offload for hash+verify; `max_length=72` on every password field (invite-accept + password-login request models) so truncation never silently bites; unit test asserts a 72-char password verifies. |
| 5 | No brute-force/lockout throttle (Drift D4) | Out of scope this spike (tracked carryover `AD-Auth-PasswordLogin-Lockout-Phase58`); the generic-401 + bcrypt cost=12 raise the per-guess cost; documented in §9 + design note Open-Invariants. |
| 6 | Migration head drift (0027 taken / wrong down_revision) | Day-0 Prong-3 confirmed head = `0026_invites`; Day-1 reads the `0026` header for the exact `revision` id before writing `down_revision`; apply both directions on Docker DB. |
| 7 | Exempt-path change accidentally exempts more than intended | Add ONLY `/api/v1/auth/password-login`; a test asserts a non-exempt path (e.g. admin) still requires auth + the new prefix is present. |
| 8 | invite-accept regression (adding `password` param breaks 57.85 callers/tests) | `password: str \| None = None` default → existing `accept(...)` calls unaffected; full `test_invites.py` must stay green; the extend-test asserts the new store-path. |

## 9. Out of Scope (this sprint; carryover → next-phase-candidates.md)

- **Self-service tenant registration** (`AD-Auth-Register-Backend-IAM-Block-B-Phase58`) — POST `/tenants/register` (create tenant + first admin user + password). Separate Block-B slice; the register page is still fixture/501 after this sprint.
- **MFA TOTP + WebAuthn** (`AD-Auth-MFA-Backend-IAM-Block-C-Phase58`) — the `/auth/mfa` page stays stub 501; password-login lands the user via `consumePostLoginRedirect()` (MFA step-up is a separate slice).
- **Brute-force lockout / rate-limit on auth** (`AD-Auth-PasswordLogin-Lockout-Phase58`, NEW) — no per-tenant login-attempt throttle this spike (Drift D4 / Risk #5).
- **Password-strength policy + min-length** — invite-accept keeps `min_length=1` (no strength rules); a policy (min length, complexity, breach check) is a follow-up. password fields gain only `max_length=72` (bcrypt safety).
- **Password reset / recovery flow** (`AD-Auth-Recovery-Page-Phase58`) — the `/auth/recovery` page does not exist; forgot-password is a separate slice.
- **Login-page "sign in with password" link** — discoverability link from the OIDC `/auth/login` page to `/auth/password-login` is a mockup-gated follow-up (keeps the login mockup pristine this sprint; `/auth/password-login` is reachable by direct route + is its own real consumer).
- **Invite email delivery** (57.85 Drift D1) — still returns the raw token in-response; email-send is a Phase-58 follow-up.
