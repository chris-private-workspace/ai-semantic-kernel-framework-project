# Sprint 57.68 — Checklist (HANDOFF Control-Transfer + Platform Session-Boot — A-3b backend slice)

**Plan**: [`sprint-57-68-plan.md`](./sprint-57-68-plan.md)
**Created**: 2026-06-02
**Status**: Draft (code gated on Day-0 GO)

> Rule: only `[ ]` → `[x]`; never delete unchecked items; defer with `🚧 + reason`.
> SPIKE (per Day-0 verdict) → Day-4 design-note extract + 8-point quality gate mandatory (`sprint-workflow.md §Step 5.5`).
> Scope locked (user 2026-06-02): **Option B full platform session-boot**; THIS sprint = backend-complete slice (FE session-pivot deferred — plan §9). Two-round Day-0 audit pre-confirmed D1-D5 + the 4 session-boot facts (plan §0); re-confirm residual unknowns (exact `LoopCompleted`/`handoff_request` shape + `SessionRepository.create_session` signature) before Day 1 code.

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify (per `.claude/rules/sprint-workflow.md §Step 2.5`)
- [ ] **Prong 1 (path)**: confirm `loop.py:1067-1074` (`HANDOFF_NOT_IMPLEMENTED`) + `:654-655` (output parser → OutputType.HANDOFF) / `_contracts/events.py` (SubagentSpawned `:316`) / `subagent/modes/handoff.py` + `dispatcher.py:280-297` / `infrastructure/db/models/sessions.py:73-122` / `repositories/session_repository.py:50-85` / `api/v1/chat/{router.py:203/241/280-532, handler.py:94/153/269, sse.py, event_wire_schema.py}` / `infrastructure/db/audit_helper.py:90-102`; `platform_layer/handoff/` does NOT exist
- [ ] **Prong 2 (content)**: READ the exact `LoopCompleted` dataclass fields + the `handoff_request` object the output parser produces (target_agent attr name? reason?) before the loop edit (AD-Day0-Codegen-Existing-Shape-Capture lesson — read the real shape, not just names); `SessionRepository.create_session` exact signature (does it accept `meta_data`? add `handoff_parent_id`?); `append_audit` exact kwargs; `handler.py` where DEMO_SYSTEM_PROMPT is passed (per-session persona insertion point); the `AgentSpec` shape (`_contracts/subagent.py:74-86`)
- [ ] **Prong 3 (schema)**: confirm `sessions` columns (`status` String(32) free-text / `tenant_id` TenantScopedMixin / `meta_data` JSONB physical "metadata" alias / NO handoff/persona column); next migration number (`ls migrations/versions/ | sort -V | tail -3` → expect `0022`); `sessions` RLS policy exists (column-add needs no new RLS — `check_rls_policies` stays green); **physical-column-vs-ORM-alias** check for any raw SQL touching `meta_data`
- [ ] **Doc-location verify**: 17.md §4.1 emit-ownership (add `AgentHandoff` row); 02.md §SSE auto via 57.67 registry note; design note → next planning doc number `18-handoff-design.md`
- [ ] Catalogue D-DAY0-N in progress.md Day 0 table; **go/no-go** (expect GO — architecture pre-validated by 2 researcher rounds; residual = exact LoopCompleted/create_session signatures)

### 0.2 Branch + decisions
- [ ] Branch `feature/sprint-57-68-handoff-session-boot` from current main `0439235e`; plan+checklist committed (1st commit)
- [ ] Scope decisions resolved: backend slice (FE pivot deferred); context-transfer = `handoff_parent_id` linkage only; persona in `meta_data["agent_role"]` (no column); migration `0022` = `handoff_parent_id` FK+index only; minimal persona registry; **Agent-delegated: yes** (Stage-1 backend core / Stage-2 SSE+router+tests; design note parent-authored); pre-start Postgres for integration tests (AD-AgentDelegate-DevStack-Precheck)

---

## Day 1 — Backend core (Stage 1: migration + service + persona + loop + event)

### 1.1 DB migration + ORM (US-2) — `0022` + `sessions.py` + `session_repository.py`
- [ ] `0022_session_handoff_linkage`: `sessions.handoff_parent_id UUID NULL` FK→sessions(id) + `idx_sessions_handoff_parent`; down drops both; `alembic upgrade`/`downgrade` clean
- [ ] `Session` ORM += `handoff_parent_id` mapped column; `SessionRepository.create_session` accepts `handoff_parent_id` + `meta_data`; NEW `mark_handed_off(session_id, tenant_id)` (status="handed_off")

### 1.2 Persona registry (US-3) — `platform_layer/handoff/persona_registry.py` (NEW)
- [ ] Minimal typed `target_agent → system_prompt` dict (2-3 named agents) + `resolve_persona(target_agent) -> str | None`; file header notes it is a thin stand-in (design-note open question)

### 1.3 Handoff service (US-2) — `platform_layer/handoff/service.py` (NEW)
- [ ] `HandoffService.boot_handoff(*, parent_session_id, target_agent, reason, tenant_id, user_id, db)` — resolve persona (reject unknown → typed error, no boot); create child session (parent tenant_id, handoff_parent_id, meta_data["agent_role"]); mark parent handed_off; `append_audit("session.handoff", ...)`; ALL in one transaction; returns `new_session_id`
  - DoD: unit test (mock db) — child fields correct + parent marked + audit kwargs + unknown-target rejected + rollback-on-error

