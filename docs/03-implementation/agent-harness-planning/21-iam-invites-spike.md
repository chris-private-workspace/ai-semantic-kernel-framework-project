# 21 — IAM Block B: invites vertical spike (design note extract)

**Purpose**: Design note extracted from the Sprint 57.85 invites vertical spike (C-12 IAM Block B). Documents the verified invite lifecycle (DB-backed token + admin create + guest accept), the decisions that shaped it, and the explicit deferred boundary. Per `.claude/rules/sprint-workflow.md` §Step 5.5 (spike → retrospective → extract design note); per CLAUDE.md §"V2 不是『先寫一批新規劃文件』" this was extracted from a shipped spike, NOT pre-written.
**Category / Scope**: Platform / Identity (IAM) — C-12 Block B / Sprint 57.85
**Created**: 2026-06-06
**Status**: Active (verified against shipped code on `feature/sprint-57-85-iam-invites`)

> **Modification History**
> - 2026-06-06: Initial extract from Sprint 57.85 (invites spike)

**Related**:
- `c12-iam-block-bc-analysis-20260601.md` §4-§5 (mandated the thin invites slice)
- `20-iam-deep-dive.md` (Block A — JWT / OIDC / DB-RBAC reused here)
- `09-db-schema-design.md` §Group 1 Identity & Tenancy
- `0025_billing_outbox.py` (the sentinel-escape RLS precedent this spike mirrors)

---

## 1. Spike Summary (US-1..US-5)

A tenant admin invites a member (email + role) and receives a one-time token; the invitee views the invite metadata by token and accepts it to become an active User with the granted role. Invites are **DB-backed** (revocable / single-use / expiring), reusing the Block-A `User`/`Role`/`UserRole` ORM + WORM audit chain. The shipped frontend invite page (Sprint 57.23/57.35) is now wired to the real backend (fixture + AP-2 banner removed).

**Verified scope**: invite lifecycle (create → view → accept → user+role+audit), single-use, expiry, revoke, tenant scoping. **Deferred** (see §5): local-password credentials, self-service registration, MFA, invite email delivery, admin invites-list UI.

---

## 2. Decision Matrix

### 2.1 Token mechanism (US-1) — **DB-backed opaque token** chosen

