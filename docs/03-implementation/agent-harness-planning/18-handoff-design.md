# 18 — HANDOFF Control-Transfer + Platform Session-Boot (Design Note)

**Purpose**: Authoritative design for Cat 11 HANDOFF — the 4th subagent mode — as a real control transfer (parent agent exits, a new persisted child session boots for the target agent). Extracted from the Sprint 57.68 (A-3b) backend-slice implementation per `sprint-workflow.md §Step 5.5` (spike → design-note extract).
**Category / Scope**: Cat 11 (Subagent Orchestration — HANDOFF) + platform-layer session-boot + Cat 1 (loop stop_reason) + Cat 12 (`agent_handoff` SSE event); Phase 57.68
**Created**: 2026-06-02
**Status**: Active (slice 1 backend control-transfer shipped 57.68; slice 2 agent-side context carry + FE session-pivot shipped 57.69 — §8; user-visible transcript continuity remains an Open Invariant §5)
**Author**: Sprint 57.68 A-3b (slice 1) + Sprint 57.69 A-3b (slice 2)

> **Modification History**
> - 2026-06-02: Sprint 57.69 — add §8 (slice 2: agent-side context carry + FE session-pivot); update §5 (FE pivot + agent-side carry now verified; user-visible transcript continuity still deferred)
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

**Verified — slice 1 (57.68)**: loop control transfer; atomic tenant-scoped session-boot; parent handed-off + linked + audited; persona resolution on the booted child; `agent_handoff` SSE event; cross-tenant rejection.

**Verified — slice 2 (57.69, §8)**: agent-side context carry (the parent's in-memory conversation is snapshotted at HANDOFF, capped, and seeded into the target's persona prompt so the target runs with the prior conversation); FE session-pivot (the `agent_handoff` event pivots the active chat session to `new_session_id` + a transition banner).

**Deferred (NOT verified — toward full Option B / future)**:
- **User-visible transcript continuity** — the pivoted UI showing the parent's prior MESSAGES (slice 2 carries agent-side context into the target's prompt + pivots the session, but the child's chat window starts visually empty + a banner). This needs a message-persistence subsystem (writer + `MessageRepository` + `GET sessions/{id}/messages` + FE history loader) — conversation messages are never persisted today (the `messages` table is dormant; the FE rebuilds the transcript from the live SSE stream). 2+ sprints; its own epic.
- **Summarize-carry (copy-vs-summarize)** — slice 2 carries a message-count-capped VERBATIM copy; summarizing the parent conversation via the Cat-4 `SemanticCompactor` is a design alternative (§8.4), not built.
- **Target auto-first-turn** — the target agent runs on the NEXT client request to `new_session_id`, not auto-run on boot.
- **Multi-hop handoff chains** (A→B→C) + cycle/loop guards — unbuilt.
- **Real agent/persona catalog** — `persona_registry.py` is a 3-entry hardcoded stand-in; a DB-backed per-tenant catalog (custom personas, allowed tools, memory scopes, risk limits) is future work.
- **`sessions.agent_role` / `carried_context` dedicated columns** — persona + carried context are in `meta_data` JSONB; columns are a future refinement if querying-by-agent / large-context offloading is needed.

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

---

## 8. Slice 2 (Sprint 57.69) — Agent-Side Context Carry + FE Session-Pivot

### 8.1 Summary (maps to the slice-2 user stories)

Slice 1 (57.68) carried only the parent→child FK linkage; the booted child ran the target persona but with NO prior conversation, and the FE only recorded `agent_handoff` in `rawEvents` (no pivot). Slice 2 closes the **agent-side** half of "context carry" + the **FE pivot**:

- **US-1 loop context snapshot** — the loop snapshots the parent's in-memory conversation at HANDOFF and carries it to the platform layer.
- **US-2 platform context-carry storage** — `boot_handoff` stores a capped verbatim copy in the child's `meta_data["carried_context"]`.
- **US-3 handler seeds the carried context** — the child's persona prompt is extended with the carried conversation so the target agent runs with the prior context.
- **US-4 FE session-pivot + banner** — the `agent_handoff` event pivots the active session to `new_session_id` + a transition banner.

