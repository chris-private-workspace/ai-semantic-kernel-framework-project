# Sprint 57.68 Plan — HANDOFF Control-Transfer + Platform Session-Boot (A-3b, backend slice)

**Purpose**: Ship the **4th Cat 11 subagent mode — HANDOFF** as a REAL control-transfer on the production chat path, the first (backend-complete, server-side-first) slice toward the user-chosen **full platform session-boot** model: when the agent emits a HANDOFF, the parent agent exits, a NEW persisted child session is booted for the target agent (under a resolved persona, same tenant, linked to the parent), the parent is marked `handed_off` + audited, and an `agent_handoff` SSE event (carrying the new session id) is emitted so the client can later pivot. A-3a (Sprint 57.64) shipped FORK/TEAMMATE/AS_TOOL and **explicitly excluded HANDOFF** because — unlike those delegate-and-return modes — HANDOFF is a control transfer that `loop.py:1067` currently dead-ends with `HANDOFF_NOT_IMPLEMENTED`. This sprint replaces that dead-end with a real session-boot. **This is a SPIKE** (new control-transfer mechanism) → Day-4 design-note extract + 8-point quality gate (per `sprint-workflow.md §Step 5.5`).
**Category / Scope**: Cat 11 (Subagent Orchestration — HANDOFF) + platform-layer session-boot service + Cat 1 (loop stop_reason) + Cat 12 (new `agent_handoff` SSE event via the 57.67 codegen) + sessions DB (Alembic `0022`) + governance (audit); Phase 57.68
**Created**: 2026-06-02
**Status**: Draft (user-approved scope: Option B "full platform session-boot"; backend slice this sprint, FE session-pivot deferred — see §0/§9; code execution gated on Day-0 GO)
**Source**: Area-A capstone (A-3b component) + **two-round Day-0 reality audit (codebase-researcher, 2026-06-02)** (module/mode map + 4 session-boot/persona/audit facts) + user AskUserQuestion decision 2026-06-02 (Option B full platform session-boot over thin in-loop / mechanism-only)

> **Modification History**
> - 2026-06-02: Initial creation — A-3b HANDOFF backend session-boot slice; SPIKE (8-point design note); folds Day-0 audit (D1-D5 + the 4 session-boot facts) into §0; backend-first decomposition per server-side-first discipline

---

## 0. Background

A-3a (Sprint 57.64) wired Cat 11 onto the chat path but excluded HANDOFF (57.64 plan §9: "hollow executor + missing platform session-boot; needs a design spike + design note"). A-3b is that spike.

### Decomposition (user chose Option B = full platform session-boot, a multi-sprint destination)
The user accepted Option B ("~大；可能 2+ sprint"). Per **server-side-first** (`10-server-side-philosophy.md`) + thin-vertical spike discipline + rolling-planning (no pre-written future plans), this sprint = the **backend-complete slice**: loop control-transfer → platform session-boot → child session persisted (tenant-scoped, linked, audited) → `agent_handoff` SSE event. The **frontend session-pivot UI** (the client following the handoff to the new session) is a distinct follow-up sprint (§9; carryover — NOT planned now). Full message-context carry, target auto-first-turn, and multi-hop handoff chains are design-note open questions (§9).

### ⚠️ Day-0 audit findings (two researcher rounds, folded per `sprint-workflow.md §Step 2.5`)

