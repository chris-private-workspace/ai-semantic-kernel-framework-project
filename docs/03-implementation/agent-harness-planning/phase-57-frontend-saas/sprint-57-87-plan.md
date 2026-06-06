# Sprint 57.87 Plan — C-12 IAM Block B: self-service tenant registration backend (`POST /tenants/register` → tenant + first-admin user + seeded admin role + audit) (closes AD-Auth-Register-Backend-IAM-Block-B-Phase58)

**Branch**: `feature/sprint-57-87-register-backend` (from `main` `ab2adcc7`)
**Closes**: `AD-Auth-Register-Backend-IAM-Block-B-Phase58` — the **self-service tenant registration leg** of C-12 IAM Block B. This is the THIRD vertical spike of C-12 (after 57.85 invites + 57.86 local credentials; per the thin-spike discipline: minimal self-contained slice → retrospective → extract design note; **NOT** a full Block B/C plan). MFA (`AD-Auth-MFA-Backend-IAM-Block-C-Phase58`), password recovery (`AD-Auth-Recovery-Page-Phase58`), brute-force lockout (`AD-Auth-PasswordLogin-Lockout-Phase58`), DB-RBAC→JWT effectiveness wiring, and OIDC-user linkage remain explicit out-of-scope follow-up slices (rolling — not pre-written).

---

## 0. Background

57.85 stood up `invites` (admin create → guest accept → User + role + audit); 57.86 added the local-credentials store + `POST /auth/password-login`. Both assume a tenant ALREADY exists (dev-login auto-creates one; admin-create goes through ProvisioningWorkflow). There is **no self-service path for a brand-new org to register itself** — the shipped frontend register wizard (`/auth/register`, 4 steps, Sprint 57.23/57.35) posts to `POST /api/v1/tenants/register` but the backend returns a 501 stub (frontend shows `register.errorStubbed`). User picked 57.87 (2026-06-06) to continue "process all" of the C-12 backend legs (register first, per the natural create-account continuation of invite/password-login).

**The two design forks (resolved Day-0 via AskUserQuestion, 2026-06-06)**:
1. **Tenant state on register** → **ACTIVE immediately** (self-serve trial; skip ProvisioningWorkflow — its 8 steps are all stubs that only stamp `provisioning_progress` JSONB, and onboarding 6-step + health-check are unimplemented so a REQUESTED/PROVISIONING tenant would never auto-advance to ACTIVE). The self-registered tenant is usable at once.
2. **First-admin role** → **seed a real "admin" Role + UserRole** in the new tenant. This is the codebase's **first real `Role(...)` creation** (today nothing creates Role rows; `seed_default_roles` in `provisioning.py` is a stub). The DB becomes RBAC-ready and consistent with `invites.accept`'s `role_id` assumption. **Honest boundary**: gating is JWT-claim-based and the OIDC callback still bakes `roles=["user"]` (auth.py:302), so the seeded admin UserRole is DB-real but **not yet authz-effective** until a future DB-RBAC→JWT wiring sprint → tracked carryover (NOT this spike).

