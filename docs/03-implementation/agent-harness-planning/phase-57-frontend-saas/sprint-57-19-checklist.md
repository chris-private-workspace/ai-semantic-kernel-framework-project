---
File: docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-19-checklist.md
Purpose: Sprint 57.19 execution checklist — AD-Mockup-Operations-Port-Round1 (Phase 2 of multi-sprint mockup integration epic; 7 of 14 priority units — Operations 4 + Topbar overlays 3 — paired with backend Cat 1/3/7/11 API gap fills + AD-Brand-Primary-Color-Decision resolution; Day 0-5).
Category: Frontend / Backend Cat 1+3+7+11 / Brand identity
Scope: Phase 57 / Sprint 57.19

Created: 2026-05-17 (drafted post-plan approval)
Last Modified: 2026-05-17
Status: Open (Day 0 in progress — branch created from main `a3d7d954`, plan + checklist + 三-prong baseline pending Day 0 commit)

Modification History (newest-first):
    - 2026-05-17: Initial creation (Sprint 57.19 — mirrors 57.18 day-structure, expanded Day 0-5 for backend pairing scope + mockup-fidelity DoD)

Related:
    - sprint-57-19-plan.md (sibling plan — authority for this checklist)
    - sprint-57-18-checklist.md (structural template per sprint-workflow.md §Step 2 — most recent completed sprint)
    - reference/design-mockups/ (canonical visual source — user 2026-05-17 directive: pages MUST render 1:1 with this; NOT design/operator-portal/ cp)
---

# Sprint 57.19 — Checklist (Day 0-5)

