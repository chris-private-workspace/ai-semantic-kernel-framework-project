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
