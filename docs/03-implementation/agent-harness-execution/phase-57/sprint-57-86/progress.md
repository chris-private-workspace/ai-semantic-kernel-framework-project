# Sprint 57.86 Progress — C-12 IAM Block B/C: local credentials + password-login vertical spike

**Branch**: `feature/sprint-57-86-credentials-password-login` (from `main` `f61df966`)
**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-86-plan.md`
**Closes**: `AD-Auth-Credentials-PasswordLogin-Phase58` (local-password leg of C-12 Block B/C; the password 57.85 deferred)

---

## Day 0 — 2026-06-06 — Plan-vs-Repo Verify + Branch + Decisions

### Context
57.85 invite-accept accepts `{full_name, password}` but stores nothing (no local-credential store; OIDC/dev-login only). User split the credential leg to 57.86, then picked it (2026-06-06) to continue "process all" of the C-area gaps.

### Day-0 三-prong verify (Explore two-pass + parent grep/read, main `f61df966`)
- **Prong 1 (path)** — JWTManager HS256 `jwt.py:103-237`; dev-login JWT+cookie+AuthMeResponse template `auth.py:375-436` (`_JWT_COOKIE='v2_jwt'`, `_cookie_kwargs` httponly/secure/samesite=lax `:81-92`, `AuthMeResponse` `:110-126`); **`Tenant.code String(64) unique` `identity.py:116`**; tenant-by-code `select(Tenant).where(Tenant.code==...)` `:251`; OIDC roles `["user"]` `:292`; EXEMPT_PATH_PREFIXES per-subpath (`tenant_context.py`).
- **Prong 2 (content)** — route `App.tsx:97-103` + lazy `:38-45`; dev page `fetchWithAuth(POST)`→`bootstrap()`→`navigate(consumePostLoginRedirect())` `dev/index.tsx:100-113`; authStore.bootstrap→`fetchAuthMe()` GET `/me`; primitives `@/components/mockup-ui` (Card/Field/Button/Icon)+AuthShell, classes `.col/.input/.card` (reuse — no new CSS); i18n en/zh-TW `auth.json`; mockup `page-auth-extras.jsx` (AuthRegister/Invite/MFA) + `i18n.jsx`.
- **Prong 3 (schema)** — `User` has NO credential column (`identity.py:187-225`); no bcrypt/passlib/argon2 dep; migration head `0026_invites` → next `0027`; `users` already RLS-enabled → no new policy.

### Drift findings
- **D1** — No bcrypt dep + no password column → add `bcrypt` to requirements + `users.password_hash` nullable. Plan §3.1/§3.2.
- **D2** — 57.85 `InvitesService.accept` has no `password` param (`invites.py:248-311`); endpoint drops `body.password` (`api/v1/invites.py:181-192`) → wire it (param `password=None` default to avoid regressing callers). Plan §3.3 / Risk #8.
- **D3** — dev-login passes creds as QUERY string (logged) → password-login uses a **JSON body**. Plan §3.4 / §3.0.
- **D4** — No auth rate-limit/lockout → brute-force throttle is a tracked carryover (`AD-Auth-PasswordLogin-Lockout-Phase58`), NOT built. Plan §9 / Risk #5.
- **D5** — bcrypt is sync/CPU-bound + truncates at 72 bytes → `anyio.to_thread.run_sync` offload + `max_length=72` on password fields. Plan §3.2 / Risk #4.

### Decisions locked (AskUserQuestion ×2, 2026-06-06)
1. **Scope** = **full vertical slice + new login page** (the only option with no Potemkin AND no fidelity violation — store password + `POST /auth/password-login` + NEW `/auth/password-login` page + a deliberate mockup `AuthPasswordLogin` extension so the canonical source stays honest). (Rejected: backend-only = Potemkin; defer = user wants this leg.)
2. **Tenant resolution** = **tenant-code field** — page has tenant code + email + password; endpoint `(tenant_code, email)` lookup (email is per-tenant unique; same email can exist in 2 tenants). Sentinel/global-email rejected (breaks multi-tenant uniqueness).
3. **Hash** = **bcrypt direct, cost=12** (well-maintained; no passlib bcrypt-4.x compat noise). argon2/passlib rejected.
4. **Defaults (parent call)**: `users.password_hash` nullable column (reuse users RLS, no new policy) over a separate `user_credentials` table (lean monolithic identity convention); endpoint EXEMPT (pre-JWT); generic-401 for all failure modes + constant-time miss (anti-enumeration); lockout deferred.

### go/no-go
**GO.** ~1.5-2× a small sprint (≈ 57.85: new security domain + new public auth endpoint + new page + mockup extension). Safe cut-line at Day-2-end (passwords + credentials + invite-accept storage + service/unit tests, nothing HTTP/UI-wired); endpoint + frontend + mockup can carryover as `AD-PasswordLogin-Endpoint-Frontend-Wire` if Day-3 over-runs.

### Calibration (plan-time)
- **Agent-delegated: no** (parent-direct — security-sensitive: bcrypt offload/72-byte guard, generic-401/enumeration, auth endpoint + cookie/JWT, multi-tenant credential isolation; consistent with billing 57.79-84 + IAM 57.85 all parent-direct). `agent_factor` 1.0 → 3-segment.
- `medium-backend` 0.80 (backend dominates). **Greenfield-IAM 2nd data point** — 57.85 ran ~1.25 over; if this confirms (> 1.0) → propose `iam-backend-spike` class in retro (do NOT pre-create).
- Bottom-up est ~10.5 hr → class-calibrated commit ~8.4 hr (0.80).

### Day 0 actions
- Branch `feature/sprint-57-86-credentials-password-login` created (from `main` `f61df966`).
- Plan + checklist drafted (mirror 57.85 structure: plan 9 sections; checklist Day 0-4).
- This progress.md Day-0 entry.

### Remaining for next day
- Day 1: `bcrypt` dep + `passwords.py` util + `User.password_hash` ORM + migration `0027` (read `0026` header for down_revision; both-direction apply).

---

## Day 1 — 2026-06-06 — Schema + hashing util

- EDIT `requirements.txt` — `bcrypt>=4.1,<5.0` (installed bcrypt 4.3.0).
- NEW `platform_layer/identity/passwords.py` — `hash_password`/`verify_password` (bcrypt cost=12; both offloaded via `anyio.to_thread.run_sync`; UTF-8 truncated to 72 bytes in BOTH so behaviour is deterministic + version-independent — bcrypt 4.x may raise on >72 bytes; `verify` swallows malformed-hash `ValueError` → False, never raises). Pure (no DB).
- EDIT `infrastructure/db/models/identity.py` — `User.password_hash: Mapped[str | None] = mapped_column(String(255))` (nullable via Optional; no alias — `users` has no alias pattern) + MHist.
- NEW migration `0027_user_password_hash` (down_revision `0026_invites`) — `add_column`/`drop_column`; NO new RLS policy (the column inherits the existing `users` row-level RLS). Applied **both directions** on Docker DB (`alembic current`=`0027_user_password_hash (head)`).
- Gates: black/isort/flake8 0; mypy **0/341**; `run_all.py` **10/10** (`check_rls_policies` green — `users` already covered, no new policy). Commit (pending).

### Remaining
- Day 2 (SAFE CUT-LINE): `CredentialsService` (set_password + authenticate, generic-error + constant-time miss) + wire `InvitesService.accept(password=…)` storage + unit tests (passwords + credentials) + extend invite test (accept stores hash).
