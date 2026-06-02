# CHANGE-036: HANDOFF Control-Transfer + Platform Session-Boot (A-3b backend slice)

**Date**: 2026-06-02
**Sprint**: 57.68
**Scope**: Cat 11 (Subagent Orchestration — HANDOFF) + platform-layer session-boot + Cat 1 (loop stop_reason) + Cat 12 (`agent_handoff` SSE event) + sessions DB (Alembic 0022) + governance (audit)

## Change Summary
Ships the 4th Cat 11 subagent mode — **HANDOFF** — as a real control transfer on the production chat path (backend-complete slice toward the user-chosen full platform session-boot model). When the agent emits a HANDOFF, the parent loop ends with `stop_reason="handoff"`, a new platform service boots a persisted, tenant-scoped, linked, audited child session for the target agent (running under a resolved persona), and an `agent_handoff` SSE event is emitted. Frontend session-pivot is deferred (a follow-up sprint). This is a SPIKE — see the design note `docs/03-implementation/agent-harness-planning/18-handoff-design.md` (8-point gate).

## Change Reason
57.64 (A-3a) shipped FORK/TEAMMATE/AS_TOOL and excluded HANDOFF because — unlike those delegate-and-return modes — HANDOFF is a control transfer (`01-eleven-categories-spec.md:1080` "完全交棒，父 agent 退出") that `loop.py` dead-ended with `HANDOFF_NOT_IMPLEMENTED`. A pure tool/allow-list wiring would return a session id nobody boots = Potemkin (AP-4). Real HANDOFF needs a loop stop_reason + a platform session-boot.

## Detailed Changes
- **`loop.py`** — `OutputType.HANDOFF` branch swapped from `HANDOFF_NOT_IMPLEMENTED` to `LoopCompleted(stop_reason="handoff", handoff_target, handoff_reason)`; target/reason read from the `handoff` tool_call's `arguments` (Day-0 correction: there is no `response.handoff_request` — it's a tool call). `TerminationReason.HANDOFF="handoff"` (removed dead `HANDOFF_NOT_IMPLEMENTED`).
- **`_contracts/events.py`** — `LoopCompleted` += optional `handoff_target`/`handoff_reason`; NEW `AgentHandoff` LoopEvent (Cat 11) `{target_agent, reason, parent_session_id, new_session_id}`.
- **`platform_layer/handoff/service.py`** (NEW) — `HandoffService.boot_handoff` (atomic: resolve persona → tenant guard → create child session [parent tenant_id, `handoff_parent_id`, `meta_data["agent_role"]`] → mark parent `handed_off` → `append_audit("session.handoff")`). `HandoffError` on unknown target / foreign parent.
- **`platform_layer/handoff/persona_registry.py`** (NEW) — minimal `target_agent → system_prompt` map (researcher/reviewer/planner; thin stand-in — design-note open question).
- **`api/v1/chat/router.py`** — post-loop hook: on `handoff` stop_reason → `boot_handoff` → emit `AgentHandoff` (fail-soft on `HandoffError`).
- **`api/v1/chat/handler.py`** — `resolve_session_persona` (per-session persona from `meta_data["agent_role"]`, fallback DEMO); builders accept `system_prompt`.
- **`api/v1/chat/event_wire_schema.py`** + codegen — `agent_handoff` wire-type (18→19); regen `events.json` + `loopEvents.generated.ts`. **`sse.py`** — `AgentHandoff → agent_handoff` branch.
- **`infrastructure/db`** — `Session.handoff_parent_id`; `SessionRepository.create_session(+handoff_parent_id,+meta_data)` + `mark_handed_off`; Alembic `0022_session_handoff_linkage` (FK + index).

## Verification
- Backend: full `pytest tests/unit tests/integration` **1999 passed / 4 skipped / 0 failed**; integration `test_chat_handoff.py` **5 passed** (success frame + child persisted/tenant-scoped/linked + parent handed_off + audit + cross-tenant reject + fail-soft); parity **19** wire-types; `mypy src/` **0/324**; `run_all.py` **10/10** (SDK leak 0, RLS green); Alembic `0022` up/down/re-up clean.
- Frontend: `tsc` 0; `vitest` 698; build ✓ (generated regen + `chatStore` `agent_handoff` passthrough).
- Multi-tenant 鐵律: child uses parent's tenant_id; cross-tenant target → `HandoffError` (no child, parent unmutated).

## Impact
loop/events/sessions/repo/router/handler/sse/event_wire_schema + new `platform_layer/handoff/` + Alembic 0022 + codegen regen + FE `chatStore` passthrough. The Cat 11 dispatcher is untouched (other 3 modes unaffected). Bundled bug fix: FIX-026 (test-isolation leak surfaced by the new endpoint DB call). FE session-pivot + full context-carry + multi-hop + real persona catalog = deferred (design note §5).
