# Sprint 57.92 Progress — Between-Turns Guardrail ESCALATE Pause Point (地基 A Slice 3 leg 2)

**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-92-plan.md`
**Checklist**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-92-checklist.md`
**Branch**: `feature/sprint-57-92-between-turns-pause` (from `main` `0ceb788d`)

---

## Day 0 — 2026-06-08 — Plan-vs-Repo Verify + Branch

### Three-prong verify (real greps on `loop.py` / `engine.py` / `_abc.py` / `handler.py` / `business_domain` / `frontend`)

**Prong 1 (path)** — confirmed:
- `loop.py`: `_emit_deferred_pause` (`:1037`, kind-agnostic durable-pause tail) / `_cat9_input_check` (`:546`) + `_cat9_input_hitl_pause` (`:631`, the exact mirror template) / `_cat9_output_check` (`:1088`, called `:1668`, runs OUTPUT chain per LLM response) / `_run_turns` (`:1261`; `while True` `:1282`; termination checks end `~:1307`; `turn_count += 1` LAST in body `:2050`) / `run()` `_run_turns` call site `:1242` / `resume()` kind-branch `:2147` + shared `_run_turns` drive `:2275`.
- `engine.py`: `_chains` factory `{gt: [] for gt in GuardrailType}` (`:80-82`, auto-includes a new value) / `check_output` (`:126`) / `_run_chain` (`:100`).
- `_abc.py`: `GuardrailType` (`:31`, INPUT/OUTPUT/TOOL).
- `handler.py`: `CHAT_HITL_ESCALATE_TOOLS={"echo_tool"}` (`:121`) / `CHAT_HITL_ESCALATE_INPUT_PHRASES={"approval required"}` (`:131`) / `DEMO_SYSTEM_PROMPT` (`:103`) / guardrail registration block (`:306-321`) / `make_default_executor(...)` (`:255`).
- Guardrail dir structure: `guardrails/input/` + `guardrails/output/` (toxicity + sensitive_info) + `guardrails/tool/` already exist → `guardrails/between_turns/` is the consistent parallel.

**Prong 2 (content)** — confirmed:
- (a) `_emit_deferred_pause` body (`:1066-1086`) is kind-agnostic (takes any `pending_approval` + messages + audit fields). ✅ reusable verbatim.
- (b) `run()` `_run_turns` call (`:1242`) passes raw locals only → adding `skip_between_turns_once: bool = False` is additive; `run()` passes default. ✅
- (c) `resume()` reads `kind = str(pending.get("kind", "tool"))` (`:2147`); the shared drive (`:2275`) is reached by both kinds. ✅ a `between_turns` elif slots in.
- (d) per-response `_cat9_output_check` runs the OUTPUT chain (`check_output`, `:1104`) → a BETWEEN_TURNS chain does NOT double-fire. ✅
- (e) `_cat9_input_hitl_pause` (`:631-749`) = the exact build template (identity gate → ApprovalRequest → request_approval try/except → ApprovalRequested → pending_approval → `_emit_deferred_pause`). ✅ mirror.
- (f) echo_tool tool-escalates (`CHAT_HITL_ESCALATE_TOOLS`) + a tool resume execs the pending tool OUTSIDE the loop then re-enters `_run_turns(turn_count=0)` → the re-entered turn 0 produces the final answer → `turn_count` never reaches 1 → the between-turns gate (`turn_count > 0`) is unreachable via echo. ✅ confirms a non-escalate tool is required.

**Prong 2.5 (GuardrailType exhaustiveness)** — confirmed SAFE:
- All `GuardrailType` usages (backend src) = import / `guardrail_type = GuardrailType.X` (per-guardrail type assign) / `_chains` factory (auto) / `_run_chain(GuardrailType.X)` (per-type). **NO `match GuardrailType`, NO `len(GuardrailType)` assertion, NO dict-literal-over-all-types.** `cat9_mutator.py` / `cat9_fallback.py` only copy `wrapped.guardrail_type` (pass-through). → adding `BETWEEN_TURNS` (4th value) breaks nothing structurally.

**Prong 3 (schema)** — N/A: no DB/migration/ORM change; `pending_approval.kind="between_turns"` additive JSONB.

**Frontend mirror** — confirmed NO change: `guardrail_type` is a free `string` (`loopEvents.generated.ts:101`, `events.json:71`); `LoopVisualizer.tsx` renders it as a string (`:205`, `:417`). → `"between_turns"` renders fine; no Literal/enum exhaustiveness.

**Baseline**: main `0ceb788d` (57.91 merged) — pytest 2243 / mypy 0/347 / run_all 10/10 / Vitest 772. To re-confirm before editing.

### Drift findings