### 1.4 Loop stop_reason swap (US-1) — `loop.py` (~:1067)
- [ ] Replace `HANDOFF_NOT_IMPLEMENTED` → `LoopCompleted(stop_reason="handoff")` carrying `handoff_request` (target_agent, reason per Prong-2 shape); no other loop control-flow change
  - DoD: unit test — HANDOFF output → stop_reason="handoff" + target_agent reachable; existing loop tests green (HANDOFF stub test re-pointed)

### 1.5 `AgentHandoff` event (US-4) — `_contracts/events.py`
- [ ] NEW `AgentHandoff` LoopEvent (Cat 11): `{ target_agent, reason, parent_session_id, new_session_id }`
- [ ] Backend sweep: black/isort/flake8 + `mypy src/` 0/N + `check_llm_sdk_leak` 0 + full pytest green

---

## Day 2 — SSE wiring + router/handler + unit tests (Stage 2)

### 2.1 `agent_handoff` wire-type + codegen (US-4)
- [ ] `event_wire_schema.py` `WIRE_SCHEMA` += `agent_handoff` `{ target_agent, reason, parent_session_id, new_session_id }` (all string) → run `scripts/codegen/generate_event_schemas.py` → regen `events.json` + `loopEvents.generated.ts` (18→19); `--check` exit 0
- [ ] `sse.py` `AgentHandoff → agent_handoff` serializer branch (str(UUID)s); 57.67 parity test now covers 19 wire-types

### 2.2 Router post-loop hook + handler persona (US-2/US-3)
- [ ] `router.py` `_stream_loop_events`: on `LoopCompleted.stop_reason == "handoff"` → `HandoffService.boot_handoff(...)` (tenant_id/user_id from TraceContext/auth) → construct + yield `AgentHandoff` (with new_session_id) → serialize
- [ ] `handler.py`: resolve per-session persona from `meta_data["agent_role"]` via registry (fallback DEMO_SYSTEM_PROMPT)
  - DoD: unit — router handoff branch (mock service); handler persona fallback (with/without agent_role)

### 2.3 Sweep
- [ ] `mypy src/` 0/N; `run_all.py` **10/10** (parity + RLS + SDK leak green); pytest green; Vitest 697 (generated regen only — no FE feature change)

---

## Day 3 — Integration + multi-tenant + full sweep

### 3.1 Integration (US-5) — `test_chat_handoff.py` (NEW)
- [ ] Drive a loop emitting HANDOFF → assert: parent `stop_reason="handoff"`; child session persisted (`tenant_id`==parent, `handoff_parent_id`==parent, `meta_data["agent_role"]`==target); parent `status="handed_off"`; `session.handoff` audit row; `agent_handoff` SSE frame with `new_session_id`
- [ ] **Multi-tenant 鐵律**: child session tenant == parent tenant; cross-tenant target rejected; booted session resolves target persona (not DEMO)
- [ ] autouse singleton-reset fixture if touching chat app singletons (Risk Class C)

### 3.2 Full sweep
- [ ] backend pytest green (+ handoff cases) / `mypy src/` 0/N / `run_all.py` 10/10 (SDK leak 0, RLS green) / `alembic upgrade 0022` + downgrade clean / codegen `--check` 0 / Vitest 697 / frontend build ✓ (generated regen only)

---

## Day 4 — Design note (8-point gate) + Closeout

### 4.1 Design note extract (US-5) — `18-handoff-design.md` (NEW, per `sprint-workflow.md §Step 5.5`)
- [ ] Use `claudedocs/templates/spike-design-note-template.md`; **8-point gate** (each verified by reviewer):
  - [ ] 1. Section header maps to spike user story (not generic)
  - [ ] 2. Every technical claim has file:line
  - [ ] 3. Decision matrix (B full session-boot vs in-loop persona-swap vs Potemkin tool-only — why B; persona registry minimal vs catalog)
  - [ ] 4. Verification command (the integration test invocation)
  - [ ] 5. Test fixture reference
  - [ ] 6. Open invariants explicit (verified: loop swap + session-boot + audit + event; deferred/NOT verified: FE pivot + full context-carry + target auto-turn + multi-hop)
  - [ ] 7. Rollback path (revert `0022` + router hook + loop swap; ~1 day)
  - [ ] 8. 17.md §4.1 cross-ref (AgentHandoff emit-ownership)
- [ ] retrospective.md §Design Note Extract record (verified ratio + 8-point self-check)

### 4.2 Closeout
- [ ] Full validation sweep (pytest / mypy src 0/N / run_all 10/10 / codegen --check 0 / Vitest 697 / build ✓ / migration up+down) — parent independently re-verified
- [ ] 17.md §4.1 `AgentHandoff` emit-ownership; `CHANGE-036-handoff-session-boot.md`
- [ ] progress.md (Day 0-4) + retrospective.md (Q1-Q7)
- [ ] Calibration: `backend-control-transfer-spike` 0.55 (NEW, 1 data point) + `agent_factor mechanical-greenfield-design-decisions` 0.65 (CAVEATED — 6th consecutive no-clean-wall-clock); record `calibration-log.md §3`
- [ ] Area-A capstone: A-3b backend slice shipped; FE session-pivot + full context-carry + multi-hop + real agent catalog = carryover (toward full Option B)
- [ ] MEMORY.md pointer + `project_phase57_68_*.md` subfile + CLAUDE.md lean Current Sprint/Last Updated
- [ ] commit (Day 1-4) + push + PR — user-authorized
