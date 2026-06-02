# 18 — HANDOFF Control-Transfer + Platform Session-Boot (Design Note)

**Purpose**: Authoritative design for Cat 11 HANDOFF — the 4th subagent mode — as a real control transfer (parent agent exits, a new persisted child session boots for the target agent). Extracted from the Sprint 57.68 (A-3b) backend-slice implementation per `sprint-workflow.md §Step 5.5` (spike → design-note extract).
**Category / Scope**: Cat 11 (Subagent Orchestration — HANDOFF) + platform-layer session-boot + Cat 1 (loop stop_reason) + Cat 12 (`agent_handoff` SSE event); Phase 57.68
**Created**: 2026-06-02
**Status**: Active (backend slice shipped; FE session-pivot + full context-carry are Open Invariants §5)
**Author**: Sprint 57.68 A-3b

> **Modification History**
> - 2026-06-02: Initial extract from the Sprint 57.68 A-3b backend-slice implementation (verified-ratio target ≥95%)

---

## 1. Spike Summary (maps to the A-3b user stories)

A HANDOFF is a **control transfer**, not a delegate-and-return: per `01-eleven-categories-spec.md:1080` (`HANDOFF = "handoff" # 完全交棒，父 agent 退出`) the parent agent exits and the target agent takes over the conversation. This is structurally unlike FORK/TEAMMATE/AS_TOOL (which spawn a child and merge its result back). Before this sprint `loop.py` dead-ended HANDOFF with a `HANDOFF_NOT_IMPLEMENTED` terminator; 57.64 (A-3a) shipped the other 3 modes and explicitly excluded HANDOFF for exactly this reason.

This backend slice (the first toward the user-chosen full platform session-boot model) wires HANDOFF end-to-end on the production `POST /api/v1/chat/` path:

- **US-1 loop control transfer** — the loop ends the parent with `stop_reason="handoff"` carrying the target.
- **US-2 platform session-boot** — a new platform service boots a persisted, tenant-scoped, linked, audited child session for the target.
- **US-3 persona resolution** — the booted child runs under the target persona (not the demo persona).
- **US-4 `agent_handoff` SSE event** — the handover is observable (target + new_session_id).
- **US-5 validation + this design note.**

Frontend session-pivot, full message-context carry, target auto-first-turn, and multi-hop chains are **deferred** (§5).

---

## 2. Decision Matrix

### 2.1 Spike depth (user decision, AskUserQuestion 2026-06-02)

| Option | What | Verdict |
|--------|------|---------|
| **A — in-loop persona swap, same session** | loop re-enters under the target persona within the SAME session | rejected by user — not the "new session" semantics they want |
| **B — full platform session-boot** ✅ | new persisted child session, context transfer, FE pivot, parent handed-off + audit | **chosen** (multi-sprint; this sprint = backend-complete slice) |
| **C — mechanism-only, hardcoded target** | loop transfer to one hardcoded persona, no resolution | rejected — too thin to be useful |
| ~~D — dispatcher/tool-only wiring (like A-3a)~~ | register a `handoff` tool, loop still terminates | **forbidden** — returns a UUID nobody boots = Potemkin (AP-4); Day-0 D3 REFUTED a pure allow-list extension |

### 2.2 Where the handoff target comes from (Day-0 correction)

The plan assumed `response.handoff_request`; the **real** mechanism is a tool call named `handoff` (`HANDOFF_TOOL_NAME`, see `output_parser/classifier.py`). `classify_output(response)` (`loop.py:1048`) returns `OutputType.HANDOFF`; the target is in the `handoff` tool_call's `arguments` dict (`{"target_agent", "reason"}`), extracted at `loop.py:1082-1091`.

### 2.3 Persona resolution — minimal registry vs catalog

No agent/persona registry exists (Day-0 D4: the Phase-48 7 YAML configs are policy configs; the chat path uses one hardcoded `DEMO_SYSTEM_PROMPT` at `handler.py:95`). This slice defines a **minimal hardcoded `target_agent → system_prompt` registry** (`platform_layer/handoff/persona_registry.py` — researcher/reviewer/planner) as a thin stand-in. A real DB-backed per-tenant agent catalog is Open Invariant §5; `resolve_persona()` keeps its signature so the catalog can replace the dict.