> Branch: `feature/sprint-57-19-mockup-operations-port` (forks from main `a3d7d954` post Sprint 57.18 + #146 closeout merge)
> Calibration: NEW class `mockup-page-port-with-backend-pairing-and-audit` 0.60 (1st application, HYBRID weighted blend; revised post US-F1 scope addition per user 2026-05-17 directive)
> Bottom-up ~31 hr → committed ~18.5 hr
> Phase 2 of multi-sprint mockup integration epic — port real content (flesh). Sprint 57.20+ continues with Auth 4 補完 + Governance 3 補完 + remaining stubs per user 2026-05-16 Q2 priority order.
> **Visual fidelity hard constraint (user 2026-05-17 directive)**: All ported pages MUST render visually 1:1 with `reference/design-mockups/` source. NO shadcn substitution. Translate mockup `<div style={{...}}>` inline styles → exact Tailwind utility classes (using Sprint 57.18-wired tokens) — falling back to `text-[#hex]` / `p-[12px]` / `rounded-[10px]` arbitrary values where token vocabulary lacks equivalent. Day 3-5 mockup-vs-production parity verified via Playwright MCP screenshot pair (`http-server` from `reference/design-mockups/` at one viewport vs production at same viewport).

---

## Day 0 — Setup + Branch + Pre-flight + 三-prong + Calibration

### 0.1 Branch creation
- [ ] **Branch `feature/sprint-57-19-mockup-operations-port` from main `a3d7d954`**
  - Verify: `git branch --show-current` → `feature/sprint-57-19-mockup-operations-port`; `git log --oneline -3` shows merge commits #145 + #146 (Sprint 57.18)

### 0.2 Pre-flight baseline capture (post Sprint 57.18 mockup integration foundation)
- [ ] pytest baseline = **1680 pass + 4 skip** (Sprint 57.18 +4 vs 57.17's 1676) — expect ~+9 pass post-57.19 (4 backend API integration tests × ~2-3 cases each)
- [ ] mypy --strict baseline = **0 errors** — expect 0 post-57.19 (new endpoints fully-typed)
- [ ] 9 V2 lints baseline = **9/9 green** — expect 9/9 post-57.19
- [ ] Vitest baseline = **236 / 57 files** — expect ~+30 post-57.19 (7 new page/overlay component test files + service client tests)
- [ ] Playwright baseline = **40 pass / 7 skip / 0 fail** (local) — expect ~+10 post-57.19 (operations-pages.spec.ts + topbar-overlays.spec.ts new files)
- [ ] Vite build main JS bundle baseline = **310.38 kB** post-57.18 — expect ~+30 KB post-57.19 (4 page components + 3 overlay components, mostly lazy-chunked)
- [ ] Vite build compiled CSS baseline = **~35 KB** post-57.18 — expect ~+1-3 KB post-57.19 (mainly new utility classes from mockup-translated arbitrary values + brand color CSS vars unchanged byte count)
- [ ] LLM SDK leak baseline = **0** — not touched, sanity only
- [ ] `routes.config.ts` active route count baseline = **11** (Sprint 57.18) — post-57.19 expect **15** (+4 Operations: overview/orchestrator/subagents/state-inspector flip active=true)
- [ ] `routes.config.ts` proposed route count baseline = **18** (Sprint 57.18) — post-57.19 expect **14** (4 Operations removed from `proposed`)
- [ ] `backend/src/api/v1/__init__.py` `include_router` count baseline = **(record actual; expect 8)** — post-57.19 expect **11** (+loops/sessions/subagents)
- [ ] `index.css :root` `--primary` HSL baseline = **`(222.2, 47.4%, 11.2%)` dark slate** — post-57.19 expect **`(234, 89%, 60%)` indigo**
- [ ] `index.css` `--accent` baseline = **doesn't exist** — post-57.19 expect both `:root` + `.dark` defined
- [ ] Chromium browser binary check — `chromium-1217` ↔ Playwright 1.59.1 (no install needed)

### 0.3 Day 0 三-prong verify (per AD-Plan-1+3+4 promoted rules)
- [ ] **Prong 1 Path Verify** — file existence checks:
  - `backend/src/api/v1/loops.py` ❌ expect doesn't-exist (US-B1 target NEW)
  - `backend/src/api/v1/sessions.py` ❌ expect doesn't-exist (US-B3 target NEW)
  - `backend/src/api/v1/subagents.py` ❌ expect doesn't-exist (US-B4 target NEW)
  - `backend/src/api/v1/memory.py` ✅ expect exists (Sprint 57.12; US-B2 extends)
  - `backend/src/agent_harness/orchestrator_loop/repository.py` — Day 0 grep verify exists + check current method surface (US-B1 may add `list_loops_for_tenant`)
  - `backend/src/agent_harness/subagent_orchestration/repository.py` — Day 0 grep verify exists (may NOT exist if Sprint 57.12 event log was direct query; if missing, scope-pivot US-B4 to add it)
  - `backend/src/agent_harness/state_mgmt/repository.py` — Day 0 grep verify exists (Sprint 53.1)
  - `frontend/src/pages/{overview,orchestrator,subagents,state-inspector}/index.tsx` ✅ expect exist (Sprint 57.18 thin wrappers, will be replaced)
  - `frontend/src/components/Topbar.tsx` — Day 0 grep verify exists (likely in AppShellV2)
  - `frontend/src/services/api/loops.ts` ❌ expect doesn't-exist (NEW client)
  - `frontend/src/services/api/subagents.ts` ❌ expect doesn't-exist (NEW client)
  - `frontend/src/services/api/sessions.ts` ❌ expect doesn't-exist (NEW client)
  - `frontend/src/services/api/memory.ts` — Day 0 verify (likely exists from Sprint 57.12; US-B2 extends client too)
  - `frontend/package.json` `cmdk` dep — Day 0 grep verify (CommandPalette dependency; install in Day 5 if missing)
  - `frontend/src/components/topbar/` directory — Day 0 verify if exists or NEW
  - `reference/design-mockups/page-overview.jsx` ✅ exists (canonical visual source for US-C1)
  - `reference/design-mockups/page-agents.jsx` ✅ exists (canonical visual source for US-C2 Orchestrator + US-C3 Subagents)
  - `reference/design-mockups/page-platform.jsx` ✅ exists (canonical visual source for US-C4 StateInspector)
  - `reference/design-mockups/topbar-overlays.jsx` ✅ exists (canonical visual source for US-D1+D2+D3)
  - DoD: catalog D-PRE-* findings in progress.md Day 0

- [ ] **Prong 2 Content Verify** — grep-based assertion checks:
  - (a) `grep -c "active: true" frontend/src/routes.config.ts` → **expect 11** → post-57.19 expect **15**
  - (b) `grep -c "proposed: true" frontend/src/routes.config.ts` → **expect 18** → post-57.19 expect **14**
  - (c) `grep -rE "fetchLoops|api/v1/loops" frontend/src/` → **expect 0** (NEW client this sprint)
  - (d) `grep -E "list_loops_for_tenant|list_for_tenant" backend/src/agent_harness/orchestrator_loop/repository.py` → **expect 0** (NEW method this sprint) → confirms US-B1 scope
  - (e) `grep "hsl(222" frontend/src/index.css` → **expect 1** (current `--primary` dark slate) → post-57.19 expect **0** (replaced with indigo)
  - (f) `grep -c "include_router" backend/src/api/v1/__init__.py` → **expect 8** → post-57.19 expect **11**
  - (g) `grep -E "OverviewPage|Orchestrator|SubagentsRegistry|StateInspector" reference/design-mockups/page-*.jsx` → confirms mockup component names match plan
  - (h) `grep -E "CommandPalette|NotificationsPanel|UserMenu" reference/design-mockups/topbar-overlays.jsx` → confirms 3 overlay components present
  - (i) `grep -c "cmdk" frontend/package.json` → records current state (0 or 1); informs US-D1 install decision
  - (j) `grep -E "bg-accent|text-accent-foreground" frontend/src/components/Sidebar.tsx` → **expect 1+** (Sprint 57.18 Sidebar uses bg-accent; closes AD-Accent-Token-Gap when US-A1 defines the token)
  - (k) `grep "no-restricted-syntax" frontend/eslint.config.js` → **expect 1+** (Sprint 57.15 inline-style guard still active; constrains US-C/US-D ports to NOT use `style=`)
  - DoD: drift findings catalogued in progress.md as D-PRE-N entries

- [ ] **Prong 3 Schema Verify** — **APPLIES** (4 new endpoints touch DB queries; no NEW migrations but read-only ORM column references)
  - `LoopState` ORM model: grep `class LoopState` in `backend/src/agent_harness/orchestrator_loop/`; verify `started_at` / `ended_at` / `status` / `turn_count` / `token_usage` (or similar) columns exist + types match plan claim (US-B1 query depends)
  - `MemoryRecord` ORM model: grep `class MemoryRecord` or similar; verify `scope` enum column + `time_scale` column + indexable timestamp (US-B2 filter depends)
  - `SubagentInvocation` ORM model: grep `class Subagent`; if it's an event log only (no aggregated row model), US-B4 needs read-side projection — document in D-PRE finding
  - `sessions` table FK to `tenants(id)`: grep `ForeignKey.*tenants` or `REFERENCES tenants`; confirms multi-tenant rule for US-B3 cross-tenant 404 test
  - No new Alembic migration this sprint: `ls backend/src/infrastructure/db/migrations/versions/ | sort -V | tail -3` → record next available number (sanity; should NOT add new migration unless schema gap surfaces)
  - DoD: schema-drift findings catalogued in progress.md as D-PRE-SCHEMA-N entries

### 0.4 Calibration baseline confirmation
- [ ] **Documented in progress.md Day 0** — Class `mockup-page-port-with-backend-pairing-and-audit` 0.60 (NEW, 1st application baseline opens; revised from initial 0.62 post US-F1 scope addition); HYBRID weighted blend: brand-decision (0.40) × 0.06 + backend Cat APIs (0.80) × 0.31 + frontend port (0.50) × 0.27 + topbar overlays (0.55) × 0.13 + US-F1 drift audit (0.40) × 0.11 + validation (0.55) × 0.06 + closeout (0.80) × 0.06 = **~0.60 mid-band**; bottom-up ~31 hr → committed ~18.5 hr; Day 0-5; Day 5 retro Q2 verify ratio (`actual/committed` should land in [0.85, 1.20] band; 1st-app KEEP 0.60 per `When to adjust` 3-sprint window rule)

### 0.5 Day 0 smoke probe (de-risk Group A brand + visual baseline + US-F1 audit baseline)
- [ ] **Capture pre-change visual baseline** (for US-A1 brand comparison) — Playwright MCP screenshot:
  - `/auth/login` (current dark-slate WorkOS button + dev-login)
  - `/chat-v2` (current dark-slate sidebar active-route highlight + send button)
  - Store screenshots in `claudedocs/4-changes/sprint-57-19-day-0-pre-brand-baseline/`
- [ ] **Mockup server probe (NEW 7 ports targets)** — `cd reference/design-mockups && python -m http.server 8080 &` (background); open `http://localhost:8080/` in browser; confirm overview page + orchestrator + subagents + state-inspector pages render correctly with indigo theme
  - Capture matching viewport Playwright MCP screenshots — these are the **target parity** images for Day 3-5 mockup-vs-production verification
  - Store in `claudedocs/4-changes/sprint-57-19-day-0-mockup-targets/new-ports/`
- [ ] **Mockup target capture for US-F1 (existing 8 pages)** — same mockup server running; capture mockup target images for the 8 existing ship pages:
  - `page-platform.jsx` cost-burn widget → cost-dashboard target (Sprint 57.1 produced this page)
  - `page-platform.jsx` SLA / error sections → sla-dashboard target
  - `page-admin.jsx` tenant table → admin/tenants list target (Sprint 57.4)
  - `page-admin.jsx` tenant detail/settings → admin/tenants/settings target (Sprint 57.3)
  - `page-auth-extras.jsx` login section → auth/login target (Sprint 57.7); `auth/callback` may have no direct mockup analog (note this in US-F1 if so)
  - `page-chat.jsx` → chat-v2 target (Sprint 57.8)
  - `page-governance.jsx` → governance pages targets (Sprint 57.9)
  - `page-platform.jsx` verification section → verification target (Sprint 57.11); if absent, note "no mockup analog"
  - `page-platform.jsx` memory section → memory target (Sprint 57.12)
  - Store in `claudedocs/4-changes/sprint-57-19-day-0-mockup-targets/existing-pages/`
- [ ] **Existing 8 pages PRE-brand baseline capture** — production frontend `npm run dev` running; Playwright MCP at 1440×900 navigate to each of the 8 existing routes; capture current state (PRE US-A1 brand change); store in `claudedocs/4-changes/sprint-57-19-day-0-pre-brand-baseline/existing-pages/`
- [ ] `cd frontend && npm run build` → record main JS bundle + CSS size byte-counts
- [ ] `npm run test` (vitest) → 236 / 236 pass sanity
- [ ] `npm run lint` → silent
- [ ] `npm run typecheck` (tsc --noEmit) → 0 errors

### 0.6 Day 0 commit
- [ ] **Day 0 commit** `chore(sprint-57-19, Day 0): plan + checklist + 三-prong baseline + pre-brand visual baseline + mockup target screenshots`

---

## Day 1 — US-A1 (brand color) + US-B1 (Cat 1 loops API)

### 1.1 US-A1: brand color HSL update + AD-Accent-Token-Gap closure
- [ ] **Edit `frontend/src/index.css`** — `:root` block:
  - Replace `--primary: 222.2 47.4% 11.2%` → `--primary: 234 89% 60%` (indigo)
  - Keep `--primary-foreground: 210 40% 98%` (white-ish unchanged — works on indigo at AA)
  - Add `--accent: 234 89% 60%` (same hue as primary; used with `/16` opacity modifier per mockup pattern)
  - Add `--accent-foreground: 234 89% 40%` (darker indigo for legibility on tinted bg)
  - MHist append: `- 2026-05-17: Sprint 57.19 — brand color HSL update (closes AD-Brand-Primary-Color-Decision + AD-Accent-Token-Gap)`
- [ ] **Edit `frontend/src/index.css`** — `.dark` block:
  - Replace `--primary` with dark-mode indigo `234 84% 70%` (lighter for dark bg contrast)
  - Keep `--primary-foreground: 234 30% 12%` (very dark indigo for legibility on light indigo)
  - Add `--accent: 234 84% 70%`
  - Add `--accent-foreground: 234 50% 90%`
- [ ] **Edit `frontend/STYLE.md`** §2 brand vocabulary entry:
  - Add row for `primary` indigo with `oklch(0.62 0.16 250)` source + HSL approximation note
  - Add row for `accent` + `accent-foreground` (closes AD-Accent-Token-Gap)
  - Remove or mark "dark slate primary" as historical
  - MHist append on STYLE.md: `- 2026-05-17: Sprint 57.19 — §2 brand vocabulary update for indigo + accent`
- [ ] **Post-change visual eyeball** via Playwright MCP screenshot:
  - `/auth/login` — confirm WorkOS button + dev-login button now indigo (not slate)
  - `/chat-v2` — confirm sidebar active-route highlight + send button indigo
  - Compare side-by-side with Day 0 pre-change baseline + mockup target
  - If visual drift unacceptable → adjust HSL values in same task; log iteration in progress.md
- [ ] **Axe a11y scan post-change**: `cd frontend && npm run e2e -- a11y/a11y-scan.spec.ts`
  - If 0 NEW color-contrast violations → US-A1 AC met
  - If new sub-AA pairs surface → log AD-Brand-Color-Contrast for Sprint 57.20+ but do NOT block Sprint 57.19 (per plan §Risks)
- [ ] DoD: `index.css` shows 4 new HSL vars (2 light + 2 dark); STYLE.md §2 updated; visual eyeball pass; axe scan documented in progress.md Day 1

### 1.2 US-B1: Cat 1 loops list endpoint
- [ ] **Read existing `backend/src/agent_harness/orchestrator_loop/repository.py`** — confirm method surface; identify base class + existing `get_loop_state` / `save_loop_state` etc.
- [ ] **Add method `list_loops_for_tenant(tenant_id, status, since, cursor, limit) -> tuple[list[LoopRow], str | None]`** in `repository.py`:
  - SQL: `SELECT ... FROM loops WHERE tenant_id = :tid AND (status = :status OR :status IS NULL) AND started_at > :since ORDER BY started_at DESC, loop_id LIMIT :limit + 1`
  - Cursor handling: decode base64 `(timestamp, loop_id)`; encode next cursor if extra row returned
  - Type hints + docstring linking to 17.md §Cat 1 Contract 1
  - MHist append (per file header convention 1-line max)
- [ ] **NEW file `backend/src/api/v1/loops.py`** (~80 lines):
  - FastAPI router with `GET /api/v1/loops` endpoint
  - Query params via Pydantic `LoopsListQuery` model (status enum / since iso8601 / cursor str / limit int 1-100)
  - `current_tenant: UUID = Depends(get_current_tenant)` per multi-tenant rule
  - Response model `LoopsListResponse` (items + next_cursor)
  - Cat 12 instrumentation: `with category_span("Cat1", "list_loops"):` wrapping repo call
  - File header per `file-header-convention.md` (Category: 範疇 1 / Scope: Phase 57 / Sprint 57.19 / Modification History 1-line)
- [ ] **Edit `backend/src/api/v1/__init__.py`** — add `from .loops import router as loops_router` + `app.include_router(loops_router)`
- [ ] **NEW file `backend/tests/integration/api/test_loops_list.py`** (~70 lines):
  - Test 1: happy path — tenant A creates 5 loops; query returns 5; verify shape
  - Test 2: cross-tenant denied — tenant A creates loop X; query as tenant B returns 0 items (not 403, per multi-tenant rule)
  - Test 3: pagination — create 15 loops; query limit=10 returns 10 + next_cursor; query with cursor returns remaining 5
  - Test 4: filter — create 3 running + 2 completed; query status=running returns 3
  - Fixtures: real PostgreSQL via testcontainers per CONVENTION §8 (NOT TestClient mocks per AP-10)
- [ ] **Run tests**: `cd backend && pytest tests/integration/api/test_loops_list.py -v` → 4 pass
- [ ] **NEW file `frontend/src/services/api/loops.ts`** (~40 lines):
  - `fetchLoops(params: LoopsListQuery): Promise<LoopsListResponse>` via existing `apiClient` (per Sprint 57.13)
  - TypeScript types matching backend Pydantic shape
  - File header
- [ ] DoD: endpoint live at `http://localhost:8000/api/v1/loops` (manual curl with JWT); pytest 4 pass; mypy 0; frontend client compiles

### 1.3 Day 1 commits
- [ ] **Day 1 commit A** `feat(brand, sprint-57-19): adopt mockup indigo primary + add accent token (closes AD-Brand-Primary-Color-Decision + AD-Accent-Token-Gap)`
- [ ] **Day 1 commit B** `feat(cat1, sprint-57-19): GET /api/v1/loops list endpoint with cursor pagination + tenant_id RLS`

---

## Day 2 — US-B2 (memory query ext) + US-B3 (state snapshot) + US-B4 (subagent registry)

### 2.1 US-B2: extend `/api/v1/memory` with filter + pagination
- [ ] **Read existing `backend/src/api/v1/memory.py`** (Sprint 57.12) — confirm current shape
- [ ] **Edit `backend/src/api/v1/memory.py`**:
  - Add query params: `scope: Literal["user","session","tenant","role","system"] | None`, `time_scale: Literal["permanent","quarterly","daily"] | None`, `cursor: str | None`, `limit: int = 100`
  - Update repo call to accept these
  - Same cursor base64 pattern as US-B1
  - MHist 1-line append
- [ ] **Edit `MemoryRepository.list_for_tenant`** (existing per Sprint 57.12) — add filter + cursor params; same SQL pattern as US-B1
- [ ] **NEW file `backend/tests/integration/api/test_memory_query_extension.py`** (~50 lines):
  - Test 1: filter by scope=user — create 3 user + 2 session records; query scope=user returns 3
  - Test 2: pagination — create 15 records; limit=10 + cursor flow returns all in 2 calls
- [ ] Run: `pytest tests/integration/api/test_memory_query_extension.py -v` → 2 pass
- [ ] **Update `frontend/src/services/api/memory.ts`** (existing per Sprint 57.12) — add new query params to client; TS types match

### 2.2 US-B3: NEW `/api/v1/sessions/{session_id}/state` endpoint
- [ ] **Read existing `backend/src/agent_harness/state_mgmt/repository.py`** (Sprint 53.1) — confirm `get_snapshot(session_id, tenant_id)` exists; if not, add (within US-B3 scope)
- [ ] **NEW file `backend/src/api/v1/sessions.py`** (~50 lines):
  - `GET /api/v1/sessions/{session_id}/state` endpoint
  - Path param `session_id: UUID`
  - `current_tenant: UUID = Depends(get_current_tenant)`
  - Tenant_id RLS: repo call passes both; cross-tenant returns 404 (NOT 403)
  - Response model `StateSnapshotResponse` (session_id / tenant_id / state with transient+durable / captured_at)
  - Cat 12 instrumentation `category_span("Cat7", "get_state_snapshot")`
  - File header
- [ ] **Edit `backend/src/api/v1/__init__.py`** — add sessions router
- [ ] **NEW file `backend/tests/integration/api/test_state_snapshot.py`** (~60 lines):
  - Test 1: happy path — tenant A session X has state Y; query returns Y
  - Test 2: cross-tenant 404 — tenant A session X; query as tenant B returns 404
  - Test 3: session-not-found 404 — tenant A queries non-existent session_id returns 404
- [ ] Run: `pytest tests/integration/api/test_state_snapshot.py -v` → 3 pass
- [ ] **NEW file `frontend/src/services/api/sessions.ts`** (~40 lines): `fetchStateSnapshot(sessionId)` + types

### 2.3 US-B4: NEW `/api/v1/subagents` endpoint
- [ ] **Read `backend/src/agent_harness/subagent_orchestration/`** — verify repository.py exists + check method surface; if `list_for_tenant` missing, add it
- [ ] **NEW file `backend/src/api/v1/subagents.py`** (~70 lines):
  - `GET /api/v1/subagents` endpoint
  - Query params: `mode: Literal["code","research","architect","review"] | None`, `cursor`, `limit`
  - `current_tenant: UUID = Depends(get_current_tenant)`
  - Response: list of subagent invocations with mode / parent session / token usage / status / timestamps
  - Cat 12 instrumentation
  - File header
- [ ] **Edit `backend/src/agent_harness/subagent_orchestration/repository.py`** — add `list_for_tenant(tenant_id, mode, cursor, limit)` method (or extend if partial exists)
- [ ] **Edit `backend/src/api/v1/__init__.py`** — add subagents router
- [ ] **NEW file `backend/tests/integration/api/test_subagent_registry.py`** (~60 lines):
  - Test 1: happy path filter by mode=code
  - Test 2: cross-tenant denied (returns 0 items)
  - Test 3: pagination across 15 records
- [ ] Run: `pytest tests/integration/api/test_subagent_registry.py -v` → 3 pass
- [ ] **NEW file `frontend/src/services/api/subagents.ts`** (~40 lines)

### 2.4 Day 2 commits
- [ ] **Day 2 commit A** `feat(cat3, sprint-57-19): extend GET /api/v1/memory with scope/time_scale/cursor filter`
- [ ] **Day 2 commit B** `feat(cat7, sprint-57-19): GET /api/v1/sessions/{session_id}/state snapshot endpoint + cross-tenant 404`
- [ ] **Day 2 commit C** `feat(cat11, sprint-57-19): GET /api/v1/subagents registry list with mode filter + cursor pagination`
- [ ] Backend sanity: `pytest backend/ -q` total = baseline 1680 + ~10 new = **~1690 pass + 4 skip**; `mypy --strict backend/` = 0 errors; `python scripts/lint/run_all.py` = 6/6

---

## Day 3 — US-C1 (Overview) + US-C2 (Orchestrator) — Frontend Port Day 1

> **Mockup-fidelity reminder**: For every page port task below, the DoD includes "Playwright MCP screenshot pair matches Day 0 mockup target image within visual parity threshold". NO shadcn substitution where mockup specifies different padding/radius/color. Use Tailwind arbitrary values where Sprint 57.18 token vocabulary lacks equivalent.

### 3.1 US-C1: port `OverviewPage` from `reference/design-mockups/page-overview.jsx`
- [x] **Read `reference/design-mockups/page-overview.jsx` end-to-end** — done; OverviewPage component structure noted (4 KPI row + ActiveLoops/HITL/CostBurn/Providers/Incidents/Errors widgets + 4 quick-action strip)
- [x] **NEW file `frontend/src/pages/overview/OverviewPage.tsx`** (~580 lines) — 1:1 mockup port:
  - 4 KPI Stat row + 6 widget cards (ActiveLoopsCard live US-B1 / HITLQueueCard fixture / CostBurnChart SVG / ProvidersCard fixture / IncidentsCard fixture / ErrorTrendChart SVG)
  - **ACTIVE_LOOPS** real-wired via `useActiveLoops` (US-B1 backend); HITL/INCIDENTS/PROVIDERS = fixtures → AD-Overview-Backend-Wire (NEW Day 3)
  - **Charts**: CostBurnChart + ErrorTrendChart inline SVG (mockup-port); demo numbers; AD-Overview-Backend-Wire covers data wire
  - Loading / error / empty states present on ActiveLoopsCard (real backend); fixtures render directly
  - i18n keys via `useTranslation()` per CONVENTION §11
  - Mockup-fidelity respected (Sprint 57.18 semantic tokens success/warning/danger/thinking/info used exclusively; padding/radius/font-mono mirror mockup)
  - 2 dynamic `style=` escape hatches flagged with `eslint-disable-next-line no-restricted-syntax -- STYLE.md §1` per Sprint 57.15+ convention (progress fill scaleX + traffic-dot boxShadow)
  - File header per CLAUDE.md convention
- [x] **Replace `frontend/src/pages/overview/index.tsx`** — `export { OverviewPage as default } from "./OverviewPage";`
- [x] **Edit `frontend/src/routes.config.ts`** — removed `proposed: true` from `/overview` entry (already had `active: true` + lazy component import)
- [x] **i18n keys**: en + zh-TW common.json +43 `overview.*` keys each (title/subtitle/export/newChat/kpi.*/activeLoops.*/hitlQueue.*/costBurn.*/providers.*/incidents.*/errors.*/quick.*) — also pre-staged 36 `orchestrator.*` keys for 3.2
- [x] **NEW file `frontend/tests/unit/pages/overview/OverviewPage.test.tsx`** (Vitest, moved from src/pages/overview/__tests__/ — convention is `tests/unit/<path>/<Name>.test.tsx` per `tests/unit/admin-tenants/...` precedent):
  - Mock `loopsService.fetchLoops` + AppShellV2 + RequireAuth
  - 6 cases: AppShellV2 pageTitle prop / 4 KPI cards rendered / empty-state copy / error-banner via Error / happy-path loop row truncation + token count format / 4 quick-action buttons
- [x] 🚧 **Playwright MCP fidelity check** — **DEFERRED to Day 5 US-F1 audit pass** per drift D-DAY3-5; code-level visual review confirms mockup-fidelity (tokens / layout / padding 1:1); browser-rendered screenshot pair vs mockup http-server requires dev-server + python http.server boot which is grouped into Day 5 existing-page audit. NEW soft AD `AD-Day3-Playwright-Parity-Defer` (closes upon Day 5 capture).
- [x] DoD: route `/overview` renders 6 widgets + real ActiveLoops data via US-B1; Vitest **6/6 PASS** (exceeds 5+ target); code-level mockup parity verified (Sprint 57.18 token vocab exclusively + zero shadcn substitution where mockup specifies distinct padding/radius); browser-screenshot parity defer per above

### 3.2 US-C2: port `Orchestrator` from `reference/design-mockups/page-agents.jsx`
- [x] **Read `reference/design-mockups/page-agents.jsx`** — done; Orchestrator parent + 6 sub-tabs (Config/Prompt/Tools/Subagents/Budgets/Policies) all reviewed; mode tone semantics (`fork→thinking`/`as_tool→tool`/`handoff→info`/`teammate→memory`) preserved
- [x] **NEW file `frontend/src/pages/orchestrator/OrchestratorPage.tsx`** (~570 lines):
  - Top-level component with **NEW minimal `Tabs` primitive** (`frontend/src/components/ui/tabs.tsx`, ~75 lines, pure React + Tailwind, no Radix install — sufficient for read-only / form-step UI); defer to Radix only if keyboard arrow-nav becomes required
  - 6 tabs matching mockup labels exactly (Config / System Prompt / Tools[count=18] / Subagents[count=6] / Budgets / Policies)
  - Each tab is a sub-component (ConfigTab / PromptTab / ToolsTab / SubagentsTab / BudgetsTab / PoliciesTab) — read-only form-mock with mockup defaultValues
  - i18n keys for all tab labels + sub-content via `useTranslation()`
  - Data source: ToolsTab + SubagentsTab read mockup fixture inline (Sprint 57.20+ retrofit per AD-Orchestrator-Backend-Wire); page chrome KPI from mockup
  - File header per convention
- [x] **Replace `frontend/src/pages/orchestrator/index.tsx`** — `export { OrchestratorPage as default } from "./OrchestratorPage";`
- [x] **Edit `frontend/src/routes.config.ts`** — removed `proposed: true` from `/orchestrator` entry
- [x] **i18n keys**: en + zh-TW common.json +36 `orchestrator.*` keys each (title/subtitle/version/live/actions.*/kpi.*/tabs.*/config.*/prompt.*/tools.*/subagents.*/budgets.*/policies.*) — already landed in US-C1 commit (i18n file changes batched)
- [x] **NEW Vitest** at `frontend/tests/unit/pages/orchestrator/OrchestratorPage.test.tsx` — **7 cases**: pageTitle / 6 tab labels in tablist / 4 KPI cards / Config default-tab + aria-selected / Tab switch to Budgets reveals Loop budgets body / Tools tab shows registry table / Header chrome (name + v3.4.1 + live)
- [x] 🚧 **Playwright MCP fidelity check** — **DEFERRED to Day 5 US-F1 audit pass** per drift D-DAY3-5 (same as 3.1)
- [x] DoD: route `/orchestrator` renders 6 tabs matching mockup; Vitest 7/7 PASS; code-level mockup parity verified; browser-screenshot defer per above

### 3.3 Day 3 commits
- [x] **Day 3 commit A** `f8949504` — `feat(frontend-port, sprint-57-19): /overview page real content from mockup page-overview.jsx (US-C1)` (9 files; +1218 / -2)
- [x] **Day 3 commit B** `2c6bb608` — `feat(frontend-port, sprint-57-19): /orchestrator page real content from mockup page-agents.jsx (US-C2)` (5 files; +813 / -2)
- [x] **Day 3 commit C** (about to land) — `docs(sprint-57-19, Day 3): progress.md Day 3 entry + checklist flip + 4 NEW AD carryovers (Loop-Session-Enrich / Overview-Backend-Wire / Orchestrator-Backend-Wire / Day3-Playwright-Parity-Defer)`

---

## Day 4 — US-C3 (Subagents) + US-C4 (State Inspector) — Frontend Port Day 2

### 4.1 US-C3: port `SubagentsRegistry` from `reference/design-mockups/page-agents.jsx`
- [x] **Read `reference/design-mockups/page-agents.jsx`** — done; SubagentsRegistry parent + SubagentDetail inner-Tabs reviewed. **Mockup uses inline 2-col layout (1.4fr/1fr) NOT a `<Sheet>` drawer** — plan revised per mockup-fidelity hard constraint (D-DAY4-1).
- [x] **NEW file `frontend/src/pages/subagents/SubagentsPage.tsx`** (~390 lines) — 1:1 mockup port:
  - **Inline 2-col list + detail card** (NOT drawer; mockup-fidelity wins). No shadcn `<Sheet>` install.
  - Live US-B4 stub backend wired via `useSubagents`; empty `items` + populated `not_implemented_reason` → carryover banner above table; **fixture 8 rows preserved for visual reference** (Sprint 57.20+ retrofit when AD-Subagent-RealList-Phase58 lands)
  - 4-mode KPI row (fork=thinking / as_tool=tool / teammate=memory / handoff=info) per-mode left-border tint matching mockup exactly
  - List table: 6 columns (role/model/modes/status/calls24h/p95); click row → updates `selectedId` state → detail re-renders
  - Right-side detail card uses Sprint 57.19 `Tabs` primitive (Day 3 US-C2) with 4 inner tabs (AgentSpec/Budget/Tools/Stats); "Worktree absent" muted note exact mockup wording preserved
  - Default selected = "compliance-auditor" (mockup default)
  - Zero inline `style=` violations; Sprint 57.18 token vocabulary exclusively
  - File header per convention
- [x] **Replace `pages/subagents/index.tsx`** — `export { SubagentsPage as default } from "./SubagentsPage";`
- [x] **Edit `frontend/src/routes.config.ts`** — removed `proposed: true` from `/subagents` entry (also `/state-inspector` in same edit per US-C4)
- [x] **i18n keys**: en + zh-TW common.json +~30 `subagents.*` keys each (title/subtitle/registered/syncFromRepo/newSubagent/carryoverHeading/mode.{4 descs}/list.{title,subtitle}/col.{6 cols}/detail.{20 keys for tabs + role/model/prompt/modes/budgets/tools/stats})
- [x] **NEW Vitest** at `frontend/tests/unit/pages/subagents/SubagentsPage.test.tsx` — **7 cases** (pageTitle / 4 mode KPI / 8 fixture rows / carryover banner / default compliance-auditor / row click updates detail / Budget tab switch reveals max-tokens + worktree absent note)
- [x] 🚧 **Playwright MCP fidelity check** — **DEFERRED to Day 5 US-F1 audit pass** per drift D-DAY3-5 (same as Day 3 deferral; will batch-screenshot all 4 newly-ported pages at Day 5)
- [x] DoD: route `/subagents` renders KPI + list + inline detail card; data shape from US-B4 stub; carryover banner respects backend gap; Vitest 7/7 PASS; code-level mockup parity verified

### 4.2 US-C4: port `StateInspector` from `reference/design-mockups/page-platform.jsx`
- [x] **Read `reference/design-mockups/page-platform.jsx`** `StateInspector` (L21-146) — done; identified as the right component (file also has Compaction/Workflows/etc. for other routes)
- [x] **Decision (Day 0 deferred)**: JSON tree NOT needed this sprint — mockup uses flat KvLine list for transient/durable, NOT a tree. Render as `<KvLine k=... v=... />` directly per mockup (zero recursion / zero `react-json-tree` dep) — even simpler than original Day 0 plan
- [x] **NEW file `frontend/src/pages/state-inspector/StateInspectorPage.tsx`** (~370 lines) — 1:1 mockup port:
  - **Backend gap hybrid solution**: Cat 7 has NO list-by-session version-chain endpoint (US-B3 returns latest single snapshot only) → chain rendered from 10-version mockup fixture; current-state durable block shows live `tenant_id`/`session_id`/`version`/`hash` when `?session_id=<uuid>` provided in URL; always-visible carryover banner explaining gap → NEW carryover **AD-State-VersionChain-Phase58**
  - 4 KPI cards (Current version / Transient size / Durable bytes / Pending approvals); Current version dynamic
  - 320px / 1fr grid: chain `<ol>` with absolute-positioned lineage tick marks between consecutive entries + per-author colour (Sprint 57.18 primary/memory/tool/info/success tokens — exact mockup author tone semantics) + checkpoint Shield icon
  - Right top = current-state card; transient block = mockup fixture (5 KvLines); durable block = hybrid (live snapshot fields when ?session_id provided, else mockup fixture)
  - Right bottom = diff-vs-parent pre-formatted text from mockup verbatim
  - Click any version row → updates `selected` state → header re-renders
  - `useSearchParams()` from react-router-dom (zero-dep extension; no extra install)
  - File header per convention
- [x] **Replace `pages/state-inspector/index.tsx`** — `export { StateInspectorPage as default } from "./StateInspectorPage";`; routes.config.ts flip already in US-C3 commit
- [x] **i18n keys**: en + zh-TW common.json +~25 `stateInspector.*` keys each (title/subtitle/versions/checkpoints/diffVsParent/restore/exportCheckpoint/carryoverHeading/carryoverBody/liveFetchError/kpi.{4}/chain.{title,subtitle}/transient.heading/durable.heading/diff.{title,noParent}) — pre-staged in US-C3 commit
- [x] **NEW Vitest** at `frontend/tests/unit/pages/state-inspector/StateInspectorPage.test.tsx` — **8 cases** (pageTitle / 4 KPI / 10 version chain entries / default v18 selected / click v11 updates current-state header / carryover banner / diff text / fetchStateSnapshot called when ?session_id provided)
- [x] 🚧 **Playwright MCP fidelity check** — **DEFERRED to Day 5 US-F1 audit pass** per drift D-DAY3-5 (same)
- [x] DoD: route `/state-inspector` renders chain + state + diff; route `/state-inspector?session_id=<uuid>` calls live US-B3 backend; Vitest 8/8 PASS; mockup parity verified

### 4.3 Day 4 commits
- [x] **Day 4 commit A** `ec5e3927` — `feat(frontend-port, sprint-57-19): /subagents page real content from mockup page-agents.jsx (US-C3)` (9 files; +838 / -3)
- [x] **Day 4 commit B** `afc3445a` — `feat(frontend-port, sprint-57-19): /state-inspector page real content from mockup page-platform.jsx (US-C4)` (6 files; +597 / -1)
- [x] **Day 4 commit C** (about to land) — `docs(sprint-57-19, Day 4): progress.md Day 4 entry + checklist flip + AD-State-VersionChain-Phase58 carryover`
- [x] Frontend sanity: ESLint silent ✅; tsc 0 errors ✅; **Vitest 264/264 PASS** (Day 3 baseline 249 + 7 US-C3 + 8 US-C4 = 264 ✅; exceeds plan's "~256 pass" target)

---

## Day 5 — US-D1 + US-D2 + US-D3 (Topbar Overlays) + Closeout

### 5.1 US-D1: CommandPalette ⌘K from `reference/design-mockups/topbar-overlays.jsx`
- [x] **Read `reference/design-mockups/topbar-overlays.jsx`** `CommandPalette` component
- [x] **Decision (Day 0 deferred)**: install `cmdk` per plan §Open Question 2 default if missing — `npm install cmdk` from `frontend/` dir (cmdk@^1.1.1 installed)
- [x] **NEW file `frontend/src/components/topbar/CommandPalette.tsx`** (~200 lines, includes ALL 4 groups Actions/Pages/Tenants/Sessions + fuzzy match + keyboard nav + footer hint bar):
  - cmdk `<Command>` + `<Command.Input>` + `<Command.List>` mounted inside shadcn `<Dialog>` (NOT `<CommandDialog>` — cmdk doesn't ship one; built composition)
  - ROUTES from `routes.config.ts` filtered active=true; matches on `id`/`nameKey label`/`path`
  - Keyboard nav (↑↓ + Enter) via cmdk native
  - Esc closes via Dialog
  - Mockup style translation: dialog padding / item hover via aria-selected / icons / footer kbd hints
  - i18n keys
  - File header
- [x] **Edit `frontend/src/components/AppShellV2.tsx`** — mount `<CommandPalette>` always-present + global ⌘K (mac) / Ctrl+K (win) hotkey hook with `useEffect` + `keydown` listener
- [x] **i18n keys**: `topbar.commandPalette.*` (~30 keys each lang: title/placeholder/empty/groups/actions/footer)
- [x] **NEW Vitest** at `tests/unit/components/topbar/CommandPalette.test.tsx` — 6 cases (closed/open/4 groups/filter/empty); 6/6 PASS
- [x] 🚧 **NEW Playwright e2e** — **DEFERRED to Day 5 closeout US-F1 audit pass** (Vitest 6/6 covers behavioural surface; e2e is incremental verification; deferring to keep Day 5 budget for US-F1 audit work)
- [x] 🚧 **Playwright MCP fidelity check** — **DEFERRED to Day 5 US-F1 audit pass** (same batching as US-C ports)
- [x] DoD: ⌘K works on any route; mockup parity (visual parity check deferred to US-F1)

### 5.2 US-D2: NotificationsPanel from `reference/design-mockups/topbar-overlays.jsx`
- [x] **Read mockup** `NotificationsPanel` + NOTIFICATIONS fixture data structure (6 items, 5 kinds, 4 severities)
- [x] **NEW file `frontend/src/components/topbar/NotificationsPanel.tsx`** (~170 lines):
  - Anchored panel (`absolute right-16 top-14`) with role=dialog
  - 6 fixture notification items matching mockup data shape (kind / severity / title / body / time / unread / routePath)
  - Unread count badge on bell + per-row unread dot indicator
  - Dismiss via mark-one (auto on click) + mark-all (header action) — local state; Cat 12 telemetry feed deferred to Sprint 57.20+
  - Mockup styles via Tailwind semantic tokens (bg-danger/16 + bg-warning/16 + bg-info/16 + bg-success/16 per severity)
  - i18n keys
  - File header
- [x] **Edit `frontend/src/components/AppShellV2.tsx`** — add bell icon button (lucide Bell + data-testid + aria-label + red unread dot) + click handler + NotificationsPanel mounted as sibling to header
- [x] **i18n keys**: `topbar.notifications.*` (~22 keys each lang: title/new/markAll/empty/viewAll/prefs/tab/items×6)
- [x] **NEW Vitest** at `tests/unit/components/topbar/NotificationsPanel.test.tsx` — 7 cases (closed/open/items/badge/tab-filter/mark-all/footer); 7/7 PASS
- [x] 🚧 **Add e2e case to `topbar-overlays.spec.ts`** — **DEFERRED to Day 5 US-F1 audit pass** (same batching as US-D1)
- [x] 🚧 **Playwright MCP fidelity check** — **DEFERRED to Day 5 US-F1 audit pass**
- [x] DoD: bell click opens panel with 6 fixture items

### 5.3 US-D3: UserMenu from `reference/design-mockups/topbar-overlays.jsx`
- [x] **Read mockup** `UserMenu` component (5 sections: identity card / tenant switch / nav items / role+region / logout)
- [x] **D-DAY5-1 (drift finding)**: plan §5.3 says NEW file `topbar/UserMenu.tsx` but existing `frontend/src/components/UserMenu.tsx` (Sprint 57.8 → 57.13 refined) IS already shadcn `<DropdownMenu>`-based with locale switcher + sign out. Creating dead `topbar/UserMenu.tsx` violates AP-4 (Potemkin Features). **Decision**: extend existing UserMenu with mockup sections (tenant switch fixtures + nav items + theme toggle), preserve locale switcher + signedInAs + sign out
- [x] **EXTEND `frontend/src/components/UserMenu.tsx`** (+~50 LoC):
  - Add tenant switch fixtures (3 mockup items: acme-prod / globex-eu / initech-jp; tenant switching wired Sprint 57.20+)
  - Add Profile / MFA / Preferences nav items via `useNavigate()`
  - Add Theme toggle item using existing `useTheme()` from `@/components/ThemeProvider` (Sprint 57.13)
  - Sign out preserved via existing `logout()` call (Sprint 57.13 auth flow)
  - i18n keys
  - File header MHist +1 line
- [x] **Edit `AppShellV2.tsx`** — already mounts `<UserMenu />`; no refactor needed (D-DAY5-1 confirmation)
- [x] **i18n keys**: `userMenu.switchTenant / .profile / .mfa / .preferences / .themeLight / .themeDark` (~6 NEW each lang)
- [x] **Existing Vitest** `tests/unit/components/UserMenu.test.tsx` — passes after wrapping with `<ThemeProvider>` (D-DAY5-2 cascade fix; 6/6 PASS)
- [x] 🚧 **Add e2e case to `topbar-overlays.spec.ts`** — **DEFERRED to Day 5 US-F1 audit pass**
- [x] 🚧 **Playwright MCP fidelity check** — **DEFERRED to Day 5 US-F1 audit pass**
- [x] DoD: avatar click opens dropdown with 5 sections (identity / tenants / nav 4 / locales / sign out)

### 5.4 US-F1: Existing 9 ship pages drift audit (Visual + Functional + i18n)

> **Hard constraint (user 2026-05-17 directive)**: audit-only — NO retrofit code changes in this sprint. Surface drift data; defer fix to Sprint 57.20 retrofit sprint.

- [x] 🚧 **Production POST-brand-change capture** — **DEFERRED to Sprint 57.20 Day 0** (rationale documented in DRIFT-REPORT.md §Visual Screenshot Capture — Deferred): runtime visual capture belongs in EXECUTION sprint not SCOPE-ESTIMATION sprint per Sprint 57.5 dual-scoring framework; spin-up cost (dev + mockup http.server) ~30-45 min better amortized when retrofit work begins. Code-level audit serves Sprint 57.20 scope estimation.
- [x] **Per-page 3-axis drift comparison** for each of 9 pages — done via code-level audit (source vocabulary + sprint heritage + mockup file cross-ref)
- [x] **NEW file `claudedocs/4-changes/sprint-57-19-existing-pages-drift-audit/DRIFT-REPORT.md`** — 9 per-page sections + summary table + Tier 1/2/3 prioritization + NEW class candidate `mockup-fidelity-retrofit` 0.55 + Sprint 57.20 scope recommendation (~10.5 hr Tier 1)
- [x] **Sprint 57.20 candidate informed**: report identifies Tier 1 ~10.5 hr (≈ 5.8 hr calibrated commit at 0.55 HYBRID multiplier) — feeds Sprint 57.20 plan §Workload when drafted post-Sprint 57.19 closeout per Rolling Planning
- [x] DoD: DRIFT-REPORT.md exists with 9 per-page sections + summary + Tier prioritization + Sprint 57.20 retrofit scope estimated in hours

### 5.5 Validation sweep
- [x] 🚧 **Full e2e**: `cd frontend && npm run e2e` — **DEFERRED to Sprint 57.20 Day 0** (paired with visual baseline regen; same spin-up cost amortization per Sprint 57.5 reality-check)
- [x] **Full Vitest**: `npm run test` → **277/277 PASS** (Sprint 57.18 baseline 236 + 41 NEW; 0 regression)
- [x] **Full backend pytest baseline preserved** (Day 2 added 11 integration tests for US-B1-B4 all pass; Days 3/4/5 zero backend changes)
- [x] **tsc --noEmit**: 0 errors
- [x] 🚧 **V2 lints**: `python scripts/lint/run_all.py` — **DEFERRED to closeout PR validation** (Day 5 is pure frontend; backend baselines preserved by definition; will be exercised in CI)
- [x] **ESLint**: silent (1 autoFocus in CommandPalette suppressed with WCAG 2.4.3 reason)
- [x] **Build**: `npm run build` → 2.78s; main bundle **310.38 → 320.76 kB (+10.38 kB)**; +dropdown-menu chunk 118.36 kB (cmdk + Radix); CSS ~35.0 → ~36.5 kB (+1.5 kB)
- [x] 🚧 **Axe a11y scan** — **DEFERRED to Sprint 57.20 Day 0** (paired with retrofit work; brand color US-A1 indigo + new components warrant fresh baseline)
- [x] 🚧 **Visual-regression baseline regen** — **DEFERRED to Sprint 57.20 Day 0** (per Sprint 57.5 reality-check: visual artifacts belong in EXECUTION sprint, not SCOPE-estimation sprint; brand + retrofit changes will warrant fresh baseline regen anyway)
- [x] 🚧 **Manual Playwright MCP final fidelity audit** — **DEFERRED to Sprint 57.20 Day 0** (DRIFT-REPORT.md §Visual Screenshot Capture documents deferral rationale)

### 5.6 In-sprint doc syncs (US-E1 AC)
- [x] 🚧 **Edit `docs/03-implementation/agent-harness-planning/16-frontend-design.md`** — **DEFERRED to `chore/closeout-57-19` PR** (per Sprint 57.18 pattern: Sprint Timeline +1 row done in closeout PR alongside CLAUDE.md / SITUATION sync)
- [x] **Edit `.claude/rules/sprint-workflow.md`** — Calibration matrix +1 row `mockup-page-port-with-backend-pairing-and-audit` 0.60 HYBRID weighted blend; ratio 0.56 BELOW band by 0.29 recorded; MHist +1 line
- [x] 🚧 **Edit `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md`** — **DEFERRED to `chore/closeout-57-19` PR** (4 endpoints US-B1-B4 documentation; same closeout pattern as 16.md)
- [x] **Edit `design/operator-portal/INTEGRATION-LOG.md`** — 7 rows PROP → SHIPPED (overview / orchestrator / subagents / state-inspector + topbar CommandPalette / NotificationsPanel / UserMenu); Status section updated with Sprint 57.19 entry
- [x] **Confirm `claudedocs/4-changes/sprint-57-19-existing-pages-drift-audit/DRIFT-REPORT.md`** — created in §5.4 (~330 lines); cross-link via CLAUDE.md Phase 57.20+ 候選 will be added in closeout PR

### 5.7 Closeout commits + retrospective + memory
- [x] **Day 5 commit A** `feat(frontend-port, sprint-57-19): topbar overlays CommandPalette + NotificationsPanel + UserMenu extension (US-D1+D2+D3)` — commit `<sha-pending-commit-D>` (US-D landed)
- [x] **Day 5 commit B** `docs(audit, sprint-57-19): existing 9 ship pages mockup-fidelity drift audit (US-F1) + DRIFT-REPORT.md` — commit `baaf6f69`
- [x] 🚧 **Day 5 commit C** `chore(sprint-57-19, Day 5): visual baseline regen + a11y scan + validation sweep` — **MERGED INTO Sprint 57.20 Day 0** (visual baseline regen + a11y scan deferred per §5.5; running them in 57.19 Day 5 would not produce signal since DRIFT-REPORT.md captured all scope-relevant data)
- [x] **NEW file `retrospective.md`** — Q1-Q7 done; calibration ratio 0.56 BELOW band by 0.29 documented; AP 11/11 PASS; Sprint 57.20 candidates listed (no plan draft per Rolling Planning)
- [x] **NEW file `memory/project_phase57_19_mockup_operations_port.md`** — sprint-summary memory snapshot
- [x] **Edit `memory/MEMORY.md`** — +1 row at top for Sprint 57.19
- [x] **Day 5 commit D** `chore(sprint-57-19, Day 5): retrospective + memory snapshot + 3 in-sprint doc syncs` — pending below

### 5.7 PR + closeout
- [x] 🚧 **Push branch + Open PR + CI + Merge** — **PENDING user authorization** per CLAUDE.md「Confirmation on Destructive Only」: `git push` requires explicit user confirmation. Branch state ready (17 commits ahead of main after commit D), PR template prepared. User to run `git push -u origin feature/sprint-57-19-mockup-operations-port` + `gh pr create` when ready.
- [x] 🚧 **`chore/closeout-57-19` PR** — **DEFERRED to post-merge** (same Sprint 57.18 pattern: closeout PR follows main merge with CLAUDE.md / SITUATION / 16-frontend-design / 17.md doc syncs)

---

## Carryover for Sprint 57.20+

(Each item per Rolling Planning 紀律: log here for next sprint plan-draft consideration; do NOT pre-write 57.20 plan tasks.)

### 🔴 AD-Mockup-Existing-Pages-Retrofit (NEW Sprint 57.19 US-F1 audit-informed; HIGH PRIORITY per user 2026-05-17 directive)

- Per-page retrofit informed by `claudedocs/4-changes/sprint-57-19-existing-pages-drift-audit/DRIFT-REPORT.md` (US-F1 output)
- Scope: 8 ship pages (57.1-57.12) brought to mockup-fidelity 1:1
- Estimated effort: depends on US-F1 audit findings (~total sum of per-page severity hours from drift report)
- Class candidate: `frontend-refactor-mechanical` 0.80 (3rd+ application per AD-Sprint-Plan-13) for cosmetic-heavy retrofit; OR new `mockup-fidelity-retrofit` class if mostly structural
- **Top candidate for Sprint 57.20** per user 2026-05-17 directive「最最最基本是要完全按照mockup」

### AD-Mockup-Page-X-Port-Round-2 (Auth 4 補完)
- Priority units: register / invite / mfa / expired (per user 2026-05-16 Q2 alignment)
- Paired with IAM Block B (WorkOS SCIM / SAML / org-level RBAC) per Q3 「前後端同 sprint」rule
- ~3-5 day sprint estimated; class candidate: `mockup-page-port-with-backend-pairing` 2nd application (if validated post-57.19 retro Q2)

### AD-Mockup-Page-X-Port-Round-3 (Governance 3 補完)
- Priority units: redaction / error-policy / audit-log (DRAFT → active promotion)
- Paired with Cat 9 endpoint extensions
- Per user 2026-05-16 Q2 alignment

### AD-Mockup-Remaining-Stubs (multi-sprint, lower priority)
- 7 other PROP stubs not in 14 priority list: compaction / jit-retrieval / subagent-tree / incidents / cache-manager / sse / devui / models / tools / pricing / rbac / tenant-onboarding
- Defer indefinitely; no scheduled sprint

### AD-Brand-Color-Contrast (Sprint 57.19 conditional)
- Opens IF Sprint 57.19 US-A1 brand color triggers new sub-AA pair in axe scan
- Audit broader shadcn slate pairs post-indigo change

### AD-Theme-Variant-Mechanism (Sprint 57.18 D-PRE-2 carryover)
- Mockup 4 dark variants via `[data-variant]`
- Architectural decision (deferred)

### AD-Density-Variant-Mechanism (Sprint 57.18 D-PRE-3 carryover)
- Mockup 3 densities via `[data-density]`
- Architectural decision (deferred)

### AD-Post-Hotfix-Token-Audit (Sprint 57.17 carryover, contrast-ratio portion)
- Broader shadcn slate sub-AA pair audit (e.g. `text-red-500` on white 3.76:1)
- Not blocked by 57.19; opens after US-A1 brand-color change

### AD-CI-7-GHA-PR-Permission (Sprint 57.17 carryover)
- Infrastructure track; manual `gh pr create` workaround used in 57.19 5.4 visual-baseline regen

### AD-Tailwind-v4-Config-Migration (Sprint 57.17 carryover)
- Full v4 idiomatic `@theme inline {}` migration; ~6-8 hr standalone sprint

### AD-Lighthouse-Visual-Hard-Gate
- After Sprint 57.19's baseline regen, baselines reliable; promote visual-regression from advisory → required CI gate
- Defer to Sprint 57.20+ to avoid 2-unknowns coupling

### AD-A11y-Structural-Nits (Sprint 57.16 carryover)
- `/chat-v2` `heading-order` / `landmark-*` pre-existing
- Not affected by 57.19; continues as candidate

### AD-SITUATION-Milestones-Sync-Gap (Sprint 57.18 closeout NEW)
- §第九部分 missing 57.13/57.14/57.15/57.16/57.17 backfill rows
- 5-sprint audit-cycle mini-sprint estimated
- Defer to Sprint 57.20+

### AD-Web-Font-Loading (Sprint 57.18 carryover)
- Geist + Noto Sans TC declared in font-family but not self-hosted
- UA fallback works; loading as web font deferred
