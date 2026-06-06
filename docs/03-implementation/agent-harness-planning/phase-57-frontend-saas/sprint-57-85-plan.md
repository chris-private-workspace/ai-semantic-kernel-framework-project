# Sprint 57.85 Plan — C-12 IAM Block B: invites vertical spike (DB-backed invite lifecycle + admin create + guest accept) (opens C-12 / closes AD-Auth-Invite-Backend-IAM-Block-B-Phase58)

**Branch**: `feature/sprint-57-85-iam-invites` (from `main` `259d6070`)
**Closes**: `AD-Auth-Invite-Backend-IAM-Block-B-Phase58` — the **invites leg** of C-12 IAM Block B. This is the FIRST vertical spike of C-12 (per the thin-spike discipline: minimal self-contained slice → retrospective → extract design note; **NOT** a full Block B/C plan). Self-service tenant registration (`AD-Auth-Register-Backend-IAM-Block-B-Phase58`) + local-password credentials + MFA (Block C) are explicit out-of-scope follow-up slices (rolling — not pre-written).

---

## 0. Background

C-12 analysis (`claudedocs/5-status/c12-iam-block-bc-analysis-20260601.md`) established that IAM Block B/C is an **intentional Phase-58 gap, not a regression**: the auth frontend (invite / register / mfa pages) shipped mockup-fidelity in Sprint 57.23 with fixture fallback + AP-2 demo banner, while the backend endpoints (`/invites/{token}`, `/tenants/register`, `/mfa/verify`) deliberately don't exist (frontend gets 501 → shows fixture). 3 Phase-58 ADs track the backend wiring. The analysis §4-§5 mandates: **do the minimal `invites` vertical spike first** (most self-contained: 1 table + a few endpoints, reusing the Block-A JWT/tenant/RBAC infra) → retrospective → extract design note. **Do NOT pre-write the full Block B/C plan** (CLAUDE.md §"V2 不是『先寫一批新規劃文件』").

User picked C-12 as the next area (2026-06-06) to "process all" remaining A/B/C gaps; C-12 is the only in-repo, zero-external-blocker C-area item with the frontend already shipped (highest-confidence wire-to-shipped-frontend pattern, mastered across Area-A + Phase-58 write-side).

