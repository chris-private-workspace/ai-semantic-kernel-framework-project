# Sprint 57.85 — Checklist (C-12 IAM Block B: invites vertical spike)

**Plan**: `sprint-57-85-plan.md`
**Branch**: `feature/sprint-57-85-iam-invites` (from `main` `259d6070`)
**Closes**: `AD-Auth-Invite-Backend-IAM-Block-B-Phase58` (invites leg of C-12 Block B). Register / credentials / MFA = follow-up slices (§9).

---

## Day 0 — Plan-vs-Repo Verify + Branch + Decisions

### 0.1 Day-0 verify (Explore three-prong + parent grep/read, main `259d6070`)
- [x] **Prong 1 (path)** — reusable Block-A infra confirmed: `jwt.py:133-189` (JWTManager), `auth.py:62-98` (tenant/user deps) + `:142-154` (admin RBAC), `rbac.py:66-112` (has_role_code), `worm_log.py` (WORMAuditLog.append), `identity.py:101-287` (Tenant/User/Role/UserRole ORM). 0 invites backend files (greenfield).
- [x] **Prong 2 (content)** — frontend invite contract: GET `/invites/{token}` (`invite/index.tsx:69`) + POST `/invites/{token}/accept` `{full_name, password}` (`:90`); fixture+banner at `:48-53`/`:154-162`. login page OIDC-only (no password field, `:158-176`). No email/credential facility (Drift D1/D4). OIDC callback EXEMPT precedent for guest context (`auth.py:164-209`).
- [x] **Prong 3 (schema)** — `User` email per-tenant unique (`identity.py:218` `uq_users_tenant_email`, Drift D2); migration head `0025_billing_outbox` → next `0026` (exact down_revision read Day-1); RLS two-policy + sentinel-escape template from `0025` (reuse); new model must register in `models/__init__.py`.
- [x] **Drift findings** — D1 (no email → create returns raw token in-response); D2 (User email per-tenant unique → accept duplicate → 409); D3 (guest-context RLS → sentinel escape, mirror billing_outbox); D4 (password deferred — accepted-not-stored, split to 57.86).
- [x] **Design locked** (AskUserQuestion ×4, 2026-06-06): DB-backed opaque token (not JWT); admin create endpoint INCLUDED (true e2e); **password split to 57.86** (after the new-info round: login OIDC-only + mockup forbids password field + no UI consumer). 57.85 = invite lifecycle only.
- [x] **go/no-go** — GO; Day-2-end cut-line (table+service+tests); HTTP+frontend wire can carryover as `AD-Invites-Endpoints-Wire` if Day-3 over-runs.

### 0.2 Branch + decisions
- [x] **Branch created** `feature/sprint-57-85-iam-invites` (from `main` `259d6070`)
- [x] **Decisions locked**: `invites` table (TenantScopedMixin); opaque token `secrets.token_urlsafe(32)` + `sha256` hash (raw shown once); status state machine pending→accepted(single-use)/revoked/expired; sentinel-scoped guest lookup + per-row `set_config` for writes; admin create (RBAC) + guest GET/accept (exempt path); password accepted-not-stored; parent-direct (`agent_factor` 1.0).
- [x] **Day-0 commit** plan + checklist + progress.md Day 0 (`0d5d81d6`)

---

## Day 1 — Schema: `invites` table + migration + ORM (US-1/US-4)

### 1.1 ORM model
- [x] **NEW `infrastructure/db/models/invites.py`** — `Invite` (TenantScopedMixin): id(UUID PK)/tenant_id/email/role_id(FK roles)/invited_by(FK users)/token_hash(64)/status/expires_at/accepted_at/accepted_user_id(FK users)/created_at + UNIQUE(token_hash) + status CHECK + idx_invites_tenant + partial-unique(tenant_id,email WHERE pending)
  - DoD: mypy clean (337 files) ✅; columns match plan §3.1
- [x] **Register** in `infrastructure/db/models/__init__.py` (after `identity` import) + `__all__`
  - DoD: `check_rls_policies` discovers `invites` (10/10 green) ✅

### 1.2 migration 0026
- [x] **Read `0025_billing_outbox.py` header** → `revision="0025_billing_outbox"` → `down_revision="0025_billing_outbox"`
- [x] **NEW `migrations/versions/0026_invites.py`** — CREATE TABLE + FK(roles CASCADE/invited_by users CASCADE/accepted_user_id users SET NULL) + UNIQUE(token_hash) + partial-unique `uq_invites_pending_email` (tenant_id,email WHERE pending) + idx_invites_tenant + status CHECK + ENABLE+FORCE RLS + `tenant_isolation_invites` (USING + **system-sentinel escape** for guest lookup) + `tenant_insert_invites` (WITH CHECK) — mirror `0025` two-policy
  - DoD: applied **both directions** on Docker DB (upgrade 0025→0026 → downgrade -1 → re-upgrade; `alembic current`=`0026_invites (head)`) ✅; `check_rls_policies` green ✅
