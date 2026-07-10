# Sprint 57.165 Plan — LLM-assisted `--fix` for the tool-description lint

**Summary**: The Tool-range's last core carryover (③2 `AD-Tool-Description-AutoFix`). The 57.144 `check_tool_descriptions.py` lint REPORTS flawed tool/param descriptions but does not draft replacements. This sprint adds an opt-in `--fix` mode that drafts descriptions via the neutral `ChatClient` ABC (cheap tier), plus a `--write` mode that applies the drafts to source (user AskUserQuestion pick: **Option B — default dry-run report, explicit `--write` to apply, git-diff = 2nd review gate**). Backend/CI-tooling only — NO agent_harness runtime change / NO migration / NO wire / NO frontend, and therefore **NO drive-through** (dev/CI tooling, no user-driven UI surface; pure-tooling exemption per Before-Commit item 8). Closes ③2 → the Tool range becomes 4/4 done. CHANGE-132. Spike sprint → design note required.

**Status**: Draft (awaiting user approval to execute; `--fix` apply-mode = Option B fixed via AskUserQuestion 2026-07-10)
**Branch**: `feature/sprint-57-165-tool-desc-autofix`
**Base**: `main` HEAD after Sprint 57.164 merges (sha TBD at branch-creation; 57.164 = PR-pending, `107148e7`). If 57.164 has not merged when this starts, branch from its tip instead + rebase on merge.
**Slice**: closes ③2 `AD-Tool-Description-AutoFix` (57.144 carryover) — the LAST core Tool-range item (③1+④ 57.163 / ③3 57.164 already done → 4/4).
**Scope decisions**: (a) **Option B apply-mode** — `--fix` dry-run report by default; `--fix --write` applies to source; git-diff is the 2nd conscious gate. (b) **No new dep** — `--write` uses position-based AST splicing (`ast` node end-position spans), NOT libcst. (c) **Neutral drafting client** — build via `adapters.azure_openai.profile.build_azure_model_profile().cheap`, lazy-imported only under `--fix`; CI reporting path unchanged + imports nothing new. (d) **Self-validating drafts** — each LLM draft is re-checked against the very lint before it is reported/written (retry once, else flag as `<needs-manual>`), so `--fix` never emits a draft that still fails.

---

## 0. Background

### The gap (③2 `AD-Tool-Description-AutoFix`)

`scripts/lint/check_tool_descriptions.py` (57.144 Half A) is the 11th run_all lint: it flags every `ToolSpec(...)` with a missing / empty / `<20`-char / placeholder `description=`, and every `input_schema` property lacking a `description`. It **reports and stops** — the developer must hand-author each fix. The 57.144 design note listed this as the open follow-on: *"lint reports, doesn't fix."*

### Why it matters (the missing capability)

Research #7 (`ai-agent-harness-consolidated-analysis §2.3`): tool-description quality measurably affects tool selection. When a new tool lands with a stub description, the lint blocks the PR but leaves the author to draft prose cold. An opt-in `--fix` that drafts a first-cut description (which the author reviews for accuracy) removes the toil of the blank page while keeping the human as the accuracy gate — the whole point of Option B's two review gates (read the draft → decide to `--write` → review `git diff`).

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main`, verified via 57.144 artifacts) | Anchor |
|-------|-----------------------------------------------------|--------|
| Lint core is pure AST, report-only | `find_violations(root) -> list[Violation]`; `main()` prints + exits 1 | `scripts/lint/check_tool_descriptions.py:164,196` |
| Violation carries the anchor | `Violation(file, lineno, tool, reason)` — has file+lineno but NOT the AST node span | `check_tool_descriptions.py:61` |
| CI invocation has no `--fix` | run_all calls `["--root", "backend/src"]` only | `scripts/lint/run_all.py:89` |
| No source-rewrite dep | `libcst` absent from pyproject/requirements | (grep 0 matches) |
| Neutral client build precedent | `from adapters.azure_openai.profile import build_azure_model_profile` lazy in async main; `profile.cheap` ChatClient; `RUN_AZURE_INTEGRATION=1` gate | `backend/scripts/benchmark_tool_error_reflection.py:306-318` |
| Lint runs at top-level `scripts/lint/` | it does NOT import `backend/src`; `adapters` needs `backend/src` on `sys.path` | (`--fix` sys.path decision — Day-0) |

→ The fix must (1) extend `Violation` to carry the AST node span (for `--write` splicing), (2) add a neutral LLM drafter, (3) add a position-based source splicer gated behind `--write`, all WITHOUT changing the pure CI reporting path or adding a dependency.

### The design (backend/tooling-only: 1 lint file extended + 1 sibling autofix module + drafter + splicer + fixtures + smoke)

```
scripts/lint/check_tool_descriptions.py   EDIT  find_violations now records node spans;
                                                main() gains --fix / --write; when --fix,
                                                lazy-delegate to _autofix (CI path unchanged)
