# 29 — HANDOFF Completion + Sidechain Transcript Persistence (B3 spike extract)

**Purpose**: Verified design extract from Sprint 57.107 (harness-deepening Workflow B slice B3) — the dispatcher-stub convergence that made handoff LLM-drivable, per-tenant handoff governance, the sessions lineage list, and the CC parentUuid/isSidechain-borrowed sidechain transcript persistence.
**Category / Scope**: Cat 11 Subagent × platform_layer.handoff/governance × api × infrastructure / Sprint 57.107
**Created**: 2026-06-12
**Last Modified**: 2026-06-12
**Status**: Active (extracted from real implementation; ≥95% verified ratio)

> **Modification History**
> - 2026-06-12: Initial creation (Sprint 57.107 Day 3 — spike extract)

---

## 1. Spike Summary

US-1 (stub retirement + spec-only trigger): the chat 主流量 had a complete handoff pipeline (classifier → router hook → `HandoffService`, 57.68-70) that **no real LLM could trigger** — the `handoff` ToolSpec was never registered (`business_domain/_register_all.py` "HANDOFF intentionally excluded"), while the parallel `HandoffExecutor` UUID stub had zero 主流量 callers. 57.107 deleted the stub trio and registered a **spec-only** tool: `make_handoff_spec(suggested_targets)` (`agent_harness/subagent/tools.py:144-196`) whose handler raises `RuntimeError("handoff is loop-intercepted")` — the loop's output classifier (`output_parser/classifier.py:47,68`) terminates the run with `stop_reason="handoff"` BEFORE tool execution (`loop.py` HANDOFF branch), so the handler is an AP-4 negative guard, not dead code.

US-2 (governance): `HarnessPolicy` 9→11 (`handoff_enabled` + `handoff_target_allowlist`, `platform_layer/governance/harness_policy.py:108-133`); **double-gate** — registration (`api/v1/chat/handler.py` handoff-targets block: Off → tool absent, zero-cost) + boot (`platform_layer/handoff/service.py` `boot_handoff(allowed_targets=)` off-list → `HandoffError` before any write).

US-3 (lineage list): `GET /api/v1/sessions` (`api/v1/sessions.py` `SessionListItem{…, agent_role, handoff_parent_id}`) over `SessionRepository.list_sessions` (top-level only); chat-v2 SessionList real-data + `↳ {agentRole}` badge.

