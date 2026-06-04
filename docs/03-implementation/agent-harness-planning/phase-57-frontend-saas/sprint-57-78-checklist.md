# Sprint 57.78 — Checklist (Subagents Registry real list: re-point GET /subagents → agent_catalog + FE wire)

**Plan**: `sprint-57-78-plan.md`
**Branch**: `feature/sprint-57-78-subagents-real-list` (from `main` `2947010a`)
**Closes**: `AD-Subagent-RealList-Phase58` — **last Area-A "process all carryover except A-4 Tier 2" item**

---

## Day 0 — Plan-vs-Repo Verify + Branch + Decisions

### 0.1 Day-0 verify (2 researcher passes, main `2947010a`)
- [x] **Prong 1 (path)** — confirm: `infrastructure/db/models/agent_catalog.py`, `repositories/agent_catalog_repository.py` (list_by_tenant), `api/v1/subagents.py` (STUB), `api/v1/admin/agents.py` (serialize ref), `migrations/0023_agent_catalog.py` (seed), `frontend/src/features/subagents/{types,services/subagentsService,hooks/useSubagents}.ts`, `pages/subagents/SubagentsPage.tsx`.
- [x] **Prong 2 (content)** — D-DAY0-1..7 in plan §0 (catalog vs invocations resolved; mode enum aligns; seed 3 minimal agents; repo ready; deps trio; page ported).
- [x] **Prong 2.5 (child tree)** — SubagentsPage.tsx: shadcn residue 0; 2 `oklch(from var(--primary)...)` mockup-verbatim under file-top eslint-disable.
- [x] **Prong 3 (schema)** — N/A (no new table/migration; agent_catalog from 57.70).
- [x] **go/no-go** — GO; user-locked catalog/registry view (AskUserQuestion). Real catalog sparse (3 seed) but honest.

### 0.2 Branch + decisions
- [x] **Branch created** `feature/sprint-57-78-subagents-real-list`
- [x] **Decisions locked**: Agent Catalog/Registry view (AskUserQuestion) — re-point GET /subagents → agent_catalog; usage metrics honest-gap; sequential Track A backend → Track B frontend + parent re-verify; NOT runtime invocations (heavy path deferred).
- [x] **Day-0 commit** plan + checklist + progress.md Day 0

---

## Day 1 — Backend re-point (US-1/US-2/US-3)

### 1.1 Pydantic registry shape
- [ ] **NEW `SubagentSpecItem` + `SubagentsResponse`** in `subagents.py`
  - SubagentSpecItem: key/name/model(null)/allowed_modes/status/system_prompt/budget(dict|null)/tools(list)
  - SubagentsResponse: items + gapped (usage metrics list)
  - **remove** invocations SubagentMode/SubagentItem/SubagentsPage(stub)

### 1.2 Re-point handler
- [ ] **`GET /subagents` → agent_catalog** query
  - deps `get_current_tenant` + `get_db_session_with_tenant` (RLS); `AgentCatalogRepository(db).list_by_tenant(tenant_id=current_tenant)`
  - map row → SubagentSpecItem (budget=`meta_data.get("budget")`, tools=`meta_data.get("tools",[])`)
  - `gapped = ["calls_24h","p95_latency","success_rate","avg_tokens","top_orchestrator"]`
  - drop mode/cursor params; docstring + MHist update
  - DoD: mypy clean; tenant-scoped

### 1.3 Backend test
- [ ] **`test_subagents.py`** — GET returns seed 3 rows; budget/tools mapped; gapped present; cross-tenant empty; deps. Mirror test_memory_matrix.py RLS/fixture style.

---

## Day 2 — FE data layer + page wire (US-1/US-2/US-4)

### 2.1 Types + service + hook
- [ ] **types.ts** — remove invocations `Subagent`; NEW `SubagentSpec` + `SubagentsResponse`; keep `SubagentMode`
- [ ] **subagentsService.ts** — `fetchSubagents(signal?)` → `SubagentsResponse` (drop mode/cursor)
- [ ] **useSubagents.ts** — return `SubagentsResponse`; queryKey `["subagents","list"]`; staleTime 30_000

### 2.2 SubagentsPage wire
- [ ] **consume `useSubagents()`** + `items = data?.items ?? []` (preserve defensive `?.` guard — AD-Overview-PreExisting-Route-Crashes)
  - list 6-col: role←key/name, model←model(`—` null), modes←allowed_modes Badges, status, calls24h→`—`, p95→`—`
  - MODE_KPI 4 cards: counts derived `items.filter(i=>i.allowed_modes.includes(mode)).length`
  - page-head `{items.length} registered` real
  - detail spec/budget/tools real (budget null→empty+note, tools []→empty state); **stats tab honest-gap `—`**
  - loading/error/empty states (mockup-native); **remove** SUBAGENT_LIST/MODE_KPI fixtures + not_implemented_reason banner
  - DoD: mockup classes verbatim; English copy; MHist

---

## Day 3 — Tests (US-5)

### 3.1 Vitest rewrite
- [ ] **`SubagentsPage.test.tsx`** — mock `useSubagents` real items; assert real rows + KPI derived counts + null model `—` + usage `—` + loading/error/empty + detail tab switch; remove 8-fixture-row assertions; preserve defensive guard test

### 3.2 e2e
- [ ] **NEW `tests/e2e/subagents/subagents.spec.ts`** — mock GET /subagents catalog (2-3 rows); assert rows + row-click select + detail spec; mock 403 → error

### 3.3 Parent re-verify (Before-Commit item 7)
- [ ] **read all agent-changed code** + run ALL gates (incl. check:mockup-fidelity); don't trust agent report; pin English copy

---

## Day 4 — Sweep + Closeout

### 4.1 Full sweep (parent re-verify, Before-Commit item 7)
- [ ] **Backend gates** — `mypy src/` 0 + `pytest` (new + regression) + `scripts/lint/run_all.py` (check_rls_policies unchanged — no schema change)
- [ ] **Frontend gates** — `npm run lint` (NO `--silent`) 0 + `npm run build` (tsc 0) + `npm run test` (Vitest) + `npm run check:mockup-fidelity` (byte-identical + baseline unchanged) + `npx playwright test subagents`
- [ ] **Read all agent-changed code** — re-point correct, registry shape, honest-gap (not fabricated), fixture+banner removed, mockup classes verbatim, English copy, RLS tenant-scoped

### 4.2 Closeout docs
- [ ] **CHANGE-046** in `claudedocs/4-changes/feature-changes/`
- [ ] **progress.md** Day 0-4 + **retrospective.md** Q1-Q7
- [ ] **Checklist** all `[x]` (no deletion of unchecked)
- [ ] **Calibration** record (mixed-multidomain-bundle 0.65 + agent_factor 0.65; CAVEAT consecutive agent-delegated)
- [ ] **AD status**: `AD-Subagent-RealList-Phase58` CLOSED → **Area-A program COMPLETE**; next-phase-candidates.md
- [ ] **MEMORY subfile + pointer** + **CLAUDE.md lean**
- [ ] **Design note?** — NO (feature-continuation: re-point existing endpoint + wire mockup-ported page; no new contract / no 17.md change)

### 4.3 Ship
- [ ] **Commit mapping** Day-0 / backend re-point / FE wire / tests / closeout
- [ ] **Push + PR** (user-gated — explicit authorization required)