### 2.4 Persistence shape — column vs JSONB (Day-0 D3)

`sessions.status` is a free-text `String(32)` (not a DB enum) → holds `"handed_off"` with no type change. The parent→child linkage needs referential integrity → a real FK column `handoff_parent_id` (Alembic `0022`). The persona is non-relational → stored in `sessions.meta_data["agent_role"]` (JSONB, no column; YAGNI — a dedicated `agent_role` column is a future refinement).

---

## 3. Verified Invariants (each with file:line)

1. **Loop ends with `handoff` stop_reason** — `loop.py:1073-1091`: `OutputType.HANDOFF` → `LoopCompleted(stop_reason=TerminationReason.HANDOFF.value, handoff_target=…, handoff_reason=…)`; target/reason from the `handoff` tool_call's `arguments` (None-safe default `{}`). `TerminationReason.HANDOFF = "handoff"` in `orchestrator_loop/termination.py` (old `HANDOFF_NOT_IMPLEMENTED` removed — grep-confirmed only 3 sites). `LoopCompleted.handoff_target/handoff_reason` are additive optional fields in `_contracts/events.py` (do not affect the `loop_end` serializer).
2. **Platform session-boot is atomic + tenant-safe** — `platform_layer/handoff/service.py:87-174` `HandoffService.boot_handoff`: (1) `resolve_persona` first (unknown → `HandoffError`, NO write); (2) one transaction (`db.begin_nested()` if in a transaction else `db.begin()`); (3) tenant guard `repo.get_session(session_id=parent, tenant_id=tenant_id)` (foreign/missing parent → `HandoffError`, no orphan child); (4) `create_session` with the **parent's** `tenant_id`, `handoff_parent_id=parent`, `meta_data={"agent_role": target_agent}`; (5) `mark_handed_off`; (6) `append_audit(operation="session.handoff", …)`. Multi-tenant 鐵律: child inherits parent tenant; cross-tenant rejected.
3. **Booted child runs the target persona** — `handler.py:369` `resolve_session_persona(db, session_id, tenant_id)`: reads `session.meta_data["agent_role"]` → `resolve_persona` → target system_prompt; falls back to `DEMO_SYSTEM_PROMPT` on any miss (no db / no row / no agent_role / unknown role / error — fail-open). The builders (`build_real_llm_handler`/`build_handler`) accept `system_prompt`, threaded into `AgentLoopImpl`.
4. **`agent_handoff` is observable** — `event_wire_schema.py` `WIRE_SCHEMA["agent_handoff"]` = `{target_agent, reason, parent_session_id, new_session_id}` (the 57.67 single source; 18→19 wire-types); `sse.py` `AgentHandoff → agent_handoff` branch (UUIDs via `str()`); the router constructs the `AgentHandoff` event POST-boot (so `new_session_id` is populated) and serializes it through the normal path.
5. **Router post-loop hook, fail-soft** — `router.py:488-538` `_stream_loop_events`: on `LoopCompleted.stop_reason == "handoff" and db is not None and event.handoff_target` → `HandoffService().boot_handoff(...)` (tenant_id/user_id from `TraceContext`) → yield serialized `AgentHandoff`. `HandoffError` → log + emit nothing; any other exception → log + emit nothing (the stream never crashes); empty target → service never called.
6. **Migration `0022`** — `0022_session_handoff_linkage` (`down_revision="0021_rate_limit_alerts"`): `sessions.handoff_parent_id UUID NULL FK→sessions.id ON DELETE SET NULL` + `idx_sessions_handoff_parent`; no new RLS (column-add on an existing RLS table — `check_rls_policies` green). Verified upgrade→downgrade→re-upgrade clean against live Postgres.

---

## 4. Cross-Category Contracts (17.md single-source)

