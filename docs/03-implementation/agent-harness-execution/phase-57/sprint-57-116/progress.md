# Sprint 57.116 Progress — Skills Force-Load Inspector Affordance (user-turn "active skill" chip)

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-116-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-116-checklist.md)

**Goal**: surface the 57.115 deterministic `/skill-name` force-load (currently invisible after send) — the chat router emits a SERVER-CONFIRMED `active_skill` on the opening `loop_start` SSE event (additive field, count 24, `loop.py`/`events.py` untouched), and chat-v2 stamps the just-sent user turn + renders a "⚡ {skill}" chip. Closes `AD-Skills-Inspector-Affordance`.

---

## Day 0 — 2026-06-14 — Plan-vs-Repo Verify (三-prong) + Branch

### Three-prong Day-0 verify (against `main` HEAD `fc385a87`)

Head-start = 2 Explore recon agents (backend wire taxonomy + FE chat-v2 store/render) + direct greps. Formal catalog below.

**Prong 1 — path verify** ✅
- NEW absent (Glob-0): `test_loop_start_active_skill.py`, `chatStore.activeSkill.test.ts`, `UserTurn.skillChip.test.tsx` — confirmed 0 (basenames unique across the tree, per the 57.109 lesson).
- EDIT present: `sse.py` / `event_wire_schema.py` / `router.py` / `types.ts` / `chatStore.ts` / `components/turns/UserTurn.tsx` / `tests/integration/api/test_chat_force_load_skill.py` (57.115) — confirmed.
- Codegen targets present: `frontend/src/features/chat_v2/generated/loopEvents.generated.ts` + `events.json` (regen targets).
- CHANGE 083 free (082 = slash-command). NO design note (feature continuation). NO migration.

**Prong 2 — content verify** (drift findings)
- **D-sse-loopstarted** 🟢: `sse.py` `_serialize_inner` `LoopStarted` branch (`:138-143`) → `{type:"loop_start", data:{session_id, request_id}}`. Add `"active_skill": None`. **CONFIRMED a conformance test EXISTS** — `backend/tests/unit/api/v1/chat/test_event_wire_schema_parity.py` (serializer-vs-`WIRE_SCHEMA` parity) → the `sse.py` default `None` is **REQUIRED** (else the serializer omits a key the schema declares → parity test red). Design already does this.
- **D-wire-schema** 🟢: `event_wire_schema.py` `WIRE_SCHEMA["loop_start"]` (`:87-90`) = `{session_id, request_id}`. Add `"active_skill": "string | null"`. The 24-type count is the dict-KEY count of `WIRE_SCHEMA` (top-level types) → unchanged by a field add.
- **D-router-augment (CRITICAL)** 🟢: `forced_skill` computed `:279-283`; `build_handler(force_load_skill=forced_skill)` `:330`; `StreamingResponse(_stream_loop_events(...))` `:412-413`; `_stream_loop_events` def `:570`; `serialize_loop_event(event)` `:641`. **DRIFT: `LoopStarted` is NOT imported in `router.py`** (Grep 0 matches) → MUST add the import. Plan: thread `active_skill` param into `_stream_loop_events`, pass `=forced_skill` at `:413`, inject at `:641` (`if isinstance(event, LoopStarted) and active_skill: payload["data"]["active_skill"] = active_skill`).
- **D-resume-mirror** 🟢: `_stream_resume_events` (`:1080`, serialize `:1090`) — NOT touched; resume `loop_start` keeps the serializer default `null` (the user turn carries its chip from the initial run).
- **D-fe-store** 🟢: `chatStore.ts` `case "loop_start"` (`:363`) returns a new state preserving `turns` (sets sessionId + status=running + dismisses the handoff banner). Add an immutable `turns` map stamping the last `role==="user"` turn when `ev.data.active_skill` truthy. `pushUserMessage` `:350` creates the user turn at send (no skill).
- **D-fe-userturn** 🟢: `UserTurn.tsx` `.turn-head` (`:48-59`) = `.role` + `.route-pill` (role) + conditional `injected` `.route-pill` (`:53-57`, `data-testid="injected-tag"`) + `.mono.subtle` timestamp (`:58`); `.turn-body` `:60`. The `injected` tag is the EXACT pattern to mirror for the skill chip. `types.ts` `UserTurn` `:128-136` (has `injected?`).
- **D-route-pill** 🟢: `.route-pill` (`styles-mockup.css:1101`) uses design tokens only (no colour literal) — reuse as-is (the `injected` tag already proves it). No CSS change → `check:mockup-fidelity` 51 holds.
- **D-codegen** 🟢: `scripts/codegen/generate_event_schemas.py` → `loopEvents.generated.ts` + `events.json`; `run_all` codegen `--check` diffs until regen, then clean (the 57.108 additive-field-+-regen pattern).

