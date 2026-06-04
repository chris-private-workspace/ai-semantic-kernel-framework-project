# Sprint 57.78 Retrospective — Subagents Registry real list

**Closed**: 2026-06-04
**Branch**: `feature/sprint-57-78-subagents-real-list`
**Commits**: `846b25ee` (Day-0) + `1df8fdde` (Track A backend) + `7db422a7` (Track B frontend) + closeout

---

## Q1 — Goal & delivery
Closed `AD-Subagent-RealList-Phase58` — **the last Area-A "process all carryover except A-4 Tier 2" item → Area-A program COMPLETE**. Re-pointed `GET /api/v1/subagents` from the never-persisted "runtime invocations" STUB to the real per-tenant `agent_catalog` (Sprint 57.70) as an AgentSpec **registry** view, and wired the mockup-ported `/subagents` page to it. Real role/model/modes/status/spec/budget/tools; usage metrics (calls24h/p95/stats) honest-gapped (no runtime source). User-locked **Catalog/Registry view** (AskUserQuestion) over the heavier runtime-invocations persistence path.

## Q2 — Calibration
Scope class `mixed-multidomain-bundle` (0.65 — backend re-point + frontend wire, like 57.73/57.74) + `agent_factor` `mechanical-greenfield-design-decisions` (0.65). **Agent-delegated: yes** (sequential Track A backend ~9 min + Track B frontend ~7.5 min + parent Day-0 2-researcher + test-resolution + i18n fix + full re-verify). Bottom-up ~12 hr → class-calibrated ~7.8 hr → agent-adjusted ~5 hr. **16th consecutive agent-delegated sprint with NO clean wall-clock** → ratio CAVEATED (`AD-Calibration-AgentDelegated-WallClock-Measure`); the two agent wall-clocks (~16.5 min total) exclude parent Day-0 + the D-DAY1-1 test-file resolution + the D-DAY1-2 i18n fix + full re-verify, which dominate.

## Q3 — What went well
- **Day-0 AskUserQuestion resolved a genuine semantic conflict cleanly**: the candidates doc self-contradicted (`:49` specs/57.73 vs `:95` invocations), the mockup was a registry view, but the STUB shape was invocations + nothing was persisted. Surfacing all three to the user BEFORE drafting → catalog view locked → the whole sprint was a clean thin re-point instead of a heavy new-persistence build.
- **mode enum aligned for free**: `agent_catalog.allowed_modes` was already a subset of `fork/as_tool/teammate/handoff` = the FE/mockup `SubagentMode`. The STUB's `code/research/architect/review` was the wrong invocations-era set; re-pointing to catalog resolved it with zero FE enum churn.
- **honest-gap discipline held (AP-4)**: real catalog is sparse (3 seed agents, handoff-only, empty budget/tools). Rather than keep the fake-rich 8-row fixture, the page shows the real 3 + honest-gap "—" for usage metrics (no fabricated 99.2%/2840). Vitest asserts the fabrications are gone.
- **backend reuse**: `AgentCatalogRepository.list_by_tenant` + `admin/agents.py AgentResponse` already existed → the backend track was a ~9-min thin re-point.

## Q4 — What to improve / lessons
- **D-DAY1-1 (agent missed an existing same-endpoint test file)**: the code-implementer added a NEW `test_subagents.py` without noticing the EXISTING `test_subagent_registry.py` (57.19) for the same endpoint → 2 superseded stub-contract tests failed in the full suite. **Lesson**: when delegating a re-point, the agent prompt should say "find + update the EXISTING tests for this endpoint" (grep the endpoint path in tests/) rather than "add a NEW test file" — Day-0 researcher B DID flag `test_subagent_registry.py`, but that finding didn't make it into the Track-A agent prompt. Parent resolution respected Never Delete (rewrote the existing file, deleted only the sprint's own new file). Candidate Before-Commit / agent-prompt addition if it recurs (1 data point).
- **D-DAY1-2 (i18n locale vs UI-state-string convention conflation — 57.73 D-DAY1-1 variant, 2nd occurrence)**: the agent put the 3 new keys in English in BOTH locales, citing "English convention". But the "English state strings" convention is for COMPONENT code (inline strings), NOT for zh-TW i18n LOCALE files (which ARE translated — existing subagents zh-TW keys are all 繁中). This is the 2nd time an agent has mis-applied the language convention (57.73 wrote 繁中 component state strings; 57.78 wrote English zh-TW locale values — opposite directions, same root confusion). **Stronger lesson**: the agent prompt's "English copy" instruction must distinguish "component inline strings = English" from "i18n locale files = follow the file's language (en=English, zh-TW=繁中)". Worth a Before-Commit item 7 sub-bullet given 2 occurrences.

## Q5 — Carryover
- **Runtime subagent invocations list** — the original STUB intent (per-spawn telemetry); needs NEW SubagentInvocation ORM + dispatcher persist hook (the heavy path NOT chosen). Re-log as `AD-Subagent-Invocations-Persistence-Phase58` if a real invocations timeline is later wanted.
- **agent_catalog write from /subagents** — Sync-from-repo / New-subagent buttons stay AP-2 stubs (admin CRUD already at `/admin/tenants/{id}/agents`; could expose a tenant-facing create later).
- **budget/tools loop enforcement** — stored not enforced (57.70 §9 deferred).
- **Usage metrics backing** (calls24h/p95/success/avg-tokens/top-orchestrator) — needs runtime invocation telemetry; honest-gapped this sprint.

## Q6 — Anti-pattern / discipline check
- AP-4 (no Potemkin) ✅ — real persisted catalog rows; usage metrics honest-gapped (not fabricated); sparse-but-real (removed fake 8-row fixture). AP-2 (no orphan) ✅ — fixtures + carryover banner removed; wired to live endpoint. LLM-neutrality ✅ (`check_llm_sdk_leak` green; pure DB). Multi-tenant ✅ (repo tenant_id filter + RLS session + cross-tenant isolation test). Sprint workflow ✅. File headers ✅ (MHist on all touched). Never Delete Tests ✅ (existing test rewritten not deleted; only the sprint's own new file removed).

## Q7 — Closeout verification (parent-run)
- backend mypy 0/331; pytest **2109 passed, 4 skipped, 0 failed**; `run_all.py` (project-root) **10/10 green** (check_rls_policies 21 tables unchanged — no schema change).
- frontend build tsc 0; lint exit 0; Vitest subagents 24 + full **744 passed / 131 files**; check:mockup-fidelity byte-identical + baseline 50; Playwright subagents 2 passed.
- **No design note** (feature-continuation: re-point existing endpoint + wire mockup-ported page; no new contract / no 17.md change).

---

## 🎉 Area-A "process all carryover except A-4 Tier 2" program — COMPLETE

| # | Item | Sprint |
|---|------|--------|
| #1+#2 | chat-v2 Inspector Trace + Memory tabs | 57.75 |
| #3 | admin-tenants stats aggregate | 57.74 |
| A-5c | Inspector Tree tab | 57.72 |
| A-6 | admin-tenants re-mount + memory matrix | 57.73 |
| — | Memory ops-history backend | 57.76 |
| — | Memory ops-history frontend | 57.77 |
| **last** | **FE /subagents real list** | **57.78** |

(A-4 Tier 2 real Jaeger export = explicitly EXCLUDED per user program → Area-C/DevOps.)
