# Sprint 57.78 Plan — Subagents Registry real list (re-point GET /subagents → agent_catalog + FE wire) (closes AD-Subagent-RealList-Phase58)

**Branch**: `feature/sprint-57-78-subagents-real-list` (from `main` `2947010a`)
**Closes**: `AD-Subagent-RealList-Phase58` — **the last Area-A "process all carryover except A-4 Tier 2" item**.
**Scope**: Backend (thin re-point) + Frontend (wire). Re-point the `GET /api/v1/subagents` STUB from the never-persisted "runtime invocations" shape to the real per-tenant **agent_catalog** (Sprint 57.70), and wire the already-mockup-ported `/subagents` Registry page to it.

---

## 0. Background

The `/subagents` page (Sprint 57.38 mockup-port of `page-agents.jsx` SubagentsRegistry + SubagentDetail) renders an 8-row **fixture** with a carryover banner. Day-0 (2 researchers) surfaced a semantic conflict + the user resolved it:

**User decision (AskUserQuestion, 2026-06-04): Agent Catalog/Registry view** (over runtime invocations). The page shows the tenant's **AgentSpec catalog** (role/model/modes/status), which already exists in `agent_catalog` (Sprint 57.70, tenant-scoped + RLS). Usage metrics (calls24h / p95 / stats) have **no runtime data source** → honest-gap "—" (mirrors 57.73/57.74 honest-gap). This is a 57.73-style re-mount + thin backend re-point, NOT a new persistence sprint.