- **D1 — HANDOFF is a control transfer, structurally unlike the other 3 modes** (`01-eleven-categories-spec.md:1080` "完全交棒，父 agent 退出"). FORK/TEAMMATE/AS_TOOL delegate-and-return; HANDOFF = parent exits, target takes over. → cannot be a pure api/factory allow-list extension like A-3a (that would be a Potemkin — AP-4).
- **D2 — the gap is loop + platform session-boot, NOT the dispatcher**. `DefaultSubagentDispatcher.handoff()` (`dispatcher.py:280-297`) + `HandoffExecutor.execute` (`modes/handoff.py:44-62`) already exist and return a `uuid4()` — but boot NO session and `HandoffExecutor` validates `target_agent` only as a non-empty string. `loop.py:1067-1074` dead-ends HANDOFF with `HANDOFF_NOT_IMPLEMENTED`; the output parser already routes `response.handoff_request → OutputType.HANDOFF` (`loop.py:654-655`).
- **D3 — sessions schema needs Alembic `0022`**. `Session` ORM (`infrastructure/db/models/sessions.py:73-122`): `status` is `String(32)` default `"active"` (free-text, NOT a DB enum → holds `"handed_off"` with no type change); `tenant_id` from `TenantScopedMixin`; `meta_data` JSONB (physical column `"metadata"` — alias). **No parent/handoff linkage, no persona column.** → `0022` adds `sessions.handoff_parent_id UUID NULL` FK→sessions(id) + index; persona stored in `meta_data["agent_role"]` (JSONB, no column — YAGNI). Next free migration number = `0022` (latest `0021_rate_limit_alerts`).
- **D4 — NO agent/persona registry exists**. The Phase-48 "7 YAML configs" (`backend/config/*.yaml`) are policy configs (error_budgets/retry/guardrails/risk), not persona catalogs. The chat path boots under a single hardcoded `DEMO_SYSTEM_PROMPT` (`handler.py:94`). `AgentSpec` (`_contracts/subagent.py:74-86`) has role/prompt/model but nothing maps a `target_agent` string → system-prompt. → the spike **defines a minimal `target_agent → system_prompt` registry** (small dict/YAML) as the design-note open-question deliverable.
- **D5 — a new SSE event is needed + the 57.67 codegen makes it clean**. Existing `SubagentSpawned`/`SubagentCompleted` (`events.py:316/323`) don't model control transfer (new_session_id / target persona). A NEW `AgentHandoff` LoopEvent (Cat 11) is required → register `agent_handoff` in `event_wire_schema.py` (the 57.67 single-source) + regen codegen + add a `sse.py` serializer branch + the parity test auto-covers it. The post-loop session-boot means the `AgentHandoff` event is constructed **after** the child session is booted (so it carries `new_session_id`), then serialized through the normal LoopEvent path.

**Net**: a coherent backend vertical — `loop.py` swaps the HANDOFF dead-end for a `handoff` stop_reason carrying the parsed `handoff_request`; the router's post-loop hook invokes a new platform handoff service that boots a tenant-scoped child session (linked + persona in meta_data), marks the parent `handed_off`, writes an audit row, and emits the `agent_handoff` SSE event; `handler.py` resolves per-session persona so the child session actually runs under the target. Non-Potemkin (the child session is real, persona-resolved, observable). FE pivot deferred.

---

## 1. Sprint Goal

Replace `loop.py`'s `HANDOFF_NOT_IMPLEMENTED` dead-end with a real control transfer: on a HANDOFF output the loop terminates with a `handoff` stop_reason carrying the parsed target_agent + reason; the chat router's post-loop hook invokes a new platform-layer handoff service that boots a NEW tenant-scoped child session for the target agent (linked to the parent via `handoff_parent_id`, persona in `meta_data["agent_role"]`), marks the parent session `handed_off`, writes a `session.handoff` audit row, and emits an `agent_handoff` SSE event (target_agent, reason, parent_session_id, new_session_id) via the 57.67 wire-schema codegen; `handler.py` resolves per-session persona from a minimal `target_agent → system_prompt` registry so the child session runs under the target. Prove it with integration tests (HANDOFF output → child session persisted, tenant-scoped, linked, parent handed-off, audit written, event emitted) + a Day-4 design note (8-point gate). **Multi-tenant 鐵律: child session uses the parent's tenant_id; cross-tenant handoff forbidden.** FE session-pivot deferred (§9).

---

## 2. User Stories

