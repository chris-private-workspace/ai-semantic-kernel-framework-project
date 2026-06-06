# Sprint 57.87 Progress — C-12 IAM Block B: self-service tenant registration backend

**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-87-plan.md`
**Checklist**: `…/sprint-57-87-checklist.md`
**Branch**: `feature/sprint-57-87-register-backend` (from `main` `ab2adcc7`)
**Closes**: `AD-Auth-Register-Backend-IAM-Block-B-Phase58` (3rd C-12 spike; after 57.85 invites + 57.86 credentials)

---

## Day 0 — 2026-06-06 — Plan-vs-Repo Verify + Branch + Decisions

### Accomplishments
- Day-0 three-prong recon (Explore agent + parent re-verify of the critical paths): registration is a create-tenant + first-admin-user + seed-admin-role + audit flow, mirroring `invites.accept`'s User+Role+audit pattern. All target tables already exist → **no migration**.
- Plan (9 sections, mirrors 57.86) + checklist (Day 0-4, cut-line Day-2-end) drafted.
- 2 design forks resolved via AskUserQuestion (2026-06-06): tenant state = **ACTIVE immediately**; first-admin role = **seed real "admin" Role + UserRole**.

### Drift findings (Day-0 three-prong)
- **D1** — no public `api/v1/tenants.py` (only `admin/tenants.py`, all `require_admin_platform_role`). Implication: NEW public router + 2-line `api/main.py` mount + EXEMPT `/api/v1/tenants/register`. (→ plan §3.2 / §8 Risk #7)
- **D2** — `TenantPlan` enum has ONLY `ENTERPRISE` (`identity.py:92-96`) but the register wizard sends `plan` ∈ {trial,pro,enterprise} + `size` (no column). Implication: `tenant.plan=ENTERPRISE` + `{requested_plan, company_size}` → `tenant.meta_data`; plan tiers = Phase 56+ Stage 2. (→ plan §8 Risk #5; carryover `AD-Tenant-Plan-Tiers-Phase58`)
- **D3** — `seed_default_roles` is a STUB (`provisioning.py:19,77`) + **no code ever instantiates `Role(...)`**. Implication: register is the codebase's FIRST real Role-creation (seed a minimal "admin" role). (→ plan §0 Fork-2 / §3.1)
- **D4** — authz is JWT-claim-based (`auth.py` `_require_role` reads `request.state.roles`); OIDC callback bakes `roles=["user"]` (`:302`). Implication: the seeded admin UserRole is DB-real but **NOT yet authz-effective** → honest boundary + carryover `AD-RBAC-DB-To-JWT-Wiring-Phase58`. (→ plan §0 Fork-2 / §8 Risk #3)
- **D5** — OIDC callback upserts the login user by `(tenant_id, external_id)` (`auth.py:177-209`); register creates the user by `email` (no external_id). Implication: a later OIDC login would create a SECOND user row → carryover `AD-Register-OIDC-User-Linkage-Phase58`. (→ plan §8 Risk #4)
- **D6** — `tenants` RLS-free (INSERT ok); `users`/`roles` RLS-protected. Implication: `_set_tenant(db, new_tenant.id)` before the User/Role/UserRole inserts (mirror invites.py:279). (→ plan §3.1 / §8 Risk #6)
- **D7** — **NO migration** (reuses tenants/users/roles/user_roles). Simpler than 57.85/57.86 (both added migrations). (→ plan §3.4)
- **D8** — register page + `AuthRegister` mockup already COMPLETE (57.23/57.35). Implication: frontend = un-stub only (remove 501 banner, wire 201/409); **no mockup/styles change** (oklch baseline unchanged). (→ plan §3.3/§3.4 / §8 Risk #8)

### go/no-go
GO. Scope ≈ 1× a small backend spike (smaller than 57.86: no migration, no mockup extension, frontend mostly exists; but introduces the first real Tenant-creation-service + first real Role-creation). Day-1/2 service is the safe cut-line.

### Calibration (plan-time)
- **Agent-delegated: no** (parent-direct — security-sensitive public pre-auth endpoint creating tenants + granting admin roles).
- Scope class **`iam-backend-spike` 0.65** — ADOPTED this sprint per the 57.86 carryover `AD-Sprint-Plan-IAM-Backend-Spike-Class` (register = "the next IAM backend spike"). This is its 1st validation data point.
- Bottom-up est ~8.5 hr → class-calibrated commit ~5.5 hr (×0.65). agent_factor 1.0 → 3-segment form.

### Next (Day 1)
`RegistrationService` (`platform_layer/identity/registration.py`): register method + typed errors + lenient singleton + local `_set_tenant`.

---

## Day 1-2 — 2026-06-06 — RegistrationService + service tests (SAFE CUT-LINE)

### Accomplishments
- **NEW `platform_layer/identity/registration.py`** — `RegistrationService.register(...)`: slug-unique check → `Tenant(state=ACTIVE, plan=ENTERPRISE, meta_data={requested_plan, company_size})` → `_set_tenant` → seed `Role(code="admin")` → `User(status=active)` → `UserRole(user→admin)` → `append_audit("tenant_registered")`. Typed errors (`RegistrationError` 400 / `TenantSlugTakenError` 409); local `_set_tenant`; lenient singleton (no lifespan wiring — mirrors 57.85/57.86, avoids the 57.84 leak class).
- **NEW `tests/unit/.../test_registration_service.py`** (6): happy-path (tenant+role+user+userrole+audit) / ACTIVE+ENTERPRISE+meta_data / duplicate-slug→`TenantSlugTakenError` / no-password (OIDC-first) / 2-tenant isolation / exactly-one-admin-role.
- Gates: `mypy src/` **0/343** · flake8 0 · **6/6 service tests green**.
- **Cut-line reached**: registration capability proven at the service/DB layer; nothing HTTP/UI-wired.

### Refinement vs plan
- `register()` returns a `RegistrationResult` dataclass (`.tenant`/`.user`) rather than the plan's bare `tuple[Tenant, User]` — cleaner consumer + mypy-friendly, mirrors invites' `InviteMetadata` dataclass. Trivial impl detail; scope unchanged.

### Drift caught during testing
- **D9 (RLS-untestable-under-superuser, = 57.85 D5 recurrence)** — the first isolation test asserted an RLS-filtered `SELECT *` returned only the tenant's rows; it FAILED (other tenants' rows leaked) because the test DB role is a superuser that bypasses RLS FORCE. Per 57.85's documented resolution, rewrote the isolation assertion to the **application layer** (`WHERE tenant_id == …`) — the production non-superuser role enforces the policy; the unit test pins the app-layer scoping invariant. (Confirms the 57.85 carryover "Day-0 check: if the test DB role is superuser, RLS-block is untestable → assert app-layer".)

### Next (Day 3)
Public `api/v1/tenants.py` (`POST /register`, EXEMPT) + `api/main.py` mount + `tenant_context.py` exempt + integration tests + frontend un-stub + i18n + frontend test.

---

## Day 3 — 2026-06-06 — Endpoint + exempt + mount + frontend un-stub

### Accomplishments
- **Backend**: NEW `api/v1/tenants.py` (`POST /tenants/register`, 201, EXEMPT, lenient `_service()`); `api/main.py` import + `include_router`; `tenant_context.py` EXEMPT `/api/v1/tenants/register` + MHist. NEW `test_tenant_register.py` (6): 201+shape / ACTIVE+meta_data / 409 dup-slug / 422 invalid-slug / 2-tenant isolation (app-layer) / exempt-path. Committed.
- **Frontend**: un-stubbed `/auth/register` — removed AP-2 demo banner + 501-stub copy; wired 201→`/auth/callback` + 409→slug-taken + generic error; i18n `errorSlugTaken`+`error` (en+zh-TW); header docstring + MHist. `register.test.tsx` rewritten (banner-absent + 409 + 201; stepper tests kept) → 6 passed. Committed `d711c1fb`.

### 🔴 Anomaly — concurrent-session branch collision (recovered)
- Mid-Day-3 the working tree was switched to `chore/drive-through-acceptance-principle` by another Claude session sharing the repo dir. `registration.py` (committed on 57.87) was absent on that branch → a phantom mypy `import-untyped` on the registration import, first mis-chased as editable-install staleness (~30-45 min) before `git status` showed the wrong branch.
- **Recovery (no data loss)**: `git stash -u` (preserve Day-3 edits + restore chore worktree clean) → checkout 57.87 → `git stash pop` (the 2 shared files byte-identical across branches → zero conflict) → fixed one real mypy error (`_UserOut.display_name` → `str | None`).
- **Lesson** (retro Q4): wrong-branch/missing-file is far more likely than an editable-install quirk when a first-party import shows "installed missing py.typed" + the mypy source-file count doesn't increment → check `git branch` FIRST. User chose to continue with frequent defensive commits.

---

## Day 4 — 2026-06-06 — Full sweep + design note + closeout

### Accomplishments
- Full sweep: mypy `src/` **0/344** · flake8 0 · `run_all.py` **10/10** · pytest **2214 passed**/4 skipped (+12) · frontend lint(no `--silent`)+build · Vitest **763** · check:mockup-fidelity ✓ (oklch baseline 53 unchanged).
- Design note `23-iam-registration-spike.md` (8-point gate ~95% verified; self-check in retrospective).
- CHANGE-055 + retrospective Q1-Q7 + checklist all `[x]`.
- 17.md = N/A (identity not a registered 11+1 surface).
- Calibration: `iam-backend-spike` 0.65 1st validation; ratio ≈ 1.0 core (≈1.1-1.2 incl. branch-collision anomaly) → KEEP single data point.
- AD `AD-Auth-Register-Backend-IAM-Block-B-Phase58` CLOSED; 3 NEW carryovers (RBAC-JWT-wiring / OIDC-user-linkage / plan-tiers).
