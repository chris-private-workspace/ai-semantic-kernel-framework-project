# Sprint 57.130 Progress — chat-v2 LoopTerminated wire surface

Branch `feature/sprint-57-130-chatv2-loop-terminated-wire-surface` (from `main` `b9334946`, post-#306). Closes `AD-LoopTerminated-Wire-Surface` (57.110 carryover).

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch (2026-06-16)

### Recon head-start
2 read-only Explore passes mapped the backend SSE/event path + the frontend chat-v2 store/render with file:line anchors (used to draft the plan). Day-0 re-verified the load-bearing facts via direct grep/read.

### Prong 1 — path verify ✅
All edit targets exist: `sse.py` / `event_wire_schema.py` / `tests/unit/api/v1/chat/test_event_wire_schema_parity.py` (NOTE: under `backend/tests/`, NOT `backend/src/`) / `chatStore.ts` / `types.ts` / `AgentTurn.tsx` / `tests/unit/chat_v2/chatStore.mergeEvent.test.ts` / `scripts/codegen/generate_event_schemas.py` / `scripts/lint/check_event_schema_sync.py` / `loopEvents.generated.ts`. `CHANGE-097` free.

### Prong 2 — content verify (drift catalog)

| ID | Finding | Implication |
|----|---------|-------------|
| **D-loopterminated-emission-sites** | `grep "LoopTerminated("` → defined `events.py:297`; emitted ONLY at `loop.py:2939` (hard exception) + `:3008` (soft `result.success=False`) — both in the Cat-8 tool-error path, then `return`. No 3rd site. | The drive-through trigger must go through the tool-error path (a tool that fatally errors → `max_retries_exhausted`), OR a budget cap. Both emission causes carry `reason`. |
| **D-serializer-precedent-shape** | `sse.py` `_serialize_inner` isinstance chain; `TripwireTriggered` branch `:300-307` returns `{"type":"tripwire_triggered","data":{violation_type, detail}}`; chain ends `raise NotImplementedError` `:481-484`. `serialize_loop_event` wrapper auto-injects `data["trace_id"]` (`:128-129`). | New `LoopTerminated` branch goes after the `MemoryAccessed` branch (`:479`), before `:481`; mirror the `{type, data}` envelope; do NOT add `trace_id` (auto-injected). |
| **D-wire-count-24-vs-fe-union** | `python -c "len(WIRE_SCHEMA)"` → **24** (canonical); `loop_terminated` ABSENT. `run_all` is 10/10 green incl. `check_event_schema_sync` → the FE generated union is ALREADY in sync at 24 (the recon "23" was a miscount). | Edit `WIRE_SCHEMA` → 25, run codegen → FE regenerates to 25; the sync lint stays green. No pre-existing drift to fix. |
| **D-codegen-invocation** | `scripts/codegen/generate_event_schemas.py` exists; `scripts/lint/check_event_schema_sync.py` is `run_all.py` lint #10 (`:84`). `loopEvents.generated.ts` header = "AUTO-GENERATED ... DO NOT EDIT". | Run the codegen after the `WIRE_SCHEMA` edit; never hand-edit the generated file; the sync lint gate-verifies. |
| **D-import-loopterminated** | `LoopTerminated` is NOT in `sse.py`'s `from agent_harness._contracts import (...)` (`:79-107`); it IS imported in the parity test (`:41`). | Add `LoopTerminated,` to the `sse.py` import block (alpha order: after `LoopStarted`). |
| **D-parity-test-shape** | `WIRED_EVENT_INSTANCES` ends at `MessageInjected` (`:132`); `UNWIRED_EVENT_INSTANCES` has `LoopTerminated(reason="budget_exceeded")` (`:138`) + `ErrorRetried` + `MetricRecorded`; count assert `test_wire_schema_has_24_entries` (`:144-145`). Docstring counts (`:11`/`:17`) already stale (say 23, code is 24). | Move `LoopTerminated` UNWIRED→WIRED (richer instance: reason+detail+last_state_version); bump `== 24`→`== 25` + rename the test; refresh the stale docstring counts (24→25 entries; 2 unwired) + MHist. |

### Prong 3 — schema verify
N/A — NO new DB table / migration / ORM. The `LoopTerminated` event + its emission already exist; `WIRE_SCHEMA` is a Python dict (not a DB schema).

### Baselines re-asserted ✅
pytest **2727+5skip** · wire **24** (→25 this sprint) · Vitest **904** · mockup **51** · mypy `src` **0/372** · run_all **10/10** (incl. `check_event_schema_sync`).

### Go/no-go ✅
Clean cross-stack surfacing of an EXISTING event (mirror the `tripwire_triggered` precedent). Scope shift **0%** (recon confirmed all anchors). The drive-through staging (forcing a real `LoopTerminated`) is the main wall-clock risk → D-drive-through-trigger to be settled Day 1/3. Proceed.

---

## Day 1 — Backend: serialize + wire 24→25 + codegen ✅ (2026-06-16)

- `sse.py`: imported `LoopTerminated` (alpha order after `LoopStarted`); added the serializer branch before `NotImplementedError` (`{type:"loop_terminated", data:{reason, detail, last_state_version}}`, mirrors `tripwire_triggered`; `trace_id` auto-injected by the wrapper). MHist + Last Modified.
- `event_wire_schema.py`: appended `"loop_terminated"` entry (`reason`/`detail:"string | null"`/`last_state_version:"number | null"` — both nullable forms ARE in `_RECOGNIZED_TS_TYPES`); Purpose 22→25 + Key-Components 24→25 + section header 24→25 + MHist.
- parity test: moved `LoopTerminated` UNWIRED→WIRED (richer instance), count `==24`→`==25` + renamed test, docstring counts refreshed (2 unwired / 25 entries).
- **codegen**: `python scripts/codegen/generate_event_schemas.py` → regenerated `loopEvents.generated.ts` (`LoopTerminatedEvent` + union + `KNOWN_LOOP_EVENT_TYPES`) + `events.json`.
- Gate: black/isort/flake8 clean · **mypy src 0/372** · **run_all 10/10** (`check_event_schema_sync` green → FE generated == backend wire @ 25) · parity **33 passed**.

### Day-0-MISSED drift (caught during Day 1 — retro lesson)
- **D-codegen-interface-map** (NOT in Day-0 catalog): `generate_event_schemas.py` has an EXPLICIT `WIRE_TYPE_TO_INTERFACE` dict (not fully auto from wire-type → PascalCase). The first codegen run raised `RuntimeError: No interface name mapped for 'loop_terminated'`. Fix: added `"loop_terminated": "LoopTerminatedEvent"`. **Lesson**: Day-0 Prong-2 for a new wire TYPE must also grep the codegen's interface-name map, not just `WIRE_SCHEMA`.

## Day 2 — Frontend: mergeEvent + turn field + chip + tests ✅ (2026-06-16)

- `types.ts`: `AgentTurn += terminated?: {reason; detail?}` + MHist + Last Modified; de-brittled the stale `user_message` "wire count stays 24" comment.
- `chatStore.ts`: added `case "loop_terminated"` after `loop_end` — flips active-turn pending `ToolBlock`(s) → `error` (output "terminated: {reason}", the stuck-chip fix) + records `turn.terminated` + `waiting:false` + chat `status:"completed"` (proven unfreeze path, no new status enum); Description case-list + MHist + Last Modified.
- `AgentTurn.tsx`: head renders `<span className="badge danger">terminated · {reason}</span>` when `turn.terminated` — reuses the EXISTING `.badge.danger` class (styles-mockup.css:526, `var(--danger)` + existing oklch tints) → **0 new CSS / 0 new oklch literal**; MHist.
- tests: `chatStore.mergeEvent.test.ts` +3 (`loopTerminated` fixture; pending-tool flip / terminated-record+status / no-pending-no-crash); `eventSchema.generated.test.ts` count `24→25` + new `loop_terminated` recognition test.
- Gate: **build (tsc) clean** (the `never`-default exhaustiveness forced the new case) · **lint clean** · **check:mockup-fidelity 51** byte-identical · `diff styles-mockup.css` empty · **Vitest 908** (904 +3 mergeEvent +1 recognition).

### Day-0-MISSED drift (caught during Day 2 full run — retro lesson)
- **D-three-count-test-locations** (NOT fully in Day-0 catalog): the hardcoded wire count `24` is asserted in **THREE** places, not one: (1) `test_event_wire_schema_parity.py` (`==24`, found Day-0), (2) FE `eventSchema.generated.test.ts` (`.size).toBe(24)`), (3) `test_loop_start_active_skill.py::test_wire_type_count_unchanged_24` (`==24`, a 57.116 regression guard). All three needed the 24→25 bump. **Lesson**: Day-0 Prong-2 for a wire-count change must grep `== 24` / `.size).toBe(24)` / `count.*24` across ALL test files (backend + frontend), not just the parity test. (Renamed the active_skill test to drop the brittle literal name; de-duplicating the global-count assertion from the active_skill test is a deferred cleanup.)

### Full backend suite (authoritative)
**2727 passed, 5 skipped** (parity net 0: WIRED +1 / UNWIRED -1). NOTE: running `tests/unit/api/v1/chat/` ALONE shows 2 `test_audit_log_observer` failures — a pre-existing **Risk Class C** test-isolation artifact (module-level singleton across event loops; the tests pass in the full suite), NOT this change (audit observer keys off LoopCompleted, unrelated to LoopTerminated).

## Day 3 — Drive-through (MANDATORY, real fatal terminate) — **PASS** (2026-06-16)

### The trigger (found via Cat-8 recon — clean, no code/config change)
`web_search` handler RAISES `WebSearchConfigError` (a `RuntimeError`) when `BING_SEARCH_API_KEY` is unset (`search_tools.py:104-105`). The key IS unset in dev (`grep -c "^BING_SEARCH_API_KEY=.\+" .env` → 0). `WebSearchConfigError` is UNREGISTERED in the Cat-8 policy → classified **FATAL** (default fallback `policy.py:170/186`) → `DefaultErrorTerminator` terminates immediately with `fatal_exception` (`terminator.py:151-154`; FATAL retry max=0). web_search is risk LOW + HITL AUTO → **no pause**; it fires via the HARD-exception path (`loop.py:2939`) AFTER a `tool_call_request` already streamed → **dangling pending chip = the exact stuck-chip scenario**.

### Setup (Risk Class E clean restart)
Killed stale PID 40596 (pre-edit `sse.py`/`event_wire_schema.py`), confirmed :8000 FREE (no orphan workers — it was single-process no-`--reload`), started fresh `uvicorn api.main:app` (bg `b1537857y`) → "startup complete". Logged into chat-v2 via dev-login (jamie@acme.com / acme-prod), mode **real_llm** (real Azure gpt-5.2), fresh session.

### Drive-through (real UI + real backend + real Azure) — PASS
- Sent: "Use the web_search tool to find today's top technology news headline, then tell me what it is."
- gpt-5.2 called `web_search` (`{"query":"today's top technology news headline","top_k":5}`) → handler raised `WebSearchConfigError` → FATAL → `LoopTerminated(reason="fatal_exception")`.
- **The fix (observed in the real UI)**:
  - the previously-pending `web_search` tool block flipped to **`status:"error"`** with output `terminated: fatal_exception` (NO perpetual spinner — the stuck-chip fix);
  - the agent turn head renders **`terminated · fatal_exception`** (`.badge.danger`, `lastAgentHasDangerBadge:true`);
  - **`lastAgentHasLiveDot:0`** (turn not stuck running) + the composer textbox is **editable** (`textboxDisabled:false`) → composer unfrozen.
- **End-to-end proof**: the FE can only render `terminated · fatal_exception` if the backend serialized the `loop_terminated` SSE frame (the new `sse.py` branch) AND the regenerated `KNOWN_LOOP_EVENT_TYPES` recognized it (else parseSSEFrame drops it) AND the new `mergeEvent` case ran (flip pending tool + set badge). All three layers exercised live.
- Screenshot: `.playwright-mcp/drivethrough-57130-loop-terminated-PASS.jpeg`. (Backend Cat-8 handler doesn't log the terminate at INFO — DEBUG-level — so no log line; the UI render + the web_search tool-input + the `fatal_exception` reason are the authoritative evidence.)
- **Before this sprint**: the same web_search failure → `LoopTerminated` dropped at the serializer → silent stream end → perpetual pending `web_search` chip + no reason. **Now**: terminated badge + error chip + unfrozen composer.

### Day-3 finding (calibration input)
The trigger was clean ONCE found (no code/config change — just an unset env var + a web_search prompt), but FINDING it took real digging (python_sandbox always returns success=True so it can't trigger; the Cat-8 FATAL-classification path + the unregistered-exception default + which built-in tool actually raises). This matches the `AD-DriveThrough-Deterministic-Tool-Trigger` (57.122) known-hard pattern — a forced-tool-call harness would have made it trivial.

## Day 4 — CHANGE-097 + closeout — (in progress)
