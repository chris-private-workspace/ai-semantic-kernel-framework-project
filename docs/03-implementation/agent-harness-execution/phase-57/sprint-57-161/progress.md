# Sprint 57.161 Progress — structural compactor real token re-count

**Sprint**: 57.161 · **Branch**: `feature/sprint-57-161-compaction-structural-realcount` (from `main` `204c4499`)
**AD**: closes `AD-Compaction-Structural-RealTokenCount` (57.160 carryover) · engine-debt compaction range
**Rollout**: A default-on (user AskUserQuestion 2026-07-07)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) — 2026-07-07

### Drift findings (all GREEN, 0 drift)

| ID | Verify | Result | Implication |
|----|--------|--------|-------------|
| D-structural-ctor-shape | `structural.py:107-124` keyword-only ctor, `masker` last | ✅ confirmed | additive `token_counter` param safe |
| D-preclear-realcount-pattern | `preclear.py:178-181` real-count; `TokenCounter.count(*, messages, tools)` keyword-only (`_abc.py:43-49`) | ✅ confirmed | mirror verbatim: `count(messages=...)`, ratio × loop-scale `tokens_before` |
| D-loop-consumes-tokens-after | `loop.py:2282` `tokens_used = compaction_result.tokens_after` (no re-count) | ✅ confirmed | fix reaches loop budget + marker, not just display — the `structural.py:192` "Loop.run() will re-count" comment is STALE (Karpathy §3) |
| D-factory-counter-available | `_category_factories.py:65` imports `TiktokenCounter`; used at 244 (preclear) + 295 (builder) | ✅ confirmed | injection into `StructuralCompactor` is one line |
| D-structural-test-counter-absent | `test_compactor_structural.py` 6 tests all `StructuralCompactor(...)` w/o `token_counter` (lines 60/79/97/115/139/157) | ✅ confirmed | legacy path → existing tests byte-identical |

**Prong 3 (schema)**: N/A — no DB tables / migrations / ORM columns.

**Baselines** (carried from 57.160 closeout; branch from main `204c4499` = 57.160-merged, zero code delta): pytest 3202 + 6 skipped · wire 26 · Vitest 927 · mockup 51 · mypy `src` 400 · run_all 11/11.

**Go/no-go**: **PROCEED** — 0 drift, scope-shift ~0%. The plan's root-cause table matched real code exactly (every file:line re-verified). Branch created (checklist 0.2 ✅).

---

## Day 1-2 — Code + full gate — 2026-07-07

### What shipped (backend-only, Cat 4, ZERO wire/codegen/frontend/migration)

- **`structural.py`** (EDIT) — `StructuralCompactor.__init__(*, ..., token_counter: TokenCounter | None = None)`; Step 5 branches: `token_counter is not None` → real re-count `int(tokens_before * count(kept)/count(orig))` mirroring `preclear.py:178-181`; None → verbatim legacy message-count ratio. Fixed the stale `structural.py:192` comment (loop trusts `tokens_after`, does NOT re-count) + class docstring point 6 + MHist.
- **`_category_factories.py`** (EDIT) — `make_chat_compactor` injects `TiktokenCounter(model="gpt-4o")` into `StructuralCompactor` (Option A default-on; applies to both bare-hybrid + preclear-chained paths). No new env lever. MHist.
- **`test_compactor_structural.py`** (EDIT) — +3 tests + `_LenCounter`/`_tool_transcript` helpers (mirror preclear): real-count reduction / no-counter blind no-op (the fix delta) / preclear parity.
- **`test_category_factories.py`** (EDIT) — +1: `TiktokenCounter` injected into structural.

### The fix delta (deterministic, unit level)

On the SAME tombstoned single-user-turn transcript (`_tool_transcript(7)`, keep_recent=5 → only tombstoning, distinct args → no drop → `len(kept)==original`):
- `StructuralCompactor(token_counter=X)` → `tokens_after < tokens_before` (real reduction surfaces) ✅
- `StructuralCompactor()` [no counter] → `tokens_after == tokens_before` (message-count ratio 1.0 = the 57.159 blind no-op) ✅
- structural-with-counter `tokens_after` == `PreClearCompactor` `tokens_after` (parity) ✅

This is the 57.160-Leg-1/2-vs-fixed contrast reproduced at unit level: 57.160 needed preclear to surface the reduction; now structural surfaces it alone.

### Gates (Day 2 full sweep)

- pytest **3206 passed + 6 skipped** (baseline 3202 +4)
- mypy `src` **400** (unchanged) · run_all **11/11** green (incl. LLM-SDK-leak)
- black/isort/flake8 clean (fixed 1 E501 in factory MHist)
- FE untouched (0 frontend files) → Vitest 927 / mockup 51 carry unchanged

**Note (KEY finding surfaced Day 0-1)**: `loop.py:2282` `tokens_used = compaction_result.tokens_after` — the loop TRUSTS `tokens_after` as its ongoing budget and does NOT re-count (the `structural.py:192` "Loop.run() will re-count" comment was STALE). So the message-count ratio blindness was NOT cosmetic: it pinned the loop budget at the pre-mask value → the 57.159 `4k→35k, 8 no-op compactions` pathology. This fix relieves the loop budget too, not just the marker display.

---
