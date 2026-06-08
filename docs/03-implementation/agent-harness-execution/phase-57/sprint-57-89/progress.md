# Sprint 57.89 Progress — run() Re-entrancy Refactor Slice 1 (pure extraction)

**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-89-plan.md`
**Branch**: `feature/sprint-57-89-run-loop-reentrancy` (from `main` `e2948810`)
**Analysis**: `claudedocs/1-planning/run-loop-reentrancy-refactor-analysis-20260608.md`

---

## Day 0 — 2026-06-08 — Plan-vs-Repo Verify + Branch

### Branch
- `feature/sprint-57-89-run-loop-reentrancy` created from main.

### Three-prong verify (GO)

**Prong 1 (path)** — confirmed against the analysis note's ground-truth read:
- `run()` @`loop.py:960`; entire body wrapped in `async with self._tracer.start_span(name="agent_loop.run", LOOP) as root_ctx:` (1002) → `_root_ctx_t0 = monotonic()` (1008) → `try:` (1009) → `yield LoopStarted` (1014) + `yield SpanStarted(LOOP)` (1015) → `async for ev in self._cat9_input_check(...)` (1030, return on LoopCompleted) → **`while True:` (1035)** … `turn_count += 1` (1830) → `finally: yield SpanEnded(LOOP)` (1832-1839).
- The per-turn body has its OWN `async with` TURN span + `try/finally: yield SpanEnded(TURN)` (…1821-1828) inside the while.
- `resume()` @1841 / `_resume_continuation` @1992 — **NOT touched this sprint**.

**Prong 2 (content — accumulator enumeration; the US-2 no-field-loss contract)** — per-run mutables initialized in run()'s preamble + threaded through the while body:
- `messages: list[Message]` (969) — system+user seed; appended assistant/tool messages through the body; passed to `_emit_state_checkpoint` (1811-1818) + PromptBuilder.
- `turn_count` (974) — checked `should_terminate_by_turns` (1037); incremented (1830); stamped `total_turns` on every `LoopCompleted`.
- `tokens_used` (975) — checked `should_terminate_by_tokens` (1045); incremented post-LLM; stamped `total_tokens`.
- `metrics_acc = LoopMetricsAccumulator()` (980) — Sprint 57.2 per-run accumulator (token split / provider attribution / 57.65 cache / etc.); stamped onto `LoopCompleted` fields.
- span carriers: `root_ctx` (1007) + `_root_ctx_t0` (1008).
- **Preservation guarantee**: the extraction is a VERBATIM move of the while block (1035-1831) into `_run_turns`, uniformly dedented by 8 spaces. Every update + every `LoopCompleted` stamp moves intact → no field loss by construction. `check_event_schema_sync` + the existing token/cache tests are the post-move guard.
- Note: `verification_*` fields (57.82) are stamped by the OUTER correction-loop wrapper AFTER `LoopCompleted`, NOT by run() itself → not in run()'s extraction scope (untouched).

**Prong 3 (schema)** — N/A: no DB / migration / ORM change this sprint.

### Baseline capture (to prove "unchanged" at the gate)
- Pre-sprint baseline = main `e2948810`: pytest **2229 passed / 4 skipped**, mypy **0 / 346**, run_all **10/10** (from Sprint 57.88 closeout, same HEAD). Will re-confirm exact numbers in Day-1 before editing.

### Drift findings
- **D-DAY0-1 (design refinement, documented — NOT silent; AP-2)** — plan §3.1 proposed a `LoopState` carrier for `_run_turns`. Day-0 read shows the **raw-locals signature** (`session_id, messages, turn_count, tokens_used, metrics_acc, ctx, root_ctx`) is the lower-risk pure extraction (introducing a new state object mid-extraction could itself shift behavior) AND is still reusable by resume() in Slice 2 (resume unpacks its `LoopState` → these args). → adopt raw-locals; plan §3.1's LoopState framing was aspirational. Recorded here per the "no silent plan rewrite" rule.
- **D-DAY0-2 (span ownership)** — the LOOP `async with` + `try/finally: SpanEnded(LOOP)` STAYS in run() (per plan §3.3); `_run_turns` receives `root_ctx` as a param so the per-turn TURN spans still nest under it. A `return` inside `_run_turns` ends the generator → run()'s `async for` completes → run()'s `finally` fires SpanEnded(LOOP) → behavior-identical (the LOOP SpanEnded still emits on every exit path).
- **D-DAY0-3 (boundary)** — extraction block = the `while True:` (1035) through `turn_count += 1` + comment (1830-1831), i.e. up to (not including) the try's `finally:` at 12-space indent (1832). Uniform dedent by 8 (while `True:` 16→8).

### go/no-go = **GO** (scope unchanged; raw-locals signature adopted per D-DAY0-1; verbatim-move strategy locks zero-behavior-change)

### Next: Day 1 — extract `_run_turns` (programmatic verbatim move + dedent, like Sprint 57.71's 472-line re-indent) → run() delegates → full regression gate (pytest UNCHANGED).

---

## Day 1 — 2026-06-08 — Extraction + full gate (parent-direct)

Parent-direct (no agent delegation — high-blast-radius 主流量 extraction per plan §7). Programmatic move (the Sprint 57.71 pattern), parent-run gates.

### Done (US-1/US-2/US-3 + the AP-1 fallout)
- **Extraction** — dry-run script confirmed the boundary (CRLF; `while True` @1035 unique; try-`finally` @1832 unique; 797-line block; all non-blank lines ≥8-space indent → clean dedent-by-8). Applied: verbatim move + uniform dedent-by-8 into NEW `_run_turns(self, *, session_id, messages, turn_count, tokens_used, metrics_acc, ctx, root_ctx) -> AsyncIterator[LoopEvent]`; `run()` keeps input guardrail + LOOP-span try/finally and delegates via `async for ev in self._run_turns(...): yield ev`. File 2240 → 2272 lines (+32 = sig+delegation; body moved). `py_compile` OK.
- **Raw-locals signature (D-DAY0-1)** adopted over plan §3.1's LoopState carrier — lower-risk + still resume-reusable. `mypy loop.py` "no issues" CONFIRMS no undefined free variable (a missing param would be `[name-defined]`).
- **AP-1 lint false positive fixed** — `check_ap1_pipeline_disguise.py` required the `while` lexically in `run()`; extraction moved it to `_run_turns`. Added delegation-aware `run_drives_while_loop()` (run() may drive the loop via a sibling it calls; one hop). Intent preserved (for-pipeline-behind-helper still fails). Detector test +2 (delegated-while passes / delegated-no-while fails) + stale "must contain"→"must drive" assertion fixed. `black`-clean (E501-at-79 from running flake8 at repo root w/o the backend `.flake8` 100-config = false alarm; scripts/lint not in CI flake8 scope; my lines ≤88).

### Parent re-verify (all gates run by parent)
- **pytest 2231 passed / 4 skipped** = 2229 (loop extraction **UNCHANGED** — the zero-behavior-change proof) + 2 (new AP-1 detector tests). 104s.
- `mypy src/` **0 / 346** ✅ · `run_all` **10/10** ✅ (AP-1 delegation-aware green) · black + isort + flake8 clean (loop.py + detector + test).
- `test_reconstructs_loop_turn_operation_tree_with_correct_nesting` + 8 pause-resume unit + 5 integration green (span tree + pause path intact — both in the 2231).
- **Scope-guard**: `git diff main -- loop.py` → 0 +/- lines touching `resume()` / `_resume_continuation` (byte-unchanged; Slice 2 untouched).

### Justified test-count delta (honest)
- Plan §Acceptance said "pytest UNCHANGED (2229)". Actual 2231 = 2229 **unchanged for the loop extraction** (the contract held) + 2 NEW detector tests. The +2 is the AP-1 detector enhancement (a necessary consequence — the lint had to learn the legitimate delegation pattern), NOT a smuggled behavior change. Documented per the "no silent scope change" rule.

### Files changed (Day-1)
- `backend/src/agent_harness/orchestrator_loop/loop.py` (extract `_run_turns` + run() delegates + MHist)
- `scripts/lint/check_ap1_pipeline_disguise.py` (delegation-aware while check + docstring/MHist)
- `backend/tests/unit/scripts/lint/test_ap1_pipeline_disguise.py` (+2 tests + assertion fix)
- Commit `75243368`.

### Next: closeout — REFACTOR-006 + retrospective + calibration + MEMORY.md + CLAUDE.md lean; push + PR (user-authorized).

---

## Day 2-4 (compressed) — 2026-06-08 — Closeout

The extraction + full gate landed Day-1 (single mechanical move; the per-day split in the checklist collapsed since a pure extraction is one atomic change verified by the unchanged suite). Closeout:
- REFACTOR-006 written.
- retrospective.md (Q1-Q7 + calibration).
- calibration-log §3: `backend-core-loop-refactor` 0.55 (NEW, 1 pt, caveated) + `agent_factor` 1.0 (parent-direct).
- MEMORY.md pointer + `project_phase57_89_run_loop_reentrancy.md` subfile + CLAUDE.md lean.
- No drive-through (no user-facing change — Slice 1 gate is the unchanged suite; Slice 2 carries the drive-through).

### Next: closeout-docs commit + push + PR — user-authorized.
