---
title: 20-iam-deep-dive design note
purpose: Spike-extract design note from Sprint 57.7; documents verified runtime invariants for IAM Foundation (OIDC hosted login + DB-backed RBAC + sessions/tool_calls observer)
category: V2 extension docs (post-22-sprint era)
created: 2026-05-10 (Sprint 57.7 Day 4 closeout)
sprint_source: 57.7
verified_ratio: ≥ 95% (per 8-Point Quality Gate; only §4 deferred items NOT verified)
status: Active
---

# 20-iam-deep-dive Design Note (Sprint 57.7 extract)

## 0. Spike Summary

- **Sprint scope** (7 USs): IAM Foundation (US-A1 vendor matrix + US-A2 OIDC backend + frontend + US-A3 DB-backed RBAC) + Frontend Foundation 1/N (US-B1 install + US-B2 AppShell + US-B3 cost-dashboard migrate) + AD-Reality-3a/3b backfill (US-R1 sessions/tool_calls observer)
- **Verified period**: 2026-05-09 ~ 2026-05-10 (Day 0 ~ Day 3 production code; Day 4 doc closeout)
- **Calibration**: bottom-up est ~26-33 hr / committed ~18 hr (HYBRID 0.60 1st application AD-Sprint-Plan-9) / actual ~13.5 hr / **ratio ~0.75** (still below band [0.85, 1.20]; Day 4 ~3 hr → projected ~0.92 in band)
- **Verification**: pytest 1602 → 1622 (+20: 7 oidc/auth + 6 repos + 7 RBAC) / Vitest 35 → 41 (+6) / Playwright 23 → 23 (no regression sentinel) / mypy 0/300 (+6 source files) / 9/9 V2 lints / 0 LLM SDK leak

---

## 1. Decision Matrix — IAM Vendor (US-A1)

**✅ CHOSEN: WorkOS** (intermediate artifact: `agent-harness-execution/phase-57/sprint-57-7/iam-vendor-matrix.md`)

| Capability | WorkOS ✅ | Clerk ❌ | Auth0 ❌ | Supabase Auth ❌ |
|------------|-----------|----------|----------|------------------|
| **Cost @ V2 5K MAU + 5 conn** | ~$1,250/mo ($15K/yr) | ~$250/mo ($3K/yr) | ~$1,500-2,500/mo ($18-30K/yr) | ~$100/mo ($1.2K/yr) |
| **Cost @ V2 50K MAU + 15 conn** | ~$3,000/mo ($36K/yr) | ~$1,075/mo ($13K/yr) | ~$2,500-5K/mo ($30-60K/yr) | ~$775/mo ($9K/yr) |
| **SCIM 2.0** | ✅ Native | ⚠️ April 2026 GA (immature) | ✅ Free tier | ❌ **NOT supported** |
| **SAML 2.0** | ✅ Best-in-class B2B | ✅ Pro tier add-on | ✅ B2B tier (3-5 conn cap) | ⚠️ Pro+ limited |
| **SOC 2 Type II** | ✅ Inherited | ⚠️ **Behind Business paywall** | ✅ Enterprise tier $30K+/yr | ✅ Pro+ |
| **Vendor lock-in** | 🟡 Medium (standard OIDC export) | 🔴 High (frontend SDK heavy) | 🟡 Medium-high | 🟢 Low (OSS) |
| **APAC presence** | ✅ Global edge | ✅ Global | ✅ Mature | ⚠️ US/EU focus |

### 1.1 Chosen reason (WorkOS)

B2B-focused (best SAML + SCIM + Audit Logs combo) + cost-predictable per-connection model + 1M+ MAU free + clean OIDC standards (low lock-in) + APAC accessible + SOC 2 Type II inherited + clear migration off-ramp via standard OIDC tokens.

### 1.2 Rejection rationale (specific, NOT「best practice」hand-wave)

