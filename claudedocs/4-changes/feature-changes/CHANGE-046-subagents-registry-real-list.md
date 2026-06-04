# CHANGE-046: Subagents Registry real list (re-point GET /subagents → agent_catalog)

**Date**: 2026-06-04
**Sprint**: 57.78
**Scope**: Backend (thin re-point) + Frontend (wire) / Category 11 (Subagent) + agent_catalog
**Closes**: `AD-Subagent-RealList-Phase58` — **the last Area-A "process all carryover except A-4 Tier 2" item → Area-A program COMPLETE**

## Problem
The `/subagents` page (mockup-ported 57.38) rendered an 8-row fixture with a carryover banner. The backend `GET /subagents` was a STUB returning an empty "runtime invocations" list (`not_implemented_reason`) — SubagentSpawned/Completed are in-memory SSE only, never persisted.

## Root Cause
Day-0 (2 researchers) surfaced a semantic conflict: the candidates doc self-contradicted (`:49` specs/like-57.73 vs `:95` invocations), the mockup is a registry view, the STUB shape is invocations, and nothing is persisted. The user (AskUserQuestion) chose the **Agent Catalog/Registry view** — the tenant's AgentSpec catalog already exists in `agent_catalog` (Sprint 57.70).

## Solution
- **Backend** (`subagents.py`): removed the invocations stub (`SubagentMode`/`SubagentItem`/`SubagentsPage`/`not_implemented_reason`); NEW `SubagentSpecItem` (key/name/model/allowed_modes/status/system_prompt/budget/tools) + `SubagentsResponse` (items/gapped) + `USAGE_GAPPED`; deps `get_current_tenant` + `get_db_session_with_tenant` (RLS); `AgentCatalogRepository.list_by_tenant`; meta_data → budget/tools (safe defaults). No new migration.
- **Frontend**: `SubagentSpec`/`SubagentsResponse` types; `fetchSubagents` → registry; `useSubagents` (queryKey `["subagents","list"]`); `SubagentsPage` wired — real role/model/modes/status, KPI counts derived from allowed_modes, detail spec/budget/tools real, usage metrics (calls24h/p95/stats) honest-gapped "—" (AP-4, removed fabricated 99.2%/2840); removed 8-row fixture + carryover banner; loading/empty mockup-native.
- **Parent review fixes**: D-DAY1-1 (rewrote existing `test_subagent_registry.py` into catalog contract + deleted agent's new dup test file — Never Delete respected); D-DAY1-2 (fixed i18n zh-TW 3 keys English→繁中 for locale consistency).

Commits: `846b25ee` (Day-0), `1df8fdde` (Track A backend), `7db422a7` (Track B frontend).

## Verification (parent-run, Before-Commit item 7)
- backend mypy 0/331; pytest **2109 passed, 4 skipped, 0 failed**; `run_all.py` (project-root) **10/10 green** (check_rls_policies 21 tables unchanged).
- frontend build tsc 0; lint exit 0; Vitest subagents 24 + full **744 passed/131 files**; check:mockup-fidelity byte-identical + baseline 50; Playwright subagents **2 passed**.

## Impact
Backend re-point (thin) + frontend wire. No new migration / ORM / wire-schema change. Real catalog is sparse (3 seed agents, handoff-only) but honest. `AD-Subagent-RealList-Phase58` closed → **Area-A program complete**.