- **US-1 (loop control transfer)** — As the agent loop, when the LLM emits a HANDOFF, I want to terminate the parent cleanly with a `handoff` stop_reason carrying the target_agent + reason (instead of dead-ending with `HANDOFF_NOT_IMPLEMENTED`), so the platform can act on the handoff. → `loop.py:1067-1074` swap; carry the already-parsed `handoff_request` (`loop.py:654-655`).
- **US-2 (platform session-boot service)** — As the platform, when a parent loop ends with `handoff`, I want to boot a NEW persisted child session for the target agent (same tenant, `handoff_parent_id`=parent, persona in `meta_data["agent_role"]`), mark the parent `handed_off`, and write a `session.handoff` audit row, so the handover is durable + auditable. → new `platform_layer/handoff/service.py` invoked from `router.py`'s post-loop hook; Alembic `0022` (`handoff_parent_id` FK + index).
- **US-3 (persona resolution)** — As the booted child session, I want to run under the target agent's persona (not the hardcoded `DEMO_SYSTEM_PROMPT`), so the handoff is real. → minimal `target_agent → system_prompt` registry; `handler.py` resolves per-session persona from `meta_data["agent_role"]` (fallback `DEMO_SYSTEM_PROMPT`).
- **US-4 (`agent_handoff` SSE event)** — As a client, I want an `agent_handoff` event (target_agent, reason, parent_session_id, new_session_id) on the stream after a handoff, so the UI can later pivot to the new session. → new `AgentHandoff` LoopEvent (Cat 11) + `agent_handoff` in `event_wire_schema.py` + codegen regen + `sse.py` branch + parity test (auto).
- **US-5 (validation + design note)** — As a reviewer, I want integration tests proving the full backend handover (child session persisted/tenant-scoped/linked, parent handed-off, audit, event) + a Day-4 design note (8-point gate) capturing the control-transfer design + open questions, so the spike's learnings are extracted and the next slice (FE pivot) is well-scoped.

---

## 3. Technical Specifications

### 3.0 Architecture (backend session-boot slice)

```
LLM emits HANDOFF → output parser → OutputType.HANDOFF (loop.py:654-655)
        ▼
loop.py:1067  [WAS: HANDOFF_NOT_IMPLEMENTED dead-end]
        → set LoopCompleted(stop_reason="handoff") + carry handoff_request {target_agent, reason}
        ▼
router.py _stream_loop_events post-loop hook (the LoopCompleted handler, ~:532)
        → if stop_reason == "handoff":  HandoffService.boot_handoff(parent_session, target_agent, reason, tenant_id, user_id)
                ├─ resolve target_agent → system_prompt (minimal registry)  [persona]
                ├─ SessionRepository.create_session(child, tenant_id=parent.tenant_id,
                │        handoff_parent_id=parent.id, meta_data={"agent_role": target_agent})
                ├─ mark parent.status = "handed_off"
                └─ append_audit(operation="session.handoff", resource_type="session",
                         resource_id=parent.id, operation_data={target_agent, new_session_id}, tenant_id, user_id)
        → yield AgentHandoff LoopEvent {target_agent, reason, parent_session_id, new_session_id}
        → serialize_loop_event → "agent_handoff" SSE frame  (event_wire_schema.py registry, 57.67 codegen)
        ▼
(next chat request to new_session_id) handler.py resolves persona from session meta_data["agent_role"] → target system_prompt
```

The Cat 11 dispatcher stays LLM-neutral (no change to `dispatcher.handoff()` semantics beyond what the service needs); `loop.py` changes ONLY the stop_reason swap (no control-flow rewrite). Session-boot lives in the platform layer (crosses sessions DB + audit + persona — not a dispatcher concern).

### 3.1 Loop control transfer (US-1) — `loop.py` (~:1067-1074)
- Replace the `HANDOFF_NOT_IMPLEMENTED` terminate with: build `LoopCompleted(stop_reason="handoff", ...)` and carry the parsed `handoff_request` (`target_agent`, `reason`) so the router can read it post-loop (add a field to `LoopCompleted` OR a small handoff carrier — Day-1 reads the exact `LoopCompleted` shape + the `handoff_request` object from the output parser). Minimal change; no other loop control flow touched.
- Loop does NOT boot the session (no DB/router knowledge in the loop — server-side-first layering).