### Day-0 ground-truth (2 researcher passes + parent reads, main `2947010a`)
- **D-DAY0-1 (candidates doc self-contradiction)**: `next-phase-candidates.md:49` "specs exist, like 57.73" vs `:95` "invocations list backend". Resolved → catalog/registry (user-locked).
- **D-DAY0-2 (mode enum — catalog view aligns)**: STUB `SubagentMode = code/research/architect/review` (`subagents.py:73`) is the wrong invocations-era set. `agent_catalog.allowed_modes` is a subset of `fork/as_tool/teammate/handoff` (`agent_catalog.py:16-17,88-91`) = **exactly the FE/mockup `SubagentMode`** (`types.ts:27`). Re-point to catalog resolves the mismatch; drop the STUB mode set.
- **D-DAY0-3 (STUB shape discarded)**: STUB `SubagentItem` (`invocation_id/parent_session_id/total_tokens/...`, `subagents.py:76-85`) = runtime invocations, never persisted (SubagentSpawned/Completed are in-memory SSE only). Discard; replace with an AgentSpec registry shape.
- **D-DAY0-4 (real catalog is minimal but honest)**: seed (`0023_agent_catalog.py:198-205`) = **3 default agents** (researcher/reviewer/planner) per tenant, all `allowed_modes=["handoff"]` / `model=NULL` / `metadata={}` (empty budget/tools). So the wired page shows 3 handoff-mode agents (sparser than the 8-row fixture) — but real. budget/tools (meta_data) + usage metrics honest-gap when absent.
- **D-DAY0-5 (backend reuse)**: `AgentCatalogRepository.list_by_tenant(tenant_id)` (`agent_catalog_repository.py:52-60`) is ready (newest-first). `admin/agents.py` (`AgentResponse` :77-93) already serializes agent_catalog → response-mapping reference.
- **D-DAY0-6 (deps trio)**: mirror `memory.py` (`get_current_tenant` + `get_db_session_with_tenant` RLS + repo tenant_id filter, defence-in-depth) — same pattern as the /matrix + /ops endpoints. Registry is tenant-facing read (any tenant user sees their tenant's catalog); NO audit-role gate (not audit data).
- **D-DAY0-7 (page already ported)**: `SubagentsPage.tsx` (57.38) is fully mockup-ported + fixture-backed; `useSubagents`/`subagentsService`/`types.ts` exist but consume the invocations STUB. `SubagentsPage.test.tsx` (8 tests) asserts 8 fixture rows + 4 KPI cards → must be rewritten for real catalog.

---

## 1. Sprint Goal

Re-point `GET /api/v1/subagents` from the never-persisted invocations STUB to the real per-tenant `agent_catalog` (registry view), and wire the `/subagents` page to it — real role/model/modes/status/spec, honest-gapped usage metrics — closing the last Area-A item.

---

## 2. User Stories

- **US-1** — 作為 tenant user，我希望 `/subagents` 顯示我 tenant 真實的 agent catalog（role/model/modes/status），以便看到實際註冊的 subagent specs（不是假 fixture）。
- **US-2** — 作為 tenant user，我希望選中一個 agent 看到它真實的 spec（system_prompt / allowed_modes / budget / tools），以便 inspect 定義。
- **US-3** — 作為 auditor，我希望無 runtime 數據源的 usage metrics（calls24h/p95/stats）誠實顯示「—」而非假數字，以便不被誤導（AP-4）。
- **US-4** — 作為前端維護者，我希望移除 8-row fixture + carryover banner + invocations-era types，以便 `/subagents` 無 orphan（AP-2）。
- **US-5** — 作為 QA，我希望 backend endpoint test + Vitest（rewrite）+ e2e 覆蓋，以便回歸保護。

---

## 3. Technical Specifications

### 3.0 Architecture
`useSubagents()` (TanStack) → `fetchSubagents()` → re-pointed `GET /api/v1/subagents` → `AgentCatalogRepository.list_by_tenant`. Registry view: real spec fields from agent_catalog; usage metrics honest-gapped via a `gapped` list (mirror 57.74).

### 3.1 Re-point `GET /subagents` (US-1/US-2/US-3) — `api/v1/subagents.py`
- **Remove** invocations-era `SubagentMode = code/research/architect/review`, `SubagentItem`, `SubagentsPage` (empty stub + `not_implemented_reason`).
- **NEW** Pydantic:
  ```python
  class SubagentSpecItem(BaseModel):
      key: str
      name: str
      model: str | None
      allowed_modes: list[str]   # subset of fork/as_tool/teammate/handoff
      status: str                # live / staging
      system_prompt: str
      budget: dict[str, Any] | None   # meta_data.get("budget") — None if unset
      tools: list[str]                # meta_data.get("tools", [])
  class SubagentsResponse(BaseModel):
      items: list[SubagentSpecItem]
      gapped: list[str]   # ["calls_24h","p95_latency","success_rate","avg_tokens","top_orchestrator"]
  ```
- Re-point handler: deps `get_current_tenant` + `get_db_session_with_tenant` (RLS); `AgentCatalogRepository(db).list_by_tenant(tenant_id=current_tenant)`; map each row (budget/tools from `meta_data`); return `SubagentsResponse(items=..., gapped=USAGE_GAPPED)`. Drop `mode`/`cursor` query params (catalog is small, no pagination); keep an optional `limit` cap or drop entirely.
- File header MHist + docstring update (invocations stub → catalog registry).

### 3.2 FE types (US-1) — `features/subagents/types.ts`
- Keep `SubagentMode = fork|as_tool|teammate|handoff`.
- **Remove** invocations `Subagent` interface. **NEW** `SubagentSpec { key; name; model: string|null; allowed_modes: SubagentMode[]; status: string; system_prompt: string; budget: Record<string,unknown>|null; tools: string[] }` + `SubagentsResponse { items: SubagentSpec[]; gapped: string[] }`.

### 3.3 FE service + hook (US-1) — `subagentsService.ts` + `useSubagents.ts`
- `fetchSubagents(signal?)`: GET `/api/v1/subagents`; return `SubagentsResponse` (drop mode/cursor params; keep simple).
- `useSubagents()`: queryKey `["subagents","list"]`; queryFn forwards signal; staleTime 30_000. Return `SubagentsResponse`.

### 3.4 SubagentsPage wire (US-1/US-2/US-3/US-4) — `pages/subagents/SubagentsPage.tsx`
- Consume `useSubagents()`; `items = data?.items ?? []`. Default-select first item.
- **list table** (6-col, mockup verbatim): role←`key`/`name`, model←`model` (`—` if null), modes←`allowed_modes` (Badges), status←`status`, calls24h→`—`, p95→`—`.
- **MODE_KPI** (4 cards): counts derived real from items (`items.filter(i => i.allowed_modes.includes(mode)).length`).
- **page-head count**: `{items.length} registered` real.
- **detail card** (selected spec): spec tab role/model/system_prompt/allowed_modes real; budget tab from `budget` (empty/`—` if null + "No budget configured" note); tools tab from `tools` (empty state if []); **stats tab honest-gap** all "—" (usage metrics in `gapped`).
- States: loading → mockup-native; error → existing error banner; empty (0 items) → "No subagents registered." row. **Remove** `SUBAGENT_LIST`/`MODE_KPI` fixtures + the `not_implemented_reason` carryover banner.
- Sync/New buttons stay AP-2 visual stubs (no backend).

### 3.5 Tests (US-5)
- Backend `test_subagents.py` (NEW or extend): re-pointed GET returns tenant's agent_catalog rows (seed 3); maps budget/tools from meta_data; `gapped` present; tenant-scoped (cross-tenant empty); deps (get_current_tenant). Mirror `test_memory_matrix.py` fixture/RLS style.
- FE `SubagentsPage.test.tsx` (rewrite): mock `useSubagents` real items; assert real rows render; KPI counts derived; null model → `—`; usage metrics `—`; loading/error/empty; detail tab switch. Remove 8-fixture-row assertions.
- e2e `tests/e2e/subagents/subagents.spec.ts` (NEW): mock GET /subagents catalog (2-3 rows); assert rows + row-click select + detail spec; mock 403 → error.

### 3.6 Lint / validation
`npm run lint` (NO `--silent`), `npm run build`, `npm run test`, `npm run check:mockup-fidelity` (byte-identical + baseline unchanged — 0 new color literals), `npx playwright test subagents`; backend `mypy src/` + `pytest` + `scripts/lint/run_all.py` (check_rls_policies unchanged — no schema change).

---

## 4. File Change List

**NEW (2)**
- `frontend/tests/e2e/subagents/subagents.spec.ts`
- `backend/tests/integration/api/test_subagents.py` (if absent; else extend)

**EDIT (6)**
- `backend/src/api/v1/subagents.py` (re-point STUB → agent_catalog registry)
- `frontend/src/features/subagents/types.ts` (invocations → SubagentSpec/SubagentsResponse)
- `frontend/src/features/subagents/services/subagentsService.ts` (fetchSubagents → SubagentsResponse)
- `frontend/src/features/subagents/hooks/useSubagents.ts` (return type + queryKey)
- `frontend/src/pages/subagents/SubagentsPage.tsx` (fixture → hook; list/KPI/detail real + honest-gap; remove banner)
- `frontend/tests/unit/pages/subagents/SubagentsPage.test.tsx` (rewrite for real catalog)

**NO new migration / wire-schema / ORM change** (agent_catalog + repo already exist from 57.70).

---

## 5. Acceptance Criteria

- `GET /subagents` returns the tenant's agent_catalog rows (registry shape: key/name/model/allowed_modes/status/system_prompt/budget/tools) + `gapped` usage-metric list; tenant-scoped (cross-tenant empty); deps `get_current_tenant`.
- `/subagents` page renders real catalog rows (3 seed agents in a fresh tenant); KPI counts derived from allowed_modes; model null → `—`; usage metrics (calls24h/p95/stats) → `—`; detail spec/budget/tools real (or honest empty); no fixture import; no carryover banner.
- Mode badges use real `allowed_modes` (fork/as_tool/teammate/handoff).
- Gates: backend mypy 0 + pytest + run_all green; FE lint (no `--silent`) 0 + build tsc 0 + Vitest green + check:mockup-fidelity byte-identical + Playwright subagents green.

---

## 6. Deliverables

- [ ] Re-pointed `GET /subagents` → agent_catalog registry (Pydantic + repo + deps + meta_data map + gapped)
- [ ] FE types (SubagentSpec/SubagentsResponse) + service + hook
- [ ] SubagentsPage wired (list/KPI/detail real + honest-gap usage) + fixture/banner removed
- [ ] Backend endpoint test + Vitest rewrite + Playwright e2e
- [ ] All gates green; closeout (CHANGE-046 + progress + retro + MEMORY + CLAUDE lean; Area-A program COMPLETE)

---

## 7. Workload Calibration

Scope class `mixed-multidomain-bundle` (0.65 — backend re-point + frontend wire, like 57.73/57.74) + `agent_factor` `mechanical-greenfield-design-decisions` (0.65 — NEW registry Pydantic + display mapping + honest-gap decisions). **Agent-delegated: yes** (sequential Track A backend → Track B frontend + parent Day-0 research + full re-verify).

Bottom-up est ~12 hr → class-calibrated commit ~7.8 hr (mult 0.65) → agent-adjusted commit ~5 hr (agent_factor 0.65).

---

## 8. Dependencies & Risks

- **Risk: real catalog is sparse (3 seed agents, handoff-only, empty budget/tools)** — wired page looks thinner than the 8-row fixture. Mitigation: this is the honest real state (AP-4 — fixture richness was fake); document; budget/tools/usage honest-gap when absent.
- **Risk: meta_data shape (budget/tools keys)** — seed `metadata={}`; budget/tools absent. Mitigation: `meta_data.get("budget")` → None, `meta_data.get("tools", [])` → []; detail tabs show empty-state, not crash. Per Day-0 `AD-Day0-Prong2-Nested-Shape-Read`, the agent must READ a non-empty meta_data shape if any tenant has one (else default safely).
- **Risk: RLS on plain vs tenant session** — `admin/agents.py` uses plain `get_db_session` + repo filter; this sprint uses `get_db_session_with_tenant` (RLS SET LOCAL) like memory.py — RLS-correct. Verify the seed rows are visible under the RLS session in the endpoint test.
- **Risk: SubagentsPage.test 8-row + KPI assertions** — rewrite for real items; the defensive `?.items?.length` guard (AD-Overview-PreExisting-Route-Crashes) must be preserved.
- **Dependency**: `agent_catalog` + `AgentCatalogRepository` live (57.70). No new migration.

---

## 9. Out of Scope (this sprint; carryover)

- **Runtime subagent invocations list** — the original STUB intent; needs NEW SubagentInvocation ORM + dispatcher persist hook (the heavy path the user did NOT choose). Re-log as `AD-Subagent-Invocations-Persistence-Phase58` if needed later.
- **agent_catalog write from /subagents** — Sync-from-repo / New-subagent buttons stay AP-2 stubs (admin CRUD already at `/admin/tenants/{id}/agents`).
- **budget/tools loop enforcement** — stored not enforced (57.70 §9 deferred).
- **Usage metrics backing** (calls24h/p95/success/avg-tokens/top-orchestrator) — needs runtime invocation telemetry; honest-gapped this sprint.
