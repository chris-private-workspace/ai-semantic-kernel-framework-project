# Sprint 57.89 Retrospective — run() Re-entrancy Refactor Slice 1 (pure extraction)

**Sprint**: 57.89 / **Branch**: `feature/sprint-57-89-run-loop-reentrancy` / **Closed**: 2026-06-08
**Plan**: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-89-plan.md`
**Type**: REFACTOR (Cat 1 core) → REFACTOR-006, no design note.

---

## Q1 — Goal & outcome

Goal: extract run()'s per-turn body into a re-enterable `_run_turns(...)` unit with ZERO behavior change (gate = full backend pytest unchanged), as Slice 1/2 of paying down `AD-Resume-Continuation-Fidelity`. **Hit in full.** `_run_turns` extracted; run() delegates; pytest 2231 = 2229 (loop UNCHANGED) + 2 (detector); mypy 0/346; run_all 10/10; resume()/_resume_continuation byte-unchanged.

## Q2 — Estimate accuracy (calibration)

- Scope class: **`backend-core-loop-refactor` 0.55 (NEW, 1 data point, pending validation)** — high-care pure-extraction of the 主流量 Cat 1 `run()` body (797-line deeply-nested block) with a byte-identical-behavior gate.
- `agent_factor`: **1.0 (parent-direct)** — too high-blast-radius to delegate (plan §7); the mechanical move was done programmatically (the Sprint 57.71 pattern), parent-run gates.
- Committed: bottom-up ~10 hr → ~5.5 hr (mult 0.55).
- **Ratio**: the analysis note pre-did the read (the costly part), and the programmatic move + clean gate landed in one Day → actual well under the ~5.5 hr commit (ratio likely < 0.7). But it's a **single data point + the pre-done analysis confound** the measurement → record CAVEATED, KEEP 0.55, no generalization. Note: parent-direct here (NOT agent-delegated) so this does NOT extend the `AD-Calibration-AgentDelegated-WallClock-Measure` streak.
- Record to `calibration-log.md §3`.

## Q3 — What went well

- **The "full pytest unchanged" gate is the perfect proof for a pure refactor** — 2229 → 2229 (for the loop) is unambiguous: behavior is byte-identical. No need to author characterization tests for the extraction.
- **Programmatic move + dry-run-first** (the 57.71 pattern) de-risked an 800-line re-indent: the dry-run verified unique anchors + uniform ≥8-space indent BEFORE any write; `py_compile` + `mypy` then caught structure/undefined-name issues before the (expensive) full suite.
- **mypy as a free completeness check**: `mypy loop.py` "no issues" confirmed `_run_turns`'s param list was complete (a missing free variable = `[name-defined]`) — caught the "did I pass every local?" risk for free.
- **Day-0 analysis paid double**: the analysis note's ground-truth read = most of Prong-2, so Day-0 was fast and the extraction had no surprises.

## Q4 — What to improve / lessons

- **A 主流量 refactor has lint blast-radius too** — the AP-1 detector false-positived because it assumed the `while` is lexical in `run()`. Lesson: when extracting a method out of a lint-anchored method, check the AP-N detectors' heuristics, not just the tests. (Caught by run_all before commit.)
- **Don't run flake8 from repo root for `scripts/`** — it picks the default 79-char limit (no `.flake8` there), a false alarm; the project config (100) is backend-scoped and CI doesn't flake8 `scripts/`. Confirmed my lines via `black` (88) instead.
- **The +2 test-count delta needed honest framing** — "pytest unchanged (2229)" held for the LOOP extraction; the +2 detector tests are a documented consequence of the lint enhancement, not a smuggled change. Stated explicitly (progress Day-1) rather than quietly moving the baseline.

## Q5 — Action items / carryover (→ `next-phase-candidates.md`)

- **Slice 2** (the immediate next): rewire `resume()` to execute the pre-approved pending tool then drive `_run_turns`; **DELETE `_resume_continuation`**; multi-pause-per-run (2nd ESCALATE in continuation pauses again) + drive-through. The pre-approved-pending-tool-must-not-re-escalate decision (analysis note §6.1) locks in the Slice-2 plan.
- Slice 3 (generalized pause) + subagent child-loop (Cat 11) downstream.
- Remaining 57.88 carryover ADs (checkpoint-bloat / tenant-capability-policy / reject-path) unchanged.

## Q6 — Discipline self-check

- ☑ Plan → Checklist → Day-0 verify → Code → Update checklist → Progress → Retro (5-step honored)
- ☑ No future sprint plan pre-written (rolling); analysis note is grounding, not a pre-written plan
- ☑ No unchecked `[ ]` deleted
- ☑ LLM neutrality (no adapter/SDK touched; `check_llm_sdk_leak` 0); no multi-tenant surface touched (pure internal refactor)
- ☑ File headers + MHist updated (loop.py structural change; detector); MHist 1-line E501-safe (57.88 lesson applied — checked the new line)
- ☑ No drive-through needed (no user-facing change; Slice 2 carries it) — stated, not implied
- ☑ Format chain run (black/isort/flake8) — the 57.88 lesson (don't skip it) applied from the start

## Q7 — Numbers

pytest 2231 passed / 4 skipped (2229 loop UNCHANGED + 2 detector) · mypy 0/346 · run_all 10/10 · black+isort+flake8 clean · 3 commits (8965a8c7 Day-0 setup → 75243368 extraction → closeout). loop.py 2240→2272 lines (+32 net; 797-line body moved).
