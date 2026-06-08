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
