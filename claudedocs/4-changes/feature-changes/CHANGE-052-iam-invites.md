# CHANGE-052: IAM Block B invites vertical spike (DB-backed invite lifecycle)

**Date**: 2026-06-06
**Sprint**: 57.85
**Scope**: platform_layer.identity + api/v1 + infrastructure/db + frontend/auth (C-12 IAM Block B invites leg)

## Problem
IAM Block B was an intentional Phase-58 gap: the auth frontend (invite/register/mfa pages) shipped mockup-fidelity in Sprint 57.23 with a fixture fallback + AP-2 demo banner, while the backend endpoints deliberately did not exist (frontend got 501). C-12's analysis mandated a thin **invites** vertical spike as the first slice (no full Block B/C plan). Without it, a tenant admin had no way to onboard a member and the invite page was a Potemkin.

## Root Cause
Block B backend (invites / self-register) + Block C (MFA) were deferred at Sprint 57.23 with 3 tracking ADs. This change closes the **invites** leg (`AD-Auth-Invite-Backend-IAM-Block-B-Phase58`).

## Solution
DB-backed invite lifecycle (user chose DB-opaque token over stateless JWT — revocable / single-use / expiring; design note `21-iam-invites-spike.md`):
- **NEW `invites` table** (migration `0026`, `TenantScopedMixin`): email / role_id / invited_by / `token_hash` (sha256, UNIQUE) / status (pending/accepted/revoked/expired) / expires_at / accepted_at / accepted_user_id. Partial-unique `(tenant_id,email) WHERE status='pending'`. RLS two-policy + a system-sentinel USING escape (mirrors `billing_outbox` 57.84) so the unauthenticated guest can look up by the high-entropy `token_hash`.
- **`InvitesService`** (`platform_layer/identity/invites.py`): `create` (opaque token via `secrets.token_urlsafe`, sha256-stored, returned once; role-in-tenant + lazy-expire + dup-pending guards; `invite_created` audit), `get_metadata` (sentinel lookup → switch to invite tenant → tenant/inviter/role names), `accept` (create User + grant UserRole + single-use consume via `UPDATE ... RETURNING id` + `invite_accepted` audit; `password` accepted-not-stored — deferred), `revoke`. Tenant context via `set_config` (mirrors the billing_outbox drainer).
- **3 endpoints** (`api/v1/invites.py`): POST `/admin/tenants/{tenant_id}/invites` (`require_admin_platform_role`) + GET `/invites/{token}` + POST `/invites/{token}/accept` (guest, exempt). `/api/v1/invites` added to `TenantContextMiddleware.EXEMPT_PATH_PREFIXES` (guest paths only; admin create stays non-exempt).
- **Frontend wire** (`invite/index.tsx`): removed fixture + AP-2 banner; consumes real GET (200→form / 404→invalid / 410→gone) + real accept error; i18n keys swapped (drop demoBanner/errorStubbed, add loading/invalid/gone/acceptError in en + zh-TW).

PR: pending (branch `feature/sprint-57-85-iam-invites`).

## Verification
- Unit (`test_invites_service.py`, 11): create/role/dup-pending guards + get_metadata resolve/expired/revoked/invalid + accept user+role+consume+audit + single-use + dup-email + hash_token.
- Integration (`test_invites.py`, 7 HTTP e2e): create-requires-admin(401) / create→GET→accept→User+UserRole+consumed / single-use(410) / invalid(404) / expired(410) / tenant-scoping / exempt-path contract.
- Frontend (`invite.test.tsx`, 5, rewritten in-place): real metadata / accept→navigate / accept-fail / 404-invalid / 410-gone.
- Gates: mypy 0/339 · full pytest **2179 passed** · run_all 10/10 (`check_rls_policies` for `invites`) · frontend lint(no `--silent`)+build · Vitest **757** · check:mockup-fidelity ✓ (oklch baseline 50 unchanged).
- No real-Azure needed (no LLM in the invites path; e2e proven by integration tests).

## Impact
Backend (+ migration `0026`) + frontend invite page + 2 i18n locales. New tenant-facing onboarding endpoints (admin create + guest accept). The accept's `password` is accepted-not-stored (local credentials deferred to 57.86). Rollback: revert the 5 NEW + 3 EDIT files + `alembic downgrade -1` (new empty table; < 30 min). DB-level RLS enforcement is untestable under the superuser test role → isolation asserted at the application layer (codebase convention); RLS policies present + enforce in production.

## Notes (design decisions)
- `get_by_token`→`get_metadata` (needs tenant/inviter/role names → sentinel lookup then switch to invite tenant, since users/roles have no sentinel escape).
- `.returning(Invite.id)` instead of `.rowcount` (mypy strict types `execute(update())` as `Result`, no `.rowcount`).
- Own-tenant guard dropped (redundant — `_ADMIN_PLATFORM_ROLES` are cross-tenant by design); invite scoped to path tenant + RLS.
- Lenient singleton (`maybe_get_invites_service() or InvitesService()`) — no lifespan wiring → no singleton-leak (avoids the 57.84 Day-3 regression class).