- **D-DAY0-1** — `note_tool` location resolved (explicit Day-0 TODO in plan). echo_tool registered at `business_domain/_register_all.py:237-238` (`registry.register(ECHO_TOOL_SPEC)` + `handlers["echo_tool"] = echo_handler`); impl in `agent_harness/tools/echo_tool.py`. → `note_tool` = NEW `agent_harness/tools/note_tool.py` (mirror) + 2 lines in `_register_all.py`. **Auto-available to chat** (chat uses `make_default_executor`) + **auto-PASS in chat** (not in `CHAT_HITL_ESCALATE_TOOLS` → CapabilityMatrix gives requires_approval=False). Handler needs only the DEMO_SYSTEM_PROMPT line + the between-turns guardrail registration (NO note_tool registration in handler). Plan §File Change List updated accordingly. Implication: scope unchanged; note_tool surface is small (1 new tool file + 2 lines).
- **D-DAY0-2** — `GuardrailType` has NO exhaustiveness consumer → `BETWEEN_TURNS` safe (Prong 2.5). Implication: plan §3.1 + §8-risk "new GuardrailType breaks exhaustiveness" → mitigated/non-issue.
- **D-DAY0-3** — frontend `guardrail_type` is a free `string` → `between_turns` needs NO frontend change. Implication: plan §3.7 confirmed; the conditional frontend row stays conditional (likely none).
- **D-DAY0-4** — `run()` `_run_turns` call site = `:1242`, resume = `:2275`. `skip_between_turns_once` default False → `run()` byte-unchanged, `resume()` passes the flag. Implication: plan §3.4 confirmed.

### Go/No-Go: **GO**

All 4 drifts anticipated by the plan; scope shift ~0% (D-DAY0-1 only refined the note_tool location, same scope). The between-turns gate is reachable end-to-end via `note_tool` + the new gate; new GuardrailType value has no exhaustiveness break; no ResumeService / endpoint / migration / frontend change. Day-0 commit then Day 1.

---

## Day 1-2 — 2026-06-08 — Code + tests (US-1..US-5)

### Code (all in one Day; mirror of leg-1 input pattern kept the surface thin)