US-4 (sidechain transcripts): migration `0028_sidechain_sessions` adds `sessions.parent_session_id` + `sessions.is_sidechain` (CC parentUuid/isSidechain borrow — DISTINCT from `handoff_parent_id`: handoff = control transfer between top-level sessions, sidechain = nested subagent child) + **DEFAULT partitions** for `messages`/`message_events`; api-layer observer `_persist_subagent_transcript` (`api/v1/chat/router.py`) consumes the 57.95 relay buffer → sidechain session row + per-turn `message_events` rows (that table's FIRST writer) + completion summary/tokens.

## 2. Decision Matrix

| Decision | Chosen | Rejected | Why |
|----------|--------|----------|-----|
| Stub convergence | DELETE trio + spec-only tool | dispatcher delegating to `HandoffService` | Cat 11 → platform_layer import inverts category layering; the loop-interception path already exists and is tested |
| Trigger handler | defensive raise | no-op return | reaching the handler means classifier interception was bypassed — must be loud (AP-4) |
| Spec target hint | `allowlist or sorted(DEFAULT_AGENTS)` (no hot-path DB) | per-request persona-catalog query | description is guidance only; boot-time validation is authoritative; hot-path DB read rejected (C1/C3 TTL precedent) |
| Governance knobs | 2 fields (`enabled` + `allowlist`); PUT rejects `[]` | one tri-state list (`[]`=off) | one knob per concern; `[]` would shadow the enabled gate (UX + audit clarity) |
| Sidechain lineage | NEW column pair | reuse `handoff_parent_id` | semantics clash would corrupt both chain queries |
| Child-event storage | `message_events` (existing partitioned table, first consumer) | new table / meta_data blob | the table was built for exactly this (SSE replay/debug); per-turn rows queryable by sequence |
| Persistence site | api-layer observer (SAVEPOINT, both drain sites) | inside Cat 11 executors | agent_harness must stay persistence-free (no infra imports); mirrors sessions/audit observer pattern |
| Partition fix | DEFAULT partitions (both tables) | monthly partition cron | 2-line insurance in the same migration; explicit months still attachable later |

## 3. Verified Invariants (this spike)

1. **A real LLM can hand off** — drive-through: gpt-5.2 called `handoff` → `loop_end stop=handoff` → child session (`handoff_parent_id` set) → `agent_handoff` SSE → FE banner + ↳ badge (`artifacts/dt57107-A-handoff-banner.png`). `pytest tests/integration/api/test_chat_handoff.py` (8).
2. **Allowlist double-gate** — spec layer steered the live LLM to the only allowed target (B1 observation); boot layer rejects off-list before any write (`test_chat_handoff_offlist_target_fails_soft_no_child`: no child + parent stays active + no frame).
3. **Off = absent** — `handoff_enabled=false` → tool not registered (`test_make_default_executor_omits_handoff_by_default`); live: same ask ends `end_turn`, LLM fell back to `task_spawn`.
4. **Sidechain transcript round-trip** — `test_subagent_transcript_observer.py` (3) + live DB probe: session `709ded76…` (teammate, completed, summary + tokens folded) + 6 `message_events` rows seq 1-6.
5. **Tenant isolation 鐵律** — sessions list + sidechain rows invisible cross-tenant (`test_sessions_list.py::test_list_sessions_tenant_isolation` + `test_sidechain_invisible_cross_tenant`).
6. **No-policy byte-compat caveat** — the ONLY intentional behavior change: handoff now defaults ON (3 default personas); everything else default-path unchanged (full suite 2460, 0 deletions).
7. **Partition time-bomb defused** — `0028` DEFAULT partitions; pre-fix both tables un-writable from 2026-07-01 (`0002` months end at `2026_06`, no creation helper).

Fixtures: `tests/integration/api/test_subagent_transcript_observer.py::_SpawningLoop` (buffer-filling fake loop) · `test_chat_handoff.py::_HandoffLoop`.

## 4. Cross-Category Contracts (17.md)

- `SubagentDispatcher` row UPDATED: `handoff()` REMOVED (spawn/wait_for only); HANDOFF = classifier + platform path.
- §3.1 `handoff` tool row UPDATED: spec-only + policy gate semantics.
- `HarnessPolicy` stays platform_layer (57.105 D12 precedent — N/A for a 17.md ABC row); the observer is api-layer composition (no new contract).

## 5. Open Invariants (deferred — NOT verified here)

- Sidechain transcript READ API + Inspector replay UI (`AD-Sidechain-Transcript-Read-API`).
- Parent-transcript `messages` writes (durable parent transcript remains `state_snapshots`).
- Child checkpoint/resume; detached teammate (§2.5); depth>1; multi-hop lineage TREE walk (v1 = parent pointer).
- Boot-time allowlist rejection observed only via integration test (the live LLM never attempted an off-list target — spec steering is that effective).

## 6. Rollback

Revert the 57.107 commits; migration `0028` has a clean `downgrade()` (drops DEFAULT partitions + columns — sidechain rows lose lineage but sessions survive). The stub trio is in git history; `handoff_enabled=false` is the no-code kill switch for the new LLM-drivable path (per tenant), `HANDOFF_*`-free env rollback not needed.

## 7. References

- `claudedocs/4-changes/feature-changes/CHANGE-074-handoff-finish-sidechain-transcripts.md`
- `claudedocs/1-planning/harness-deepening-proposal-20260610.md` §2.4 (B3) · design notes 20 (subagent) / 28 (harness policy)
- `cc-source-blueprint-pause-resume-phases-20260608.md` §2.4 (parentUuid/isSidechain borrow)
- Sprint artifacts: `agent-harness-execution/phase-57/sprint-57-107/` (progress + artifacts)
