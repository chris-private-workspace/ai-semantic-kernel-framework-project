# Sprint 57.87 — Checklist (C-12 IAM Block B: self-service tenant registration backend)

**Plan**: `sprint-57-87-plan.md`
**Branch**: `feature/sprint-57-87-register-backend` (from `main` `ab2adcc7`)
**Closes**: `AD-Auth-Register-Backend-IAM-Block-B-Phase58` (self-service registration leg of C-12 Block B). MFA / recovery / lockout / RBAC-JWT-wiring / OIDC-user-linkage / plan-tiers = follow-up slices (§9).

---

## Day 0 — Plan-vs-Repo Verify + Branch + Decisions

### 0.1 Day-0 verify (Explore three-prong + parent grep/read, main `ab2adcc7`)
- [x] **Prong 1 (path)** — reusable infra confirmed: `invites.py:279-325` (User+UserRole+audit pattern) + `:385,392` (`_set_tenant` set_config RLS); `Tenant.code String(64) unique` (`identity.py:117`); 2 Tenant-create sites (`auth.py:408-410` dev-login bare / `admin/tenants.py:166-173` admin + ProvisioningWorkflow); router mount `api/main.py:348-363` (invites precedent `:72`/`:350`); EXEMPT_PATH_PREFIXES `tenant_context.py:119-134`.
- [x] **Prong 2 (content)** — authz is JWT-claim-based (`auth.py` `_require_role` reads `request.state.roles`); OIDC callback bakes `roles=["user"]` (`:302`) + upserts user by `(tenant_id, external_id)` (`:177-209`); `seed_default_roles` is a STUB (`provisioning.py:19,77`); **no code ever instantiates `Role(...)`**; frontend register page + `AuthRegister` mockup COMPLETE (57.23/57.35), posts `{email,full_name,company_name,tenant_slug,region,size,plan}` → `/auth/callback`.
- [x] **Prong 3 (schema)** — all tables EXIST → **NO migration**: `roles(code,display_name,description?,meta_data)` UNIQUE`(tenant_id,code)`; `user_roles(user_id,role_id,granted_by?)` PK`(user_id,role_id)`; `users.password_hash` (0027); `tenants` RLS-free, `users`/`roles` RLS-protected; `TenantPlan` enum only ENTERPRISE; head `0027`.
- [x] **Drift findings** — D1 (no public `api/v1/tenants.py` → NEW router + 2-line main.py mount); D2 (`TenantPlan` only ENTERPRISE vs frontend trial/pro/enterprise → map ENTERPRISE + meta_data); D3 (`seed_default_roles` stub + 0 Role-creation → register is 1st real Role-creation); D4 (JWT-claim authz; OIDC bakes roles=[user] → seeded admin NOT yet authz-effective → carryover); D5 (register user by email ≠ OIDC user by external_id → dup-user carryover); D6 (`_set_tenant` before user/role inserts); D7 (NO migration); D8 (register page + mockup COMPLETE → frontend un-stub only, no styles/mockup change).
- [x] **Design locked** (AskUserQuestion ×2, 2026-06-06): tenant state = **ACTIVE immediately** (skip all-stub ProvisioningWorkflow); first-admin role = **seed real "admin" Role + UserRole** (JWT-authz-effectiveness deferred → carryover). Defaults: no password (OIDC-first; frontend has no field); slug caller-provided → 409 collision; plan/size → meta_data; EXEMPT; 201 {tenant,user} (no cookie — frontend redirects to OIDC); service in `identity/registration.py`; lenient singleton.
- [x] **go/no-go** — GO; Day-2-end cut-line (RegistrationService + service/unit tests); endpoint + frontend can carryover as `AD-Register-Endpoint-Frontend-Wire` if Day-3 over-runs.

### 0.2 Branch + decisions
- [x] **Branch created** `feature/sprint-57-87-register-backend` (from `main` `ab2adcc7`)
- [x] **Decisions locked** (see 0.1 Design locked)
- [x] **Day-0 commit** plan + checklist + progress.md Day 0

