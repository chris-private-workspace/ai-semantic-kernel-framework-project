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