- [x] **black + isort + flake8 + mypy src/** — clean (mypy 0/337; flake8 0; black/isort applied)

---

## Day 2 — Service: InvitesService + tests (US-1/US-2/US-3/US-4) — SAFE CUT-LINE

> Day 2 = pure new module + tests, ZERO router/middleware wiring (no live-path risk). The lifecycle is integration-proven at the service/DB layer BEFORE Day-3 wires the HTTP surface.

### 2.1 InvitesService.create + token
- [x] **NEW `platform_layer/identity/invites.py`** — `InvitesService.create(db, *, tenant_id, inviter_user_id, email, role_id, ttl_hours) -> (Invite, raw_token)`; `secrets.token_urlsafe(32)` + `sha256` hex; role-belongs-to-tenant validation; lazy-expire stale pending + dup-pending guard; insert in caller's txn + `invite_created` audit; **lenient singleton** (`maybe_get_invites_service() or InvitesService()` in endpoint — NO lifespan wiring → no leak risk; `set_/get_/maybe_get` retained for test injection)
  - DoD: create persists hash (raw never stored) ✅ (unit)

### 2.2 InvitesService.get_metadata + accept + revoke + errors
- [x] **`get_metadata(db, raw)`** (renamed from get_by_token) — sentinel lookup `WHERE token_hash=:hash` → guard → switch to invite.tenant → read Tenant/User/Role names → `InviteMetadata`; lazy-expire (pending + expires_at<now → expired); typed errors (`InviteNotFoundError`→404 / Expired/Consumed/Revoked→410)
- [x] **`accept(db, raw, *, full_name)`** — sentinel re-resolve → guard status → `set_config('app.tenant_id', invite.tenant_id, true)` → create User (uq_users_tenant_email conflict → `InviteEmailExistsError`→409) → grant UserRole(role_id, granted_by=invited_by) → mark consumed `UPDATE ... WHERE status='pending' RETURNING id` (None=loser→410; **RETURNING not rowcount** — mypy-clean) → `append_audit("invite_accepted")`. password NOT passed to service.
- [x] **`revoke(db, *, tenant_id, invite_id)`** — pending→revoked RETURNING guard (US-4 revocable)
- [x] **Typed errors** — `InviteError` base + 7 subclasses (status_code hint) co-located
  - DoD: single-use guard works; audit row written ✅ (unit + integration)

### 2.3 unit + integration tests + gate (SAFE CUT-LINE)
- [x] **NEW `tests/unit/platform_layer/identity/test_invites_service.py`** (db_session) — 11 tests: create raw+hash+audit / unknown-role / dup-pending / get_metadata resolve+invalid+expired+revoked / accept user+role+consume+audit / single-use / dup-email / hash_token helper
- [x] **NEW `tests/integration/api/test_invites.py`** — **7 HTTP tests** (went beyond Day-2 service-layer plan to full HTTP e2e): create-requires-admin(401) / e2e create→GET→accept→User+UserRole+consumed / single-use(410) / invalid(404) / expired(410) / **tenant-scoping (app-level; RLS untestable under superuser test role — D5)** / exempt-path contract
- [x] **black + isort + flake8 + mypy src/ + pytest** — clean (mypy 0/339; flake8 0); **18/18 new tests green** (11 unit + 7 integration); full suite **2179 passed**
- [x] **Cut-line checkpoint** — service+endpoints+tests all green; OIDC path untouched (guest paths exempt-only; admin create role-gated)

---

## Day 3 — Endpoints + exempt path + frontend wire (US-2/US-3/US-5)

### 3.1 endpoints
- [x] **NEW `api/v1/invites.py`** — POST `/admin/tenants/{tenant_id}/invites` (`require_admin_platform_role`) + GET `/invites/{token}` (sentinel lookup) + POST `/invites/{token}/accept` (`{full_name, password}`; password accepted-not-stored). **own-tenant guard REMOVED** (redundant: `_ADMIN_PLATFORM_ROLES` treats admin/platform_admin as cross-tenant by design, matching admin/tenants.py; invite scoped to PATH tenant + RLS). Pydantic models w/ `serialization_alias` (invitedBy/expiresIn).
  - DoD: 201 token-once / 200 metadata / 200 accept / 404 / 410 / 409 / 401 ✅
- [x] **`api/main.py`** — include invites router (after auth_router) + import (alpha order health/loops)

### 3.2 exempt path (guest context)
- [x] **`platform_layer/middleware/tenant_context.py`** — add `/api/v1/invites` to `TenantContextMiddleware.EXEMPT_PATH_PREFIXES` (class attr; GET/accept guest paths ONLY; admin create `/api/v1/admin/...` stays NON-exempt)
  - DoD: `test_create_requires_admin` (401) + `test_exempt_path_contract` (prefix present, admin path not covered) ✅

### 3.3 frontend wire
- [x] **`frontend/src/pages/auth/invite/index.tsx`** — removed FIXTURE_METADATA + AP-2 banner; consume real GET (200→form / 404→invalid / 410→gone) + real accept error; added `loading`/`invalid`/`gone` states via `DangerNote` (reuses existing danger-alert inline style — NO new mockup widgets, NO new oklch literals); accept body unchanged. + i18n: removed `demoBanner`/`errorStubbed`, added `loading`/`invalid`/`gone`/`acceptError` to en + zh-TW (繁中 per locale-file-is-translated rule).
  - DoD: `check:mockup-fidelity` ✓ (CSS byte-identical + oklch baseline **50 unchanged**, delta 0); no happy-path layout change ✅
- [x] **`frontend/tests/unit/pages/auth/invite.test.tsx`** — **REWROTE EXISTING file in-place** (per Sprint 57.78 D-DAY1-1 lesson — found the 57.23/57.35 fixture/banner test, did not add a dup): 5 tests — real metadata render (no fixture/banner) / accept 200→navigate /auth/mfa / accept 410→error+no-navigate / GET 404→invalid no-form / GET 410→gone no-form
  - DoD: 5/5 green; full Vitest **757 passed** (132 files); lint(no `--silent`)+build+mockup-fidelity green

### 3.4 test-isolation (Risk Class C)
- [→] **conftest singleton reset** — **N/A** (no lifespan-wired singleton; endpoint uses `maybe_get_invites_service() or InvitesService()` lenient fallback → nothing to leak; deliberately avoids the 57.84 Day-3 singleton-leak class). Full suite 2179 green, no event-loop leak.

---

## Day 4 — Full sweep + design note + Closeout

### 4.1 Full sweep
- [ ] **Backend gates** — black/isort/flake8 0 + `mypy src/` 0 + `pytest` green + `run_all.py` 10/10 (`check_rls_policies` for `invites`)
- [ ] **Frontend gates** — `npm run lint` (**NO `--silent`**) + `npm run build` + `npm run test` + `npm run check:mockup-fidelity` green
- [ ] **Read all changed code** — final pass (migration, service, endpoints, exempt path, frontend wire)
- [ ] **real-Azure smoke?** — N/A (no LLM in invites path; e2e proven by integration tests). Manual local e2e (admin create → GET → accept) optional if backend running.

### 4.2 design note (SPIKE — §Step 5.5 mandatory)
- [ ] **NEW `docs/03-implementation/agent-harness-planning/21-iam-invites-spike.md`** — extract from real impl; 8-point quality gate (section→US, file:line per claim, decision matrix (token: DB-opaque vs JWT), verification command, test fixture ref, open-invariant boundary (verified: lifecycle/isolation; deferred: credentials/register/MFA/email), rollback path, 17.md cross-ref). Record verified-ratio + 8-point self-check in retrospective.
- [ ] **17.md assess** — likely platform_layer-internal note (not 11+1 cross-category); same call as 57.84 — document in design note + CHANGE if not in 17.md

### 4.3 Closeout docs
- [ ] **CHANGE-052** in `claudedocs/4-changes/feature-changes/`
- [ ] **progress.md** Day 0-4 + **retrospective.md** Q1-Q7 (token design + guest RLS + password-deferral rationale + design-note 8-point gate)
- [ ] **Checklist** all `[x]` (or `🚧`/`[→]` carryover with reason — never delete)
- [ ] **Calibration** record (medium-backend 0.80; agent_factor 1.0 parent-direct; greenfield-domain data point — flag if ratio > 1.0 for possible `iam-backend-spike` class)
- [ ] **AD status**: `AD-Auth-Invite-Backend-IAM-Block-B-Phase58` CLOSED; NEW `AD-Auth-Credentials-PasswordLogin-Phase58` (57.86) + register/MFA/email/admin-list carryovers → next-phase-candidates.md
- [ ] **MEMORY subfile + pointer** + **CLAUDE.md lean** (Current Sprint + Last Updated)
- [ ] **Design note?** — **YES** (spike sprint — new IAM domain; 8-point gate per §Step 5.5)

### 4.4 Ship
- [ ] **Commit mapping** Day-0 / Day-1 schema / Day-2 service+tests / Day-3 endpoints+frontend / Day-4 closeout
- [ ] **Push + PR** (user-gated — explicit authorization required)
