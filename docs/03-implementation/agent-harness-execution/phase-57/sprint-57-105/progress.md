# Sprint 57.105 Progress — RBAC DB→JWT wiring

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-105-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-105-checklist.md)

---

## Day 0 — 2026-06-12 — Three-prong plan-vs-repo verify ✅ GO

**Baseline**: `main` HEAD `ed52d435` (post-#279 docs-reorg merge). Branch `feature/sprint-57-105-rbac-jwt-wiring` created at kickoff.

### Drift findings

| ID | Finding | Implication |
|----|---------|-------------|
| D1 | `grep \.encode\(` sweep: exactly **3 JWT issue sites** in src — callback `auth.py:299-304` (kw `roles=["user"]`, `extra={email, external_id}`), dev-login `:429-434`, password-login `:493-498` (`extra={email}`). No hidden 4th site. | Plan §4 file list complete; rewire = 2 sites (dev-login untouched). |
| D2 | password-login (`:512`) **and** dev-login (`:438`) also put roles in the **response body** (`AuthMeResponse`) — the SPA sets `authStore` from the login payload directly (no /auth/me wait). | The DB-sourced list must feed BOTH `encode()` and the body (one local `roles` var already shared — minimal). Drive-through role render is immediate after login. |
| D3 | **Stale comments** claim "RBAC actual roles loaded per-request via RBACManager" — `auth.py:302`, the `:449-457` password-login comment block, `registration.py:20-24` Honest-boundary docstring. Path 2 is dormant (flag default False) so the claim is false today. | Day 1 fixes all three (Karpathy-3 stale-docstring rule); registration.py docstring updated to "resolved by 57.105". |
| D4 | `RBACManager` house style = `@staticmethod` + keyword-only args (`has_role_code(*, user_id, tenant_id, allowed_codes, session=None)`); inner `_has_role_code_with_session` JOIN (`rbac.py:114-137`) lifts cleanly to a `select(Role.code)` projection. | New method signature aligned: `get_user_role_codes(*, user_id, tenant_id, session)` — **session REQUIRED** (login handlers pass the request session; no factory fallback on this path). |
| D5 | **CONVERT list is EMPTY** (plan §8 risk dissolves): `test_password_login.py:120` user is seeded with NO UserRole → claim stays `["user"]` → green; the invite-joiner test (`:253`) asserts email+cookie only; `test_auth_me.py:118` self-encodes its claim (echo path, unaffected); `test_dev_login` untouched. | Day 2 becomes EXTEND-only: founding-admin chain + invited-role-in-body assertions. 0 conversions, 0 deletions. |
| D6 | dev-login prod gate confirmed: `_is_production()` → 404 (`auth.py:381-402`, `Settings.env in {production, prod}`). | Keeping `_DEV_LOGIN_ROLES` is dev-only debt — documented in CHANGE-072, not hidden. |
| D7 | password-login tenant key: roles query will use `user.tenant_id` — the exact value encoded into the JWT (`:495`) and used for the tenant lookup (`:490`). | Cross-tenant isolation pinned by unit test. |
| D8 | Integration test apps (`test_password_login.py:_build_app`) use an `X-Test-Roles` header middleware + `require_admin_platform_role` dependency-override — the REAL gate's claim→200/403 behavior is covered by the existing admin suites. | US-4 chain test proves the claim by **decoding the login response's `v2_jwt` cookie** (JWTManager().decode → roles ⊇ {user, admin}); the gate poles ride existing fixtures. |
| D9 | `registration.py:13`: the shipped register wizard redirects to OIDC `/auth/callback` to log in — but register stores the password (57.86 CredentialsService), so the founding admin CAN password-login directly. | Drive-through spine confirmed: register → `/auth/password-login` → admin (no OIDC, no dev-login) — exactly plan §0. |
| D10 | Prong 2.5: `authStore.roles` sources = `/auth/me` (`authStore.ts:76`) + login payload only; no other FE roles source. Prong 3: N/A (no schema change); `Role` unique `(tenant_id, code)` + `UserRole` PK `(user_id, role_id)` confirmed. | Zero FE code holds. |

### Go/no-go

**GO** — scope shift ≈ 0 (D5 actually shrinks Day 2: convert→extend). No plan §Technical Spec rewrite needed; D2/D3/D4/D8 folded as execution detail.

---

## Day 1 — 2026-06-12 — Backend wiring (US-1/2/3) ✅

- **`rbac.py`**: NEW `RBACManager.get_user_role_codes(*, user_id, tenant_id, session)` — `select(Role.code) JOIN UserRole` tenant-scoped projection, sorted+deduped; session REQUIRED (login handlers pass the request session). `has_role_code` untouched.
- **`auth.py`**: callback (`roles=["user"]` hardcode retired) + password-login (`_PASSWORD_LOGIN_ROLES` deleted) both issue `sorted({"user", *db_codes})` into the JWT AND the response body (D2); dev-login untouched (dev-only, `_is_production()` 404 gate — D6). Stale "per-request RBAC" comments fixed (D3).
- **`registration.py`**: honest-boundary docstring resolved (the seeded admin grant is now JWT-effective at login).
- **Unit tests**: `TestGetUserRoleCodes` (sorted+dedup / empty) — `test_rbac.py` 9/9.
- Gates: mypy `src` 0/357 · black/isort/flake8 clean.

## Day 2 — 2026-06-12 — Integration chain (US-4) ✅

### Drift finding

| ID | Finding | Implication |
|----|---------|-------------|
| D11 | **`POST /tenants/register` collects NO password** (request body: email/full_name/company_name/tenant_slug/region/plan/size — `test_tenant_register.py:51-60`); the shipped 57.87 wizard logs in via OIDC `/auth/callback` (`registration.py:13`). Plan §0's "register stores the password via CredentialsService" assumption was WRONG. | The founding-admin chain sets the password via `CredentialsService.set_password` (the 57.86-proven primitive) after register. **Day 3 drive-through adjusted**: register via UI → set founding password via one out-of-band `set_password` call (or use the invite-accept UI path) → password-login via UI → admin proof. The authz proof (DB grant → claim → gate) is unaffected; password mechanics were 57.86's already-proven scope. |

### Work

- `test_password_login.py` +3 tests (12/12 green): **founding-admin chain** (register HTTP → `set_password` → password-login → claim+body `== ["admin","user"]`, JWT-decoded) · **grant test** (`Role(code="admin")`+`UserRole` → `["admin","user"]`) · **cross-tenant isolation** (foreign-tenant grant invisible → `["user"]`, multi-tenant 鐵律). Existing invite test EXTENDED: invited `member` role now claim-effective (`["member","user"]`).
- D5 confirmed in practice: ZERO conversions needed (role-less success test stays `["user"]` green).
- Full auth/identity sweep: 95/95. Full pytest: **2384 passed + 4 skipped (+5, 0 deletions)**. `run_all` 10/10 (event count UNCHANGED). `loop.py` / DB / migration / wire schema / frontend diff = 0.
- Infra note: Docker Desktop + Postgres were DOWN at Day-2 start (57.101 Risk Class lesson applied — port check first, `docker compose up -d`, then tests).

---

## Day 3 — 2026-06-12 — Drive-through (US-5) ✅ PASS + CHANGE-072 + note-23 edit

### Clean restart (Risk Class E)

Environment was already clean: NO listener on :8000/:3007, NO stale python spawn-workers
(`Win32_Process` sweep = zero python.exe). Started a **fresh no-`--reload` single uvicorn**
(PID 7672, sole :8000 owner; `api.main:app --app-dir src`) with startup log captured
(`artifacts/backend-dt57105.log` — "startup complete" + pricing loader wired) + Vite :3007.

### Drive-through — observed vs intended (NO dev-login anywhere)

| Step | Intended | Observed |
|------|----------|----------|
| Register | `/auth/register` wizard → 201 | 4-step wizard (Identity → Organization → Plan) → **`POST /tenants/register` 201** (tenant `dt57105-rbac` / `founder@dt57105.test`); wizard then redirected to `/auth/callback` (OIDC, unconfigured locally) → bounced to `/auth/login`. Expected boundary per D9/D11 + `AD-Register-OIDC-User-Linkage-Phase58`. The Confirm step was not observed as a separate stop (Plan-step Continue submitted) — pre-existing wizard flow, out of scope. |
| Set password (D11 adjustment) | one out-of-band `CredentialsService.set_password` | One inline call (user_id `6af30afd…`, tenant_id `aba7f2a9…`); no leftover script file. |
| Password-login | `/auth/password-login` → lands in app | **POST 200** + `GET /auth/me` 200 → landed `/cost-dashboard`. |
| Role renders admin (ISSUE-6) | sidebar/user card shows admin | Sidebar user card: **"DT Founder / admin"**; header "· admin". **ISSUE-6 observably closed** (was: every page renders role=user). Screenshot `dt57105-admin-renders.png`. |
| Admin write (C1 tab) | Model Policy PUT 200, not 403 | Tenant Settings showed the REAL tenant (DT57105 RBAC Co / dt57105-rbac); Model Policy tab → Edit → action `gpt-5.4-mini` (priced) → Save → **PUT `/admin/tenants/aba7f2a9…/model-policy` 200** + saved value re-rendered. **First admin write ever driven with no dev-login.** Screenshot `dt57105-model-policy-put200.png`. |
| Negative pole | role-less session → 403 | Minted a role-less JWT (`roles=["user"]`, SAME user/tenant) → same PUT → **403 "Platform admin role required"**. |
| Cleanup | revert policy edit; note throwaway tenant | Override cleared via the tab (Edit → empty → Save → "System default" re-rendered; clear path proven). Throwaway tenant `dt57105-rbac` left in dev DB (valid data; trial plan; no shared-tenant pollution — the edit never touched acme-prod). |

**Honest carryover (pre-existing, NOT this sprint)**: the sidebar tenant-switcher + header
tenant label render fixture "acme-prod tenant_01h9a2 · Pro" regardless of the real logged-in
tenant (the Tenant Settings page itself shows the real tenant). FE tenant-display sourcing is
a separate AD candidate — logged to next-phase-candidates at closeout.

### Drift finding

| ID | Finding | Implication |
|----|---------|-------------|
| D12 | Checklist 3.3 said "17.md — JWT roles-claim sourcing semantics row"; but note 23 §4 (and the 57.84/85/86/87 precedent, 4 sprints) explicitly rules identity **N/A to 17.md** ("identity is a platform_layer surface, NOT one of the 11+1 categories"). Adding a first-ever identity row would break the registry's scope consistency. | Resolved by precedent: semantics recorded in note 23 §5 RESOLVED entry + CHANGE-072 instead; checklist item marked done with annotation (decision = the deliverable). |

### Docs

- `CHANGE-072-rbac-db-to-jwt-wiring.md` created (problem / Option A design / verification / open invariants).
- note 23 §5: `AD-RBAC-DB-To-JWT-Wiring-Phase58` → **✅ RESOLVED Sprint 57.105** (OIDC-linkage stays open); MHist +1. No new design note (gap-fix continuation).

---

## Day 4 — 2026-06-12 — Closeout ✅

- retrospective.md Q1-Q7 written (Q2: `iam-backend-spike` 0.65 2nd validation, actual ≈6.5 hr vs committed 6.8 hr → ratio ≈0.95 IN band → KEEP; 3-sprint window now 57.87 ≈1.0 + 57.105 ≈0.95).
- sprint-workflow.md matrix: `iam-backend-spike` 0.65 row ADDED (had been plan-only since 57.87).
- CLAUDE.md Current Sprint + Last Updated (lean) · MEMORY.md quality pointer + `project_phase57_105_rbac_jwt_wiring.md` subfile (auto-memory dir — initial Write to repo `memory/` was relocated; the repo has no `memory/` dir).
- next-phase-candidates.md: AD closed + 🆕 `AD-FE-Tenant-Display-Fixture-Phase58` + next slice **C3** per interleave decision.
- Checklist: all items `[x]`; 0 deleted.