scripts/lint/_autofix.py                   NEW   draft_descriptions(violations, client)  — neutral LLM drafting
                                                 apply_fixes(source, drafts)            — position-based AST splice
                                                 render_report(drafts)                  — dry-run stdout report
                                                 (lazy sys.path insert of backend/src for the adapter)
backend/scripts/... (drafting client)      —     reuse adapters.azure_openai.profile.build_azure_model_profile().cheap
tests/unit/scripts/lint/test_tool_description_autofix.py  NEW  fake-client drafting + splice + idempotency + self-validate
```

The drafter prompt (neutral, cheap tier) gets: tool name + its `input_schema` shape + the existing (too-short) description (if any) for a tool-level fix; or tool name + tool description + param name + param schema for a param fix. It returns ONE imperative sentence (`MIN_DESCRIPTION_LEN..~200` chars, placeholder-free). Each draft is re-run through the lint's own predicate before it is emitted (self-validation; retry once, else mark `<needs-manual>`).

The splicer (`--write` only) uses the AST node's `lineno/col_offset/end_lineno/end_col_offset`: **replace** an existing string-literal description in place; **insert** a `description=<quoted>` kwarg on a ToolSpec (anchor = after `name=`); **insert** a `"description": <quoted>` key into a param property `ast.Dict`. Re-running `--write` on already-fixed source finds 0 violations → no-op (idempotent).

### Ground truth (recon head-start — code read; ALL re-verified §checklist 0.1)

- `scripts/lint/check_tool_descriptions.py:164` — `find_violations` is the shared pure core; keep it CI-deterministic (no backend import on the report path).
- `scripts/lint/run_all.py:89` — CI calls the lint with `--root backend/src` only; `--fix`/`--write` are opt-in and never hit CI.
- `backend/scripts/benchmark_tool_error_reflection.py:306-318,347-353` — neutral client build (`build_azure_model_profile().cheap`) + `RUN_AZURE_INTEGRATION` gate + cp950 stdout reconfigure to mirror.
- The lint currently passes with 0 violations (57.144 filled all 40) → `--fix` is exercised via tmp_path fixtures + an opt-in real-Azure smoke on a deliberately-stripped fixture, NOT on live source.

**Baselines (57.164 closeout)**: pytest 3231 (+5 skip) · run_all 11/11 (incl. `check_tool_descriptions`) · mypy `src` 400/0 · wire 26 / Vitest 933 / mockup 51 (this sprint touches NONE of wire/FE/mockup). Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-sys-path-fix** — confirm the lazy `sys.path` insert of `backend/src` resolves `adapters.azure_openai.profile` when `--fix` runs from repo root (`python -m scripts.lint.check_tool_descriptions --fix`); if the import fails, fall back to running the drafter as a `backend/scripts/` sibling. Shifts §8 risk row.
- **D-node-span-avail** — confirm `ast.Call` / `ast.Dict` / `ast.Constant` nodes expose `end_lineno`/`end_col_offset` in the repo's Python (3.8+ yes); verify the ToolSpec literals in `backend/src` are single-call (not built across statements) so a span-splice is well-defined.
- **D-profile-cheap** — verify `build_azure_model_profile().cheap` is a `ChatClient` with the `.chat(ChatRequest)` shape the drafter will call (mirror 57.144 usage), not a different attr.
- **D-runall-untouched** — confirm run_all's entry stays `["--root", "backend/src"]` (no `--fix`) so the CI gate is byte-identical.

## 1. Sprint Goal

Ship an opt-in `--fix` (dry-run draft report) + `--fix --write` (apply to source) on the existing tool-description lint, so a flagged description can be first-cut drafted by the neutral cheap-tier `ChatClient` and consciously applied by the developer (report → `--write` → `git diff`). PROVEN by: CI-safe unit tests (fake client) covering drafting + self-validation + the position-based splice for all three mutation kinds + idempotency + the CI reporting path staying byte-identical (run_all 11/11 unchanged); PLUS an opt-in real-Azure smoke drafting a description for a deliberately-stripped fixture tool and confirming the draft passes the lint (honest accuracy note, NOT an A/B — there is no runtime metric). NO drive-through (dev/CI tooling, no user-driven surface). CHANGE-132 + a spike design note.

## 2. User Stories

- **US-1** (drafting): 作為維護工具的開發者，我希望 `--fix` 用中性 cheap-tier LLM 為每個被 lint 標記的 tool/param 草擬一句描述並印成報告（source 不動），以便我讀過、判斷準確性後決定是否套用。
- **US-2** (apply): 作為開發者，我希望 `--fix --write` 把草稿以 position-based splice 寫入 source（replace 字串 / insert `description=` kwarg / insert param key），並且對已修好的 source 重跑是 no-op，以便我用 `git diff` 做第二道把關。
- **US-3** (evidence): 作為維護者，我希望一個 opt-in real-Azure smoke 對「故意抽掉描述」的 fixture 跑 `--fix`，確認草稿能通過原 lint，以便證明它非 Potemkin（誠實記錄準確性，非 A/B）。
- **US-4** (closeout): 作為維護者，我希望 CHANGE-132 + design note + 校準 + navigators + next-phase 更新，以便 ③2 CLOSED、Tool range 4/4。

## 3. Technical Specifications

### 3.0 Architecture (backend/CI-tooling only — NO agent_harness runtime / migration / wire / frontend / drive-through)

```
EDIT   scripts/lint/check_tool_descriptions.py
         - Violation gains an optional node-span field (col_offset/end_lineno/end_col_offset)
           OR find_violations returns (Violation, ast.Call/ast.Dict) pairs for --fix
         - main() += --fix / --write; when --fix → lazy import scripts.lint._autofix, delegate
         - the no-flag path (run_all CI) is byte-identical (same find_violations + print + exit)