---

## Day 1 — RegistrationService build (US-1/US-2/US-3)

### 1.1 RegistrationService
- [x] **NEW `platform_layer/identity/registration.py`** — `RegistrationService.register(db, *, email, full_name, company_name, tenant_slug, region, requested_plan, company_size) -> tuple[Tenant, User]`:
  - slug-unique check (`select(Tenant).where(code==slug)` → `TenantSlugTakenError` if exists)
  - create `Tenant(code=slug, display_name=company_name, state=ACTIVE, plan=ENTERPRISE, region=…, meta_data={requested_plan, company_size})` → flush
  - `_set_tenant(db, str(tenant.id))` (RLS context — D6)
  - seed `Role(tenant_id, code="admin", display_name="Admin", description=…)` → flush (1st real Role-creation — D3)
  - `User(tenant_id, email, display_name=full_name, status="active")` → flush
  - `UserRole(user_id, role_id, granted_by=user.id)`
  - `append_audit(db, tenant_id, "tenant_registered", {tenant_code, email, requested_plan}, user_id)`
  - DoD: mypy clean
- [x] **Typed errors + helpers** — `RegistrationError` (400) base + `TenantSlugTakenError` (409); local `_set_tenant` 1-liner (mirror invites.py:392); lenient singleton `set_/get_/maybe_get_registration_service`
  - DoD: mypy clean; file header + MHist

---

## Day 2 — Service tests + harden (US-1/US-2/US-3/US-5) — SAFE CUT-LINE

> Day 2 = unit/service tests + RLS-isolation + slug-collision + meta_data verification, ZERO HTTP/frontend. Registration capability proven at service/DB layer BEFORE Day-3 wires the endpoint + page.

### 2.1 unit/service tests
- [x] **NEW `tests/unit/platform_layer/identity/test_registration_service.py`** (db_session, **6**) — register creates Tenant(state=ACTIVE, plan=ENTERPRISE, meta_data has requested_plan+company_size) + admin Role(code="admin") + User(status=active) + UserRole(user→admin) + audit row; slug collision → `TenantSlugTakenError`; the User/Role land under the new tenant's RLS (queryable with tenant context); 2-tenant isolation at service layer (two registers don't cross-leak)
  - DoD: all green; one error type for slug collision
- [x] **black + isort + flake8 + mypy src/ + pytest** — clean (mypy 0/343; flake8 0); **6/6 service tests green**
- [x] **Cut-line checkpoint** — registration provable at service/DB layer; nothing HTTP/UI-wired yet ✓ (isolation asserted app-layer per 57.85 D5 — test DB role is superuser, RLS-bypass)

---

## Day 3 — Public endpoint + exempt + mount + frontend un-stub (US-1/US-3/US-4)

### 3.1 public router + endpoint + mount + exempt
- [x] **NEW `api/v1/tenants.py`** — `APIRouter(prefix="/tenants")` + `TenantRegisterRequest` (slug pattern-validated; extra-ignore) + `TenantRegisterResponse({tenant,user})` + `POST /register` (201, EXEMPT): `RegistrationService.register` → `TenantSlugTakenError`→409 / success→201; lenient `_service()`; no cookie/JWT
  - DoD: 201 / 409 ✓ (integration)
- [x] **EDIT `api/main.py`** — `from api.v1.tenants import router as tenants_router` + `include_router(tenants_router, prefix="/api/v1")` (alphabetical between telemetry/verification)
- [x] **EDIT `platform_layer/middleware/tenant_context.py`** — add `/api/v1/tenants/register` to `EXEMPT_PATH_PREFIXES` + comment + MHist
  - DoD: exempt-path test (prefix present; admin paths still gated) ✓

### 3.2 integration tests (HTTP e2e)
- [x] **NEW `tests/integration/api/test_tenant_register.py`** (`_build_app`, **6**) — 201 + response shape; ACTIVE+meta_data; duplicate slug → 409 generic; invalid slug → 422; 2-tenant isolation (app-layer); exempt-path contract
  - DoD: 6/6 green; 409 generic ✓