### 3.2 Platform handoff service (US-2) — `backend/src/platform_layer/handoff/service.py` (NEW)
- `HandoffService.boot_handoff(*, parent_session_id, target_agent, reason, tenant_id, user_id, db) -> HandoffResult(new_session_id)`:
  1. resolve `target_agent` → system_prompt (§3.3 registry; reject unknown target → typed error, no boot).
  2. `SessionRepository.create_session(session_id=uuid4(), user_id=, tenant_id=parent.tenant_id, title=..., handoff_parent_id=parent_session_id, meta_data={"agent_role": target_agent})`.
  3. mark parent `status="handed_off"` (SessionRepository update; status is free-text String → no enum change).
  4. `append_audit(db, tenant_id=, operation="session.handoff", resource_type="session", resource_id=str(parent_session_id), operation_data={"target_agent", "new_session_id", "reason"}, user_id=)`.
  - **Multi-tenant 鐵律**: child uses parent's `tenant_id`; cross-tenant target forbidden. All within one DB transaction (atomic boot + parent-mark + audit).
- Context transfer = the `handoff_parent_id` LINKAGE only this slice (the child references the parent's messages by the FK); full message-copy/summary carry is a design-note open question (§9).

### 3.3 Persona resolution (US-3) — minimal registry + `handler.py`
- NEW minimal `target_agent → system_prompt` registry (`platform_layer/handoff/persona_registry.py` — a small typed dict, e.g. 2-3 named agents; explicitly a thin stand-in pending a real agent catalog — design-note open question). A `resolve_persona(target_agent) -> str | None`.
- `handler.py` (~:94/:153/:269): resolve per-session persona — if the session has `meta_data["agent_role"]`, resolve it via the registry → system_prompt; else fall back to `DEMO_SYSTEM_PROMPT`. (Without this the booted session would run the demo persona = Potemkin.)

### 3.4 `agent_handoff` SSE event (US-4) — events.py + 57.67 codegen + sse.py
- NEW `AgentHandoff` LoopEvent (Cat 11) in `_contracts/events.py`: `{ target_agent: str, reason: str, parent_session_id: UUID, new_session_id: UUID }` (+ base trace_context). 17.md §4.1 emit-ownership entry.
- Register `agent_handoff` in `backend/src/api/v1/chat/event_wire_schema.py` `WIRE_SCHEMA` (`{ target_agent: string, reason: string, parent_session_id: string, new_session_id: string }`) → run `scripts/codegen/generate_event_schemas.py` → regen `events.json` + `loopEvents.generated.ts` (19 wire-types) → add the `sse.py` serializer branch (`AgentHandoff → agent_handoff`, str(UUID)s). The 57.67 parity test auto-covers the new branch (and the codegen `--check` lint gates the regen).
- The router constructs the `AgentHandoff` event AFTER `boot_handoff` returns (so `new_session_id` is populated), then yields it through the normal `serialize_loop_event` path.

### 3.5 Router wiring (US-2) — `router.py` `_stream_loop_events` (~:280-532)
- In the `LoopCompleted` post-loop hook: if `stop_reason == "handoff"`, call `HandoffService.boot_handoff(...)` (tenant_id + user_id from the request's `TraceContext`/auth), then yield the `AgentHandoff` event. Keep `mark_completed` semantics for the parent (it ended; status now `handed_off`).

### 3.6 DB migration (US-2) — Alembic `0022` (NEW)
- `0022_session_handoff_linkage`: `ALTER TABLE sessions ADD COLUMN handoff_parent_id UUID NULL REFERENCES sessions(id)` + index `idx_sessions_handoff_parent`. No new RLS policy needed (sessions already TenantScopedMixin/RLS; `check_rls_policies` lint stays green — adding a nullable column doesn't change tenant scoping). `status="handed_off"` reuses the existing String column. Persona in `meta_data` JSONB (no column). Down-migration drops the column + index.

### 3.7 Lint / neutrality / doc single-source
- `check_llm_sdk_leak` 0 (service + registry are provider-free; `agent_harness/**` only gets the `loop.py` stop_reason swap + the new `AgentHandoff` dataclass — no SDK). `check_rls_policies` green (`0022` adds a column to an RLS table, not a new table). The new `agent_handoff` wire-type goes through the 57.67 single-source (`event_wire_schema.py`) — no hand-maintained FE drift.
- **Doc single-source**: 17.md §4.1 += `AgentHandoff` emit-ownership; `02-architecture-design.md §SSE` += `agent_handoff` (auto via the 57.67 registry note). The Day-4 design note (`18-handoff-design.md`) is the control-transfer design authority.

### 3.8 Validation (US-5)
- **Integration** (`test_chat_handoff.py` NEW): drive a loop that emits HANDOFF → assert (a) parent `LoopCompleted.stop_reason == "handoff"`; (b) a child session row persisted with `tenant_id == parent.tenant_id`, `handoff_parent_id == parent.id`, `meta_data["agent_role"] == target_agent`; (c) parent `status == "handed_off"`; (d) a `session.handoff` audit row written; (e) an `agent_handoff` SSE frame emitted carrying `new_session_id`. **Multi-tenant**: assert the child session is the parent's tenant + a cross-tenant target is rejected (鐵律).
- **Unit**: loop handoff stop_reason branch; `HandoffService.boot_handoff` (mock db); `resolve_persona` (known + unknown); the 57.67 parity test now covers `agent_handoff` (19 wire-types); persona fallback in `handler.py`.
- **migration**: `alembic upgrade 0022` + `downgrade` clean (Prong-3 verified Day-0).

---

## 4. File Change List

| File | Change |
|------|--------|
| `backend/src/agent_harness/orchestrator_loop/loop.py` | **EDIT** (~:1067-1074) — HANDOFF_NOT_IMPLEMENTED → `LoopCompleted(stop_reason="handoff")` + carry `handoff_request` (US-1) |
| `backend/src/agent_harness/_contracts/events.py` | **EDIT** — NEW `AgentHandoff` LoopEvent (Cat 11) (US-4) |
| `backend/src/platform_layer/handoff/service.py` | **NEW** — `HandoffService.boot_handoff` (child session-boot + parent mark + audit) (US-2) |
| `backend/src/platform_layer/handoff/persona_registry.py` | **NEW** — minimal `target_agent → system_prompt` registry + `resolve_persona` (US-3) |
| `backend/src/api/v1/chat/router.py` | **EDIT** (`_stream_loop_events` post-loop hook) — on `handoff` stop_reason → `boot_handoff` → yield `AgentHandoff` (US-2/US-4) |
| `backend/src/api/v1/chat/handler.py` | **EDIT** (~:94/:153/:269) — resolve per-session persona from `meta_data["agent_role"]` (fallback DEMO) (US-3) |
| `backend/src/api/v1/chat/event_wire_schema.py` | **EDIT** — add `agent_handoff` wire-type (US-4) |
| `frontend/src/features/chat_v2/generated/{events.json, loopEvents.generated.ts}` | **REGEN** (codegen) — 18→19 wire-types (US-4) |
| `backend/src/api/v1/chat/sse.py` | **EDIT** — `AgentHandoff → agent_handoff` serializer branch (US-4) |
| `backend/src/infrastructure/db/models/sessions.py` | **EDIT** — `handoff_parent_id` column on `Session` (US-2) |
| `backend/src/infrastructure/db/repositories/session_repository.py` | **EDIT** — `create_session` accepts `handoff_parent_id` + `meta_data`; a `mark_handed_off` (US-2) |
| `backend/src/infrastructure/db/migrations/versions/0022_session_handoff_linkage.py` | **NEW** — add column + index (US-2) |
| `backend/tests/integration/api/test_chat_handoff.py` | **NEW** — full backend handover (US-5) |
| `backend/tests/unit/...` | **NEW/extend** — loop branch + service + persona + handler fallback + parity (19) (US-5) |
| `docs/03-implementation/agent-harness-planning/17-cross-category-interfaces.md` | **EDIT** §4.1 — `AgentHandoff` emit-ownership |
| `docs/03-implementation/agent-harness-planning/18-handoff-design.md` | **NEW (Day-4 extract)** — control-transfer design note (8-point gate) |
| `claudedocs/4-changes/feature-changes/CHANGE-036-handoff-session-boot.md` | **NEW** — change record |

**No frontend feature work** (FE session-pivot deferred — §9); generated FE files are codegen output only. No Azure-adapter change.

---

## 5. Acceptance Criteria

- A HANDOFF output makes the parent loop end with `stop_reason="handoff"` (no `HANDOFF_NOT_IMPLEMENTED`); the parsed target_agent + reason reach the router.
- The handoff service boots a child session persisted with: parent's `tenant_id`, `handoff_parent_id`=parent, `meta_data["agent_role"]`=target_agent; the parent session `status="handed_off"`; a `session.handoff` audit row written; all atomic.
- A booted session resolves + runs under the target persona (not DEMO) via `handler.py` + the minimal registry; an unknown target_agent is rejected (no orphan session).
- An `agent_handoff` SSE event (target_agent, reason, parent_session_id, new_session_id) is emitted through the 57.67 wire path; `WIRE_SCHEMA` has 19 entries; codegen `--check` green; the parity test covers `agent_handoff`.
- Alembic `0022` upgrades + downgrades clean; `check_rls_policies` green; **multi-tenant**: cross-tenant handoff rejected, child session tenant-scoped.
- All existing tests green; `mypy --strict src/` 0; 10/10 V2 lints (LLM SDK leak 0); Vitest 697 unchanged (generated regen only). Day-4 design note passes the 8-point gate.

---

## 6. Deliverables

- [ ] `loop.py` HANDOFF stop_reason swap (US-1)
- [ ] `events.py` `AgentHandoff` LoopEvent (US-4)
- [ ] `platform_layer/handoff/service.py` `boot_handoff` (US-2)
- [ ] `platform_layer/handoff/persona_registry.py` minimal registry (US-3)
- [ ] `router.py` post-loop handoff hook + `handler.py` persona resolution (US-2/US-3)
- [ ] `event_wire_schema.py` `agent_handoff` + codegen regen + `sse.py` branch (US-4)
- [ ] `sessions.py` + `session_repository.py` + Alembic `0022` (US-2)
- [ ] integration `test_chat_handoff.py` + unit tests + multi-tenant (US-5)
- [ ] 17.md §4.1 emit-ownership; `18-handoff-design.md` Day-4 design note (8-point gate) (US-5)
- [ ] CHANGE-036 + progress.md + retrospective.md

---

## 7. Workload Calibration

Scope class: **`backend-control-transfer-spike` (0.55, NEW — pending validation)** — a backend SPIKE introducing a new control-transfer mechanism (loop + platform session-boot + new event + migration + persona registry) with a mandatory Day-4 design note; analogous to the existing `frontend-arch-spike` 0.50 / `iam-frontend-spike` 0.60 spike classes. **Agent-delegated: yes** (staged: Stage-1 backend core — migration + service + persona + loop swap + event dataclass; Stage-2 SSE wiring + codegen regen + router/handler + tests; design note parent-authored). `agent_factor` **`mechanical-greenfield-design-decisions` 0.65** (genuine design: event plumbing, persona registry, service transaction, layering).

> Bottom-up est ~16 hr → class-calibrated commit ~8.8 hr (mult 0.55) → agent-adjusted commit ~5.7 hr (agent_factor 0.65).

Caveat (carried 57.63-57.67): agent-delegated sprints have no clean wall-clock (`AD-Calibration-AgentDelegated-WallClock-Measure`; would be 6th consecutive). The NEW `backend-control-transfer-spike` class is a single unvalidated data point — record caveated, do NOT generalize. If the integration proves larger than one sprint at Day-1, slice (defer persona registry to a 1-agent stub, or split the migration) and re-confirm scope.

---

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **D1 — HANDOFF ≠ delegate-and-return; pure tool-wiring is a Potemkin (AP-4)** | this sprint does the real control transfer (loop stop_reason + platform session-boot); the booted session is real (persisted, persona-resolved, observable) |
| **D2 — gap is loop + platform, not dispatcher** | `loop.py` minimal stop_reason swap; session-boot in a NEW platform service; `dispatcher.handoff()`/`HandoffExecutor` reused as-is (no rewrite) |
| **D3 — sessions schema lacks linkage** | Alembic `0022` adds `handoff_parent_id` FK + index; `status="handed_off"` reuses the String column; persona in `meta_data` (no column) — Prong-3 verified Day-0 |
| **D4 — no persona registry exists** | spike defines a MINIMAL `target_agent → system_prompt` registry (thin stand-in; design-note open question — a real agent catalog is future work); `handler.py` falls back to DEMO when no `agent_role` |
| **D5 — new SSE event** | `AgentHandoff` via the 57.67 single-source (`event_wire_schema.py` + codegen + parity) — no hand-maintained FE drift; event constructed post-boot so `new_session_id` is populated |
| **Multi-tenant leakage** | child session created with the parent's `tenant_id`; cross-tenant target rejected; integration test asserts tenant scoping + rejection (鐵律 1) |
| **Atomicity** (partial boot: child created but parent not marked / no audit) | `boot_handoff` runs child-create + parent-mark + audit in ONE DB transaction; test the rollback-on-error path |
| **Potemkin booted session** (session exists but never runs the target) | `handler.py` per-session persona resolution makes the child actually run the target persona; integration asserts persona resolved |
| **Scope > 1 sprint** (the user chose the multi-sprint B) | this slice is backend-complete only; FE pivot + full context-carry + multi-hop deferred (§9); Day-1 slice further if needed (§7) |
| **`LoopCompleted` shape / `handoff_request` object** | Day-0 Prong-2 reads the exact `LoopCompleted` fields + the output parser's `handoff_request` before the loop edit (`AD-Day0-Codegen-Existing-Shape-Capture` lesson — read the real shape) |
| **Migration head / RLS** | Day-0 Prong-3 confirmed next number `0022`; `check_rls_policies` green (column add, not new table) |
| **LLM-neutrality** | service + registry provider-free; `agent_harness/**` only gets the dataclass + stop_reason; `check_llm_sdk_leak` gates |

---

## 9. Out of Scope (this sprint; carryover toward full Option B)

- **Frontend session-pivot UI** — the client following the handoff to `new_session_id` (the FE half of Option B). Distinct follow-up sprint; this slice emits the `agent_handoff` event the FE will consume.
- **Full message-context carry / summary** — this slice links child→parent via `handoff_parent_id` (the child can reference the parent's messages); copying/summarizing the conversation into the child is a design-note open question.
- **Target auto-first-turn** — whether the target agent auto-runs a turn on boot vs runs on the next client request (this slice = runs on next request to `new_session_id`).
- **Multi-hop handoff chains** (A→B→C) + handoff loop/cycle guards — design-note open question.
- **Real agent/persona catalog** — the minimal `target_agent → system_prompt` registry is a thin stand-in; a real catalog (DB-backed, per-tenant agents) is future work.
- **`sessions.agent_role` dedicated column** — persona stored in `meta_data` JSONB this slice (YAGNI; a column is a future refinement if querying-by-agent is needed).
- **`loop.py` control-flow rewrite** — only the stop_reason swap; no nested-loop / re-entrancy changes.