**Day-0 ground-truth (Explore three-prong + parent grep/read, main `259d6070`)**:
- **Reusable Block-A infra (do NOT rebuild)**: `JWTManager.encode/decode` (`platform_layer/identity/jwt.py:133-189`); `get_current_tenant` / `get_current_user_id` deps (`platform_layer/identity/auth.py:62-98`); admin RBAC dep `require_admin_platform_role` (`auth.py:142-154`) + `RBACManager.has_role_code` (`rbac.py:66-112`); `WORMAuditLog.append(tenant_id, event_type, content)` (`agent_harness/guardrails/audit/worm_log.py`); identity ORM `Tenant`/`User`/`Role`/`UserRole` (`infrastructure/db/models/identity.py:101-287`); RLS two-policy + system-sentinel escape template (migration `0024`/`0025`); `set_config('app.tenant_id', v, true)` for asyncpg (`middleware/tenant_context.py`).
- **0 invites backend files** (Explore parent-verified `git ls-files "backend/src/**" | grep -i invite` → empty) → fully greenfield.
- **No email/notification facility** → the spike returns the raw token in the create response (the only time it's shown); sending an invite email is a Phase-58 follow-up (not built here). **Drift D1.**
- **User email is per-tenant unique** (`UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email")`, `identity.py:218`) — relevant for the accept's user-creation (insert under invite.tenant_id; duplicate-email-in-tenant → 409). **Drift D2.**
- **Guest-context RLS wrinkle**: GET `/invites/{token}` + POST accept are called by an **unauthenticated guest** (holds token, no JWT / no `app.tenant_id`). The OIDC callback precedent (`auth.py:164-209`) runs EXEMPT from the tenant middleware. Resolution (mirrors the `billing_outbox` drainer sentinel I built in 57.84): invites RLS `USING` carries a **system-sentinel escape** so the guest endpoint can look up the invite by its globally-unique high-entropy `token_hash` under sentinel context, then `SET LOCAL app.tenant_id = invite.tenant_id` for the user-creation writes. **Drift D3 / Risk #3.**
- **Migration head = `0025_billing_outbox`** (Explore) → next = `0026`. Exact `down_revision` confirmed Day-1 by reading `0025` header.
- **password is deferred (user decision 2026-06-06, two AskUserQuestion rounds)**: the system has NO local-password storage (auth is OIDC/WorkOS + dev-login only); the login page is OIDC-only (email field is decorative, `login/index.tsx:158-176` → `window.location → /api/v1/auth/login`); mockup-fidelity forbids adding a password field to the login page. Adding local credentials this sprint would be a ~2x backend-ahead slice with no UI consumer → user chose to **split**: 57.85 = invite lifecycle only (accept's `password` field is **accepted but NOT stored**, documented deferral); 57.86 (rolling, not pre-written) = credentials table + bcrypt + password-login endpoint. **Drift D4 / §9.**

---

## 1. Sprint Goal

Stand up the **invites vertical slice** of IAM Block B end-to-end: a DB-backed `invites` table (opaque single-use token, status state machine, expiry) + an admin create endpoint + guest GET-metadata + guest accept (creates the User, grants the role, marks the invite consumed, writes an audit row), reusing the Block-A JWT/tenant/RBAC/audit infra — and wire the already-shipped frontend invite page to the real backend (remove fixture + AP-2 banner) — so a tenant admin can invite a member and the member can onboard, without regressing the OIDC auth path and without pre-committing to local-password credentials (deferred to 57.86).

## 2. User Stories

- **US-1**: As a tenant admin, I want to create an invite for an email + role and receive a one-time invite token, so I can onboard a new member. (admin create endpoint + token generation)
- **US-2**: As an invited user, I want to view an invite's metadata (tenant, inviter, role, expiry) from its token before accepting, so I know what I'm joining. (guest GET metadata, exempt path)
- **US-3**: As an invited user, I want to accept an invite (providing my name) and have my user account created with the granted role, so I become an active member — with the invite consumed single-use. (guest accept: user create + role grant + single-use + audit)
- **US-4**: As a security owner, I want invites tenant-isolated (RLS), single-use, expiring, and revocable, with the guest lookup constrained to the high-entropy token only (no cross-tenant enumeration), so the invite flow is not an isolation/replay hole. (RLS + token state machine + sentinel-scoped lookup)
- **US-5**: As a member of the onboarding team, I want the shipped frontend invite page wired to the real backend (fixture + AP-2 banner removed; 404/410 error states shown) plus unit/integration tests pinning the lifecycle/isolation/state-machine, so the slice is a verifiable real e2e (not a Potemkin).

## 3. Technical Specifications

### 3.0 Architecture

Single new domain in `platform_layer/identity/invites.py` (NOT a new top-level dir — invites belong to the existing Identity range, alongside `jwt.py`/`auth.py`/`oidc.py`/`rbac.py`). `InvitesService` owns the lifecycle: `create` (admin, request-tenant-scoped) / `get_by_token` (guest, sentinel-scoped lookup) / `accept` (guest, sentinel-lookup → switch to invite.tenant_id → user create + role grant + mark consumed + audit). Token = opaque random (`secrets.token_urlsafe(32)`), stored as `sha256(token)` hex (`token_hash`); the raw token is returned ONCE by create and never persisted. Status state machine: `pending → accepted` (single-use) / `pending → revoked` (admin) / `pending → expired` (TTL). The 3 endpoints live in a NEW `api/v1/invites.py` router (guest GET/accept) + the admin create endpoint co-located under the existing admin-tenants surface (`api/v1/admin/tenants.py` if present, else `invites.py` with an admin-RBAC dep) — decided Day-1 against the real router layout. LLM neutrality: N/A (no LLM). Multi-tenant: `invites` table is `tenant_id`-scoped + RLS two-policy + a system-sentinel escape for the guest token lookup; the accept's user-creation runs under `SET LOCAL app.tenant_id = invite.tenant_id`.

**password deferral (live-path safety)**: the accept endpoint accepts `{full_name, password}` (the shipped frontend contract) but **only uses `full_name`**; `password` is validated-as-present but NOT stored (no credential write this sprint). The created User authenticates via the existing OIDC/dev-login afterward. Documented in §9 + the endpoint docstring + CHANGE so 57.86 wires credentials without surprise. This is NOT a Potemkin: the invite lifecycle (create→view→accept→user+role+audit→single-use) is fully real and tested; only the *password credential* leg is an explicit, tracked deferral.

### 3.1 `invites` table + migration `0026` (US-1/US-2/US-3/US-4) — NEW

- NEW `infrastructure/db/models/invites.py` — `Invite` ORM (`TenantScopedMixin`): `id UUID PK`, `tenant_id UUID NOT NULL`, `email VARCHAR(256) NOT NULL`, `role_id UUID NOT NULL` (FK `roles.id`), `invited_by UUID NOT NULL` (FK `users.id`), `token_hash VARCHAR(64) NOT NULL` (sha256 hex), `status VARCHAR(16) NOT NULL DEFAULT 'pending'` (pending/accepted/revoked/expired), `expires_at TIMESTAMPTZ NOT NULL`, `accepted_at TIMESTAMPTZ`, `accepted_user_id UUID` (FK `users.id`), `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`. Register in `models/__init__.py` (after `identity` import) so Alembic + `check_rls_policies` see it.
- Constraints/indexes: `UNIQUE (token_hash)` (globally-unique bearer lookup — supports the sentinel-scoped guest query); `UNIQUE (tenant_id, email, status) WHERE status='pending'` partial (one live pending invite per email per tenant; decided Day-1 if partial-unique is cleanest vs app-level check); `idx_invites_tenant` on `(tenant_id)`; `CHECK` on status enum.
- NEW `infrastructure/db/migrations/versions/0026_invites.py` (`down_revision` = `0025_billing_outbox` revision id, confirmed Day-1 by reading the `0025` header): CREATE TABLE + indexes + FK + `ENABLE`+`FORCE ROW LEVEL SECURITY` + `tenant_isolation_invites` (`USING (tenant_id = current_setting('app.tenant_id', true)::uuid OR current_setting('app.tenant_id', true)::uuid = '<SENTINEL>')` — sentinel escape for the guest token lookup, mirroring `0025_billing_outbox`) + `tenant_insert_invites` (`WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)`). `run_all.py check_rls_policies` must stay green (recall 57.84 leniency: it checks ENABLE + CREATE POLICY presence, not USING body — so the sentinel escape lands in this one migration).

### 3.2 `InvitesService` (US-1/US-2/US-3) — `platform_layer/identity/invites.py` NEW

- `async def create(self, db, *, tenant_id, inviter_user_id, email, role_id, ttl_hours) -> tuple[Invite, str]`: validate role belongs to tenant (reuse role lookup); generate `raw = secrets.token_urlsafe(32)`; `token_hash = sha256(raw)`; insert `Invite(status='pending', expires_at=now+ttl)` in the caller's (admin request) txn; return `(invite, raw)` — raw token shown once.
- `async def get_by_token(self, db, raw_token) -> Invite`: `sha256(raw)` → query `WHERE token_hash = :hash` (under sentinel context set by the endpoint); compute effective status (lazy-expire: if `pending` and `expires_at < now` → treat as `expired`); raise typed errors (`InviteNotFoundError` → 404; `InviteExpiredError`/`InviteConsumedError`/`InviteRevokedError` → 410).
- `async def accept(self, db, raw_token, *, full_name) -> User`: re-resolve invite under sentinel; guard status; `SET LOCAL app.tenant_id = invite.tenant_id`; create `User(tenant_id=invite.tenant_id, email=invite.email, display_name=full_name, status='active')` (handle `uq_users_tenant_email` conflict → `InviteEmailExistsError` → 409); grant role via `UserRole(user_id, role_id=invite.role_id, granted_by=invite.invited_by)`; mark invite `accepted` + `accepted_at` + `accepted_user_id` (single-use; a concurrent double-accept must lose — `UPDATE ... WHERE status='pending'` rowcount guard); `WORMAuditLog.append(invite.tenant_id, "invite_accepted", {...})`. (`password` param accepted by the endpoint but NOT passed to the service — deferred.)
- `async def revoke(self, db, *, tenant_id, invite_id) -> None`: admin-scoped status `pending → revoked` (rowcount guard). (Minimal — supports US-4 revocable; admin-list is a follow-up.)
- Typed errors module-co-located (`InviteError` base + subclasses). Module-level singleton + `set_/get_/maybe_get_invites_service` accessors mirroring `cost_ledger.py`/`billing_outbox.py` (testability + reset hook per testing.md §Module-level Singleton Reset).

### 3.3 Endpoints (US-1/US-2/US-3/US-4) — `api/v1/invites.py` NEW + admin create

- **POST `/api/v1/admin/tenants/{tenant_id}/invites`** (admin RBAC dep `require_admin_platform_role`; request-tenant-scoped) → body `{email, role_id, ttl_hours?}` → `InvitesService.create` → 201 `{invite_id, token, expires_at}` (raw token shown once). Tenant from path validated == `get_current_tenant` (no cross-tenant create).
- **GET `/api/v1/invites/{token}`** (EXEMPT path — add to `EXEMPT_PATH_PREFIXES` in `middleware/tenant_context.py`, mirroring callback) → endpoint sets `app.tenant_id = SENTINEL` for the lookup → `InvitesService.get_by_token` → 200 `{tenant, invitedBy, role, expiresIn}` (shape per `invite/index.tsx:41-46` `InviteMetadata`) / 404 / 410.
- **POST `/api/v1/invites/{token}/accept`** (EXEMPT path) → body `{full_name, password}` (password accepted, not stored) → sentinel lookup → switch to invite.tenant_id → `InvitesService.accept` → 200 `{ok, user_id}` (frontend navigates to `/auth/mfa` on 200) / 404 / 410 / 409. `revoke` endpoint optional this sprint (service method exists; HTTP surface decided Day-1 — minimal is fine).
- Router registration in `api/main.py` (mirror `auth_router` include at `main.py:348`).

### 3.4 Frontend invite-page wiring (US-5) — `frontend/src/pages/auth/invite/index.tsx`

- Remove `FIXTURE_METADATA` fallback (`invite/index.tsx:48-53`) + AP-2 demo banner (`:154-162`); consume the real GET metadata (already called at `:69`) + real accept (`:90`). Add error states for 404 (invalid token) + 410 (used/expired/revoked) per mockup error UX (reuse the page's existing error surface; do NOT add new mockup widgets). The accept request body is unchanged (still sends `{full_name, password}`; backend ignores password). Mockup-fidelity: no visual/layout change (banner removal is the only delta; the banner was the AP-2 interim marker). DoD: `check:mockup-fidelity` baseline unchanged (oklch delta 0); the page still matches the mockup minus the (always-temporary) AP-2 banner.

### 3.5 Tests (US-5)

- Unit (`tests/unit/platform_layer/identity/test_invites_service.py`, db_session): create returns raw token + persists hash (raw never stored); `get_by_token` resolves / lazy-expires / typed errors; token_hash mismatch → not found; pure helpers (sha256, ttl). ~7-9 tests.
- Integration (`tests/integration/api/test_invites.py`, committed-data + cleanup per testing.md): **e2e admin-create → guest-GET → guest-accept → User+UserRole+audit row** (the real vertical slice); single-use (second accept → 410); expired token → 410; revoked → 410; invalid token → 404; duplicate-email-in-tenant → 409; **2-tenant isolation** (tenant A's admin cannot create for tenant B; guest token lookup constrained to its own invite; Risk Class C singleton reset fixture). ~8-10 tests.
- Frontend (`frontend/tests/unit/pages/auth/invite.test.tsx`, Vitest): real metadata render (no fixture) + 404/410 error states + accept submit calls real endpoint. ~4-6 tests.

### 3.6 Lint / validation

`black + isort + flake8 + mypy src/` 0 + `run_all.py` 10/10 (esp. `check_rls_policies` for the new `invites` table). Frontend `npm run lint` (NO `--silent`) + `npm run build` + `npm run test` + `npm run check:mockup-fidelity`. Full format chain pre-commit.

## 4. File Change List

**Code — NEW (4)**:
1. `backend/src/infrastructure/db/models/invites.py` — `Invite` ORM (TenantScopedMixin) + status enum
2. `backend/src/infrastructure/db/migrations/versions/0026_invites.py` — table + indexes + FK + RLS (two-policy + sentinel escape)
3. `backend/src/platform_layer/identity/invites.py` — `InvitesService` (create/get/accept/revoke) + typed errors + singleton accessors
4. `backend/src/api/v1/invites.py` — guest GET/accept router + admin create endpoint

**Code — EDIT (3)**:
5. `backend/src/infrastructure/db/models/__init__.py` — register `Invite`
6. `backend/src/api/main.py` — include invites router
7. `backend/src/middleware/tenant_context.py` — add `/api/v1/invites/` to `EXEMPT_PATH_PREFIXES` (guest paths)

**Frontend — EDIT (1)**:
8. `frontend/src/pages/auth/invite/index.tsx` — remove fixture + AP-2 banner; consume real backend; 404/410 states

**Tests (3 NEW)**:
9. `backend/tests/unit/platform_layer/identity/test_invites_service.py`
10. `backend/tests/integration/api/test_invites.py` (+ conftest singleton reset if needed)
11. `frontend/tests/unit/pages/auth/invite.test.tsx`

**Docs (3)**:
12. `docs/03-implementation/agent-harness-planning/21-iam-invites-spike.md` — **design note extract** (spike sprint; 8-point quality gate per §Step 5.5)
13. `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md` — invites endpoint contract IF a cross-category contract emerges (assess Day-4; likely a platform_layer-internal note, not a 11+1 cross-category contract — same call as 57.84)
14. `claudedocs/4-changes/feature-changes/CHANGE-052-iam-invites.md`

## 5. Acceptance Criteria

1. `invites` table exists (migration `0026` applies on the `0025` head, both directions), `tenant_id` + RLS two-policy + sentinel escape present, `UNIQUE(token_hash)` enforced; `check_rls_policies` green.
2. Admin create returns a one-time token (raw never persisted — only `sha256` stored); a non-admin / cross-tenant create is rejected (403).
3. Guest GET resolves metadata by token (exempt path, sentinel-scoped); invalid → 404; used/expired/revoked → 410.
4. Guest accept creates the User (under invite.tenant_id) + grants the role + marks the invite consumed single-use (second accept → 410) + writes an audit row; duplicate-email-in-tenant → 409; `password` is accepted-but-not-stored (documented deferral, not a credential write).
5. Multi-tenant isolation holds: an admin cannot create/list across tenants; the guest token lookup cannot enumerate other tenants' invites (isolation test).
6. Frontend invite page consumes the real backend (fixture + AP-2 banner removed; 404/410 states shown); `check:mockup-fidelity` baseline unchanged (oklch delta 0).
7. `mypy src/` 0; full backend pytest green; frontend lint(no `--silent`)/build/test/mockup-fidelity green; `run_all.py` 10/10.

## 6. Deliverables

- [ ] US-1: `invites` table + migration `0026` + RLS + ORM + register; admin create endpoint + token generation
- [ ] US-2: guest GET metadata (exempt path + sentinel lookup) + typed 404/410
- [ ] US-3: guest accept (user create + role grant + single-use + audit; password deferred)
- [ ] US-4: RLS + sentinel-scoped lookup + status state machine (single-use/expire/revoke) + isolation test
- [ ] US-5: frontend invite-page wire (remove fixture/banner) + unit + integration + frontend tests
- [ ] Closeout: **design note `21-iam-invites-spike.md` (8-point gate)** + CHANGE-052 + 17.md assess + progress + retrospective + checklist + MEMORY + CLAUDE lean + next-phase-candidates (defer register/credentials/MFA → 57.86+)

## 7. Workload Calibration

- **Agent-delegated: no** (parent-direct — greenfield IAM security domain: token design, guest-context RLS/sentinel, single-use concurrency, email-uniqueness handling are judgment-sensitive; consistent with the security-sensitive billing sprints 57.79-57.84 all parent-direct). `agent_factor` 1.0 → 3-segment form.
- Scope class: **`medium-backend` 0.80** (closest established class; backend table + service + 3 endpoints + RLS + tests dominate; the frontend wire is modest). **Greenfield-domain caveat**: medium-backend's recent 3-sprint mean ran low (~0.5-0.6, over-estimating) on *pattern-reuse* backend; this is a *greenfield IAM* spike (no prior invites pattern) → expect a higher ratio than the pattern-reuse data points. Flag as a greenfield-domain `medium-backend` data point in Day-4 retro Q2; if it lands > 1.0, consider a new `iam-backend-spike` class (do NOT pre-create — accumulate data per the diversification discipline).
- Bottom-up est ~9 hr (table+ORM+register ~0.5 / migration+RLS+sentinel ~1.5 / InvitesService create+get+accept+revoke+errors ~2 / 3 endpoints+exempt-path+RBAC ~1.5 / frontend wire ~1 / tests unit+integration+frontend ~2.5) → class-calibrated commit ~7.2 hr (`medium-backend` 0.80).
- **Size caveat (honest)**: ~1.5-2× a small sprint; touches a new security domain + the tenant-context middleware (exempt path). The Day structure carries the safety: **Day-2-end is a safe cut-line** (table + service + unit/integration tests green = the invite lifecycle is provable at the service/DB layer before any router/middleware wiring). If the Day-3 endpoint + exempt-path + frontend wire over-runs, ship Day-1-2 (table + service + tests) and carryover the HTTP surface + frontend wire as `AD-Invites-Endpoints-Wire` (clean split; not a failure — the lifecycle core is the spike's learning). Noted §8 Risk #2.

## 8. Dependencies & Risks

| # | Risk | Mitigation |
|---|------|-----------|
| 1 | Guest endpoints (GET/accept) bypass tenant middleware (exempt) — risk of an isolation/enumeration hole | Token is high-entropy `secrets.token_urlsafe(32)`; only `sha256(token)` stored; sentinel escape allows ONLY a `token_hash =` equality lookup (no listing/enumeration); 404 (not 403) hides existence; isolation test (US-4) is the gate; `check_rls_policies` green. |
| 2 | Spike is ~1.5-2× a small sprint + touches middleware | Day-2-end cut-line (table + service + tests, nothing wired) = safe partial ship; HTTP surface + frontend wire can carryover as `AD-Invites-Endpoints-Wire`. Not a failure — lifecycle core is the learning. |
| 3 | RLS: guest token lookup needs cross-tenant read but writes per-tenant (Drift D3) | Mirror the `billing_outbox` (57.84) sentinel pattern I just built: `tenant_isolation_invites` USING carries a system-sentinel escape for the token lookup; endpoint sets `app.tenant_id = SENTINEL` for the lookup then `SET LOCAL app.tenant_id = invite.tenant_id` before user-creation; `set_config(...)` form (asyncpg rejects bind params on `SET`). Isolation test gates it. |
| 4 | Single-use race (two concurrent accepts of one token) → double user creation | Mark-consumed is `UPDATE invites SET status='accepted' WHERE id=:id AND status='pending'` with a **rowcount guard**: the loser (rowcount 0) raises `InviteConsumedError` → 410 and its user-insert is rolled back (same txn). Unit/integration test covers double-accept. |
| 5 | password contract mismatch (frontend sends it; no credential store exists) — Drift D4 | Accept validates `password` present (matches frontend contract) but does NOT store it; documented deferral (§9 + endpoint docstring + CHANGE); 57.86 wires credentials. NOT a Potemkin — the lifecycle is fully real/tested; only the credential leg is tracked-deferred. |
| 6 | Background-task / singleton leak into test event loops (Risk Class C) | `InvitesService` singleton autouse reset in conftest (testing.md §Module-level Singleton Reset); integration tests use the committed-data + cleanup pattern (per 57.84 drain-test precedent). |
| 7 | Migration head drift (0026 already taken / wrong down_revision) | Day-0 Prong-3 confirmed head = `0025_billing_outbox`; Day-1 reads the `0025` header for the exact `revision` id before writing `down_revision`; apply both directions on Docker DB. |
| 8 | Exempt-path change could accidentally exempt more than intended | Add ONLY `/api/v1/invites/` prefix to `EXEMPT_PATH_PREFIXES`; the admin create (`/api/v1/admin/tenants/.../invites`) stays NON-exempt (admin RBAC); a test asserts the admin path still requires auth. |

## 9. Out of Scope (this sprint; carryover → next-phase-candidates.md)

- **Local-password credentials + bcrypt + password-login endpoint** (`AD-Auth-Credentials-PasswordLogin-Phase58`, NEW) — user split this out (2026-06-06). The accept's `password` field is accepted-but-not-stored this sprint. 57.86 (rolling — not pre-written) wires a `user_credentials` table + bcrypt + a tenant-scoped password-login endpoint. (Login-page UI wiring is further gated by mockup-fidelity — the mockup login page has no password field.)
- **Self-service tenant registration** (`AD-Auth-Register-Backend-IAM-Block-B-Phase58`) — POST `/tenants/register` (create tenant + first admin user). Separate Block-B slice; not built here.
- **MFA TOTP + WebAuthn** (`AD-Auth-MFA-Backend-IAM-Block-C-Phase58`) — Block C; the accept page navigates to `/auth/mfa` (still stub 501 after this sprint). Separate slice.
- **Invite email delivery** (Drift D1) — no email facility exists; create returns the raw token in-response this sprint. Email-send is a Phase-58 follow-up.
- **Admin invites list / resend UI** — `revoke` service method exists (US-4 revocable); a full admin invites-management surface (list pending / resend / revoke UI) is a follow-up.
- **`/auth/recovery` page backend** (`AD-Auth-Recovery-Page-Phase58`) — unrelated Block-C-adjacent item.
