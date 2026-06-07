# Frontend Drive-Through Audit — 35 pages (2026-06-06)

**Purpose**: Systematic drive-through verification of all V2 frontend pages — open the real UI (dev server :3007) + real backend (:8000) + real LLM (Azure), walk every control, and record per-page verdict (達標 / Potemkin / stub / 死控件 / 假資料 / 不渲染). Per CLAUDE.md §Drive-Through Acceptance Hard Constraint: gate-green ≠ "人能真的用".
**Category / Scope**: Status / Drive-Through audit (all 35 frontend pages)
**Created**: 2026-06-06
**Status**: In progress (drive-through sweep)
**Method**: Playwright MCP (single browser session) — navigate → accessibility snapshot → interact → screenshot. Screenshots in `shots/`.

> NOTE: audit only — no code change this pass. Issues feed `next-phase-candidates.md` for later sprints.

---

## 1. Environment (as found)

| Item | State |
|------|-------|
| Backend | ✅ :8000 (PID 15056, parallel-session) · `GET /api/v1/health` 200 |
| Frontend | ✅ :3007 (PID 38824; not the CLAUDE.md-documented 3005 — port drift / parallel session) |
| Docker | ❌ `docker-compose` not detected by dev.py (postgres/redis likely host-native; health 200 implies DB reachable) |
| Azure (real LLM) | ✅ `AZURE_OPENAI_API_KEY/ENDPOINT/DEPLOYMENT_NAME/MODEL_NAME` all SET in `.env` |
| `DEV_LOGIN` in .env | absent — but dev-login **works** (backend dev-mode accepts; see §3) |
| Branch | `chore/drive-through-acceptance-principle` (parallel session switched it; = main + 1 chore commit) |

⚠️ Two-sessions-one-worktree: the running backend/frontend were started by a parallel Claude session and may `--reload` or be otherwise touched mid-audit. Findings noted where relevant.

## 2. Route map — 35 pages, three states (from `routes.config.ts`)

- **Full impl (15, active no-proposed)**: overview, chat-v2, orchestrator, subagents, loop-debug, memory, state-inspector, governance, verification, redaction, error-policy, cost-dashboard, sla-dashboard, admin-tenants, tenant-settings
- **Proposed stub (12, active+proposed → ComingSoonPlaceholder)**: compaction, jit-retrieval, subagent-tree, incidents, cache-manager, sse, devui, models, tools, tenant-onboarding, pricing, rbac
- **Designed-only (4, active=false → no route, sidebar DRAFT)**: audit-log, feature-flags, profile, mfa-settings
- **Auth (8)**: login, callback, register, invite/:token, password-login, mfa, expired, dev (DEV-only)

## 3. Login finding ✅ + ⚠️

- **dev-login works** (`/auth/dev` → select identity/tenant/role → Continue → redirect `/cost-dashboard`). This is the drive-through entry for all 27 protected pages.
- ⚠️ **RBAC not effective** (`AD-RBAC-DB-To-JWT-Wiring`): selected identity = `dan@acme.com · admin`, but header + sidebar render role = **user**, and "admin-only" content (cost-dashboard Provider mix) still shows to that user. The dev-login role selection does not flow into the JWT `roles` claim → admin gating is cosmetic, not enforced.

## 4. Per-page verdict

Legend: 🟢 達標(接通+渲染) · 🟡 混合(部分真+部分標示fixture) · 🔵 stub(誠實ComingSoon) · 🔴 Potemkin(死控件/假資料不標示/不渲染/誤導)