**Day-0 ground-truth (Explore three-prong + parent grep/read, main `ab2adcc7`)**:
- **Reusable infra (do NOT rebuild)**: `invites.accept` is the mirrorable pattern — `_set_tenant(db, str(tenant_id))` (set_config RLS context, `invites.py:385,392`) → `User(tenant_id, email, display_name, status="active")` → flush → `UserRole(user_id, role_id, granted_by)` → `append_audit(db, tenant_id, operation, ...)` (`invites.py:279-325`). `Tenant.code String(64) unique` (`identity.py:117`); dev-login + admin-create are the two existing Tenant-creation call sites (`auth.py:408-410` bare; `admin/tenants.py:166-173` + ProvisioningWorkflow). Router mount = `api/main.py:348-363` `include_router(..., prefix="/api/v1")` (invites precedent `:72`/`:350`). `append_audit` = `infrastructure/db/audit_helper.py`. EXEMPT_PATH_PREFIXES per-subpath (`middleware/tenant_context.py:119-134`).
- **Schema (Prong 3, all tables EXIST — NO migration this sprint)**: `roles(id, code String(64), display_name String(256), description Text?, meta_data JSONB "metadata", created_at)` UNIQUE`(tenant_id, code)` `uq_roles_tenant_code` (`identity.py:236-262`); `user_roles(user_id FK, role_id FK, granted_at, granted_by FK?)` PK`(user_id, role_id)` (`:270-294`); `users` has `password_hash` (0027, nullable) + UNIQUE`(tenant_id, email)`; `tenants` is **RLS-free** (`0009_rls_policies.py` global), `users`/`roles` **RLS-protected**. Migration head = `0027` (no new migration needed).
- **Drift findings**:
  - **D1**: no public `api/v1/tenants.py` (only `admin/tenants.py`, all `require_admin_platform_role`) → NEW public router + 2-line `api/main.py` mount + EXEMPT `/api/v1/tenants/register`.
  - **D2**: `TenantPlan` enum has ONLY `ENTERPRISE` (`identity.py:92-96`; Phase 56+ Stage 2 adds BASIC/STANDARD) but the frontend sends `plan` ∈ {trial, pro, enterprise} + `size` (no Tenant column) → map `tenant.plan = ENTERPRISE` (only valid) + store `{requested_plan, company_size}` in `tenant.meta_data`. Plan tiers are not real yet.
  - **D3**: `seed_default_roles` is a STUB (`provisioning.py:19,77`) + **no code ever instantiates `Role(...)`** → register is the FIRST real Role-creation (seed a minimal "admin" role).
  - **D4**: authz is JWT-claim-based (`auth.py` `_require_role` reads `request.state.roles`); OIDC callback bakes `roles=["user"]` (`:302`) → seeded admin UserRole is DB-real but NOT yet authz-effective → carryover `AD-RBAC-DB-To-JWT-Wiring-Phase58` (NEW).
  - **D5**: OIDC callback upserts the login user by `(tenant_id, external_id)` (`auth.py:177-209`); register creates the user by `email` (no external_id) → a subsequent OIDC login would create a SECOND user row → carryover `AD-Register-OIDC-User-Linkage-Phase58` (NEW; callback should link-by-email or register be OIDC-initiated).
  - **D6**: `tenants` RLS-free (INSERT ok with no context); `users`/`roles` RLS-protected → `_set_tenant(db, tenant.id)` before the User/Role/UserRole inserts (mirror invites.py).
  - **D7**: **NO migration** (reuses tenants/users/roles/user_roles) — simpler than 57.85/57.86.
  - **D8**: register page + `AuthRegister` mockup already COMPLETE (57.23/57.35) → **no mockup extension, no `styles-mockup.css` change** (oklch baseline unchanged); frontend EDIT = un-stub only (remove the 501 banner/copy, wire real 201→`/auth/callback` + 409 slug-taken states).

---

## 1. Sprint Goal

Stand up the **self-service tenant registration vertical slice** of IAM Block B end-to-end: a public, EXEMPT `POST /api/v1/tenants/register` that validates a unique tenant slug (generic 409 on collision), creates a new `Tenant` (state ACTIVE, plan ENTERPRISE, requested-plan/size in meta_data), seeds a real "admin" `Role` + grants the founding `User` an `admin` `UserRole` under the new tenant's RLS context, writes a `tenant_registered` WORM audit row, and returns `201 {tenant, user}` — then un-stub the shipped `/auth/register` wizard so it consumes the real endpoint (201 → `/auth/callback`, 409 → slug-taken error). Honest boundary: the seeded admin role is DB-real but not yet JWT-authz-effective, and the register-user↔OIDC-user linkage is deferred — both tracked carryovers, NOT this spike.

## 2. User Stories