### 3.3 frontend un-stub + i18n + test
- [x] **EDIT `frontend/src/pages/auth/register/index.tsx`** — removed 501-stub banner/copy; wired 201 → `/auth/callback` + 409 → slug-taken inline error; 4-step wizard intact; header docstring + MHist
- [x] **EDIT `frontend/src/i18n/locales/{en,zh-TW}/auth.json`** — dropped `register.errorStubbed`+`demoBanner`; added `register.errorSlugTaken`+`error`; zh-TW 繁中
- [x] **NEW/extend `frontend/tests/unit/pages/auth/register.test.tsx`** (**6**) — banner-absent + 409 slug-taken + 201 success + stepper tests kept
  - DoD: 6/6 green; full Vitest **763**; lint(no `--silent`)+build+mockup-fidelity green (oklch baseline 53 UNCHANGED) ✓

### 3.4 test-isolation (Risk Class C)
- [→] **conftest singleton reset** — **N/A** (RegistrationService lenient `maybe_get… or RegistrationService()`; no lifespan singleton → no leak, same as 57.85/57.86). Full backend **2214 passed**, no event-loop leak.

---

## Day 4 — Full sweep + design note + Closeout

### 4.1 Full sweep
- [x] **Backend gates** — black/isort/flake8 0 + `mypy src/` 0 + `pytest` green + `run_all.py` 10/10 (`check_rls_policies` unchanged — no new table)
- [x] **Frontend gates** — `npm run lint` (NO `--silent`) + `npm run build` + `npm run test` + `npm run check:mockup-fidelity` ✓ (oklch baseline UNCHANGED; CSS byte-identical)
- [x] **Read all changed code** — final pass (registration service, public router/endpoint, main.py mount, exempt path, frontend un-stub)
- [x] **real-Azure smoke?** — N/A (no LLM in registration path; e2e proven by unit + integration + frontend tests)

### 4.2 design note (SPIKE — §Step 5.5 mandatory)
- [x] **NEW `docs/03-implementation/agent-harness-planning/23-iam-registration-spike.md`** — extracted from shipped impl; 8-point gate all ✓ (self-check in retrospective)
- [x] **17.md assess** — expected **N/A** (identity not a registered 11+1 surface; same call as 57.84/57.85/57.86). Contracts in design note + docstrings + CHANGE-055.

### 4.3 Closeout docs
- [x] **CHANGE-055** in `claudedocs/4-changes/feature-changes/`
- [x] **progress.md** Day 0-4 + **retrospective.md** Q1-Q7 (1st real Tenant+Role creation service + ACTIVE-now + admin-role-seed honest boundary + iam-backend-spike 0.65 1st validation)
- [x] **Checklist** all `[x]`/`[→]` (no deletions)
- [x] **Calibration** record (`iam-backend-spike` 0.65 1st validation; agent_factor 1.0 parent-direct; ratio ≈1.0 core / ≈1.1-1.2 incl. branch-collision → KEEP single data point)
- [x] **AD status**: `AD-Auth-Register-Backend-IAM-Block-B-Phase58` CLOSED; NEW `AD-RBAC-DB-To-JWT-Wiring-Phase58` + `AD-Register-OIDC-User-Linkage-Phase58` + `AD-Tenant-Plan-Tiers-Phase58` + (carry) MFA/recovery/lockout → next-phase-candidates.md
- [x] **MEMORY subfile + pointer** + **CLAUDE.md lean** (Current Sprint + Last Updated)
- [x] **Design note?** — YES (spike sprint — new registration + role-seed domain; 8-point gate per §Step 5.5)

### 4.4 Ship
- [x] **Commit mapping** Day-0 `850ed16c` / Day-1-2 `cbd1ccae` / Day-3 backend `18c246b3` / Day-3 frontend `d711c1fb` / Day-4 closeout `a973d90d` (+ navigator commit pending)
- [ ] **Push + PR** (user-gated — explicit authorization required)
