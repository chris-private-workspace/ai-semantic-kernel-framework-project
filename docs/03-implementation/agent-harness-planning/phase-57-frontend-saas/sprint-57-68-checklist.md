# Sprint 57.68 — Checklist (HANDOFF Control-Transfer + Platform Session-Boot — A-3b backend slice)

**Plan**: [`sprint-57-68-plan.md`](./sprint-57-68-plan.md)
**Created**: 2026-06-02
**Status**: Complete (commit/push/PR user-gated)

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> SPIKE → Day-4 design-note extract + 8-point gate (`18-handoff-design.md`). Scope: Option B full platform session-boot; backend-complete slice (FE pivot deferred — plan §9).

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify
- [x] **Prong 1 (path)**: loop.py:1067-1074 HANDOFF + :1048 classify_output(response) + parser→OutputType.HANDOFF; subagent dispatcher/modes; sessions.py:73-122; session_repository.py:50-85; router/handler/sse/event_wire_schema; audit_helper.py:90-102; `platform_layer/handoff/` absent
- [x] **Prong 2 (content)**: `response` in scope at HANDOFF branch → target reachable; `LoopCompleted` fields → ADD optional handoff_target/reason (additive); create_session/append_audit/handler DEMO insertion + AgentSpec shapes (researcher round 2)
- [x] **Prong 3 (schema)**: `status` String(32) free-text holds "handed_off"; tenant_id TenantScopedMixin; meta_data JSONB "metadata" alias; next migration `0022`; RLS column-add no new policy
- [x] **Doc-location**: 17.md §4.1 (add AgentHandoff); design note → `18-handoff-design.md`
- [x] Catalogued D-DAY0-1..6 in progress.md; **go/no-go = GO**

### 0.2 Branch + decisions
- [x] Branch `feature/sprint-57-68-handoff-session-boot` from `0439235e`; plan+checklist (`23bbb2af`); Day-0 progress (`e89ba1ed`)
- [x] Scope: backend slice (FE deferred); context-transfer = linkage only; persona in meta_data (no column); migration `0022` = handoff_parent_id FK+index; minimal persona registry; **Agent-delegated: yes** (Stage-1 core / Stage-2 SSE+router+tests; design note parent-authored); live Postgres pre-checked

---

## Day 1 — Backend core (Stage 1)

### 1.1 DB migration + ORM (US-2)
- [x] `0022_session_handoff_linkage`: `handoff_parent_id` FK→sessions(id) ON DELETE SET NULL + index; up/down/re-up clean vs live Postgres
- [x] `Session` ORM += handoff_parent_id; `SessionRepository.create_session(+handoff_parent_id,+meta_data)` + `mark_handed_off`

### 1.2 Persona registry (US-3)
- [x] `platform_layer/handoff/persona_registry.py` — `target_agent → system_prompt` (researcher/reviewer/planner) + `resolve_persona`; thin stand-in (design-note open question)

### 1.3 Handoff service (US-2)
- [x] `HandoffService.boot_handoff` — atomic (begin_nested/begin); resolve persona first (unknown→HandoffError); tenant guard; create child (parent tenant_id, handoff_parent_id, meta_data agent_role); mark handed_off; append_audit("session.handoff"); unit-tested (mock db + cross-tenant + unknown-target + rollback)

### 1.4 Loop stop_reason swap (US-1)
- [x] `loop.py:1073-1091` HANDOFF → `LoopCompleted(stop_reason="handoff", handoff_target/reason)` from the `handoff` tool_call args (**Day-1: NO `response.handoff_request`**); `TerminationReason.HANDOFF="handoff"` (removed dead `HANDOFF_NOT_IMPLEMENTED`, grep-confirmed 3 sites, re-pointed 2 tests)

