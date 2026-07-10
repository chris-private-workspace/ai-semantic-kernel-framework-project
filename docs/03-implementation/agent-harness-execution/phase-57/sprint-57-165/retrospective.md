# Sprint 57.165 Retrospective — LLM-assisted `--fix` for the tool-description lint

**Closed**: 2026-07-10 · **Branch**: `feature/sprint-57-165-tool-desc-autofix` · **CHANGE-132** · **design note 64**

## Q1 — What shipped

Closes ③2 `AD-Tool-Description-AutoFix` (the last core Tool-range carryover → Tool range **4/4**). The 57.144 tool-description lint gains an opt-in `--fix` (LLM-drafts a description for each flagged tool/param via the neutral cheap-tier `ChatClient`, self-validated against the lint's own predicate) + `--fix --write` (applies via position-based AST splicing). Apply-mode = Option B (user pick): dry-run report by default, `--write` to apply, `git diff` = 2nd gate. Folded into `check_tool_descriptions.py` (one module) with a LAZY backend adapter import → the CI report path is byte-identical + imports nothing new. Backend/CI-tooling only — NO agent_harness runtime / migration / wire / frontend / drive-through.

Real-Azure smoke PASS: a 5-gap fixture → 5/5 drafts (all 3 kinds) → `--write` applied → re-lint `OK`.

## Q2 — Estimate accuracy / calibration

- Scope class **NEW `tool-autofix-spike` 0.60** (anchored to `tool-reflection-and-lint-spike` 0.60 (57.144, same Cat 2 lint + measurement family) + the `benchmark-*` harness 0.60 family; a real-code core = the self-validating drafter + a 3-kind position-based splicer + 24 tests + the smoke, ≥ ~3.5 hr → the 0.60 spike multiplier holds per the 57.137 lesson, NOT a tiny-code 0.85 re-point).
- **Agent-delegated: no** (parent-direct — the splice correctness, the neutral-client discipline, the self-validation loop, and the Option-B semantics all needed the parent). `agent_factor` 1.0 → 3-segment.
- Bottom-up ~8.5 hr → class-calibrated commit ~5.1 hr (mult 0.60). **Actual ≈ 5-5.5 hr equiv → ratio ~1.0-1.08, IN band.** The work ran smoothly: one Day-1 `@dataclass`-under-importlib bug (root-caused via the existing checker tests also failing → `NamedTuple`), one E501, and the Day-0/Day-1 fold-into-checker refinement (which SIMPLIFIED the plan, saving the sibling-module + importlib-context work). The smoke ran first try. **KEEP 0.60** (1st data point IN band). If a 2nd `tool-autofix-spike` lands > 1.20, re-point toward 0.75 (the splice edge-cases + real-Azure smoke staging are the variance risk).

## Q3 — What went well / key lesson

- **Reusing the checker's own predicates single-sourced the "what is a violation" rule.** `collect_fix_targets` reuses `MIN_DESCRIPTION_LEN` / `PLACEHOLDER_RE` / `_const_str` / `_dict_get` / `_kwarg` / `_toolspec_calls` → the fix targets exactly mirror the lint's flags; no drift risk.
- **The non-Potemkin discipline paid off twice**: (1) the `run_fix` orchestration is glue that builds a real client, so I monkeypatched `_build_cheap_client` + `_draft_all` to test the write-across-files path WITHOUT Azure (3 tests) instead of leaving it untested; (2) the real-Azure smoke actually drove the tool end-to-end (drafted + applied + re-lint OK), catching the honest cosmetic findings (smart quotes, key ordering) that a fake-client test never would.
- **The self-validation loop is the honest core**: `--fix` never emits a lint-failing draft (retry → `NEEDS_MANUAL`), so the tool can't produce output that would re-trip the very lint it assists.

## Q4 — What to improve next

- **The `@dataclass`-under-importlib bug cost a debug cycle.** The existing test uses `importlib.util.spec_from_file_location` (not registered in `sys.modules`), and `@dataclass` + `from __future__ import annotations` needs the module in `sys.modules`. Lesson: when a module is loaded by importlib file-path in tests, prefer `NamedTuple` (like the existing `Violation`) over `@dataclass`, OR register the module in `sys.modules` in the loader. Recorded for future `scripts/` tooling.
- **Day-0 could have flagged the code-location fold earlier.** The plan assumed a sibling `_autofix.py`; reading the existing test's importlib loader at Day-0 Prong-2 (I did read `test_tool_descriptions.py`, but only during Day-1) would have surfaced the fold-into-checker decision before the plan committed to a sibling. For a "new script that imports another script's helpers" sprint, Day-0 should grep the consumer test's import mechanism.

## Q5 — Anti-pattern self-check

- AP-2 (side-track): `--fix` is reachable from the CLI + the real-Azure smoke drove it end-to-end (not dead code) — ✅
- AP-3 (scattering): all in one module (`check_tool_descriptions.py`) + one test file; NOT a scattered sibling — ✅
- AP-4 (Potemkin): the smoke + the monkeypatched `run_fix` tests prove the write path actually writes correct fixes (re-lint OK); the self-validation prevents lint-failing drafts — ✅
- AP-6 (speculative abstraction): no new dep (position-based splice, not libcst); reuses the ChatClient ABC + the checker's predicates — ✅
- AP-8 (PromptBuilder): N/A (a dev tool, no agent prompt) — ✅
- AP-10 (mock/real divergence): the smoke ran on the REAL cheap-tier Azure model + a real file write, not a stub — ✅
- AP-11 (version suffix): none — ✅
- v2 lints 11/11; the drafter's adapter import is lazy → `check_llm_sdk_leak` clean.

## Q6 — Carryover (→ next-phase-candidates)

- **ASCII-normalize drafts** — the model emitted Unicode smart quotes; a future polish could normalize (the ⚠ banner + git-diff gate cover it for now).
- **Param-key insert ordering** — `insert_param_desc` inserts `"description"` first; a future splice could anchor after the last key.
- **`AD-Tool-Autofix-Selection-Impact-Phase58`** — a runtime A/B on whether autofixed descriptions improve live tool selection (no cheap metric today).
- The 57.164 follow-ons remain open: `AD-Tool-Taxonomy-HumanLabel` / `AD-Tool-Reflection-PerTier-Default` / `AD-Tool-Reflection-RarePath-Near-Dead-Evaluate` / `AD-Tool-Failure-Terminate-vs-Recoverable-Policy` / `AD-RequestApproval-Placeholder-Deprecated`.

## Q7 — Gate summary

run_all 11/11 · pytest `tests/unit/scripts/lint/` 46 passed (24 NEW autofix + 10 checker unbroken + 12 other) · **full backend pytest 3255 passed, 5 skipped** (baseline 3231 + 24, 139.95s, exit 0 — no regression) · black/isort/flake8 clean (100 std) · lint self-run `OK` byte-identical · mypy `src` 400/0 UNAFFECTED (changes outside `src/`) · LLM-SDK-leak clean · real-Azure smoke PASS. NO migration / wire / frontend / drive-through.

## Design Note Extract (spike sprint)

**File**: `docs/03-implementation/agent-harness-planning/64-tool-description-autofix-design.md`
**Verified ratio (estimated)**: ≥ 95%
**8-Point Quality Gate**:
- [x] 1. Section headers map to spike US (US-1..US-3 in §2)
- [x] 2. file:line / function anchors for every technical claim (§2, §3, §2.5 config.py:37-43)
- [x] 3. Decision matrix (§1 — 5 decisions incl. Option B + fold-into-checker + NamedTuple)
- [x] 4. Verification commands (§2.1-2.5 pytest -k + the smoke reproduce block)
- [x] 5. Test fixture reference (§2.5 fixture + the fake-client unit suite)
- [x] 6. Open invariant boundary explicit (§4 — 4 deferred items)
- [x] 7. Rollback path (§5 — ~15 min, cannot affect CI)
- [x] 8. 17.md cross-ref (§3 — none new; consumes existing ChatClient ABC)

**Reviewer pass**: self-review (parent-direct spike).