| # | Page | Verdict | Notes |
|---|------|---------|-------|
| 1 | /cost-dashboard | 🟡 混合 | Real cost_ledger table + Total `$0.0291015` (真 LLM 57.79-84 data incl. `_verification` sub_type) bottom; 4 upper widgets (spend-over-time / by-category / by-tenant / provider-mix) all show fixture **but each carries a `⚠️ ...fixture data` note** (honest). "By tenant"/"CSV" buttons `disabled`. RBAC: shows user not admin (§3). Top KPIs ($0.029 real-ish, 14.2M tokens / 38% cache likely fixture — not noted). |
| 2 | /overview | 🟡 混合 | Full dashboard renders (4 KPI + Active loops + HITL queue + Cost burn + Providers + Recent incidents + Errors-24h + 4 quick-actions). 5 main widgets each carry honest `⚠️ ...fixture...AD-Overview-Backend-Extensions-Phase58` note. ⚠️ **4 top KPI cards (14 loops / 3 HITL / $2,847 MTD / 1.84s p95) carry NO fixture note** — `$2,847` contradicts real cost_ledger `$0.029` → unlabeled fixture (AP-4 risk). RBAC user-not-admin (§3). Buttons are nav-shortcuts (untested this pass). |
| 3 | /orchestrator | 🔴 **Potemkin** | Looks complete (header `orchestrator-main v3.4.1 live` + 4 KPI [2,847 sessions / 4.2 turns / 412 spawns / 18.4s] + 6 tabs [Config/SystemPrompt/Tools18/Subagents6/Budgets/Policies] + rich Config form: model combobox / temp / top-p / memory scopes 5× / verification switches 3×). BUT network = **zero orchestrator/config/data API** (only auth/me + telemetry) → all values hardcoded mockup, form not backend-wired, **NO fixture note**. "Deploy" clicked → no API call, no effect (dead control). Unlabeled fixture on a so-called full-impl page = AP-4. |
| 4 | /subagents | 🟢 達標 | Real backend ✅ `GET /api/v1/subagents → 200` (agent_catalog #244): 3 agents (researcher/reviewer/planner, handoff) render from API with real system-prompt text; 4 mode KPIs (fork0/as_tool0/teammate0/handoff3) consistent; empty Model/Calls/p95 honestly "—". Controls (Sync from repo / New subagent / Test invoke) untested. Good contrast vs orchestrator — same config-page shape, this one is real. |
| 5 | /loop-debug | 🟡 混合 | Loop Visualizer renders (session sess_4tk2p_demo + 6 event-type filters + Replay/Live + playback slider 18/18 + speed 1-16× + 4-turn/18-event tree + Event Inspector). Honest **`⚠️ DEMO DATA...live SSE populates when chat-v2 runs...Phase 58+ Sprint 57.12 AP-6`** note. No loop/session API (fixture, labelled) → not Potemkin. Core live-SSE value needs a chat-v2 run (deferred + labelled). |
| 6 | /memory | 🟢 達標 | Real backend ✅ `GET /api/v1/memory/matrix → 200` + `/memory/ops?limit=50 → 200` (57.73/57.77). Honest empty state (0 entries → "No memory entries" / "No memory operations recorded yet"; time-travel scrubber disabled). GDPR erasure form present but honestly labelled `⚠️ endpoint pending Phase 58+ POST /memory/erasure`. Data layer real. |
| 7 | /state-inspector | 🟡 混合 | Version chain (10 versions/3 checkpoints) + 4 KPI + transient/durable detail + diff-vs-parent render. Honest **"Backend gap: version chain from mockup fixture — Cat 7 list-by-session endpoint not impl (AD-State-VersionChain-Phase58); ?session_id=<uuid> fetches latest version live via US-B3"**. Fixture but labelled + real-path documented → not Potemkin. |
| 8 | /governance | 🟡 混合 | Real backend ✅ `GET /api/v1/governance/approvals → 200` → Active queue 0 (real empty "No pending approvals"). Stats KPIs (p50 2m18s / Approved184 / Rejected6 / Expired2) demo but honestly noted `⚠️ ...demo data pending backend stats endpoint`. 2 tabs (Pending/Audit Log) + sub-tabs + Teams-sync/Export. Core queue real, peripheral stats labelled-demo. |
| 9 | /verification | 🟢 達標 | Real backend ✅ `GET /api/v1/verification/recent → 200` — **Recent runs table shows REAL 57.83 B-8 judge log** (llm_judge passed 0.56-0.74 + "refuses or deflects" 0.93-0.96 + "empty/off-topic Hello" 0.98 = the actual nonsense-prompt test results). Peripheral KPIs (pass-rate/claims/failed/latency) + Failure-kinds + Flaky-checks honestly noted `⚠️ aggregation endpoint pending Phase 58+`. 2 tabs (Recent/Correction Trace). Core data real. |
| 10 | /redaction | 🟡 混合 | Observation Masker + 4 KPI + 8-pattern table (email/cc/ssn/ipv4/aws_key/bearer/ghp/private_key regex) + Recent redactions — all fixture. Honest **"Backend gap: observation-masker API not yet shipped...mockup fixtures...Phase 58+ AD-Redaction-Backend-API"**. Whole-page fixture but labelled → honest placeholder, not Potemkin. |
| 11 | /error-policy | 🟡 混合 | 4 KPI + 4-class taxonomy (TRANSIENT/LLM_REC/HITL_REC/FATAL) + Retry budget + Circuit-breakers table — all fixture. Honest **"Backend gap: errors.py wired but /api/v1/error-policy read API not shipped...mockup fixtures...Phase 58+ AD-ErrorPolicy-Backend-API"**. "Force close" button untested (likely dead; page labelled fixture). Not Potemkin. |
| 12 | /sla-dashboard | 🔴 真 bug | Most widgets honest fixture (`⚠️ ...AD-SLA-Dashboard-Backend-Extensions`; time-range tabs labelled "visual-only this sprint"). BUT **`GET /api/v1/admin/tenants/{tid}/sla-report?month=2026-06 → HTTP 500`** (`slaService.ts:16` fetchSLAReport) → UI shows `alert: Failed to load data / HTTP 500 / Retry`. Real wiring exists but backend 500s — genuine bug, NOT Potemkin. **ISSUE-1: sla-report endpoint 500.** |
| 13 | /admin-tenants | 🟢 達標 | Real backend ✅ `GET /api/v1/admin/tenants → 200` + `/stats → 200`. Table renders many REAL tenants (RACE_/GV_/AE_/ISO_/BATCH_/PATCH_ test-residue, all "requested", created 2026-06-06). KPIs (seats 27,854 / agents 7,599) real from /stats; Anomalies + trend deltas honestly noted no-backend-source. Minor: list-header "48 active · 3 anomalies" is a fixture string vs real KPI "Active tenants 0" (ISSUE-2 minor inconsistency). |
| 14 | /tenant-settings | 🟢 達標 | 6 tabs (General/FeatureFlags14/Quotas/HITLPolicies/Members8/DangerZone). General shows tenant-effective from DB (acme-prod/enterprise/5seats) + honest notes: "Region/locale/retention/seats backend PATCH supported (57.46), inline edit UI Phase58+" / "SCIM/domains/MFA via fixture-projection (57.50), SSO write deferred". Tabs map to 57.54-57.57 WRITE ship (FF/Quotas/RateLimits/HITL). Data layer real + boundaries labelled; per-tab deep-click not done this pass. |
| 15 | /chat-v2 | 🟢 達標 ⭐ | **MAIN-FLOW DRIVE-THROUGH PASS**. Sent "What does HTTP stand for?" → real **gpt-5.2** agent loop → **answer RENDERED** ("HTTP stands for Hypertext Transfer Protocol.") → verification llm_judge 0.78 passed (B-8 default-enable 57.83 LIVE) → full real trace spans in Loop visualizer (loop_start/compaction/prompt_build[2953 tok,3 cache-bp,LostInMiddle]/llm_call 3234ms/checkpoint v1/verification/loop_end end_turn). Covers Cat 1/4/5/6/7/10/12. #254 fixes verified (answer renders, real_llm default, New-session, DEMO-labelled session list). Minor: Inspector Turn metadata (tokens.in=0/out=—/cost=—/trace_id=—) NOT wired despite loop events carrying values (ISSUE-3). |
| 16-27 | 12 proposed stubs (compaction / jit-retrieval / subagent-tree / incidents / cache-manager / sse / devui / models / tools / tenant-onboarding / pricing / rbac) | 🔵 stub (誠實) | All 12 render identical `ComingSoonPlaceholder`: title + PROP badge + "Coming Soon — design is in design/operator-portal/page-*.jsx" + mockup link + "Sprint 57.18 = scaffold; 57.19+ = rolling port". No dead pages, no mislabeled fixture. Honest scaffolding per routes.config three-state. |
| 17 | /auth/login | 🟢 達標 | mockup-faithful: Sign in + 3 SSO buttons all `disabled` (honest, no WorkOS local) + Work email/Continue + dev-login link (works) + MFA hint. OIDC Continue not tested (needs real IdP — known local limit). |
| 18 | /auth/register | 🟡 前端OK / 後端stale | 4-step wizard drive-through PASS (Identity→Org→Plan→Confirm; all fields/steps/Back work, summary correct, terms checkbox, **no demo banner** 57.87). Submit → **`POST /api/v1/tenants/register → 404`** → error-UX correctly shows `alert: Could not create your workspace`. BUT code correct (`main.py:352 include_router(tenants_router)` + `api/v1/tenants.py` exists, 57.87 merged) → **404 = STALE BACKEND** (PID 15056 from parallel session predates 57.87 router; **Risk Class E**). Frontend + error-UX real; e2e blocked by stale process, NOT code bug. **ISSUE-3: restart backend to verify 57.84-87 endpoints.** |
| 19 | /auth/password-login | 🟡 前端OK / 後端stale | 57.86 page renders (tenant code + email + password + Sign in). Submit → **`POST /api/v1/auth/password-login → 404`** (SAME stale-backend pattern as register). Error-UX shows `alert: Invalid credentials` (msg imprecise for a 404, but handled). Confirms stale backend: BOTH 57.86+57.87 endpoints 404 while code correct → PID 15056 predates these routers. |
| 20 | /auth/invite/:token | 🟡 前端OK | `GET /api/v1/invites/{token} → 404` for fake token → correctly shows `alert: This invite link is invalid`. (404 expected for a fake token regardless of backend; real invite e2e needs a real token + current backend.) |
| 21 | /auth/mfa | 🔵 stub (誠實) | Two-factor page (6-digit input + Authenticator/Security-Key tabs + recovery link) + honest `⚠️ MFA backend wire pending Phase 58+ IAM Block C — verify will return 501`. |
| 22 | /auth/expired | 🟡 混合 | Session-expired page (Last activity 14h02m / sess_8a2f1c3 / jwt_expired + Sign-in-again/Resume). Static mockup values unlabelled, but informational error page (real values arrive when an auth-fail redirects here). |
| 23 | /auth/callback | 🟢 達標 | Already-authed → correctly redirects to /cost-dashboard. (OIDC code-exchange path not tested — needs real IdP.) **Bonus evidence**: cost-dashboard Total rose $0.0291→$0.0337 reflecting the chat-v2 HTTP prompt's real LLM cost → end-to-end chat→cost_ledger→dashboard flow CONFIRMED. |
| 24 | /auth/dev | 🟢 達標 | dev-login works (the audit's login entry); mockup-faithful identity/tenant/role selectors + Continue → authenticated session. |

## 5. Cross-cutting findings (accumulating)

- **CC-1 STALE BACKEND (environment, highest-impact on this audit)** — the running backend (PID 15056, started by a parallel Claude session) predates the 57.84-87 routers. Confirmed: `POST /tenants/register`, `POST /auth/password-login`, `GET /invites/{token}` all → 404 while the code is correct (`main.py:352` etc.). So **all 57.84-87 endpoint verifications are INVALID this pass** (register/invite/password-login/billing-outbox). Their FRONTEND + error-UX are real and correct; their e2e is unverifiable until the backend is restarted on current code. This is Risk Class E + the two-sessions-one-worktree hazard flagged in 57.87 carryover.
- **CC-2 Honest fixture labelling is the NORM, with ONE exception** — 11 of 15 full-impl pages (cost/overview/loop-debug/state-inspector/governance/verification/redaction/error-policy/sla + memory/subagents/admin-tenants real) clearly label fixture/demo widgets with `⚠️ ...pending Phase 58+ AD-...`. **`/orchestrator` is the lone unlabeled Potemkin** (zero API, hardcoded values, dead Deploy, no note).
- **CC-3 Real backend genuinely wired on core surfaces** — subagents (agent_catalog), memory (matrix+ops), governance (approvals), verification (REAL B-8 judge log), admin-tenants (list+stats), cost-dashboard (REAL cost_ledger incl. `_verification`), and **chat-v2 main flow** (gpt-5.2 loop → answer render → verification → trace). The platform's spine is real, not Potemkin.
- **CC-4 RBAC role not effective** — `AD-RBAC-DB-To-JWT-Wiring`: dev-login selected `admin` but every page shows role=`user`; admin-only content (cost provider-mix) not gated. Cosmetic role, not enforced.

## 6. Issue list for next sprints

| # | Severity | Issue | Where |
|---|----------|-------|-------|
| ISSUE-1 | 🔴 真 bug | `GET /admin/tenants/{tid}/sla-report?month=2026-06 → HTTP 500` (real wiring, backend 500s) → SLA dashboard "Failed to load data" | /sla-dashboard, `slaService.ts:16` |
| ISSUE-2 | 🔴 Potemkin | /orchestrator: zero data API, hardcoded form values, dead "Deploy" button, NO fixture note. Either wire backend OR add a fixture/DEMO label. | /orchestrator |
| ISSUE-3 | 🟠 env | Stale backend (PID 15056) → 57.84-87 endpoints 404. **Restart backend on current code, then re-drive register/invite/password-login/billing.** Use separate git worktree per session to avoid recurrence. | global / CC-1 |
| ISSUE-4 | 🟡 AP-4 | Overview top-4 KPI cards (14 loops / $2,847 MTD / …) are unlabeled fixture ($2,847 contradicts real $0.034). Add a fixture note (the 5 widgets below already have one). | /overview |
| ISSUE-5 | 🟡 wiring | chat-v2 Inspector Turn metadata (tokens.in=0/out=—/cost=—/trace_id=—) not wired despite loop events carrying values. | /chat-v2 Inspector |
| ISSUE-6 | 🟡 RBAC | dev-login role not authz-effective (admin→user); admin-only UI not gated. | global, `AD-RBAC-DB-To-JWT-Wiring` |
| ISSUE-7 | 🟢 minor | admin-tenants list-header "48 active · 3 anomalies" is a fixture string vs real KPI "Active tenants 0". | /admin-tenants |

## 7. Verdict tally (27 routes + 8 auth = 35 pages)

- 🟢 達標 (real, renders): 8 — subagents, memory, verification, admin-tenants, tenant-settings, chat-v2⭐, auth/login, auth/callback, auth/dev (9 incl. dev)
- 🟡 混合 (real core + labelled fixture, OR frontend-OK/backend-stale): cost-dashboard, overview, loop-debug, state-inspector, governance, error-policy, redaction, auth/register, auth/password-login, auth/invite, auth/expired
- 🔵 stub (honest ComingSoon): 12 proposed + auth/mfa = 13
- 🔴 problems: /orchestrator (Potemkin) + /sla-dashboard (HTTP 500) = 2

**Headline**: the spine is real (chat-v2 main-flow drive-through PASSES end-to-end with real gpt-5.2 + verification + trace + cost_ledger). Most "incomplete" surfaces honestly label their fixtures. Only **2 genuine page problems** (orchestrator Potemkin, sla-report 500) + **1 environment blocker** (stale backend hiding 57.84-87 e2e). Re-run register/invite/password-login after a clean backend restart.

---

## 8. Re-verification after clean backend restart (2026-06-07)

User authorized a backend restart to re-verify the 57.84-87 endpoints that CC-1 (stale backend) had blocked.

**Root cause confirmed = stale backend (Risk Class E), NOT code bugs.** The running backend was a `uvicorn --reload` listener (PID 36620) + 2 orphaned `multiprocessing.spawn` reload-worker children (34108, 13212). `dev.py stop` only kills the listener PID, leaving worker children that kept serving a half-stale module set (new `tenants.py` router → register went 404→401, but old `tenant_context.py` → register not yet in EXEMPT). Fix: killed all 3 + confirmed port 8000 free + clean `dev.py start`.

**Re-verification results (all PASS on clean backend):**

| Endpoint | stale backend | clean backend | Verdict |
|----------|---------------|---------------|---------|
| `POST /tenants/register` (57.87) | 404 → 401 | empty→**422**; full wizard→**201 Created** + redirect /auth/callback; same slug→**409** "workspace URL already taken" | ✅ e2e works; tenant written to DB; slug-unique enforced |
| `POST /auth/password-login` (57.86) | 404 | empty→**422**; bad creds→**401 "Invalid credentials"** (generic, anti-enumeration) | ✅ EXEMPT + logic correct (full success needs a seeded password account) |
| `GET /invites/{token}` (57.85) | 404 | fake token→**404 invalid** (frontend "This invite link is invalid") | ✅ EXEMPT + logic correct (full accept needs a real token) |

**Net**: `AD-DriveThrough-Phase58-Endpoints-Reverify` **RESOLVED** — 57.84-87 backends are real and correct; the earlier 404/401 were 100% stale-process artifacts. CC-1 downgraded from "blocker" to "confirmed Risk Class E, resolved by clean restart". This also vindicates 57.87's drive-through-deferred claim: register really does work end-to-end.

**NEW minor finding** — `AD-Register-Concurrent-Slug-Race`: the wizard submit fired `POST /tenants/register` twice (React StrictMode dev double-invoke), both returned 201 → likely 2 `drivethrough-audit` tenants created (slug pre-check is not atomic under concurrency; the serialized path correctly 409s). Add a DB unique constraint on slug OR an idempotency guard. Dev-mode/edge severity.