- **US-1**: As a prospective customer, I want `POST /tenants/register` to create my tenant (ACTIVE) + a first admin user from the wizard fields, so my org exists and is immediately usable. (public endpoint → `RegistrationService.register`)
- **US-2**: As the founding admin, I want a real "admin" role seeded in my new tenant + granted to me (DB `Role` + `UserRole`), so the tenant has an owner-of-record and the RBAC tables are consistent (the codebase's first real Role-creation). (seed admin Role + UserRole under tenant RLS)
- **US-3**: As a security owner, I want register to reject a duplicate tenant slug with a generic 409, be EXEMPT (pre-auth, no JWT), run User/Role inserts under the new tenant's RLS context, and write a `tenant_registered` audit row — so the public endpoint is safe, isolated, and traceable. (slug-unique check + exempt + `_set_tenant` + audit)
- **US-4**: As a user, I want the existing `/auth/register` wizard to hit the real backend (no more 501 stub banner) — 201 redirects me into the OIDC login (`/auth/callback`), 409 shows a "slug taken" error — so registration is a genuine main-flow consumer (not a Potemkin). (un-stub frontend page)
- **US-5**: As a maintainer, I want unit + integration + frontend tests pinning the create-tenant+admin+role+userrole+audit flow, the slug-collision 409, the exempt-path contract, 2-tenant isolation, and the page submit/error flow, so the slice is a verifiable real e2e.

## 3. Technical Specifications

### 3.0 Architecture

ONE new service file `platform_layer/identity/registration.py` (`RegistrationService` — the create-tenant+first-admin orchestration, mirroring `invites.accept`'s User+Role+audit pattern + adding Tenant-creation) and ONE new public router `api/v1/tenants.py` (`POST /register`, mounted in `api/main.py`, EXEMPT from the tenant middleware — the caller has no JWT yet). **No migration** (reuses `tenants`/`users`/`roles`/`user_roles`). **No password** (the register wizard has no password field — registration is OIDC-first; local-password is invite-accept's job, 57.86). **No mockup change** (`AuthRegister` already exists). LLM neutrality: N/A. Multi-tenant: `tenants` is RLS-free so the Tenant INSERT needs no context; the User/Role/UserRole INSERTs run under `_set_tenant(db, new_tenant.id)` (mirror invites.py). Response = `201 {tenant, user}` (no session/cookie — the frontend redirects to `/auth/callback` for OIDC login, matching the shipped contract).

**Divergences from admin-create (deliberate)**: admin-create (`admin/tenants.py`) is `require_admin_platform_role`-gated + runs ProvisioningWorkflow (state→PROVISIONING). register is **public/EXEMPT**, sets state **ACTIVE immediately** (skips the all-stub workflow), and **seeds the founding admin role inline** (admin-create does not). register mirrors admin-create ONLY for the Tenant-field shape.

### 3.1 `RegistrationService` (US-1/US-2/US-3) — NEW `platform_layer/identity/registration.py`

- `async def register(self, db, *, email, full_name, company_name, tenant_slug, region, requested_plan, company_size) -> tuple[Tenant, User]`:
  1. **Slug-unique check**: `select(Tenant).where(Tenant.code == tenant_slug)` → if a row exists → raise `TenantSlugTakenError` (→ 409). (RLS-free table; no context needed.)
  2. **Create Tenant**: `Tenant(code=tenant_slug, display_name=company_name, state=TenantState.ACTIVE, plan=TenantPlan.ENTERPRISE, region=region or "global", meta_data={"requested_plan": requested_plan, "company_size": company_size})` → `db.add` → `await db.flush()` (get `tenant.id`). (state ACTIVE per Fork-1; plan ENTERPRISE + requested_plan/size in meta_data per D2.)
  3. **`_set_tenant(db, str(tenant.id))`** (RLS context for the next 3 inserts — D6).
  4. **Seed admin Role**: `Role(tenant_id=tenant.id, code="admin", display_name="Admin", description="Founding tenant administrator (seeded at registration).")` → `db.add` → `await db.flush()` (get `role.id`). (First real Role-creation — D3.)
  5. **Create User**: `User(tenant_id=tenant.id, email=email, display_name=full_name, status="active")` → `db.add` → `await db.flush()` (get `user.id`). (No password — OIDC-first; no external_id yet — D5.)
  6. **Grant UserRole**: `UserRole(user_id=user.id, role_id=role.id, granted_by=user.id)` → `db.add`. (Founding admin self-grant.)
  7. **Audit**: `await append_audit(db, tenant_id=tenant.id, operation="tenant_registered", operation_data={"tenant_code": tenant_slug, "email": email, "requested_plan": requested_plan}, user_id=user.id)`.
  8. Return `(tenant, user)`.
- Typed errors co-located: `RegistrationError` base (status 400) + `TenantSlugTakenError` (status 409). Local `_set_tenant` 1-liner (mirror invites.py:385,392 — `SELECT set_config('app.tenant_id', :tid, true)`; the helper is module-private in invites, so a small local copy, like billing_outbox's own copy). Module-level **lenient singleton** (`set_/get_/maybe_get_registration_service`; endpoint uses `maybe_get_registration_service() or RegistrationService()` — NO lifespan wiring → no leak, mirrors 57.85/57.86; deliberately avoids the 57.84 Day-3 singleton-leak class).

### 3.2 Public `POST /api/v1/tenants/register` endpoint + router mount + exempt (US-1/US-3/US-4) — NEW `api/v1/tenants.py` + EDIT `api/main.py` + EDIT `tenant_context.py`

- NEW `api/v1/tenants.py`: `router = APIRouter(prefix="/tenants", tags=["tenants"])`. Request model `TenantRegisterRequest(BaseModel)`: `email: EmailStr | str (1..256)`, `full_name: str (1..256)`, `company_name: str (1..256)`, `tenant_slug: str (1..64, pattern=r"^[a-z0-9][a-z0-9_-]*$")` (mirror `TenantCreateRequest` validation, `admin/tenants.py:135`), `region: str (default "global", ≤32)`, `plan: str (≤32)` (the requested tier), `size: str | None (≤32)`. Response `TenantRegisterResponse`: `{tenant: {id, code, display_name, state}, user: {id, email, display_name}}`.
- `@router.post("/register", status_code=201)` (EXEMPT — pre-JWT): body → `RegistrationService.register(db, email=…, full_name=…, company_name=…, tenant_slug=…, region=…, requested_plan=body.plan, company_size=body.size)`; on `TenantSlugTakenError` → `HTTPException(409, "That workspace URL is already taken")`; on other `RegistrationError` → `HTTPException(400, …)`; on success → `201 TenantRegisterResponse`. No cookie/JWT (frontend redirects to OIDC).
- EDIT `api/main.py`: `from api.v1.tenants import router as tenants_router` + `app.include_router(tenants_router, prefix="/api/v1")` (mirror invites `:72`/`:350` → full path `/api/v1/tenants/register`).
- EDIT `platform_layer/middleware/tenant_context.py`: add `/api/v1/tenants/register` to `EXEMPT_PATH_PREFIXES` (precise full subpath — NOT `/api/v1/tenants`, so admin tenant paths stay gated) + comment + MHist. A test asserts the prefix is present + admin paths unaffected.

### 3.3 Frontend un-stub `/auth/register` (US-4) — EDIT

- EDIT `frontend/src/pages/auth/register/index.tsx`: remove the 501-stub error copy (`register.errorStubbed`) + the AP-2 demo banner; wire the real response — on `res.ok` (201) → `navigate("/auth/callback"…)` per existing success flow (or the shipped redirect target); on `409` → show a "workspace URL taken" inline error (reuse the existing error surface; map the slug-taken case to the slug step); on other non-ok → generic error. (Confirm the exact existing handler Day-3; minimal change — un-stub + 409 branch.)
- EDIT `frontend/src/i18n/locales/{en,zh-TW}/auth.json`: drop/replace `register.errorStubbed`; add `register.errorSlugTaken` (+ generic `register.error` if missing). zh-TW 繁中.

### 3.4 No migration / no mockup (explicit)

- **No Alembic migration** — register reuses existing tables (D7). `check_rls_policies` unchanged (no new table).
- **No mockup change** — `AuthRegister` (`page-auth-extras.jsx`) + its i18n already exist + the production page is already mockup-aligned (57.35); `styles-mockup.css` UNCHANGED → `diff` stays empty, `check:mockup-fidelity` oklch baseline **unchanged (delta 0)**.

### 3.5 Tests (US-5)

- Unit `tests/unit/platform_layer/identity/test_registration_service.py` (db_session, ~6): register creates Tenant(state=ACTIVE, plan=ENTERPRISE, meta_data has requested_plan+company_size) + admin Role(code="admin") + User(status=active, email) + UserRole(user→admin role) + audit row; slug collision → `TenantSlugTakenError`; the User/Role land under the new tenant's RLS (queryable with tenant context).
- Integration `tests/integration/api/test_tenant_register.py` (`_build_app`, ~7): `POST /tenants/register` 201 + response shape; duplicate slug → 409 generic; **exempt-path contract** (reachable w/o JWT; a non-exempt admin path still 401s); the created tenant is then resolvable by `Tenant.code` (so OIDC `/auth/callback` no longer 400s "tenant not found"); **2-tenant isolation** (two registrations with different slugs → each tenant has exactly its own admin user + role, no cross-leak); audit row on success; slug-pattern validation (invalid slug → 422).
- Frontend `frontend/tests/unit/pages/auth/register.test.tsx` (Vitest, NEW or extend if one exists, ~3): submit 201 → redirect/success; submit 409 → slug-taken error, no redirect; the demo/stub banner is gone (assert absence).

### 3.6 Lint / validation

`black + isort + flake8 + mypy src/` 0 + `run_all.py` 10/10 (esp. `check_rls_policies` — no new table; `check_llm_sdk_leak` — no LLM). Frontend `npm run lint` (NO `--silent`) + `npm run build` + `npm run test` + `npm run check:mockup-fidelity` (baseline unchanged). Full format chain pre-commit.

## 4. File Change List

**Code — NEW (2)**:
1. `backend/src/platform_layer/identity/registration.py` — `RegistrationService.register` (tenant + admin role + user + userrole + audit) + typed errors + lenient singleton + local `_set_tenant`
2. `backend/src/api/v1/tenants.py` — public router; `TenantRegisterRequest/Response` + `POST /register` (EXEMPT, 201/409)

**Code — EDIT (2)**:
3. `backend/src/api/main.py` — import + `include_router(tenants_router, prefix="/api/v1")`
4. `backend/src/platform_layer/middleware/tenant_context.py` — exempt `/api/v1/tenants/register`

**Frontend — EDIT (3)**:
5. `frontend/src/pages/auth/register/index.tsx` — un-stub (remove 501 banner; wire 201 success + 409 slug-taken)
6. `frontend/src/i18n/locales/en/auth.json` — drop `errorStubbed`; add `errorSlugTaken`
7. `frontend/src/i18n/locales/zh-TW/auth.json` — same (繁中)

**Tests (3 NEW)**:
8. `backend/tests/unit/platform_layer/identity/test_registration_service.py`
9. `backend/tests/integration/api/test_tenant_register.py`
10. `frontend/tests/unit/pages/auth/register.test.tsx` (NEW or extend)

**Docs (3)**:
11. `docs/03-implementation/agent-harness-planning/23-iam-registration-spike.md` — **design note extract** (spike sprint; 8-point quality gate per §Step 5.5)
12. `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md` — assess Day-4 (likely N/A platform_layer-internal, same call as 57.84/57.85/57.86)
13. `claudedocs/4-changes/feature-changes/CHANGE-055-iam-tenant-registration.md`

## 5. Acceptance Criteria

1. `POST /api/v1/tenants/register` creates a Tenant (state ACTIVE, plan ENTERPRISE, meta_data carries requested_plan + company_size) + a first admin User + a seeded "admin" Role + a UserRole granting it + a `tenant_registered` audit row; returns `201 {tenant, user}`.
2. Duplicate tenant slug → generic `409`; invalid slug pattern → `422`; the endpoint is EXEMPT (reachable with no JWT) while admin paths stay gated.
3. The created tenant is resolvable by `Tenant.code` (so OIDC `/auth/callback` no longer 400s "tenant not found — provision first").
4. User/Role/UserRole inserts run under the new tenant's RLS context; 2-tenant isolation holds (two registrations don't cross-leak users/roles).
5. The `/auth/register` wizard consumes the real endpoint: 201 → `/auth/callback` redirect; 409 → slug-taken error; the 501-stub banner/copy is gone.
6. **No migration / no schema change** (`check_rls_policies` unchanged); **no mockup/styles change** (`check:mockup-fidelity` oklch delta 0; `styles-mockup.css` diff empty).
7. Honest boundary documented: the seeded admin role is DB-real but not yet JWT-authz-effective + register-user↔OIDC-user linkage deferred (carryovers, NOT regressions).
8. `mypy src/` 0; full backend pytest green; frontend lint(no `--silent`)/build/test/mockup-fidelity green; `run_all.py` 10/10.

## 6. Deliverables

- [ ] US-1: `RegistrationService.register` creates Tenant(ACTIVE) + first admin User; public `POST /tenants/register` 201 + router mount + exempt
- [ ] US-2: seed real "admin" Role + grant UserRole (first real Role-creation; RBAC-ready)
- [ ] US-3: slug-unique → 409 generic + exempt-path + `_set_tenant` RLS context + `tenant_registered` audit
- [ ] US-4: un-stub `/auth/register` (remove 501 banner; wire 201→`/auth/callback` + 409 slug-taken) + i18n
- [ ] US-5: unit (registration service) + integration (register e2e + 409 + exempt + isolation + tenant-resolvable) + frontend tests
- [ ] Closeout: **design note `23-iam-registration-spike.md` (8-point gate)** + CHANGE-055 + 17.md assess + progress + retrospective + checklist + MEMORY + CLAUDE lean + next-phase-candidates (defer MFA/recovery/lockout + NEW RBAC-JWT-wiring/OIDC-user-linkage/plan-tiers)

## 7. Workload Calibration

- **Agent-delegated: no** (parent-direct — security-sensitive: a public pre-auth endpoint that creates tenants + grants admin roles + writes under RLS is judgment-heavy; consistent with 57.85/57.86 IAM + billing all parent-direct). `agent_factor` 1.0 → 3-segment form.
- Scope class: **`iam-backend-spike` 0.65** (ADOPTED this sprint per the 57.86 carryover `AD-Sprint-Plan-IAM-Backend-Spike-Class` — register is "the next IAM backend spike"; 57.85 invites ran ~1.25 over + 57.86 password-login ~1.15-1.2 over under `medium-backend` 0.80 → 2 consecutive greenfield-IAM over-runs justified a dedicated class). This sprint is the **1st `iam-backend-spike` validation data point** — record the ratio in Day-4 retro Q2; KEEP 0.65 single-data-point unless > 1.20 (then loosen) or < 0.7 (then tighten), per the 3-sprint window rule.
- Bottom-up est ~8.5 hr (RegistrationService tenant+role+user+userrole+audit+errors+singleton+_set_tenant ~2 / public router + request/response models + endpoint + main.py mount + exempt ~1.5 / frontend un-stub + i18n ~1 / tests unit+integration+frontend ~2.5 / closeout design-note + CHANGE + docs ~1.5) → class-calibrated commit ~5.5 hr (`iam-backend-spike` 0.65).
- **Simpler than 57.86 in 3 ways** (no migration / no mockup extension / frontend mostly exists) but **harder in 1**: first real Tenant-creation-as-a-service + first real Role-creation in the codebase + a public pre-auth endpoint. **Day-2-end is the safe cut-line**: `RegistrationService` + unit/service tests green = the registration capability is provable at the service/DB layer before any HTTP/frontend wiring. If Day-3 (endpoint + frontend un-stub) over-runs, ship Day-1-2 (service + tests) and carryover the HTTP + frontend wire as `AD-Register-Endpoint-Frontend-Wire` (clean split; the create-tenant+admin lifecycle is the learning). Noted §8 Risk #2.

## 8. Dependencies & Risks

| # | Risk | Mitigation |
|---|------|-----------|
| 1 | Public pre-auth endpoint creating tenants = abuse surface (spam tenants, slug squatting, enumeration) | Slug-unique → generic 409 (no "exists in tenant X" detail); slug pattern-validated (422); EXEMPT only the exact `/api/v1/tenants/register` subpath; audit every registration. Rate-limit/CAPTCHA/email-verify = tracked carryover (NOT this spike; same posture as 57.86 lockout deferral). |
| 2 | First real Tenant+Role creation service + public endpoint = larger than a pure wiring sprint | Day-2-end cut-line (service + tests, nothing HTTP/UI-wired) = safe partial ship; endpoint + frontend carryover as `AD-Register-Endpoint-Frontend-Wire`. Service/DB lifecycle is the learning. |
| 3 | Seeded admin role is NOT authz-effective (JWT bakes roles=["user"]; gating reads JWT not DB) — feature could read as "Potemkin admin" | Be explicit (§0 Fork-2 honest boundary + design-note Open-Invariants + carryover `AD-RBAC-DB-To-JWT-Wiring-Phase58`). What ships is REAL (tenant + user + role + userrole + audit rows; endpoint really creates them; OIDC login unblocked). authz-effectiveness is a system-wide RBAC-wiring gap, not register-specific. |
| 4 | register-user (by email) ≠ OIDC-callback-user (by external_id) → duplicate user on login | Out of scope; carryover `AD-Register-OIDC-User-Linkage-Phase58` (callback link-by-email OR register OIDC-initiated). register's job = create the tenant + first-admin-of-record so OIDC login is unblocked; the linkage is a separate slice. Documented §0 D5 + design note. |
| 5 | `TenantPlan` enum only has ENTERPRISE but frontend offers trial/pro/enterprise (D2) | Map `tenant.plan = ENTERPRISE` (only valid) + store `{requested_plan, company_size}` in `tenant.meta_data`; plan tiers are Phase 56+ Stage 2 (carryover `AD-Tenant-Plan-Tiers-Phase58`). A test asserts meta_data carries the requested plan. |
| 6 | RLS: User/Role/UserRole insert without tenant context fails (or leaks) | `_set_tenant(db, str(new_tenant.id))` before those 3 inserts (mirror invites.py:279); `tenants` is RLS-free so the Tenant INSERT itself needs none; an isolation test proves the rows land in the right tenant. |
| 7 | New router not mounted / wrong prefix → 404 on `/api/v1/tenants/register` | `api/main.py` import + `include_router(tenants_router, prefix="/api/v1")` (router internal prefix `/tenants`) mirrors invites; integration test hits the real path via `_build_app`. |
| 8 | Frontend un-stub regresses the existing wizard (steps/validation) | Minimal change — remove the stub banner + add the 201/409 branches only; keep the 4-step wizard + field validation intact; the frontend test asserts submit-success + 409-error + banner-absent. |

## 9. Out of Scope (this sprint; carryover → next-phase-candidates.md)

- **MFA TOTP + WebAuthn** (`AD-Auth-MFA-Backend-IAM-Block-C-Phase58`) — `/auth/mfa` stays stub 501.
- **Password recovery / reset** (`AD-Auth-Recovery-Page-Phase58`) — needs an email adapter (none exists); `/auth/recovery` does not exist.
- **Brute-force lockout / rate-limit on auth** (`AD-Auth-PasswordLogin-Lockout-Phase58`) — also covers register-spam throttle.
- **DB-RBAC → JWT effectiveness wiring** (`AD-RBAC-DB-To-JWT-Wiring-Phase58`, NEW — D4) — make the seeded admin UserRole actually grant admin in the JWT/gating (today OIDC bakes roles=["user"]; gating reads JWT not DB).
- **Register-user ↔ OIDC-user linkage** (`AD-Register-OIDC-User-Linkage-Phase58`, NEW — D5) — callback link-by-email OR register OIDC-initiated, so login doesn't create a duplicate user.
- **Plan tiers** (`AD-Tenant-Plan-Tiers-Phase58`, NEW — D2) — `TenantPlan` only has ENTERPRISE; real BASIC/STANDARD/trial tiers + enforcement are Phase 56+ Stage 2.
- **`seed_default_roles` full promotion** — register seeds only the single "admin" role; promoting the `provisioning.py` stub to seed a full default role-set (admin/user/auditor/…) for admin-create too is a separate slice.
- **Login-after-register UX** — register returns 201 + the frontend redirects to `/auth/callback` (OIDC); a register-issued session (like password-login's cookie) is NOT done (matches the shipped frontend contract).
- **Invite email delivery** (57.85) / **admin invites-list UI** (57.85) — unchanged carryovers.
