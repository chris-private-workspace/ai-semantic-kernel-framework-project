# Sprint 57.85 Progress — C-12 IAM Block B: invites vertical spike

**Branch**: `feature/sprint-57-85-iam-invites` (from `main` `259d6070`)
**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-85-plan.md`
**Closes**: `AD-Auth-Invite-Backend-IAM-Block-B-Phase58` (invites leg of C-12 Block B)

---

## Day 0 — 2026-06-06 — Plan-vs-Repo Verify + Branch + Decisions

### Context
User selected C-12 (IAM Block B/C) as the next area to "process all" remaining A/B/C gaps. C-12 analysis (`c12-iam-block-bc-analysis-20260601.md`) §4-§5 mandates a **thin invites vertical spike first** (not a full Block B/C plan). This is the first spike of C-12.

### Day-0 三-prong verify (Explore agent + parent grep/read)
- **Prong 1 (path)** — reusable Block-A infra confirmed (JWTManager `jwt.py:133-189`; tenant/user deps `auth.py:62-98`; admin RBAC `auth.py:142-154` + `rbac.py:66-112`; WORMAuditLog `worm_log.py`; identity ORM `identity.py:101-287`). 0 invites backend files → greenfield.
- **Prong 2 (content)** — frontend contract: GET `/invites/{token}` (`invite/index.tsx:69`) + POST accept `{full_name, password}` (`:90`); fixture+banner `:48-53`/`:154-162`. login OIDC-only, no password field (`:158-176`). No email/credential facility. OIDC callback EXEMPT precedent (`auth.py:164-209`).
- **Prong 3 (schema)** — User email per-tenant unique (`identity.py:218`); migration head `0025_billing_outbox` → next `0026`; RLS two-policy + sentinel template from `0025`.

### Drift findings
- **D1** — No email/notification facility → create returns the raw token in-response (email-send is a Phase-58 follow-up). Plan §0 + §9.
- **D2** — `User` email is `(tenant_id, email)` per-tenant unique (`uq_users_tenant_email`, `identity.py:218`) → accept's duplicate-email-in-tenant returns 409. Plan §3.2 / Risk N/A (handled).
- **D3** — Guest GET/accept run unauthenticated (no `app.tenant_id`); the lookup needs a cross-tenant `token_hash` read but the writes are per-tenant → **sentinel-escape RLS** (mirror the `billing_outbox` drainer I built in 57.84) + `SET LOCAL app.tenant_id = invite.tenant_id` for writes. Plan §3.1 / Risk #3.
- **D4** — `password` deferred: no local-credential store exists (OIDC/dev-login only); login page is OIDC-only + mockup forbids adding a password field → adding credentials this sprint = ~2x backend-ahead with no UI consumer. User chose to split (57.86). Accept's `password` is accepted-but-not-stored. Plan §0 / §9 / Risk #5.

### Decisions locked (AskUserQuestion ×4, 2026-06-06)
1. **Token mechanism** = DB-backed opaque token (`secrets.token_urlsafe(32)` + `sha256` hash, status state machine) — NOT stateless JWT (need revoke/single-use/list).
2. **password** = (initial answer "add local password" → after the new-info round: login OIDC-only + mockup forbids password field + no UI consumer this sprint) → **split**: 57.85 = invite lifecycle only (password accepted-not-stored); 57.86 (rolling) = credentials + bcrypt + password-login.
3. **Admin create endpoint** = INCLUDED (true e2e vertical slice: admin create → guest accept).
4. **Sprint scope** = pure invite lifecycle; credentials/register/MFA/email = follow-up slices.

### go/no-go
**GO.** Scope ~1.5-2× a small sprint (greenfield IAM + middleware exempt path). Safe cut-line at Day-2-end (table + service + tests, nothing wired); HTTP surface + frontend wire can carryover as `AD-Invites-Endpoints-Wire` if Day-3 over-runs.

### Calibration (plan-time)
- **Agent-delegated: no** (parent-direct — greenfield IAM security: token/RLS/sentinel/single-use/email-uniqueness judgment-sensitive; consistent with billing sprints 57.79-57.84). `agent_factor` 1.0 → 3-segment.
- `medium-backend` 0.80 (greenfield-domain caveat — flag ratio in retro Q2; if > 1.0, consider `iam-backend-spike` class, do NOT pre-create).
- Bottom-up est ~9 hr → class-calibrated commit ~7.2 hr (0.80).

### Day 0 actions
- Branch `feature/sprint-57-85-iam-invites` created.
- Plan + checklist drafted (mirror 57.84 structure: plan 9 sections; checklist Day 0-4).
- This progress.md Day-0 entry.

### Remaining for next day
- Day 1: `invites` ORM + register + migration `0026` (read `0025` header for down_revision; both-direction apply).

---

## Day 1 — 2026-06-06 — Schema

- NEW `infrastructure/db/models/invites.py` (`Invite` + `InviteStatus`) — UUID PK, FK role/invited_by(CASCADE)/accepted_user_id(SET NULL), UNIQUE(token_hash), status CHECK, idx_invites_tenant, partial-unique `uq_invites_pending_email` (tenant_id,email WHERE pending). Registered in `models/__init__.py`.
- NEW migration `0026_invites` (down_revision `0025_billing_outbox`) — table + indexes + ENABLE+FORCE RLS + `tenant_isolation_invites` (USING + system-sentinel escape) + `tenant_insert_invites` (WITH CHECK). Applied **both directions** on Docker DB (up 0025→0026 → down -1 → re-up; `alembic current` = `0026_invites (head)`).
- Gates: black/isort/flake8 0; mypy 0/337; `run_all.py` 10/10 (check_rls_policies discovers `invites`). Commit `e8f20e95`.

## Day 2+3 — 2026-06-06 — Service + endpoints + tests (resequenced: backend done together)

- NEW `platform_layer/identity/invites.py` — `InvitesService` (create / get_metadata / accept / revoke) + 7 typed errors (`InviteError` base w/ status_code hint) + `InviteMetadata` dataclass + lenient singleton accessors. Tenant context via `set_config` (sentinel lookup → invite.tenant writes; mirrors billing_outbox drainer). `create` lazy-expires stale pending + dup-pending guard + `invite_created` audit. `accept` creates User + grants UserRole + single-use consume via `UPDATE ... RETURNING id` (mypy-clean, no `.rowcount`) + `invite_accepted` audit; `password` NOT stored (deferred).
- NEW `api/v1/invites.py` — 3 endpoints (admin create 201 / guest GET 200 / guest accept 200) + Pydantic models (`serialization_alias` → invitedBy/expiresIn). Endpoint uses `maybe_get_invites_service() or InvitesService()` (lenient — no lifespan singleton → no leak).
- EDIT `api/main.py` (import + include invites_router after auth) + `platform_layer/middleware/tenant_context.py` (add `/api/v1/invites` to `EXEMPT_PATH_PREFIXES` — guest GET/accept only; admin create stays non-exempt).
- Tests: 11 unit (`test_invites_service.py`) + 7 integration (`test_invites.py`, full HTTP e2e via `_build_app` + X-Test headers + override get_db_session/require_admin_platform_role). All 18 green; full suite **2179 passed**, mypy 0/339, run_all 10/10.

### Day-2+3 design decisions / drift findings
- **D5 (RLS untestable under superuser test role)** — the `ipa_v2` test DB connection role bypasses RLS (superuser/BYPASSRLS), so a cross-tenant read is NOT blocked at the DB in tests (confirmed: a `select(Invite)` under tenant-B context still returned a tenant-A row). The RLS policies ARE present (check_rls_policies green) and enforce in production under a non-superuser app role. Isolation is therefore asserted at the **application layer** (invite attributed to the path tenant; tenant B has no row), per the codebase convention (hitl/quotas isolation tests do the same). The sentinel-escape RLS is correct-by-construction (mirrors the production-verified billing_outbox 57.84) but exercised only functionally in tests.
- **Own-tenant guard removed** (redundant) — `_ADMIN_PLATFORM_ROLES = {admin, platform_admin}` are both cross-tenant by design (admin/tenants.py convention); `require_tenant_match_or_platform_admin` treats "admin" as platform-level, so the guard was a no-op for the only roles that pass `require_admin_platform_role`. Dropped it (no fake defense); invite is scoped to the PATH tenant + RLS-isolated.
- **rowcount → RETURNING** — `AsyncSession.execute(update())` is typed `Result` (no `.rowcount` under mypy strict); used `.returning(Invite.id).scalar_one_or_none()` for the single-use + revoke guards instead.
- **get_by_token → get_metadata** — the GET needs tenant/inviter/role display names; reading them requires switching from sentinel to the invite's tenant context (users/roles have no sentinel escape), so the method resolves + returns an `InviteMetadata` rather than the raw row.

### Remaining
- Day 3 frontend: wire `invite/index.tsx` (remove fixture + AP-2 banner; real GET/accept; 404/410 states) + `invite.test.tsx`.
- Day 4: design note (`21-iam-invites-spike.md`, 8-point gate) + CHANGE-052 + retrospective + closeout.

---

## Day 3 (frontend) — 2026-06-06

- `invite/index.tsx` — removed FIXTURE_METADATA + AP-2 banner; consume real GET (200→form / 404→invalid / 410→gone) + real accept error; `loading`/`invalid`/`gone` states via `DangerNote` (reuses existing danger-alert inline style — no new oklch literals). i18n en+zh-TW: drop demoBanner/errorStubbed, add loading/invalid/gone/acceptError (zh-TW 繁中 per locale-is-translated rule).
- `invite.test.tsx` — REWROTE existing file in-place (Sprint 57.78 lesson; did not add a dup): 5 tests (real metadata / accept→navigate / accept-fail / 404-invalid / 410-gone).
- Gates: lint(no `--silent`)+build clean; Vitest **757 passed**; check:mockup-fidelity ✓ (CSS byte-identical + oklch baseline **50 unchanged**). Commit `6bb28d26`.

## Day 4 — 2026-06-06 — Closeout

- **Design note** `21-iam-invites-spike.md` (SPIKE — §Step 5.5; 8-point gate all ✓; ~97% verified ratio).
- CHANGE-052 + retrospective.md (Q1-Q7 + 8-point self-check + calibration).
- 17.md = N/A (assessed — identity not a registered 11+1 category surface; same call as 57.84).
- Calibration: `medium-backend` 0.80 + `agent_factor` 1.0 (parent-direct); ratio ~1.25 — **greenfield-domain over-run** (as plan flagged); single data point, outlier-ignored for the multiplier; if 57.86 confirms → propose `iam-backend-spike` class.
- Final gates: mypy 0/339 · pytest **2179** · run_all 10/10 · Vitest 757 · mockup-fidelity ✓.
- AD: `AD-Auth-Invite-Backend-IAM-Block-B-Phase58` CLOSED; carryovers (credentials/register/MFA/email/admin-list) → next-phase-candidates.md.

### Commit mapping
- Day-0 `0d5d81d6` (plan+checklist+progress) / Day-1 schema `e8f20e95` / Day-2+3 backend `890cab46` / Day-3 frontend `6bb28d26` / Day-4 closeout (pending).