- **New event `AgentHandoff`** (Cat 11) — registered in `17-cross-category-interfaces.md §4.1` emit-ownership (loop/router emit; SSE serializer + FE consume). Wire-type `agent_handoff` is the only doc delta in `02-architecture-design.md §SSE` (auto via the 57.67 registry).
- **No new ABC** — `HandoffService` is a platform-layer concrete service (not a cross-category contract); the Cat 11 `dispatcher.handoff()`/`HandoffExecutor` are reused unchanged (the loop+platform own the real transfer, not the dispatcher).
- **`SessionRepository`** extended (`create_session` += `handoff_parent_id`/`meta_data`; new `mark_handed_off`) — infrastructure, not a Cat contract.

---

## 5. Open Invariants (verified in this slice vs deferred — NOT verified)

**Verified in this slice**: loop control transfer; atomic tenant-scoped session-boot; parent handed-off + linked + audited; persona resolution on the booted child; `agent_handoff` SSE event; cross-tenant rejection.

**Deferred (NOT verified — toward full Option B / future)**:
- **Frontend session-pivot** — the client following `new_session_id` to continue the conversation in the child session. The `agent_handoff` event is emitted + lands in `chat_v2` `rawEvents` (no Inspector UI). This is the FE half of Option B — a distinct follow-up sprint.
- **Full message-context carry** — this slice transfers only the `handoff_parent_id` LINKAGE (the child can reference the parent's messages); copying/summarizing the conversation into the child is unbuilt.
- **Target auto-first-turn** — the target agent runs on the NEXT client request to `new_session_id`, not auto-run on boot.
- **Multi-hop handoff chains** (A→B→C) + cycle/loop guards — unbuilt.
- **Real agent/persona catalog** — `persona_registry.py` is a 3-entry hardcoded stand-in; a DB-backed per-tenant catalog (custom personas, allowed tools, memory scopes, risk limits) is future work.
- **`sessions.agent_role` dedicated column** — persona is in `meta_data` JSONB this slice.

---

## 6. Rollback

Low-risk, ~1 day: revert the `0022` migration (drop `handoff_parent_id` + index — nullable, no data dependency), the `router.py` post-loop hook, the `loop.py` stop_reason swap (restore a terminate-without-boot), `handler.py` persona resolution (always DEMO), and the `agent_handoff` wire-type (registry + codegen regen + sse.py branch). `HandoffService` + `persona_registry` become dead code (delete). No data migration needed (handed-off sessions revert to inert rows; `handoff_parent_id` becomes an unused nullable column until dropped). The Cat 11 dispatcher is untouched, so the other 3 modes are unaffected.

---

## 7. References

- `01-eleven-categories-spec.md §範疇 11` (HANDOFF = 完全交棒) — the semantic authority.
- `17-cross-category-interfaces.md §4.1` — `AgentHandoff` emit-ownership.
- `02-architecture-design.md §SSE` — `agent_handoff` wire-type (generated from `event_wire_schema.py` per 57.67).
- `sprint-57-68-plan.md` / `…-checklist.md` / `agent-harness-execution/phase-57/sprint-57-68/{progress,retrospective}.md`.
- `CHANGE-036-handoff-session-boot.md` + `FIX-026-handoff-persona-conn-leak.md`.

### Verification commands (reproducible)
- Integration: `cd backend && python -m pytest tests/integration/api/test_chat_handoff.py -q` → 5 passed (success frame + child persisted/tenant-scoped/linked + parent handed_off + audit + cross-tenant reject + router-hook fail-soft).
- Unit (persona): `cd backend && python -m pytest tests/unit/api/v1/chat/test_chat_handoff_unit.py -q` → 6 passed.
- Parity: `cd backend && python -m pytest tests/unit/api/v1/chat/test_event_wire_schema_parity.py -q` → green (19 wire-types).
- Full sweep: `cd backend && python -m pytest tests/unit tests/integration -q` → 1999 passed / 4 skipped / 0 failed; `mypy src/` 0/324; `python scripts/lint/run_all.py` 10/10; `python scripts/codegen/generate_event_schemas.py --check` exit 0.
- Test fixtures: `tests/integration/api/test_chat_handoff.py` (`_HandoffLoop` fake loop + `db_session` + `seed_tenant`/`seed_user`); `tests/conftest.py` `db_session` (function-scoped, `dispose_engine()` teardown).
