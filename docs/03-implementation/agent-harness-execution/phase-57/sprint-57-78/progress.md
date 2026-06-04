# Sprint 57.78 Progress — Subagents Registry real list

**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-78-plan.md`
**Checklist**: `...sprint-57-78-checklist.md`
**Branch**: `feature/sprint-57-78-subagents-real-list` (from `main` `2947010a`)
**Closes**: `AD-Subagent-RealList-Phase58` — **last Area-A item**

---

## Day 0 — 2026-06-04 — Plan-vs-Repo Verify + Decisions

### Decisions (user-locked, AskUserQuestion ×1)
- **View**: **Agent Catalog/Registry** (over runtime invocations) — `/subagents` shows the tenant's real AgentSpec catalog (agent_catalog, Sprint 57.70). Usage metrics (calls24h/p95/stats) honest-gap "—" (no runtime source). 57.73-style re-mount + thin backend re-point, NOT a new-persistence sprint.
- **Split**: sequential Track A backend (re-point) → Track B frontend (wire). Agent-delegated: yes + parent re-verify.

### Day-0 verify (2 researcher passes + parent reads, main `2947010a`)
- **D-DAY0-1 (candidates doc self-contradiction)**: `:49` "specs, like 57.73" vs `:95` "invocations list". Resolved → catalog (AskUserQuestion).
- **D-DAY0-2 (mode enum aligns)**: STUB `code/research/architect/review` (invocations-era, wrong) vs `agent_catalog.allowed_modes` ⊆ `fork/as_tool/teammate/handoff` = FE/mockup `SubagentMode`. Re-point resolves; drop STUB set.
- **D-DAY0-3 (STUB shape discarded)**: STUB SubagentItem = invocations (never persisted). Replace with AgentSpec registry shape.
- **D-DAY0-4 (real catalog minimal but honest)**: seed (`0023:198-205`) = 3 agents (researcher/reviewer/planner), `allowed_modes=["handoff"]` / `model=NULL` / `metadata={}`. Wired page = 3 handoff agents (sparser than 8-row fixture) but real. budget/tools/usage honest-gap.
- **D-DAY0-5 (backend reuse)**: `AgentCatalogRepository.list_by_tenant` (`:52-60`) ready; `admin/agents.py AgentResponse` (`:77-93`) serialize reference.
- **D-DAY0-6 (deps trio)**: mirror `memory.py` (get_current_tenant + get_db_session_with_tenant RLS + repo filter); registry = tenant-facing read, NO audit-role gate.
- **D-DAY0-7 (page ported)**: `SubagentsPage.tsx` (57.38) mockup-ported + fixture-backed; data layer consumes invocations STUB; `SubagentsPage.test.tsx` (8 tests) asserts 8 fixture rows → rewrite.

### Prong 1 (path) — GREEN
All confirmed: agent_catalog.py (ORM :71-119), agent_catalog_repository.py (list_by_tenant :52-60), subagents.py (STUB), admin/agents.py (AgentResponse), 0023 migration (seed :198-205), FE types/service/hook + SubagentsPage.tsx.

### Prong 2 (content) — researcher-confirmed
- agent_catalog.allowed_modes ⊆ fork/as_tool/teammate/handoff (docstring :16-17); seed metadata `{}` (empty budget/tools); repo.list_by_tenant newest-first + tenant_id filter; SubagentsPage fixture 8 rows + MODE_KPI 4 cards + detail 4 tabs (spec/budget/tools/stats).

### Prong 3 (schema) — N/A
No new table / migration / ORM (agent_catalog + repo from 57.70). check_rls_policies table count unchanged.

### go/no-go = **GO** (Day 1 backend re-point). User-locked catalog view; backend reuse confirmed; real data sparse but honest; no >20% drift.

---

## Day 1 — Backend re-point (Track A, agent-delegated code-implementer)

Agent wall-clock ~9 min; parent Day-0 research + re-verify.

### Implemented
- **`subagents.py` re-point**: removed invocations stub (`SubagentMode` code/research/architect/review + `SubagentItem` + `SubagentsPage` + `not_implemented_reason`); NEW `SubagentSpecItem` (key/name/model/allowed_modes/status/system_prompt/budget/tools) + `SubagentsResponse` (items/gapped) + `USAGE_GAPPED` const; deps `get_current_tenant` + `get_db_session_with_tenant` (RLS, mirrors memory.py); `AgentCatalogRepository.list_by_tenant`; meta_data → budget (None if unset) + tools (isinstance-guarded []). Dropped mode/cursor/limit params. Docstring + MHist.

### Drift findings (parent review, Before-Commit item 7)
- **D-DAY1-1 (agent missed existing test file → 2 pre-existing failures)**: the code-implementer added a NEW `test_subagents.py` but did NOT notice the EXISTING `test_subagent_registry.py` (57.19 stub-era) testing the same endpoint. After the re-point, 2 of its 3 tests failed (assert removed `not_implemented_reason` / `mode` Literal 422 — superseded stub contract). **Parent resolution (respects Never Delete)**: rewrote the EXISTING `test_subagent_registry.py` into the catalog registry contract (behavioral-change → update test,正當; the "registry" filename fits the catalog registry view) + merged the agent's 7 catalog tests into it + deleted the agent's NEW `test_subagents.py` (本 sprint 未 merge 中間產物, not an existing test). Net: single test file, existing file preserved+updated, no existing test deleted, no dup.
- **D-DAY1-3 (scope doc)**: backend `agent_catalog.allowed_modes` docstring says it can include role/handoff modes; only seed `["handoff"]`. Non-issue (FE `allowed_modes: SubagentMode[]`).

### Backend gates (parent-run)
- mypy `0/331`; `test_subagent_registry.py` 7 passed (migrated catalog tests); full pytest **2109 passed, 4 skipped, 0 failed** (baseline 2105 − 3 old stub + 7 new catalog = 2109); `run_all.py` (from project-root) **10/10 green** (check_rls_policies unchanged 21 tables — no schema change; check_llm_sdk_leak + check_ap4_frontend_placeholder green).

---

## Day 2 — Frontend wire (Track B, agent-delegated code-implementer) + parent i18n fix

Agent wall-clock ~7.5 min; parent re-verify + i18n correction.

### Implemented (agent)
- **types.ts**: invocations `Subagent` → `SubagentSpec` + `SubagentsResponse` (mirror wire).
- **subagentsService.ts**: `fetchSubagents(signal)` → `SubagentsResponse`; dropped mode/cursor/limit params.
- **useSubagents.ts**: return `SubagentsResponse`; queryKey `["subagents","list"]`; staleTime 30s.
- **SubagentsPage.tsx**: `useSubagents()` + `useMemo(data?.items ?? [])` (defensive guard preserved); list role←key / model←model(`—`) / modes←allowed_modes Badges / status / calls24h+p95→`—` (GAP CSS-var); KPI counts derived from allowed_modes; page-head count real; detail spec/budget(defensive `budgetValue`)/tools(empty-state)/stats(all `—` honest-gap); loading/empty mockup-native rows; removed SUBAGENT_LIST + MODE_KPI fixtures + carryover banner + fabricated 99.2%/2840/orchestrator-main.
- **SubagentsPage.test.tsx** rewrite (14 tests); NEW **e2e subagents.spec.ts** (happy + 403); i18n en+zh-TW 3 keys.

### Drift findings (parent review, Before-Commit item 7)
- **D-DAY1-2 (i18n zh-TW locale inconsistency — 57.73 D-DAY1-1 variant)**: agent added the 3 NEW keys (`list.loading`/`list.empty`/`detail.toolsEmpty`) in ENGLISH in BOTH en AND zh-TW locales, claiming "English convention". But the EXISTING subagents zh-TW keys are all 繁中 (子代理列表/角色/成功率/最常呼叫之編排器) — the agent confused "UI state strings stay English" (a component-code convention) with i18n LOCALE files (which ARE translated). **Parent fixed** zh-TW 3 keys → 繁中 (`載入中…` / `尚未註冊任何子代理。` / `未附加工具`), matching existing zh-TW conventions (loading=`載入中…` line 129). en locale was correct.

### Frontend gates (parent-run, after i18n fix)
- build tsc 0; lint exit 0 (3 pre-existing jsx-ast-utils info); Vitest subagents **24 passed / 3 files** + full **744 passed / 131 files**; check:mockup-fidelity byte-identical + baseline 50; Playwright subagents **2 passed**.
- Read ALL agent code + own i18n fix: re-point correct (registry shape, RLS tenant-scoped, meta_data safe defaults); FE honest-gap real (GAP CSS-var, no fabrication — Vitest asserts no 99.2%/2840); fixture+banner removed; mockup classes verbatim; defensive guard preserved; tests non-vacuous (e2e proves row-click select + 403 error).

---

## Day 4 — Closeout

- CHANGE-046; retrospective.md Q1-Q7; checklist all `[x]` (push+PR user-gated); MEMORY subfile + pointer; CLAUDE.md lean; next-phase-candidates.md.
- **`AD-Subagent-RealList-Phase58` CLOSED → Area-A "process all carryover except A-4 Tier 2" program COMPLETE.**
- **No design note** (feature-continuation: re-point existing endpoint + wire mockup-ported page; no new contract / no 17.md change).
- Calibration: `mixed-multidomain-bundle` 0.65 + `agent_factor` `mechanical-greenfield-design-decisions` 0.65 — CAVEATED (16th consecutive agent-delegated no-clean-wall-clock; sequential 2-agent + parent Day-0/test-resolution/i18n-fix/re-verify dominate wall-clock).

---