### 8.2 Decision Matrix — context-carry path (user decision, AskUserQuestion 2026-06-02, after a >50% Day-0 drift)

A >50% Day-0 reality drift broke the original "copy persisted parent messages into the child" premise: **conversation messages are NEVER persisted** — the `Message` ORM (`infrastructure/db/models/sessions.py:141-195`) is never written on the chat path (no `MessageRepository`, no reader/writer); the conversation lives only in the in-memory `LoopState.messages`, and the FE rebuilds the transcript purely from the live SSE stream (`chat_v2` has no history-fetch). "context carry" therefore splits into (i) **agent-side context** (the target's prompt includes the prior conversation) and (ii) **user-visible transcript continuity** (the pivoted UI shows the old messages).

| Option | What | Verdict |
|--------|------|---------|
| **C-1 — agent-side carry (1 sprint)** ✅ | snapshot the in-memory conversation at HANDOFF → seed it into the target's persona prompt; FE pivots + banner | **chosen** — delivers "the target runs with the prior conversation" without a persistence subsystem |
| C-2 — build message persistence first (2+ sprints) | writer + `MessageRepository` + `GET sessions/{id}/messages` + FE history loader, THEN copy parent→child | rejected for this slice — its own epic; violates thin-spike / YAGNI |
| C-3 — pivot-only | FE pivot + banner, child starts with NO context | rejected — drops the user-wanted context carry |

### 8.3 Verified Invariants (each with file:line)

1. **Loop snapshots the in-memory conversation** — `loop.py:1090`: the 57.68 HANDOFF branch's `LoopCompleted(...)` now also passes `handoff_context=list(messages)` (a shallow copy of the in-memory conversation `messages` local). `LoopCompleted.handoff_context: list[Message] | None = None` is an additive field in `_contracts/events.py:162` — **in-process only**: the `sse.py` `loop_end` serializer (`sse.py:208-217`) maps only `stop_reason/total_turns/cached_input_tokens/cache_hit_rate`, so `handoff_context` never reaches the client wire (an integration test asserts the `loop_end` frame has no `handoff_context`).
2. **Capped verbatim carry, LLM-neutral** — `platform_layer/handoff/context_carry.py` `cap_and_serialize(messages, *, max_messages=DEFAULT_MAX_CARRY_MESSAGES)` keeps the LAST `max_messages` (=20; drop-oldest over budget — a message COUNT, not a token budget, so the module is `ChatClient`-free / provider-free) and maps each `Message` to `{"role", "content"}` (`_render_content` flattens `str | list[ContentBlock]` to text). `render_carried_context_block` renders the stored dicts into a system-prompt block. `check_llm_sdk_leak` 0 (imports only the neutral `Message`/`ContentBlock`).
3. **Storage = `meta_data["carried_context"]`, no migration** — `HandoffService.boot_handoff` (`service.py`) gains `parent_context: list[Message] | None = None`; inside the existing atomic transaction it sets `meta_data["carried_context"] = cap_and_serialize(parent_context)` only when non-empty (else the 57.68-identical `{"agent_role": …}` — backward-compatible). The `meta_data` JSONB column already exists (no Alembic migration). The carry is part of the same parent-tenant-scoped atomic boot (multi-tenant 鐵律 — never cross-tenant).
4. **Router passes the snapshot** — `router.py:504`: the 57.68 post-loop hook now calls `boot_handoff(..., parent_context=event.handoff_context)` (fail-soft unchanged).
5. **Handler seeds the carried context into the persona prompt** — `handler.py:398-418` `resolve_session_persona` reads `session.meta_data["carried_context"]` (alongside `agent_role`) and appends `render_carried_context_block(carried)` to the resolved persona system prompt. A NESTED fail-open guard ensures a malformed `carried_context` never crashes and never loses the resolved persona. This delivers "the target agent runs with the prior conversation in its prompt" — chosen over seeding `LoopState.messages` directly (Day-0 D-DAY0-3: avoids tool_call_id structural fragility; reuses the existing persona-resolution path).
6. **FE session-pivot** — `chat_v2/store/chatStore.ts`: the `agent_handoff` case (was a `rawEvents`-only passthrough) now calls a pure `applyPivot(s, ev.data.new_session_id, {targetAgent, reason}, rawEvents)` that preserves the sidebar `sessions` + `mode`, keeps the accumulated `rawEvents`, resets the conversation slices (turns/status/counters/approvals/verifications/subagents), and points BOTH `sessionId` and `activeSessionId` at the child (they were unlinked). `pivotSession`/`dismissHandoffBanner` actions + `handoffBanner` state (cleared on the next `loop_start`). `HandoffBanner.tsx` renders the transition notice from existing `.badge.info`/`.btn.ghost` primitives (AP-2: no mockup source). Arrives post-stream (after `loop_end`) so there is no mid-stream abort race.

### 8.4 Copy-vs-summarize tradeoff (design decision)

The carry is a message-count-capped (last-20) VERBATIM copy. The alternative — summarizing the parent conversation via the Cat-4 `SemanticCompactor` (`context_mgmt/compactor/semantic.py:67`, LLM-neutral, `chat_client`-injected) — is deferred because: (a) `SemanticCompactor.compact_if_needed` is `LoopState`-shaped, not `list[Message]` (needs an adapter); (b) it requires an LLM call in the carry path, coupling `boot_handoff` to a `ChatClient` (slice 2 keeps the platform service `ChatClient`-free); (c) verbatim is simpler + lossless for short conversations. Summarize-carry becomes attractive when conversations routinely exceed the cap — a future refinement (token-budget cap via `ChatClient.count_tokens` + summarize the overflow).

### 8.5 Rollback (slice 2 delta)

Low-risk, additive-only (NO migration): revert the `loop.py:1090` snapshot + the `events.py` `handoff_context` field, `context_carry.py` (delete — new file), the `service.py` `parent_context` param + `meta_data["carried_context"]` write, the `router.py:504` pass-through, and the `handler.py` carried-block append. FE: revert the `chatStore.ts` `applyPivot`/`pivotSession`/`handoffBanner` + the `agent_handoff` case (back to `rawEvents`-only passthrough), delete `HandoffBanner.tsx`, un-mount it in `ChatLayout.tsx`, and revert the `HEX_OKLCH_BASELINE` 50→48. No data migration (existing `carried_context` keys in `meta_data` become inert). Slice 1 (control transfer + session-boot) is untouched.

### 8.6 Verification (reproducible)

- Backend integration: `cd backend && python -m pytest tests/integration/api/test_chat_handoff.py -q` → carried_context populated/capped/tenant-scoped + `loop_end` has no `handoff_context` + `resolve_session_persona` embeds the carried block.
- Backend unit: `cd backend && python -m pytest tests/unit/platform_layer/handoff/test_context_carry.py -q` (10) + `test_service.py` (carry with/without parent_context) + `tests/unit/api/v1/chat/test_chat_handoff_unit.py` (persona seed present/absent/malformed).
- Full backend sweep: `python -m pytest tests/unit tests/integration -q` → 2015 passed / 4 skipped / 0 failed; `mypy src/` 0/325; `python scripts/lint/run_all.py` 10/10 (no codegen drift — `WIRE_SCHEMA` 19).
- Frontend: `cd frontend && npm run check:mockup-fidelity` (50=50) + `npm run lint` (exit 0) + `npm run test` (709 passed) + `npm run build`. Tests: `tests/unit/chat_v2/chatStore.mergeEvent.test.ts` (+8 pivot) + `tests/unit/chat_v2/components/HandoffBanner.test.tsx` (3).

### 8.7 Cross-Category Contracts (17.md single-source)

No new wire contract: `agent_handoff` (the only Cat 11 handoff wire-type) was registered in `17-cross-category-interfaces.md §4.1` by slice 1 and is **unchanged** by slice 2 (slice 2 consumes it on the FE; the carry is server-side via `meta_data`). `LoopCompleted.handoff_context` is an **in-process carrier**, NOT a cross-category wire contract (it never serializes to the client — §8.3 inv. 1), so it is intentionally not registered in 17.md. No new ABC; the Cat 4 `SemanticCompactor` is referenced as a deferred alternative only (§8.4), not wired.