NEW    scripts/lint/_autofix.py
         - _ensure_backend_on_path()            lazy sys.path insert of backend/src (only on --fix)
         - draft_description(client, context)    neutral ChatClient .chat() → one sentence, self-validated
         - draft_all(violations, client)         → {violation: draft|"<needs-manual>"}
         - apply_fixes(text, drafts) -> str       position-based AST splice (replace / insert kwarg / insert key)
         - render_report(drafts) -> str           dry-run stdout report (grouped by file)
         - build_cheap_client()                   build_azure_model_profile().cheap (lazy, RUN_AZURE gate)
NEW    tests/unit/scripts/lint/test_tool_description_autofix.py   CI-safe (fake client), tmp_path fixtures
NEW    (opt-in) a stripped fixture tool for the real-Azure smoke (tmp / fixture, NOT live source)
```

### 3.1 Drafting (US-1) — `scripts/lint/_autofix.py`

- `draft_description(client, ctx)` builds a neutral `ChatRequest` (system: "you document tools for an LLM agent; write ONE imperative sentence, ≥20 chars, no TODO/FIXME/XXX/TBD"; user: the tool/param context) → `client.chat(...)` → strip to one line.
- **Self-validation**: run the draft through the same predicates the lint uses (`len >= MIN_DESCRIPTION_LEN`, `not PLACEHOLDER_RE.search`, non-empty). Fail → retry once with a terser instruction; still fail → emit `"<needs-manual>"` (never a lint-failing draft).
- Provider-neutral: the drafter takes a `ChatClient` param; only `build_cheap_client()` touches `adapters.*` (lazy). CI tests inject a fake client returning canned strings.

### 3.2 Apply (US-2) — position-based splice, `--write` only

- Requires `find_violations` (or a `--fix`-only variant) to surface the AST node so the splice target span is known. Three mutation kinds:
  - **replace** existing description literal: overwrite `[Constant span]` with the quoted draft.
  - **insert** missing `description=` kwarg: splice `description=<quoted>,` right after the `name=` kwarg value's end (or before the ToolSpec closing paren).
  - **insert** missing param `"description"`: splice `"description": <quoted>,` after the property `ast.Dict`'s opening brace.
- Multiple edits per file are applied **back-to-front** (highest offset first) so earlier splices don't shift later spans.
- Idempotent: after `--write`, re-running finds 0 violations for those tools → no-op.
- Quoting: emit a normal double-quoted string with `repr`-safe escaping; keep it single-line (≤ ~200 chars) to avoid multi-line reflow.

### 3.3 CI reporting path stays pure (US-1/US-2)

- run_all's `check_tool_descriptions.py --root backend/src` (no `--fix`) imports nothing new, does nothing new → run_all 11/11 byte-identical.
- `_autofix` (backend/adapter-dependent) is imported ONLY inside the `--fix` branch → a CI import of the lint never pulls `adapters`.

### 3.4 Evidence (US-3) — real-Azure smoke, NOT an A/B

- A tmp/fixture ToolSpec with a stripped description → `--fix` (real cheap tier, `RUN_AZURE_INTEGRATION=1`) → assert every draft passes the lint predicate + eyeball 1-2 for accuracy → record in the design note (honest: "drafts are a first cut for human review; N/N passed the lint, accuracy eyeballed OK/notes"). No metric to A/B — the value is toil reduction with a human accuracy gate.

### 3.x What is explicitly NOT done

- **No auto-apply without `--write`** (Option B): `--fix` alone never touches source.
- **No libcst / new dependency** (position-based `ast` splice instead).
- **No CI-gate change**: `--fix` is never wired into run_all; the reporting lint remains the only CI gate.
- **No runtime behavior change**: agent_harness / loop / executor untouched → 0 chance of a live regression.
- **No multi-line / comment-preserving reflow** beyond single-line description insertion (a description is one sentence).
- **No batching/parallel drafting optimization** (YAGNI; the corpus is a handful of violations at a time).

### 3.y Validation (US-1..US-4)

Gates: mypy `src` 400/0 (this sprint edits `scripts/` — confirm scripts stay within the mypy scope they were in) · run_all 11/11 (unchanged — the report path is byte-identical) · pytest ≥ 3231 (+ new autofix unit tests) · black/isort/flake8 clean · LLM-SDK-leak clean (the drafter goes through the ChatClient ABC + adapter, no direct `import openai/anthropic`). NO Vitest/mockup/build delta (no FE). **No drive-through** (tooling). Plus the §3.4 opt-in real-Azure smoke.

## 4. File Change List

> **Day-1 refinement** (progress.md §Day-1 D-fold-into-checker): the `--fix`/`--write` logic is FOLDED INTO `check_tool_descriptions.py` (one module) instead of a sibling `_autofix.py` — a sibling's `from scripts.lint.check_tool_descriptions import <predicates>` fails under the existing test's importlib file-path load (from `backend/`, `scripts.lint` is not an importable package). One module keeps the predicates single-sourced + directly testable; the backend adapter import stays lazy so the CI report path is byte-identical. Test dir is `backend/tests/…` (not top-level `tests/`).

| # | File | Action |
|---|------|--------|
| 1 | `scripts/lint/check_tool_descriptions.py` | EDIT (add `--fix`/`--write` + collect_fix_targets + async self-validating drafter + position-based splicer + dry-run report + LAZY backend adapter import; no-`--fix` report path byte-identical) |
| 2 | ~~`scripts/lint/_autofix.py` NEW~~ | **DROPPED** — folded into #1 (Day-1 D-fold-into-checker) |
| 3 | `backend/tests/unit/scripts/lint/test_tool_description_autofix.py` | NEW (fake-client drafting + splice 3 kinds + idempotency + self-validate; importlib file-path load like the existing checker test) |
| 4 | (fixtures) | inline `tmp_path` `ToolSpec(...)` literals (mirror the existing `test_tool_descriptions.py`); a separate fixture file only if the real-Azure smoke needs one |
| 5 | `claudedocs/4-changes/feature-changes/CHANGE-132-tool-description-autofix.md` | NEW |
| 6 | `docs/03-implementation/agent-harness-planning/64-tool-description-autofix-design.md` | NEW (spike design note; number 64 — Day-0 Prong-1) |
| — | `scripts/lint/run_all.py` | **UNTOUCHED** (CI gate unchanged; `--fix` never wired) |
| — | `backend/src/agent_harness/**` | **UNTOUCHED** (no runtime change) |
| — | `event_wire_schema.py` / codegen / `frontend/**` | **UNTOUCHED** (no wire / no FE) |

## 5. Acceptance Criteria

1. `--fix` (no `--write`) prints a grouped draft report and leaves source byte-identical (a `git diff` after `--fix` is empty in tests).
2. `--fix --write` applies drafts via position-based splice for all three mutation kinds (replace literal / insert kwarg / insert param key); re-running `--write` on fixed source is a no-op (idempotent).
3. Every emitted draft passes the lint's own predicate (self-validation); a draft that cannot is emitted as `<needs-manual>`, never as a lint-failing string.
4. The CI reporting path is byte-identical: `run_all` 11/11 unchanged; a plain `python -m scripts.lint.check_tool_descriptions --root backend/src` imports nothing new.
5. The drafter is provider-neutral (ChatClient ABC + adapter factory; LLM-SDK-leak clean); CI tests use a fake client (no Azure).
6. Opt-in real-Azure smoke: `--fix` on a stripped fixture tool produces drafts that all pass the lint; accuracy eyeballed + honestly noted in the design note. (NOT an A/B; NOT a drive-through.)
7. ③2 `AD-Tool-Description-AutoFix` CLOSED (Tool range 4/4); CHANGE-132 + spike design note; calibration recorded; navigators (CLAUDE.md / MEMORY.md + subfile) + next-phase-candidates updated.

## 6. Deliverables

- [ ] US-1 `--fix` dry-run report + neutral self-validating drafter
- [ ] US-2 `--fix --write` position-based splice (3 kinds) + idempotency
- [ ] US-3 opt-in real-Azure smoke + honest accuracy note
- [ ] US-4 CHANGE-132 + design note + calibration + navigators + next-phase

## 7. Workload Calibration

- Scope class **NEW `tool-autofix-spike` 0.60** (anchored to `tool-reflection-and-lint-spike` 0.60 (57.144 — same Cat 2 lint + measurement-harness family) + the `benchmark-*` harness 0.60 family; a real-code core = the neutral self-validating drafter + a position-based source splicer + fixtures + smoke, ≥ ~3.5 hr → the 0.60 spike multiplier holds per the 57.137 lesson, NOT a tiny-code 0.85 re-point). If the 1st data point lands > 1.20, re-point toward 0.75 (the splice-edge-cases + real-Azure smoke staging are the variance risk).
- **Agent-delegated: no** (parent-direct — the splice correctness, the neutral-client discipline, the self-validation loop, and the honest-review Option-B semantics all need the parent). `agent_factor` 1.0 → 3-segment.
- Bottom-up est ~8.5 hr (US-1 drafter+report+fake tests ~3 · US-2 splicer+fixtures+idempotency ~3 · US-3 smoke+evidence ~1.5 · US-4 closeout ~1) → class-calibrated commit ~5.1 hr (mult 0.60). Day-4 retro Q2 verifies.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| **`--fix` sys.path** — the top-level lint can't import `backend/src` adapters | Day-0 D-sys-path-fix: lazy `sys.path` insert of `backend/src` under `--fix` only; fallback = run the drafter as a `backend/scripts/` sibling. The CI report path never imports it. |
| **Splice edge cases** — insert-kwarg / insert-key on unusual ToolSpec formatting | Back-to-front application; cover replace/insert-kwarg/insert-key each with a tmp_path fixture; leave the fiddliest (insert brand-new kwarg into arbitrary call) covered by ≥2 formatting fixtures; anything unhandled → `<needs-manual>` (never a broken write). |
| **Plausibly-wrong draft** — LLM writes a lint-passing but inaccurate description | Option B's two gates (report → `--write` → `git diff`) + design-note honesty ("drafts are a first cut for human review"); self-validation only guarantees lint-pass, NOT semantic accuracy — stated explicitly. |
| **Silent CI-path drift** — an edit accidentally changes the no-flag behavior | Acceptance #4 + a test asserting the no-flag `main()` output is unchanged; Day-0 D-runall-untouched. |
| **Module-level singleton / per-call client** (Risk Class C) | Build the client once per `--fix` invocation (not per violation); it's a one-shot script, no test-loop reuse. |
| **cp950 stdout** on Windows for the report | Mirror `benchmark_tool_error_reflection.py:347-353` `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`. |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- Wiring `--fix`/`--write` into CI or a pre-commit hook — out (it needs real Azure creds → non-deterministic); the reporting lint stays the gate. → future AD if ever wanted.
- LLM-drafted descriptions for NON-tool docstrings / other lints — out (this AD is tool descriptions only).
- A runtime A/B on whether autofixed descriptions improve live tool selection — out (no cheap metric; the human accuracy gate is the control). → `AD-Tool-Autofix-Selection-Impact-Phase58` if ever pursued.
- The 4 minor 57.164-surfaced follow-ons (`AD-Tool-Taxonomy-HumanLabel` / `AD-Tool-Reflection-PerTier-Default` / `AD-Tool-Reflection-RarePath-Near-Dead-Evaluate` / `AD-Tool-Failure-Terminate-vs-Recoverable-Policy`) + `AD-RequestApproval-Placeholder-Deprecated` — out; remain in next-phase-candidates.
