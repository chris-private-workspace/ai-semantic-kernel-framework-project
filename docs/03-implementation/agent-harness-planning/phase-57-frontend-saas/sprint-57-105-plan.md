# Sprint 57.105 Plan — RBAC DB→JWT wiring: a DB role grant becomes authz-effective on the real login paths (OIDC callback + password-login issue DB-sourced roles claims), closing `AD-RBAC-DB-To-JWT-Wiring-Phase58` — the production-drivability unlock for every admin endpoint (C1 tab + 57.55-57.57 admin PUTs)

**Category / Scope**: platform_layer (identity — RBAC / JWT issue-time roles) × api/v1/auth (callback + password-login) — Phase 57 / Sprint 57.105
**Created**: 2026-06-12
**Status**: Draft
**Plan authority**: mirrors the most-recent completed sprint plan (`sprint-57-104-plan.md`, 9 sections 0-9). Scope differences expressed through content, not structure.

> **Modification History**
> - 2026-06-12: Initial draft (RBAC DB→JWT wiring: `get_user_role_codes` + DB-sourced roles claim at OIDC callback + password-login; founding-admin register→login→admin-PUT e2e; dev-login hardcode kept dev-only)

---

## 0. Background

Every admin endpoint is gated by `require_admin_platform_role` (`platform_layer/identity/auth.py:142-154`) whose Path 1 reads the JWT `roles` claim — but **all three login paths hard-code the claim at issue time**: the OIDC callback bakes `roles=["user"]` (`api/v1/auth.py:302`), password-login bakes `_PASSWORD_LOGIN_ROLES = ("user",)` (`auth.py:458, 491`), and only dev-login bakes `_DEV_LOGIN_ROLES = ("user", "admin", "platform_admin")` (`auth.py:378, 432`). Meanwhile the DB has REAL roles since Sprint 57.85/57.87: registration seeds an `admin` `Role` + grants the founding user a `UserRole` (`platform_layer/identity/registration.py:160-180`), and invites grant the invited `role_id` on accept. Result (drive-through audit ISSUE-6, confirmed live): a real-login admin renders role=`user` everywhere and 403s on every admin PUT — the C1 Model Policy tab + the 57.55-57.57 quotas/feature-flags/rate-limits PUTs are **only drivable via dev-login**. This slice makes the DB role grant JWT-effective on the real login paths, closing `AD-RBAC-DB-To-JWT-Wiring-Phase58` (logged 57.87; confirmed by both drive-through audits; flagged as C1's soft-prereq; user-selected as the next slice 2026-06-12 with the interleave stream mode).

### Design decision (issue-time DB roles, not per-request fallback)

The repo already has BOTH halves of the seam: `RBACManager.has_role_code(db?, user_id, tenant_id, codes)` queries `Role JOIN UserRole` (`platform_layer/identity/rbac.py:66-137`), and `_require_role` has a dormant Path 2 DB fallback behind `Settings.rbac_db_backed_fallback` (default False, `core/config/__init__.py:71`). This slice chooses **issue-time**: query the user's role codes once at login and bake them into the JWT (§3.0 options table) — single source of truth stays the JWT claim, `/auth/me` + the frontend `authStore.roles` fix themselves with zero FE code, and no per-request DB cost. The trade-off (claim staleness until re-login) is documented as an invariant (§8).

### Why password-login is the e2e spine (not OIDC)

The founding-admin proof path is **register → password-login → admin PUT**: 57.87's register stores the password via `CredentialsService.set_password` and seeds the admin role, and 57.86's `POST /auth/password-login` mirrors dev-login's JWT/cookie issue (`auth.py:469-520`). The OIDC callback gets the SAME `get_user_role_codes` wiring, but its e2e proof is blocked by a separate pre-existing AD: register creates the user by `email` with no `external_id`, while the callback upserts by `(tenant_id, external_id)` → an OIDC login of the founding admin can hit a SECOND user row with no roles (`AD-Register-OIDC-User-Linkage-Phase58` — out of scope, §9). The drive-through therefore proves the wiring on password-login; the callback wiring is unit/integration-proven.

### Ground truth (Day-0 head-start — 1 Explore recon agent, file:line anchors on `main` HEAD `ed52d435` post-#279-merge)

- **JWT encode/claims** — `platform_layer/identity/jwt.py:103-237`: `JWTManager.encode(sub, tenant_id, roles=[], …)` → HS256 payload `{sub, tenant_id, roles: list[str], iat, exp}`; claim field name exactly `"roles"` (`:160`); decode validates `roles: list[str]` (`:204-237`). Cookie `v2_jwt` httponly; middleware reads Bearer-or-cookie → `request.state.roles`.
- **The three issue sites** — OIDC callback `roles=["user"]` (`api/v1/auth.py:302`); dev-login `_DEV_LOGIN_ROLES` (`:378, :432`); password-login `_PASSWORD_LOGIN_ROLES = ("user",)` (`:458, :491`). All three handlers already have an `AsyncSession` in scope (the upsert/authenticate paths use it).
- **RBAC query shape** — `RBACManager.has_role_code` (`platform_layer/identity/rbac.py:66-137`): `Role JOIN UserRole` filtered `(user_id, tenant_id, code IN …)`; opens its own session via `get_session_factory()` only when none passed. `has_permission` (`:140-173`) is a deny-all STUB (Phase 58+; uncalled on the hot path) — NOT this slice.
- **Gates** — `_ADMIN_PLATFORM_ROLES = {"admin", "platform_admin"}` (`platform_layer/identity/auth.py:118`); `_require_role` Path 1 = `request.state.roles` claim check (`:189-235`); Path 2 DB fallback dormant (flag default False). **The founding role code `"admin"` (`registration.py:160-167`, `FOUNDING_ADMIN_ROLE_CODE`) IS in `_ADMIN_PLATFORM_ROLES`** → a founding admin passes the platform gate once the claim carries it.
- **Role write points** — registration seeds `admin` Role + founding UserRole (`registration.py:160-180`); invites grant the invited `role_id` on accept (`invites.py:144-200`); dev-login creates a dev User but NO Role/UserRole (its roles are JWT-hardcode only).
- **ORM** — `Role` tenant-scoped, unique `(tenant_id, code)` (`infrastructure/db/models/identity.py:236-261`); `UserRole` PK `(user_id, role_id)`, no tenant_id column (tenant via Role FK) (`:267-292`).
- **Frontend** — `authStore` bootstraps from `GET /auth/me` → `roles: string[]` (`frontend/src/features/auth/store/authStore.ts:72-85`); `/auth/me` reads `request.state.roles` (`api/v1/auth.py:354`) → **zero FE code needed**; the role render + admin-gated content fix themselves.
- **Tests** — `tests/integration/api/test_jwt_auth.py` (claims/expiry/signature) + `test_auth_me.py` exist; password-login/registration integration tests exist from 57.86/57.87 (pin exact files Day-0).

### STALE / drift anchors to re-confirm in the formal Day-0 三-prong (§ checklist 0.1)

- Exact line numbers of the three issue sites + whether `_PASSWORD_LOGIN_ROLES` / the callback literal are referenced anywhere else (grep before retiring).
- `JWTManager.encode` call shape at each site (positional vs kw `roles=`) + the `extra` claims each site passes.
- Whether the callback / password-login handlers' `AsyncSession` is request-scoped (`Depends(get_db_session)`) or self-opened — pass the in-scope session to `get_user_role_codes` (no second session).
- The `has_role_code` JOIN internals to extract (`_has_role_code_with_session` shape) — confirm a `select(Role.code).join(UserRole)…` projection is cleanly liftable.
- Password-login's tenant resolution (how `tenant_id` reaches the handler — body slug? cookie?) — the roles query needs the same `tenant_id` the JWT gets.
- Existing tests asserting the hardcoded claims (e.g. password-login asserts `roles == ["user"]`) — pin the convert list (Never-Delete → convert assertions to DB-sourced expectations).
- Whether dev-login is prod-disabled (Settings flag / env gate) — confirms keeping its hardcode is dev-only debt, documented not hidden.
- `/auth/me` response schema field for roles (AuthMeResponse) — confirm no FE mapping surprises.

---

## 1. Sprint Goal

A user's REAL DB roles become their JWT `roles` claim on the real login paths: the OIDC callback and password-login query `Role JOIN UserRole` at issue time (`["user"] ∪ db_codes`, deduped) instead of hard-coding, so a founding admin created by 57.87's register flow can password-login and drive every admin endpoint (C1 Model Policy tab + quotas/feature-flags/rate-limits PUTs) in a real session — no dev-login. `/auth/me` + the frontend role render fix themselves (zero FE code). Closes `AD-RBAC-DB-To-JWT-Wiring-Phase58`. `loop.py` / DB schema / wire events / frontend diff = 0.

## 2. User Stories

- **US-1 (role-codes query)** — As the platform, I want `RBACManager.get_user_role_codes(user_id, tenant_id, db) -> list[str]` (the `has_role_code` JOIN lifted to a projection, tenant-scoped, deduped, sorted), so that login handlers can fetch a user's effective role codes with one query on the request session.
- **US-2 (OIDC callback issues DB roles)** — As a platform user, I want the OIDC callback to issue my JWT with `["user"] ∪ get_user_role_codes(...)` instead of the hardcoded `["user"]` (`auth.py:302` retired), so that an OIDC login carries my real grants.
- **US-3 (password-login issues DB roles)** — As a founding admin (or invited member), I want `POST /auth/password-login` to issue my JWT the same way (`_PASSWORD_LOGIN_ROLES` retired), so that the 57.87 register-seeded admin grant is authz-effective on my next real login.
- **US-4 (admin e2e authz proof)** — As the platform, I want integration tests proving the full chain — register (seeds admin) → password-login → JWT decode contains `admin` → admin PUT 200; and a role-less user's JWT stays `["user"]` → admin PUT 403 — so the gate behavior is pinned at both poles.
- **US-5 (drive-through)** — As the developer, I want a real-UI run: register a fresh tenant → password-login as the founding admin → the role renders as admin and the tenant-settings admin write (Model Policy tab PUT) succeeds WITHOUT dev-login, so the "every page renders role=user" ISSUE-6 is observably closed (driven, not gate-only).

## 3. Technical Specifications

### 3.0 Architecture (issue-time DB roles; gating + middleware + FE untouched)

```
login (OIDC callback | password-login)
  → upsert/authenticate User (existing)
  → roles = ["user"] ∪ RBACManager.get_user_role_codes(user_id, tenant_id, db)   ← NEW
  → JWTManager.encode(sub, tenant_id, roles=roles)                               (unchanged)
  → middleware decodes → request.state.roles → _require_role Path 1              (unchanged)
  → /auth/me → authStore.roles → role render + admin gates                       (unchanged, self-healing)
```

**Key design decision — where DB roles enter the authz chain:**

| Option | Mechanism | Verdict |
|--------|-----------|---------|
| **A. Issue-time DB roles in the JWT (CHOSEN)** | Login handlers query role codes once, bake into the claim. | ✅ Single source stays the JWT; zero per-request DB cost; `/auth/me` + FE + every `_require_role` gate fix themselves with no further change; smallest diff (2 issue sites + 1 query method). Staleness = until re-login (documented invariant). |
| B. Flip `rbac_db_backed_fallback=True` (Path 2) | Per-request DB check fires when the claim fails. | ❌ The claim (and therefore `/auth/me` + FE role render) stays wrong — ISSUE-6 unfixed; adds a DB query on every gated request; dual-source ambiguity. Keep the flag as-is (dormant defense-in-depth). |
| C. Per-request middleware DB role load | Middleware replaces claim roles with a DB read each request. | ❌ Hot-path DB cost on EVERY request; bigger blast radius (middleware), needs caching → Risk Class C; staleness is the only gain (YAGNI now). |
| D. Token refresh on role change | Push new JWTs when grants change. | ❌ No refresh mechanism exists; speculative infra (AP-6). Role changes take effect at next login — documented. |

`loop.py` diff = 0; no DB schema / migration; no new event; no FE code (US-5 verifies the self-healing render).

### 3.1 Role-codes query (US-1)

- `backend/src/platform_layer/identity/rbac.py` — NEW method `get_user_role_codes(user_id, tenant_id, db) -> list[str]`: `select(Role.code).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user_id, Role.tenant_id == tenant_id)` → sorted deduped codes. Reuses the exact `has_role_code` JOIN shape (lift, don't fork — `has_role_code` itself stays as the Path 2 fallback's primitive). Accepts the caller's `AsyncSession` (login handlers pass the request session; no second session / no self-opened factory on this path). Multi-tenant 鐵律: tenant filter on `Role.tenant_id` (UserRole has no tenant column — the JOIN provides it).
- NOT a cache: roles are read once per login (not per request) — no TTL/singleton, no Risk Class C surface.

### 3.2 OIDC callback issues DB roles (US-2)

- `backend/src/api/v1/auth.py` (callback, ~`:296-302`) — after the user upsert: `role_codes = await rbac.get_user_role_codes(user.id, tenant_id, db)`; `roles = sorted({"user", *role_codes})`; `JWTManager.encode(..., roles=roles)`. The `roles=["user"]` literal is retired at this site. A role-less user's claim is exactly `["user"]` — byte-identical to today.
- Note: the OIDC path's founding-admin e2e is gated by `AD-Register-OIDC-User-Linkage-Phase58` (the callback may upsert a different user row than register created) — the wiring is correct per-user-row; the linkage AD stays its own slice (§9).

### 3.3 Password-login issues DB roles (US-3)

- `backend/src/api/v1/auth.py` (password-login, ~`:458, :491`) — same pattern: after `CredentialsService.authenticate` resolves the user, query role codes on the request session, `roles = sorted({"user", *role_codes})`, encode. Retire `_PASSWORD_LOGIN_ROLES` (grep for other references first — Day-0). Invited members (57.85 accept grants the invited role) become role-effective at next login automatically.
- **dev-login is deliberately untouched**: `_DEV_LOGIN_ROLES` stays (dev-only convenience; the dev user has no DB grants by design). Confirm + document its prod-disabled gate in Day-0; note the divergence in CHANGE-072 (honest debt, not hidden).

### 3.4 What is explicitly NOT done + Lint / neutrality / 17.md / docs

- NO `has_permission` implementation (deny-all stub stays — Phase 58+ RolePermission engine, uncalled on the hot path). NO Path 2 flag flip. NO token refresh / live revocation. NO FE code. NO new event / codegen / migration. `agent_harness/**` untouched (identity is platform_layer + api concern) — `check_llm_sdk_leak` + `check_cross_category_import` stay green.
- 17.md: update the JWT/identity contract row — the `roles` claim is now DB-sourced at issue time on real login paths (semantics note; no new ABC).
- Docs: **NO new design note** — this is a gap-fix continuation of the IAM block (57.85/86/87 spikes own notes 21/22/23), not a new domain; instead EDIT design note `23-iam-registration-spike.md` §Open Invariants (the RBAC-wiring invariant resolves) — pin the exact section in Day-0. + `CHANGE-072` + closeout set.

### 3.5 Validation (US-1..US-5)

- Backend unit (rbac): `get_user_role_codes` — no grants → `[]`; admin grant → `["admin"]`; multi-role dedup/sort; cross-tenant isolation (a grant in tenant A invisible under tenant B).
- Backend integration (auth): register → password-login → decode JWT → claim contains `admin` + `user`; a credentials user with no grants → claim exactly `["user"]`; founding-admin JWT → admin PUT (model-policy or quotas) 200; role-less JWT → 403; `/auth/me` echoes the DB-sourced roles. CONVERT any existing assertions pinned to the old hardcodes (Never-Delete → convert).
- Drive-through (US-5): real UI + real backend — register fresh tenant via the wizard → password-login as founding admin → role renders admin (ISSUE-6 closed) → tenant-settings Model Policy tab PUT 200 without dev-login; screenshots + observed-vs-intended into progress.md.

## 4. File Change List

**Backend (src) — ~2 files**
- `platform_layer/identity/rbac.py` — EDIT: NEW `get_user_role_codes(user_id, tenant_id, db)` (US-1)
- `api/v1/auth.py` — EDIT: callback + password-login issue `["user"] ∪ db_codes`; retire the two hardcode sites (`:302` literal, `_PASSWORD_LOGIN_ROLES`); dev-login untouched (US-2/US-3)

**Tests — ~3 files (convert + extend; 0 deletions)**
- `backend/tests/unit/platform_layer/identity/test_rbac*.py` — EXTEND: `get_user_role_codes` (empty / granted / dedup / cross-tenant) (US-1)
- `backend/tests/integration/api/test_auth_password_login*.py` (57.86 suite — pin Day-0) — EXTEND/CONVERT: DB-sourced claim assertions + founding-admin chain (US-3/US-4)
- `backend/tests/integration/api/` (registration / auth_me / admin-gate suites — pin Day-0) — EXTEND: register→login→admin-PUT 200 + role-less 403 + `/auth/me` roles (US-4)

**Docs**
- `claudedocs/4-changes/feature-changes/CHANGE-072-rbac-db-to-jwt-wiring.md` — NEW
- `docs/03-implementation/agent-harness-planning/23-iam-registration-spike.md` — EDIT (§Open Invariants: RBAC-wiring resolved; OIDC-linkage stays open)
- `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md` — EDIT (JWT roles-claim sourcing semantics)
- progress.md / retrospective.md / checklist / CLAUDE.md (Current Sprint + Last Updated) / MEMORY.md pointer + subfile / next-phase-candidates (AD closed; ISSUE-6 closed; next per interleave: C3) / sprint-workflow.md calibration row (`iam-backend-spike` 2nd validation)

## 5. Acceptance Criteria

1. `get_user_role_codes` returns tenant-scoped deduped role codes; empty for a role-less user. (US-1)
2. OIDC callback + password-login JWTs carry `["user"] ∪ db_codes`; the two hardcode sites are retired; a role-less user's claim is byte-identical `["user"]`. (US-2/US-3)
3. Integration chain green: register → password-login → claim contains `admin` → admin PUT 200; role-less JWT → 403; `/auth/me` echoes DB-sourced roles. (US-4)
4. dev-login behavior unchanged (`_DEV_LOGIN_ROLES`, dev-only) — existing dev flows + tests unaffected.
5. Gates: mypy `src` 0 · flake8 clean · `run_all` 10/10 (event count UNCHANGED) · full pytest green (+N, 0 deletions) · frontend build/lint/Vitest untouched-green · `check:mockup-fidelity` unchanged.
6. `loop.py` / DB schema / migration / generated wire schema / frontend diff = 0.
7. Drive-through PASS: register → password-login → admin role renders + Model Policy tab PUT 200 with NO dev-login (real UI; screenshots + observed-vs-intended). (US-5)

## 6. Deliverables

- [ ] US-1 `get_user_role_codes` (tenant-scoped projection on the request session)
- [ ] US-2 OIDC callback DB-sourced roles claim (`:302` hardcode retired)
- [ ] US-3 password-login DB-sourced roles claim (`_PASSWORD_LOGIN_ROLES` retired; dev-login untouched)
- [ ] US-4 integration chain (register→login→admin-PUT 200; role-less 403; /auth/me) + unit tests + hardcode-assertion conversions
- [ ] US-5 drive-through PASS (register → password-login → admin renders + admin PUT, no dev-login; screenshots)
- [ ] Full gate sweep green (event count unchanged; loop.py/DB/FE diff 0)
- [ ] CHANGE-072 + design note 23 §Open Invariants edit + 17.md
- [ ] Closeout (progress / retrospective / CLAUDE.md lean / MEMORY pointer + subfile / next-phase-candidates / calibration row)

## 7. Workload Calibration

- Scope class **`iam-backend-spike` 0.65 (2nd validation data point)** — 57.85/57.86 greenfield-IAM over-runs (~1.25 / ~1.15-1.2 under `medium-backend` 0.80) proposed the class; 57.87 1st validation ran ratio ≈1.0 → KEEP. This slice is the 4th IAM backend leg (smaller than the 3 spikes: no new table / no new endpoint / no FE — a query method + 2 issue-site rewires + test conversions), so 0.65 is conservative-correct; the Day 4 retro Q2 ratio feeds the 3-sprint window.
- **Agent-delegated: no** (parent-direct; `agent_factor = 1.0`) — auth/JWT issue sites are a security-sensitive small-diff surface; consistent with the 57.98-57.104 parent-direct streak.
- Bottom-up est ~10.5 hr (backend ~3 + tests/conversions ~3.5 + drive-through ~2 + docs/closeout ~2) → class-calibrated commit ~6.8 hr (mult 0.65). Day 4 retro Q2 verifies the ratio.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|-----------|
| **Claim staleness** — a grant/revoke after login isn't effective until re-login (JWT TTL). | Accepted invariant for this slice (issue-time design); documented in CHANGE-072 + design note 23. Revocation-sensitive flows can later flip `rbac_db_backed_fallback` (deny-side check) or add refresh — both out of scope. |
| **OIDC founding-admin linkage** (`AD-Register-OIDC-User-Linkage-Phase58`) — the callback may upsert a different user row (by `external_id`) than register created (by email) → that row has no roles. | Known pre-existing AD, out of scope (§9). The wiring is per-user-row correct; the e2e proof rides password-login (the linkage-free real path). Noted in CHANGE-072 Open Invariants. |
| **Existing tests pinned to hardcoded claims** — 57.86/57.87 suites may assert `roles == ["user"]` on password-login. | Day-0 Prong 2 greps the assertion sites; CONVERT expectations (Never-Delete); the conversion list is pinned before Day 1 code. |
| **Session reuse at issue sites** — opening a second session inside the login handlers (instead of passing the request session) risks pool churn + RLS context loss. | `get_user_role_codes` REQUIRES the caller's session (no self-opened factory on this path); Day-0 confirms both handlers' session is request-scoped and in scope at the encode site. |
| **Password-login tenant resolution** — the roles query must use the same `tenant_id` the JWT gets. | Day-0 pins how the handler resolves tenant (slug/body) and asserts the query + encode use the identical value; cross-tenant isolation unit test pins it. |
| **Risk Class E (stale `--reload` worker)** — the drive-through verifies issue-time behavior (login-path code). | Clean restart before the drive-through: kill stale uvicorn reloader + spawn-workers (`Get-CimInstance Win32_Process` PID/PPID/StartTime sweep), fresh PID sole :8000 owner; frontend node untouched. |
| **dev-login divergence** — dev-login keeps hardcoded roles while real paths go DB-sourced. | Deliberate (dev-only convenience; dev user has no grants by design). Day-0 confirms dev-login's prod gate; divergence documented in CHANGE-072 (honest debt). |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- **`has_permission` real implementation** (RolePermission resource-pattern engine) — Phase 58+; the stub stays deny-all and uncalled on the hot path.
- **`rbac_db_backed_fallback` default flip / per-request DB authz** — dormant defense-in-depth; revisit if revocation latency becomes a requirement.
- **Token refresh / live role revocation** — no refresh infra exists (AP-6 to invent now).
- **`AD-Register-OIDC-User-Linkage-Phase58`** — callback link-by-email OR register-OIDC-initiated; its own slice.
- **dev-login DB-backed roles** — dev-only hardcode stays; documented.
- **Role management surface** (admin UI to grant/revoke roles; role CRUD beyond register/invite seeds) — Phase 58 IAM continuation.
- **FE role-based gating expansion** (e.g. hiding admin-only widgets for non-admins beyond what exists) — the slice only makes existing gates truthful; new gating UX is its own UX slice.
- **C-12 remaining legs** (MFA TOTP/WebAuthn, recovery, lockout) — later IAM spikes.
- **C3 / B3 / C2 / B4 / A3** — later slices in the agreed interleave order (next per 2026-06-12 decision: C3).
