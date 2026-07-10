# Sprint 57.165 — Checklist (LLM-assisted `--fix` for the tool-description lint)

[Plan](./sprint-57-165-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (PRE-verify run 2026-07-10 vs current repo; final baseline re-confirm at branch creation post-57.164-merge)
- [x] **Prong 1 — path verify**: EDIT `scripts/lint/check_tool_descriptions.py` present; NEW `scripts/lint/_autofix.py` + `tests/unit/scripts/lint/test_tool_description_autofix.py` free; `CHANGE-132` slug free; design-note **64** free ✅
- [x] **Prong 2 — content verify** (drift → progress.md): 4/4 GREEN + 2 impl-note refinements ✅
  - [x] **D-sys-path-fix** — `adapters/azure_openai/profile.py` at `backend/src/`; lazy `sys.path.insert(parents[2]/backend/src)` under `--fix` resolves it; fallback (backend/scripts sibling) NOT needed ✅
  - [x] **D-node-span-avail** — Python 3.11 → all AST nodes have `end_*`; ToolSpec literals single-call (`memory_tools.py:123,173`). Nuance: multi-line `description=("a" "b")` folds to 1 `ast.Constant` (span = inner literals, not outer `()`) → replace-splice leaves `()` valid ✅
  - [x] **D-profile-cheap** — `build_azure_model_profile()->ModelProfile`; `.cheap` is `ChatClient` (`profile.py:57`). Refinement: `.chat` is **async** → drafter async + `asyncio.run` (mirror `_amain`) ✅
  - [x] **D-runall-untouched** — `run_all.py:89` = `("check_tool_descriptions.py", ["--root","backend/src"])` (no `--fix`) → CI gate byte-identical ✅
- [x] **Prong 3 — schema verify**: N/A (no DB / migration / ORM) — confirmed ✅
- [x] **D-baselines** (reference; re-confirm at branch time) — pytest 3231 (+5 skip) · run_all 11/11 (incl. `check_tool_descriptions`) · mypy `src` 400/0 · (wire 26 / Vitest 933 / mockup 51 — untouched)
- [x] **Catalog drift** — progress.md Day-0 table written ✅
- [x] **Go/no-go** — PROCEED (~0% scope shift; 2 refinements folded into design, no §Acceptance/§Workload change). Gated on 57.164 merge + user go-ahead before §0.2 branch + Day 1.

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-165-tool-desc-autofix` (from `main` `980b3357` — 57.164 merged as PR #385) ✅

---

## Day 1 — `--fix` dry-run report + neutral self-validating drafter (US-1) — DONE ✅
> Day-1 refinement (progress.md): folded into `check_tool_descriptions.py` (not a sibling `_autofix.py`); `FixTarget` is a `NamedTuple` (importlib-load safe, matches `Violation`); test at `backend/tests/unit/scripts/lint/`.

### 1.1 Surface the AST node for splicing
- [x] **`check_tool_descriptions.py` — carry the fix target** ✅ `collect_fix_targets(root) -> (list[FixTarget], unfixable_dynamic)`; reuses the checker's own predicates (single-source); `FixTarget` carries `source_segment` (LLM context); report path byte-identical
  - Verify: `python -m scripts.lint.check_tool_descriptions --root backend/src` → `OK: all ToolSpec descriptions well-formed` (byte-identical) ✅

### 1.2 Neutral drafter with self-validation
- [x] **`draft_description(client, target)` — one imperative sentence via ChatClient ABC** ✅ async; neutral `ChatRequest` (system: document-a-tool ≥20 chars, no TODO/FIXME/XXX/TBD; user: `source_segment`); only `_build_cheap_client()` touches `adapters.*` (lazy)
  - Verify: `pytest tests/unit/scripts/lint/test_tool_description_autofix.py -k draft` ✅ (fake client)
- [x] **Self-validation loop** ✅ `_lint_ok` re-checks the draft against the lint predicate; retry once with `_RETRY_HINT`; still fail → `NEEDS_MANUAL`
  - Verify: `... -k needs_manual` → too-short/placeholder → `<needs-manual>`, never a lint-failing string ✅

### 1.3 `--fix` dry-run report (source untouched)
- [x] **`--fix` prints a grouped draft report; source byte-identical** ✅ `render_report` groups by file + counts `<needs-manual>`/dynamic-skipped; `run_fix` short-circuits (no Azure) when 0 targets; cp950-safe stdout
  - Verify: `... -k render_report` ✅ + `--fix --root backend/src` short-circuits `OK: no fixable…` without Azure ✅

### 1.x Partial gate ✅
- [x] pytest lint tests 38 passed (13 new + 10 existing checker unbroken + 15 other) · black/isort/flake8 clean (100 std) · LLM-SDK-leak clean (drafter via ChatClient ABC, no `import openai/anthropic`; adapter import lazy) · mypy `src` 400/0 UNAFFECTED (changes outside `src/`)

---

## Day 2 — `--fix --write` position-based splice + idempotency (US-2) — DONE ✅

### 2.1 Splicer — three mutation kinds (`--write` only)
- [x] **replace existing description literal** ✅ overwrite the `ast.Constant` span (tool-level + empty-param); implicit-concat parens nuance handled
  - Verify: `pytest ... -k "replace"` (short tool desc + empty param) → replaced, re-collect 0, `compile()` OK ✅
- [x] **insert missing `description=` kwarg** ✅ splice `description=<q>,` after the `name=` value comma; multi-line indents, single-line inline
  - Verify: `... -k "insert_tool_desc"` (multiline + singleline fixtures) → valid Python, re-collect 0 ✅
- [x] **insert missing param `"description"`** ✅ splice `"description": <q>, ` just after the param dict `{`
  - Verify: `... -k "insert_param_desc"` → key inserted, re-collect 0 ✅
- [x] **back-to-front application** ✅ ops sorted highest-offset-first so spans don't shift
  - Verify: `... -k "multi_edit"` (tool desc + param desc in one file → 2 ops) ✅

### 2.2 Idempotency
- [x] **re-running `--write` on fixed source is a no-op** ✅ after apply, `collect_fix_targets` returns 0 → `apply_fixes(text, []) → (text, 0)`
  - Verify: `... -k "idempotent"` ✅

### 2.x Full gate ✅
- [x] run_all 11/11 (unchanged — report path byte-identical) · pytest `tests/unit/scripts/lint/` 46 passed (autofix 24 + checker 10 + other 12) · black/isort/flake8 clean · LLM-SDK-leak clean (adapter import lazy) · mypy `src` 400/0 UNAFFECTED · (NO Vitest/mockup/build delta — no FE). run_fix write path tested WITHOUT Azure via monkeypatch (non-Potemkin); real drafter = Day-3 smoke.

---

## Day 3 — Evidence: opt-in real-Azure smoke (US-3) — NOT a drive-through
_(Pure dev/CI tooling — no user-driven UI surface → the Drive-Through Hard Constraint does not apply. This day is a real-LLM SMOKE + honest accuracy note, explicitly labeled "smoke-verified (real Azure), not a runtime A/B / not a drive-through".)_

### 3.1 Real-Azure smoke on a stripped fixture — 🟢 PASS
- [x] **`--fix` (real cheap tier) drafts pass the lint** ✅ scratchpad fixture (5 gaps, 3 kinds) → real cheap-tier `--fix` produced 5 drafts → `--fix --write` applied → **re-lint `OK`** (5/5 passed the lint + valid Python). Command + output in progress.md Day 3.
- [x] **Honest accuracy note** ✅ 5/5 passed the lint; accuracy eyeballed OK; 2 honest cosmetic findings (Unicode smart quotes + param-key ordering) → the ⚠ banner + Option-B git-diff gate cover them (drafts = first cut, self-validation guarantees lint-pass NOT semantic accuracy). Recorded progress.md Day 3.
- [x] **NO agent_harness runtime touched → NO drive-through required** ✅ dev/CI tooling only; labeled "smoke-verified (real Azure), NOT a runtime A/B / NOT a UI drive-through". Fixture is throwaway (scratchpad, not committed).

---

## Day 4 — CHANGE-132 + design note + closeout

### 4.1 CHANGE-132 + design note ✅
- [x] **`CHANGE-132-tool-description-autofix.md`** ✅ (gap: lint reports-not-fixes + Option B + drafter/splicer/self-validate + smoke evidence + ③2 CLOSED)
- [x] **Spike design note `64-tool-description-autofix-design.md`** ✅ — 8-point quality gate self-checked in retrospective (decision matrix incl. Option B + fold-into-checker + NamedTuple + no-libcst + self-validation; verified invariants w/ function anchors; smoke reproduce block; open invariants; rollback; 17.md cross-ref = none new)

### 4.2 Closeout ✅
- [x] retrospective.md Q1-Q7 + calibration ✅ (NEW class `tool-autofix-spike` 0.60, 1st pt ~1.0-1.08 IN band → KEEP 0.60)
- [x] Final gate sweep ✅ run_all 11/11 · **full backend pytest 3255 passed, 5 skipped** (+24, exit 0, no regression) · black/isort/flake8 clean · LLM-SDK-leak clean · lint self-run byte-identical · mypy `src` 400/0 UNAFFECTED (NO Vitest/mockup/build delta)
- [x] Navigators ✅ CLAUDE.md Current-Sprint + Last-Updated (PR-pending) · MEMORY.md pointer + subfile `project_phase57_165_tool_desc_autofix.md` (in the real `.claude/…/memory/` store — a stray repo `memory/` dir was accidentally created + removed) · next-phase-candidates (③2 CLOSED → Tool range 4/4 + shipped-index row) · sprint-workflow matrix (NEW `tool-autofix-spike` 0.60 row)
- [x] Anti-pattern self-check (retro Q5) ✅ AP-2 (smoke + monkeypatch tests prove reachable) / AP-4 (self-validation + smoke non-Potemkin) / AP-6 (no libcst) / AP-8 N/A / AP-11 none → 0 violations; v2 lints 11/11
- [x] **Commit** `dac20880` (local, feature branch) ✅ → ⏳ PR push + open → CI → merge: PENDING USER CONFIRMATION (push is outward-facing per Developer Preferences) → post-merge status flip after gh-verified MERGED