| Option | Revocable | Single-use | Listable | Auditable | DB cost | Verdict |
|--------|-----------|------------|----------|-----------|---------|---------|
| **DB-backed opaque token** (chosen) | ✅ | ✅ (status state machine) | ✅ | ✅ | 1 table | **CHOSEN** — enterprise SaaS needs revoke + single-use + pending-list |
| Stateless JWT | ❌ (can't revoke before exp) | ❌ (replay until exp) | ❌ | weak | 0 tables | rejected — onboarding needs lifecycle control |

Token = `secrets.token_urlsafe(32)` (`invites.py:191`); only its `sha256` hex is stored (`token_hash`, `invites.py:197` + `hash_token()` `invites.py:347`); the raw token is returned **once** by create and never persisted. Lookup is a `token_hash =` equality only (`invites.py:_lookup`) — no enumeration.

### 2.2 Password handling (US-3) — **deferred (accepted-not-stored)**

Day-0 found no local-credential store (auth is OIDC/WorkOS + dev-login), the login page is OIDC-only with no password field (`frontend/src/pages/auth/login/index.tsx:158-176`), and mockup-fidelity forbids adding one. Adding credentials would be a ~2x backend-ahead slice with no UI consumer. Decision (user, 2 AskUserQuestion rounds): split — 57.85 = lifecycle only; the accept endpoint accepts `{full_name, password}` (the shipped contract) but the service does **not** receive/store `password` (`api/v1/invites.py:accept_invite` passes only `full_name`; `invites.py:accept` has no password param). Local credentials = `AD-Auth-Credentials-PasswordLogin-Phase58` (57.86).

### 2.3 Admin auth — **platform-admin gate only** (own-tenant guard dropped as redundant)

`require_admin_platform_role` (`platform_layer/identity/auth.py:142`) gates to `{admin, platform_admin}`. An initial own-tenant guard (`require_tenant_match_or_platform_admin`) was dropped: that helper (`auth.py:157`) treats both roles as cross-tenant (the codebase RBAC model + `admin/tenants.py` convention), so it was a no-op for the only roles that pass the gate. The invite is scoped to the **path** `tenant_id` and RLS-isolated; cross-tenant create by a platform admin is intentional (mirrors tenant creation).

---

## 3. Verified Invariants (file:line + verification)

| Invariant | Evidence | Verification |
|-----------|----------|--------------|
| Raw token never persisted; only sha256 stored | `invites.py:197` (`token_hash=hash_token(raw)`) + `:191` raw returned once | `test_create_returns_raw_token_and_stores_only_hash` |
| Role must belong to the tenant | `invites.py:create` role lookup `WHERE id, tenant_id` → `InviteRoleNotFoundError` | `test_create_unknown_role_raises` |
| One live pending invite per (tenant,email) | lazy-expire stale + dup-pending guard (`invites.py:create`) + partial-unique `uq_invites_pending_email` (`0026_invites.py`) | `test_create_duplicate_pending_raises` |
| Guest lookup is sentinel-scoped (no enumeration) | `invites.py:get_metadata`/`accept` set `app.tenant_id=SENTINEL` for the `token_hash=` lookup, then switch to `invite.tenant_id` | `test_get_metadata_*`, `test_e2e_create_get_accept` |
| Accept creates User + grants UserRole + WORM audit | `invites.py:accept` (`User(...)` + `UserRole(...)` + `append_audit("invite_accepted")`) | `test_accept_creates_user_grants_role_and_consumes` |
| Single-use (concurrent double-accept loses) | `UPDATE ... WHERE status='pending' RETURNING id` → None = loser → `InviteConsumedError` (`invites.py:accept`) | `test_accept_single_use` (unit + HTTP) |
| Duplicate-email-in-tenant rejected | `invites.py:accept` pre-check `User WHERE tenant_id,email` → `InviteEmailExistsError` (409) | `test_accept_duplicate_email_raises` |
| Lazy expiry on read | `_guard_pending` (`invites.py`) treats `pending && expires_at<=now` as expired (410) | `test_get_metadata_expired_raises`, `test_get_expired_token_410` |
| Guest paths exempt; admin create non-exempt | `TenantContextMiddleware.EXEMPT_PATH_PREFIXES` += `/api/v1/invites` (`tenant_context.py:118+`) | `test_create_requires_admin` (401), `test_exempt_path_contract` |
| Invite scoped to path tenant | `invites.py:create` inserts `tenant_id=<path>`; create endpoint passes path `tenant_id` | `test_invite_scoped_to_path_tenant` |

**Verification command**:
```
cd backend && python -m pytest tests/unit/platform_layer/identity/test_invites_service.py tests/integration/api/test_invites.py -q
```
**Test fixtures**: `tests/conftest.py` (`db_session`, `seed_tenant`, `seed_user`); integration `_build_app` (X-Test-User/Roles/Tenant headers + override `get_db_session`/`require_admin_platform_role`) mirrors `test_admin_tenant_hitl_policies.py`. Gates: mypy 0/339, full pytest 2179, run_all 10/10, Vitest 757.

---

## 4. Cross-Category Contracts (17.md assessment)

**17.md = N/A** (assessed, same call as 57.84 billing_outbox). `17-cross-category-interfaces.md` registers the 11+1 **category** contracts (ChatClient / LoopEvent / HITL / tool registry); `platform_layer.identity` is not a registered category surface there (sibling `auth.py` / `jwt.py` are absent too). The invite contract lives in this design note + the module docstrings + CHANGE-052. The endpoint→frontend contract is `InviteMetadata {tenant, invitedBy, role, expiresIn}` (`api/v1/invites.py:InviteMetadataResponse` serialization_alias ↔ `frontend/src/pages/auth/invite/index.tsx:InviteMetadata`).

---

## 5. Open Invariants (deferred — NOT verified here)

- **Local-password credentials + password-login endpoint** — `AD-Auth-Credentials-PasswordLogin-Phase58` (57.86). The accept's `password` is accepted-not-stored; the created user authenticates via OIDC/dev-login until then.
- **Self-service tenant registration** — `AD-Auth-Register-Backend-IAM-Block-B-Phase58` (POST /tenants/register).
- **MFA TOTP + WebAuthn** — `AD-Auth-MFA-Backend-IAM-Block-C-Phase58` (accept navigates to `/auth/mfa`, still stub 501).
- **Invite email delivery** — no email facility; create returns the raw token in-response (Phase 58 follow-up).
- **Admin invites-list / resend UI** — `revoke` service method exists; the management surface is a follow-up.
- **DB-level RLS enforcement is NOT exercised in tests** — the `ipa_v2` test DB role is a superuser (bypasses RLS even under FORCE); a cross-tenant read is not blocked at the DB in tests. The RLS policies + sentinel escape are present (`check_rls_policies` green) and enforce in production under a non-superuser app role; isolation is asserted at the application layer here (per the codebase isolation-test convention — hitl/quotas do the same). The sentinel escape is correct-by-construction (mirrors the production-verified billing_outbox 57.84).

---

## 6. Rollback

- **Backend**: revert the 5 NEW files (`models/invites.py`, `0026_invites.py`, `platform_layer/identity/invites.py`, `api/v1/invites.py`) + 3 EDITs (`models/__init__.py` register, `api/main.py` include, `tenant_context.py` exempt). DB: `alembic downgrade -1` drops the `invites` table (no other table references it). Est. < 30 min; no data migration to reverse (new empty table).
- **Frontend**: revert `invite/index.tsx` + the 4 i18n keys — restores the fixture + AP-2 banner (the page degrades to the pre-wire interim state).
- **Sentinel-escape risk**: the all-zeros sentinel in the `invites` RLS USING is identical to the production-shipped `billing_outbox` (57.84) — a real request never runs under it (the guest endpoint sets it explicitly only for the token lookup, then switches to the invite's tenant).

---

## 7. References

- Code: `backend/src/infrastructure/db/models/invites.py`, `migrations/versions/0026_invites.py`, `backend/src/platform_layer/identity/invites.py`, `backend/src/api/v1/invites.py`, `backend/src/platform_layer/middleware/tenant_context.py`, `frontend/src/pages/auth/invite/index.tsx`
- Tests: `backend/tests/unit/platform_layer/identity/test_invites_service.py`, `backend/tests/integration/api/test_invites.py`, `frontend/tests/unit/pages/auth/invite.test.tsx`
- Change record: `claudedocs/4-changes/feature-changes/CHANGE-052-iam-invites.md`
- Plan / checklist / progress / retrospective: `phase-57-frontend-saas/sprint-57-85-{plan,checklist}.md` + `agent-harness-execution/phase-57/sprint-57-85/{progress,retrospective}.md`