- **Cat 9 `GuardrailType.BETWEEN_TURNS`** (`_abc.py`) + **`GuardrailEngine.check_between_turns`** (`engine.py`, mirror of `check_output`; "three→four cut points" docstring). Prong 2.5 held — no exhaustiveness consumer broke.
- **NEW `guardrails/between_turns/keyword_detector.py`** `BetweenTurnsKeywordGuardrail` (BETWEEN_TURNS type; ESCALATE on a case-insensitive phrase; `_extract_text` mirrors the input sibling) + `__init__.py`.
- **NEW `tools/note_tool.py`** (`NOTE_TOOL_SPEC` + `note_handler`, `text`→`text`) + registered unconditionally in `_register_all.py` (covers both the `register_builtin_tools` branch and the bring-up `else` branch; not in `CHAT_HITL_ESCALATE_TOOLS` → CapabilityMatrix auto-PASS in chat).
- **loop.py** — `_latest_output_text` (static; last truthy assistant/tool message) + `_cat9_between_turns_check` (PASS→return / ESCALATE+wiring→pause / else→GUARDRAIL_BLOCKED fail-closed) + `_cat9_between_turns_hitl_pause` (verbatim mirror of `_cat9_input_hitl_pause`, between_turns-kind `pending_approval`, no tool_call, reuses `_emit_deferred_pause`). NEW loop-top gate in `_run_turns` (`turn_count > 0 and not skip_between_turns_once`, consumed after the 1st iteration). `_run_turns` gained `skip_between_turns_once: bool = False`. `resume()` gained an `elif kind == "between_turns"` branch (APPROVED→no tool + `skip_between_turns_once=True`; REJECTED→GUARDRAIL_BLOCKED) + passes the flag to the shared drive. **The input/tool branches + the `_run_turns` drive + `_cat9_output_check` are byte-unchanged.**
- **handler.py** — `CHAT_HITL_ESCALATE_BETWEEN_TURNS_PHRASES = {"checkpoint"}` (≠ the input phrase `approval required` so the input gate doesn't pre-empt) + register `BetweenTurnsKeywordGuardrail` in the same `if hitl_manager is not None:` block + extended `DEMO_SYSTEM_PROMPT` to drive `note_tool` on "note X".

### Tests

- **`test_loop_pause_resume.py`** +4: `test_between_turns_escalate_pauses_before_next_turn` (turn-0 tool runs, top-of-turn-1 ESCALATE pause, `pending_approval{kind:"between_turns",turn:1}`, no tool_call, turn-1 LLM never called) / `test_between_turns_escalate_without_hitl_blocks` (fail-closed GUARDRAIL_BLOCKED) / `test_resume_between_turns_approved_continues_no_repause` (always-escalate guardrail wired + `skip_between_turns_once` → end_turn, NO re-pause, NO tool exec) / `test_resume_between_turns_rejected_blocks`. New fakes `BetweenTurnsEscalateGuardrail` + builders `_build_between_turns_loop` / `_build_resume_loop_between_turns` / `_paused_between_turns_state`. The 13 existing input/tool cases are byte-unchanged.
- **NEW `test_between_turns_keyword_detector.py`** (7): type / match / case-insensitive / no-match / empty-phrases / blank-drop / Message-extract.

### Gate (Day 3.1 sweep pulled forward)

- pytest **2254 passed / 4 skipped** (baseline 2243 → **+11**: 4 loop + 7 guardrail); NO test deleted.
- mypy `src --strict` **0** (350 files, +2). run_all **10/10** (LLM SDK leak 0; AP-1 pipeline-disguise; AP-8 PromptBuilder; event-schema sync — no new events). black/isort/flake8 clean.

Next: Day 3 drive-through (real UI + real backend + real Azure) — the between-turns pause is user-facing.

---

## Day 3 — 2026-06-08 — Drive-through (US-6) + CHANGE-059

### Clean backend restart (Risk Class E)

`:8000` was owned by stale PID 50548 (the 57.91 drive-through process, running PRE-57.92 code — no `note_tool`, no between-turns guardrail). Full uvicorn tree killed: worker PID 16992 (`multiprocessing.spawn` child) + reloader PID 50548; `:8000` verified to have NO LISTEN state (only TimeWait). Fresh backend started via `dev.py start backend` → `:8000` LISTEN owned by **fresh PID 53688** (loads 57.92 code). Frontend was on `:3007` (dev.py restarted it → PID 6200; node, START only). Azure config present in root `.env` (all 4 keys SET).

### Drive-through — real chat-v2 UI + real backend + real Azure gpt-5.2 — **PASS**

Logged in via dev-login as `dan@acme.com · admin` / `acme-prod`; chat-v2 `real_llm` mode; sent **"note the word checkpoint"**.

**Observed vs intended** (loop visualizer + turn blocks):

| Step | Intended | Observed | ✓ |
|------|----------|----------|---|
| Turn 0 LLM | calls `note_tool` (DEMO_SYSTEM_PROMPT) | `llm_request model=gpt-5.2` → `llm_response 1 tool call` → `tool_call_request note_tool` | ✅ |
| Tool exec | `note_tool` executes (NON-escalate) | `tool_call_result note_tool`, input `{"text":"checkpoint"}` → output `checkpoint`, `state_checkpointed v2` (turn 0 ran end-to-end INSIDE the loop) | ✅ |
| Between-turns gate | ESCALATE at top of turn 1 on the output | `approval_requested risk=HIGH` AFTER the TURN span ended → `state_checkpointed v3` (the pause checkpoint) | ✅ |
| Pause | `awaiting_approval`, no answer | `loop_end stop=awaiting_approval turns=1`; HITL card **`tool: —`** (between-turns-kind, no tool_call); no agent answer rendered | ✅ |
| Frontend | renders the HITL card generically (no tool) | card shows `severity: HIGH / tool: — / policy: always_ask` + Approve/Reject; **NO frontend change needed** (events tool-agnostic) | ✅ |
| Approve | resume continues to turn 1 LLM | clicked Approve → **`Decision: APPROVED`** | ✅ |
| Resume | gate SKIPPED (no re-pause), LLM answers | turn block `stop: end_turn` → answer **"checkpoint"** (the verbatim note output); NO second pause | ✅ |

Evidence: `artifacts/sprint-57-92-between-turns-1-paused.png` (HITL card, `tool: —`, `loop_end awaiting_approval turns=1`) + `artifacts/sprint-57-92-between-turns-2-resumed-answer.png` (`Decision: APPROVED` → `end_turn` "checkpoint").

**Proven**: the between-turns pause works end-to-end on 主流量 — `note_tool` is non-escalate (reaches the between-turns boundary, unlike echo_tool which tool-escalates); the gate ESCALATEs on the just-completed turn's output; the pause is a no-tool (`tool: —`) HITL card the existing frontend renders unchanged; resume APPROVED skips the just-approved boundary (no re-pause) and the LLM answers. Drive-Through Acceptance satisfied (NOT gate-only).

**Risk Class E re-applied**: did NOT trust `dev.py`'s prior state; killed ALL stale uvicorn procs (listener + spawn-worker) + verified `:8000` had no LISTEN owner before starting the fresh process.

---

## Day 4 — 2026-06-08 — Closeout

- retrospective.md (Q1-Q7) written; calibration-log.md §3 57.92 entry (4th `backend-core-loop-refactor` data point, 2nd consecutive feature-add < 0.7 → `loop-pause-point-feature` ~0.40 split PROPOSED for the next pause-point plan).
- CHANGE-059 + `19-pause-resume-design.md §5` (legs 1+2 SHIPPED, leg 3 deferred) + `17-cross-category-interfaces.md` (`LoopCompleted` 3rd origin + new `GuardrailType.BETWEEN_TURNS` enum value).
- MEMORY subfile `project_phase57_92_between_turns_pause.md` + MEMORY.md pointer; CLAUDE.md lean (Current Sprint row + Last Updated footer); next-phase-candidates.md 57.92 carryover (leg 3 / output-guardrail ESCALATE / subagent child-loop / loop-pause-point-feature class).
- Closeout commit; push + PR pending user authorization.

**Final**: pytest **2254 / 4 skipped** (+11) · mypy 0/350 · run_all 10/10 · black/isort/flake8 clean · **drive-through PASS** (real UI + real backend + real Azure gpt-5.2; 2 screenshots). Input/tool pause-resume tests byte-unchanged. NO frontend change. One additive contract value (`GuardrailType.BETWEEN_TURNS`).