**Prong 3 — N/A**: no new table / migration / ORM this sprint.

**Catalog** — 1 real drift (D-router-augment: `LoopStarted` import absent in router.py → add) + 1 confirmed constraint (D-sse-loopstarted: parity test makes the serializer default `None` mandatory). No scope shift.

**Go/no-go**: 🟢 **GO** — design confirmed (router-augment keeps `loop.py`/`events.py` diff 0; the additive field keeps count 24; the parity test is satisfied by the serializer default). No scope shift > 20%.

### Branch
- `git checkout -b feature/sprint-57-116-skills-inspector-affordance` (from `main` `fc385a87`)

---

---

## Day 1 — 2026-06-14 — Backend: `active_skill` on `loop_start` (serializer default + wire schema + router augment) + codegen + tests

### Done
- **`sse.py`** (`_serialize_inner` LoopStarted branch `:138`): += `"active_skill": None` default (the Cat-1 loop has no skill concept; the router overrides). MHist + WHY comment.
- **`event_wire_schema.py`** (`WIRE_SCHEMA["loop_start"]` `:87`): += `"active_skill": "string | null"` (drives codegen + the parity guard). 24 wire-TYPE count unchanged (it is a field). MHist.
- **`router.py`**: imported `LoopStarted` (was absent — Day-0 drift D-router-augment); `_stream_loop_events(..., active_skill: str | None = None)` param; passed `active_skill=forced_skill` at the `:413` call; injected at `:641` after serialize — `if active_skill and isinstance(event, LoopStarted): payload["data"]["active_skill"] = active_skill`. `_stream_resume_events` UNTOUCHED. MHist + WHY comment.
- **Codegen**: `python scripts/codegen/generate_event_schemas.py` → regenerated `loopEvents.generated.ts` (`LoopStartEvent.data.active_skill: string | null`) + `events.json`. `KNOWN_LOOP_EVENT_TYPES` unchanged (24).
- **Tests**: NEW `tests/unit/api/v1/chat/test_loop_start_active_skill.py` (×4 — serializer default null / no-session / wire-schema declares / count 24 unchanged). **Day-1 DRY adjustment**: the SSE-level assertions went into `tests/integration/api/test_chat_e2e.py` (+3 — confirmed/null/unknown) reusing its echo-mode TestClient `_parse_sse` harness rather than duplicating a TestClient app in the build_handler-level `test_chat_force_load_skill.py` (echo computes `forced_skill` the same way real_llm does — it is router-level, not mode-gated → the SSE field is exercisable without a real Azure call).

### Gate
- mypy `src` **0/370** (unchanged) · black/isort/flake8 0 · `python scripts/lint/run_all.py` **10/10** (incl. `check_event_schema_sync` — codegen `--check` clean after regen; count 24) · `loop.py`/`events.py`/`LoopStarted` dataclass/`read_skill`/`_stream_resume_events` UNTOUCHED · no migration.
- full pytest **2623 passed + 5 skip** vs 2616 → **+7 (4 unit + 3 e2e, 0 del)**.

### Notes
- The router-augment design (vs the Explore agent's thread-through-loop option) kept `loop.py`/`events.py` diff-0 — Cat-1 boundary clean. The parity guard (`test_event_wire_schema_parity.py`) confirmed the serializer default `None` matches the new schema key (green).

## Remaining for Next Day
- Day 2: frontend — `types.ts` `UserTurn.activeSkill?` + `chatStore` `loop_start` stamp (truthy guard) + `UserTurn.tsx` `.route-pill` chip + Vitest.