### 1.5 `AgentHandoff` event + sweep (US-4)
- [x] `_contracts/events.py` `LoopCompleted` += handoff_target/reason; NEW `AgentHandoff` (Cat 11)
- [x] Backend green: black/isort/flake8; `mypy src/` 0/324; 31 handoff/service/persona unit tests; `check_llm_sdk_leak` 0

---

## Day 2 — SSE wiring + router/handler + tests (Stage 2)

### 2.1 `agent_handoff` wire-type + codegen (US-4)
- [x] `event_wire_schema.py` += `agent_handoff` `{target_agent, reason, parent_session_id, new_session_id}` → codegen regen `events.json` + `loopEvents.generated.ts` (18→19); `--check` exit 0
- [x] `sse.py` `AgentHandoff → agent_handoff` branch; parity test 19

### 2.2 Router hook + handler persona (US-2/US-3)
- [x] `router.py:488-538` post-loop hook (stop_reason=="handoff" + db + target → boot → emit AgentHandoff; fail-soft on HandoffError)
- [x] `handler.py:369 resolve_session_persona` (meta_data["agent_role"]→registry, fallback DEMO); builders accept `system_prompt`

### 2.3 Tests + sweep (US-4/US-5)
- [x] integration `test_chat_handoff.py` (child persisted/tenant-scoped/linked + parent handed_off + audit + agent_handoff frame + cross-tenant reject + router-hook fail-soft) — 5 passed
- [x] unit persona (6) + FE `eventSchema.generated.test.ts` 18→19 + `chatStore` agent_handoff passthrough
- [x] mypy 0/324; run_all 10/10; tsc 0; Vitest 698; build ✓

---

## Day 3 — Test-isolation root-cause (FIX-026) + full sweep

- [x] Full-suite incident `Event loop is closed` root-caused (bisected to `test_router.py`, not incident's bug / not router-hook tests): new `resolve_session_persona` SELECT + `test_router.py` no `get_db_session` override → asyncpg conn leak (Risk Class C, ordering-surfaced)
- [x] **FIX-026** (root-cause, no skip): `test_router.py` `get_db_session→None` override + 3 router-hook tests relocated to integration with `db_session`
- [x] Parent decisive re-verify: full `pytest tests/unit tests/integration` **1999 passed / 4 skipped / 0 failed**; tests/unit alone 1424/0-failed; integration 5; run_all 10/10; codegen --check 0; mypy src 0/324

---

## Day 4 — Design note (8-point gate) + Closeout

### 4.1 Design note extract (US-5)
- [x] `18-handoff-design.md` (NEW) — 8-point gate ALL ✅ (1 headers↔stories / 2 file:line claims / 3 decision matrix / 4 verify command / 5 fixture ref / 6 verified-vs-deferred / 7 rollback / 8 17.md cross-ref); verified-ratio ≥95%
- [x] retrospective.md §Design Note Extract record (8-point self-check)

### 4.2 Closeout
- [x] Full validation (parent re-verified): pytest 1999 / mypy src 0/324 / run_all 10/10 / parity 19 / Vitest 698 / migration up+down / codegen --check 0
- [x] 17.md §4.1 `AgentHandoff` emit-ownership; `CHANGE-036` + `FIX-026`
- [x] progress.md (Day 0-4) + retrospective.md (Q1-Q7)
- [x] Calibration: `backend-control-transfer-spike` 0.55 (NEW, 1 pt) + `agent_factor` 0.65 (CAVEATED — 6th consecutive no-clean-wall-clock); NEW `AD-Source-DB-Call-Test-Isolation`; `AD-Day0-Codegen-Existing-Shape-Capture` recurred (4th); recorded `calibration-log.md §3`
- [x] Area-A: A-3b backend slice shipped; FE session-pivot + full context-carry + target auto-turn + multi-hop + real agent catalog = carryover (design note §5)
- [x] MEMORY.md pointer + `project_phase57_68_handoff_session_boot.md` subfile + CLAUDE.md lean
- [ ] commit (Day 1-4) + push + PR — user-authorized