- **Clerk rejected**: SCIM 2.0 GA April 2026 too recent (Q3 2026 enterprise demos = 1-2 quarters un-battle-tested at scale); SOC 2 artifacts behind Business Plan paywall (cost surprise); `@clerk/react` SDK frontend-heavy → vendor swap = expensive frontend rewrite
- **Auth0 rejected**: B2B Essentials caps at 3 SSO connections (V2 hits ceiling Year 1); Professional tier $800/mo for 5 SSO is throwaway scale → forced Enterprise $30-60K/yr; Okta-acquired pricing trajectory (2 hikes 2024+2025) introduces unpredictable cost upside
- **Supabase Auth rejected**: SCIM 2.0 completely missing (gap-analysis §1.2 Tier 0 #6 — $50K+ ACV deals require SCIM table-stakes); SAML Pro+ limited features ("best for B2C / early B2B <10K MAU"); APAC edge presence weak (Taiwan/HK latency)

Full vendor matrix detail: `agent-harness-execution/phase-57/sprint-57-7/iam-vendor-matrix.md`

---

## 2. Verified Invariants

### 2.1 OIDC Hosted Login Flow (US-A2)

- **Implementation**:
  - `backend/src/platform_layer/identity/oidc.py` `WorkOSOIDCFlow` class (~L89)
  - `initiate_login(redirect_uri=None) -> tuple[str, str]` (~L132): sync URL builder via `client.user_management.get_authorization_url(redirect_uri, state, provider="authkit")`; returns `(authorize_url, state)` where state = `secrets.token_urlsafe(32)`
  - `exchange_callback(code, state, expected_state) -> OIDCProfile` (~L165, async): `secrets.compare_digest(state, expected_state)` CSRF check → `await client.user_management.authenticate_with_code(code=code)` → maps `AuthenticateResponse.user.{id, email, first_name, last_name}` + `access_token` to OIDCProfile
  - `signout_url(return_to, session_id=None) -> str` (~L195): vendor `get_logout_url` when session_id present; static AuthKit logout fallback otherwise
  - `backend/src/api/v1/auth.py` 3 endpoints (`/login` ~L82 + `/callback` ~L142 + `/logout` ~L195) with httpOnly secure cookie state CSRF (`oidc_state` + `oidc_redirect_to` + `oidc_tenant_code` 10-min TTL)
- **Behavior**: User → `/login?tenant_code=X&redirect_to=Y` → vendor authorize URL (302) → IdP login → `/callback?code=...&state=...` → CSRF state check → vendor SDK code exchange → DB user upsert → V2 HS256 JWT issued as `v2_jwt` cookie → 302 to original `redirect_to`
- **Verification**:
  ```bash
  cd backend && python -m pytest tests/unit/platform_layer/identity/test_oidc.py -v
  ```
  7 tests pass: initiate_login URL+state shape; CSRF state mismatch raises OIDCStateError; exchange_callback success returns OIDCProfile (mocked AsyncWorkOSClient); callback endpoint missing tenant cookie 400; unknown tenant 400; user upsert INSERT path; vendor exception → OIDCExchangeError mapping
- **Test fixture**: `MagicMock` + `AsyncMock` injected via `patch.object(WorkOSOIDCFlow, "_make_async_client", ...)` — no real workos network calls (Day 3 Tier 1)

### 2.2 V2 Internal JWT Stays HS256 (Path 1 — D2 Day 0 decision)

- **Implementation**:
  - `backend/src/platform_layer/identity/jwt.py` `JWTManager.encode(sub, tenant_id, roles, extra)` (~L133) emits HS256 JWT with reserved claims `_RESERVED_CLAIMS = frozenset({"sub", "tenant_id", "roles", "iat", "exp"})` (~L112) + arbitrary `extra` dict
  - `JWTManager.decode(token) -> JWTClaims` (~L172) validates signature + expiration via `jose_jwt.decode`
  - `backend/src/platform_layer/middleware/tenant_context.py` `TenantContextMiddleware.dispatch` (~L119) reads `Authorization: Bearer` → decodes via JWTManager → populates `request.state.{tenant_id, user_id, roles}`
- **Why NOT JWKS / RS256**: Vendor SDK (`workos.AsyncWorkOSClient.user_management.authenticate_with_code`) handles vendor JWT validation **internally** — V2 never decodes vendor tokens directly. V2 issues its own HS256 JWT post-callback. Saves: JWKS endpoint discovery + key rotation handling + RSA key management. Trade-off: V2 JWT secret is the central trust root (rotated via Settings → restart).
- **Verification**:
  ```bash
  cd backend && python -m pytest tests/unit/platform_layer/identity/test_jwt.py -v
  ```
  12 tests pass (JWT manager: encode + decode + reserved claims + roundtrip + extra payload + expiration)
- **Test fixture**: Settings stub with explicit `secret` + `algorithm="HS256"` + `expires_minutes`

### 2.3 V2 User Upsert via Composite (tenant_id, external_id) Key (US-A2)

- **Implementation**:
  - `backend/src/api/v1/auth.py` `_upsert_user_from_oidc(profile, tenant_id, db) -> User` (~L91) — composite-key lookup `(User.tenant_id, User.external_id)`, INSERT new on miss + flush
  - `backend/src/infrastructure/db/models/identity.py` `User` ORM (~L158): `external_id: Mapped[str | None]` (~L170) + `Index("idx_users_external", "external_id", postgresql_where="external_id IS NOT NULL")` (~L191) — column **already existed** pre-Sprint 57.7 (D8 Day 0 schema verify saved Alembic 0017 migration scope)
  - `Tenant.code` resolution at `/callback` (~L155): query `select(Tenant).where(Tenant.code == oidc_tenant_code)` → 400 if missing (NO "default" magic per Multi-tenant 鐵律 #1)
- **Why composite**: same WorkOS user might belong to multiple V2 tenants in multi-IdP federation (Phase 58+); `external_id` alone NOT unique. Composite preserves Multi-tenant 鐵律 #2 + matches existing `users.idx_users_external` partial index for fast lookup.
- **Subsequent login behavior**: lookup hit → preserve User row identity, refresh `display_name` if vendor profile changed (per `_format_display_name` helper at `auth.py` L132)
- **Verification**:
  ```bash
  cd backend && python -m pytest tests/unit/platform_layer/identity/test_oidc.py::TestUserUpsert -v
  ```
  1 test pass: `test_upsert_inserts_on_first_login` verifies INSERT path with mocked AsyncSession (db.add + db.flush call contract)
- **Test fixture**: `AsyncMock(AsyncSession)` + `MagicMock` for sync `add()` per SQLAlchemy 2.0 async semantics

### 2.4 DB-Backed RBAC Hybrid Path (US-A3)

- **Implementation**:
  - `backend/src/platform_layer/identity/rbac.py` `RBACManager.has_role_code(user_id, tenant_id, allowed_codes, session) -> bool` — SQL JOIN `users → user_roles → roles` filtered by `tenant_id` + `roles.code IN allowed_codes`
  - `backend/src/platform_layer/identity/auth.py` `_require_role(request, allowed_codes, ...)` (~L161): **Path 1** preserved — JWT roles claim short-circuit grant if matched (`request.state.roles & allowed_codes` non-empty); **Path 2** opt-in via `Settings.rbac_db_backed_fallback=False` default — when JWT path fails AND opt-in ON, query DB via RBACManager
  - 3 public deps preserved: `require_audit_role` / `require_approver_role` / `require_admin_platform_role` (no API surface change, internal swap only)
- **Why hybrid**: 100+ existing tests mock `request.state.roles` via `SimpleNamespace` stub WITHOUT tenant_id — pure DB-only swap would break them all. Opt-in env flag preserves test fixtures + enables per-deployment migration. Full DB-only enforcement deferred Phase 58+ when test fixtures get tenant_id retrofit.
- **Verification**:
  ```bash
  cd backend && python -m pytest tests/unit/platform_layer/identity/test_rbac.py -v
  ```
  7 tests pass: has_role_code matching → True; non-matching → False; empty allowed_codes early return; Path 1 JWT short-circuit; Path 2 opt-in OFF default falls through; Path 2 ON DB grant; Path 2 ON DB lacks role still 403
- **Test fixture**: `patch.object(RBACManager, "_has_role_code_with_session", new_callable=AsyncMock, return_value=...)` bypasses real DB session factory

### 2.5 Sessions + ToolCalls Observer (US-R1 — closes AD-Reality-3a + 3b)

- **Implementation**:
  - `backend/src/api/v1/chat/router.py` chat() POST handler (~L119) adds `current_user: UUID = Depends(get_current_user_id)` (~L123) — **no new infra needed**, existing `TenantContextMiddleware.dispatch` (~L119 of tenant_context.py) already populates `request.state.user_id` since Sprint 49.3
  - Pre-stream Session INSERT (~L210): `SessionRepository(db).create_session(session_id, user_id=current_user, tenant_id=current_tenant)` wrapped in `db.begin_nested()` SAVEPOINT (best-effort; FK violation isolation per `.claude/rules/testing.md`)
  - In-stream ToolCall INSERT in `_stream_loop_events` ~L450: on `ToolCallExecuted` event → `ToolCallRepository(db).create(session_id, tenant_id, tool_name, arguments, status="completed", duration_ms)` — co-located with `cost_ledger.record_tool_call` hook (Sprint 56.3 single-dispatch pattern)
  - Env flags `SESSIONS_CHAT_OBSERVER` + `TOOL_CALLS_CHAT_OBSERVER` default `"true"` production / `"false"` tests (autouse `monkeypatch.setenv` at `tests/unit/api/v1/chat/test_router.py` post-Sprint 57.7)
  - NEW DAOs: `backend/src/infrastructure/db/repositories/{session_repository, tool_call_repository}.py` matching audit_helper.py pattern
- **D19 critical insight**: Sprint 57.6 progress notes incorrectly claimed AD-Reality-3a was "blocked by missing user_id JWT extraction infra". Day 3 探勘 verified `TenantContextMiddleware` already populates `request.state.user_id` from JWT `claim.sub` UUID parsing since Sprint 49.3 (~3 sprint cycles ago). `get_current_user_id` dep at `auth.py:84`. **Single-line fix saved ~3-5 hr** of feared "infra design + Alembic" scope.
- **Verification**:
  ```bash
  cd backend && python -m pytest tests/unit/infrastructure/db/repositories/ tests/unit/api/v1/chat/test_router.py -v
  ```
  6 + 65 = 71 tests pass: SessionRepository 2 + ToolCallRepository 4 (INSERT contract / status / duration / permission) + chat router 65 (regression sentinel verifies dep override + env-disable autouse fixture works)
- **Test fixture**: `AsyncMock(AsyncSession)` + `MagicMock` for `session.add` (sync); `monkeypatch.setenv` for 3 observer env flags

---

## 3. Cross-Category Contracts

**None added.** This sprint's vertical is standalone — no new ABC, no new event type, no new shared dataclass. Verifications:

- `agent_harness/_contracts/` — 0 new files post-Sprint 57.7 (`grep -l "Sprint 57.7" backend/src/agent_harness/_contracts/*.py` returns empty)
- `17-cross-category-interfaces.md` — NOT modified (no §X.Y registration needed)
- All new code lives in: `platform_layer/identity/` (oidc.py + rbac.py + auth.py extension) + `infrastructure/db/repositories/` (DAOs) + `api/v1/auth.py` + `api/v1/chat/router.py` (consumer wiring) + `frontend/src/components/` + `frontend/src/features/cost-dashboard/`

---

## 4. Open Invariants (deferred to Phase 58+ — NOT verified this sprint)

- [ ] **SAML 2.0 connection setup** — deferred until first $50K+ ACV deal demands SAML (WorkOS supports natively; activation = vendor portal config + V2 connection_id mapping)
- [ ] **MFA TOTP enrollment + challenge flow** — vendor supports via `user_management.{create_authenticate, authenticate_with_totp}`; V2 not yet wired
- [ ] **Refresh token rotation** — vendor `authenticate_with_refresh_token` available; V2 currently issues 1-hour HS256 JWT requiring re-login (no rotation)
- [ ] **SCIM 2.0 directory provisioning** — vendor `directory_sync` API; V2 not yet ingested for auto-user-provisioning
- [ ] **Frontend auth UX polish** — login page is bare button + callback page is bare loading; sign-up flow / forgot password / MFA settings deferred Phase 58.2+ Frontend Pages 11
- [ ] **Sentry browser error tracking** — `AppErrorBoundary.tsx` has placeholder for Sentry integration; deferred Phase 58.2+ Tier 1
- [ ] **Production HITL wiring smoke** — RBAC opt-in `Settings.rbac_db_backed_fallback=True` + 100+ test fixture retrofit deferred Phase 58+
- [ ] **AD-Reality-3c guardrail_audit observer** + **3d verification_audit observer** — same chat router observer pattern; estimated ~2-3 hr each post-Phase 58+ when guardrail/verification events finalize their persistence schemas
- [ ] **Real Postgres integration test for FK violation SAVEPOINT isolation** — current Sprint 57.7 unit tests use `AsyncMock(AsyncSession)` verifying call contract only; integration tests deferred Phase 58+ (real Postgres + RLS context working)
- [ ] **`useQuery` TanStack migration of CostOverview** — Zustand `useCostStore.loadData` pattern preserved per surgical change scope (D23); QueryClient at root level enables future migration
- [ ] **MonthPicker + CostBreakdownTable child component Tailwind migration** — children retain inline styles per V2 紀律 surgical change discipline (D25); deferred Phase 58.2+ Frontend Pages 11 batch

---

## 5. Rollback / Fallback

### If WorkOS proves wrong vendor (Year 2-3 swap)

- **Effort estimate**: ~5-8 sprint per `iam-vendor-matrix.md` §5
- **Code revert points**:
  - `backend/src/platform_layer/identity/oidc.py` (replace `WorkOSOIDCFlow` with new vendor implementation matching same `OIDCProfile` interface)
  - `backend/src/api/v1/auth.py` callback endpoint (vendor-agnostic — no change beyond import)
  - `backend/requirements.txt` swap `workos>=4.0,<6.0` → new vendor SDK
  - DB column `users.external_id` (already exists pre-57.7; remap WorkOS user_id → new vendor user_id via 1-pass migration)
- **Sentinel**: existing branch tag `feature/sprint-57-7-iam-frontend-foundation` preserved as backup point

### If OIDC hosted login proves UX too restrictive

- **Fallback**: V2 already supports HS256 internal JWT path independent of OIDC (`JWTManager` is provider-agnostic)
- **Effort**: revert `auth.py` 3 endpoints + `oidc.py` import (~2-3 hr); restore manual user provisioning via `users` table seed

### If Frontend providers cause runtime issues

- **Fallback**: revert `main.tsx` to single `BrowserRouter` wrap (~10 min)
- **Effort**: 1 component revert; AppShell + ThemeProvider + AppErrorBoundary leave unused
- **Sentinel**: `git revert 7fee44c6` reverts Tier 3 cleanly

### If observer DB INSERTs cause production performance issue

- **Fallback**: env flag `SESSIONS_CHAT_OBSERVER=false` + `TOOL_CALLS_CHAT_OBSERVER=false` disables both (no code revert)
- **Effort**: env var change + restart (~5 min)
- **Sentinel**: best-effort SAVEPOINT pattern means failure already isolated from SSE stream

---

## 6. References

### Sprint artifacts

- Sprint plan: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-7-plan.md`
- Sprint checklist: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-7-checklist.md`
- Sprint progress: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-7/progress.md`
- Sprint retrospective: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-7/retrospective.md`
- IAM vendor matrix (intermediate): `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-7/iam-vendor-matrix.md`

### Related rules

- `.claude/rules/multi-tenant-data.md` — 鐵律 #1 (`tenant_id NOT NULL`) + #2 (composite key for cross-tenant isolation)
- `.claude/rules/llm-provider-neutrality.md` — `workos` is auth SDK (NOT LLM), allowed in `platform_layer/identity/`
- `.claude/rules/testing.md` §SAVEPOINT pattern — observer best-effort isolation
- `.claude/rules/testing.md` §Module-level Singleton Reset — applied to chat router test autouse env disable
- `.claude/rules/file-header-convention.md` — all 6+ NEW source files per convention
- `.claude/rules/sprint-workflow.md` §Step 5.5 spike-extract design note — this document follows

### Cross-references (non-Sprint-57.7 dependencies leveraged)

- `backend/src/platform_layer/identity/jwt.py` — Sprint 52.5 `JWTManager` reused unchanged
- `backend/src/platform_layer/middleware/tenant_context.py` — Sprint 49.3 + 52.5 `TenantContextMiddleware.dispatch` already populates `request.state.user_id` (D19 discovery saved 3-5 hr)
- `backend/src/api/v1/chat/router.py` audit_log observer (Sprint 57.6) — pattern reused for sessions/tool_calls
- `backend/src/infrastructure/db/audit_helper.py` (Sprint 57.6) — `append_audit` pattern reused
- `claudedocs/1-planning/enterprise-saas-gap-analysis-20260508.md` §1.2 Tier 0 #5 + #6 — gap drivers for IAM + RBAC + SCIM scope

---

## 7. Modification History

- 2026-05-10: Initial extract from Sprint 57.7 closeout (Day 4) — verified ratio ≥ 95%; 8-Point Quality Gate self-check pass
