# Sprint 57.161 Plan — structural compactor real token re-count (surface masking without preclear)

**Summary**: Closes `AD-Compaction-Structural-RealTokenCount` (57.160 carryover). `StructuralCompactor.tokens_after` is a **message-count ratio** (`structural.py:192-193`) that is blind to in-place tombstoning — when the masker tombstones tool bodies (list length preserved) it reports `N→N` even when real tokens dropped, so the 57.159 marker showed no reduction AND the loop's ongoing budget (`loop.py:2282` trusts `tokens_after`) stayed pinned at the old value (the 57.159 `4k→35k · 8 no-op compactions` pathology). Fix = inject a `TokenCounter` into `StructuralCompactor` and re-count the post-mask tokens exactly like `PreClearCompactor` (`preclear.py:178-181`), so tool-anchored masking surfaces its real reduction WITHOUT also enabling preclear. Rollout **A: default-on correctness fix** (user AskUserQuestion pick) — the factory always injects `TiktokenCounter`; a `token_counter=None` fallback keeps the message-count ratio so existing tests stay byte-identical. Backend-only, ZERO wire/codegen/frontend/migration. Drive-through MANDATORY (chat-v2 marker is user-facing). Design note 63 (spike — documents the loop-consumes-`tokens_after` runtime invariant).

**Status**: Approved-to-execute (user selected "Engine-debt 7-range — AD-Compaction-Structural-RealTokenCount" 2026-07-07; rollout posture A via AskUserQuestion 2026-07-07)
**Branch**: `feature/sprint-57-161-compaction-structural-realcount`
**Base**: `main` HEAD `204c4499` (Sprint 57.160 chore flip #377 merged)
**Slice**: closes `AD-Compaction-Structural-RealTokenCount` (NEW 57.160); engine-debt compaction range, standalone
**Scope decisions**: (a) `token_counter: TokenCounter | None = None` ctor param — injected → real re-count (mirror preclear.py:178-181), None → legacy message-count ratio (byte-identical, existing tests unchanged); (b) rollout **A default-on** — factory always injects `TiktokenCounter(model="gpt-4o")`, NO new env lever; (c) `messages_compacted` semantics UNCHANGED this sprint (still drops-only; tombstoned-count-in-marker → out-of-scope follow-on) — the fix is scoped to `tokens_after` only.

---

## 0. Background

### The gap (`AD-Compaction-Structural-RealTokenCount`)

- `StructuralCompactor.compact_if_needed` computes `token_usage_so_far = int(tokens_before * len(kept_messages) / max(original_count, 1))` — a **message-count** ratio.
- The observation masker tombstones old tool bodies **in place** (list length preserved) → `len(kept_messages) == original_count` → ratio `= 1.0` → `tokens_after == tokens_before` **even when the real token content shrank**.
- Only `PreClearCompactor` (`preclear.py:178-181`) does a real `TokenCounter` re-count. So in Sprint 57.160 the tool-anchored masking only surfaced a reduction when the preclear lever was ALSO on (Legs 1-2 without preclear → `N→N`; Leg 3 with preclear → real `−42%/−51%`).

### Why it matters (the missing capability)

`loop.py:2282` sets `tokens_used = compaction_result.tokens_after` — the loop **trusts** `tokens_after` as its ongoing budget (it does NOT re-count, contrary to the stale `structural.py:192` comment). So the blindness has two consequences: (1) the 57.159 chat-v2 marker shows a no-op `N→N`, and (2) the loop's budget stays pinned at the pre-mask value → `should_compact` keeps firing every turn but never relieves the tracked budget → the 57.159-observed `4k→35k, 8 no-op compactions`. Fixing `tokens_after` fixes BOTH the display and the budget-tracking pathology.

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `204c4499`) | Anchor |
|-------|-------------------------------------|--------|
| Structural token estimate | message-count ratio, blind to in-place tombstoning | `structural.py:192-193` |
| Stale docstring | "real Loop.run() will re-count via TokenCounter" — FALSE (loop trusts `tokens_after`) | `structural.py:192` comment |
| Real-count reference | preclear re-counts post-mask tokens via injected `TokenCounter`, applies reduction ratio to loop-scale `tokens_before` | `preclear.py:178-181` |
| Loop consumes result | `tokens_used = compaction_result.tokens_after` (no re-count) | `loop.py:2282` |
| Marker source | `ContextCompacted(tokens_before, tokens_after, ...)` drives the 57.159 `CompactionMarkerTurn` | `loop.py:2288-2293` |
| Factory has a counter | `TiktokenCounter(model="gpt-4o")` already imported + used (preclear line 244, builder 295) | `_category_factories.py:65,244,295` |

→ Mirror preclear's real-count into `StructuralCompactor` behind an optional `token_counter`; the factory injects it default-on.

### The design (backend-only: 1 ctor param + 1 real-count branch mirroring preclear + 1 factory injection + docstring fixes + tests)

```
StructuralCompactor.__init__(..., token_counter: TokenCounter | None = None)

# in compact_if_needed Step 5, replacing the message-count ratio:
if self.token_counter is not None:
    tokens_original = self.token_counter.count(messages=messages)      # full
    tokens_masked   = self.token_counter.count(messages=kept_messages) # tombstoned
    reduction_ratio = (tokens_masked / tokens_original) if tokens_original > 0 else 1.0
    new_token_usage = int(tokens_before * reduction_ratio)             # loop-scale
else:
    new_token_usage = int(tokens_before * len(kept_messages) / max(original_count, 1))  # legacy

# factory (Option A default-on):
StructuralCompactor(..., token_counter=TiktokenCounter(model="gpt-4o"))
```

Why A (default-on) over an env lever: the message-count ratio is a genuine correctness bug (it pins the loop budget on tombstoning), not a behaviour CHOICE with a tradeoff — so there is no retention floor to measure first (unlike 57.160's masking mode). The `token_counter=None` fallback already gives the byte-identical safety an env lever would, so an env lever would only preserve a WRONG default. `TiktokenCounter` is a pure tokenizer (no provider SDK) → neutrality-safe.

### Ground truth (recon head-start — code read on `main` HEAD `204c4499`; ALL re-verified §checklist 0.1)

- `structural.py:107-124` — `StructuralCompactor.__init__` is keyword-only, `masker` is the last param; NO `token_counter` today.
- `structural.py:189-197` — Step 5 builds `new_transient` with the message-count ratio; `messages_compacted = original_count - len(kept_messages)`.
- `preclear.py:82-97,178-181` — the exact real-count pattern to mirror (`token_counter: TokenCounter` required there; `count(messages=...)` is keyword-only).
- `_category_factories.py:215-221` — `make_chat_compactor` builds `StructuralCompactor(keep_recent_turns, token_budget, token_threshold_ratio, masker)`; the injection point.
- `loop.py:2280-2293` — loop consumes `tokens_after` as `tokens_used` + emits `ContextCompacted`.

**Baselines (57.160 closeout)**: pytest 3202 + 6 skipped · wire 26 · Vitest 927 · mockup 51 · mypy `src` 400 · run_all 11/11. Re-verify Day-0.

### STALE / drift findings (Day-0; full detail → progress.md — placeholder, filled in §checklist 0.1)

- **D-structural-ctor-shape** — confirm `StructuralCompactor.__init__` keyword-only + `masker` last (additive `token_counter` safe).
- **D-preclear-realcount-pattern** — confirm `preclear.py:178-181` real-count shape + `count(messages=...)` keyword-only (mirror exactly).
- **D-loop-consumes-tokens-after** — confirm `loop.py:2282` sets `tokens_used = tokens_after` (no re-count) → the fix reaches the loop budget, not just the marker.
- **D-factory-counter-available** — confirm `TiktokenCounter` importable + already used in the factory (injection is one line).
- **D-structural-test-counter-absent** — confirm existing `test_compactor_structural.py` constructs `StructuralCompactor()` WITHOUT a counter (→ legacy path → byte-identical).

## 1. Sprint Goal

Make `StructuralCompactor` report a real post-mask token count so tool-anchored observation masking surfaces its reduction on the chat-v2 marker AND relieves the loop budget WITHOUT the preclear lever — closing `AD-Compaction-Structural-RealTokenCount`. PROVEN by: (1) a deterministic unit test where structural-with-counter reports a real reduction on a tombstoned single-user-turn transcript while structural-without-counter reports `N→N` (the exact fix delta) + parity with `PreClearCompactor` on the same input; (2) the full gate sweep; (3) a MANDATORY drive-through re-running 57.160's Leg-1/2 config (tool-anchored masking ON, preclear OFF) → the 57.159 marker now renders a REAL reduction (vs 57.160's recorded `N→N`). CHANGE-128 + design note 63.

## 2. User Stories

- **US-1** (real re-count): 作為平台，我希望 `StructuralCompactor` 在注入 `TokenCounter` 時用真計數報告 `tokens_after`，以便 in-place tombstoning 的真實縮減不再被 message-count 比例遮蔽。
- **US-2** (default-on wiring): 作為 operator，我希望 chat factory 預設就注入 counter，以便主流量的 marker 與迴圈預算追蹤反映真實 token，而不需額外開 preclear lever。
- **US-3** (honesty): 作為維護者，我希望修掉 `structural.py:192` 的過時註解（迴圈其實信任 `tokens_after`，不會重新計數），以便下一位讀者不被誤導。
- **US-4** (drive-through, MANDATORY): 作為使用者，我希望在真 chat-v2 上，tool-anchored masking 開、preclear 關時，57.159 marker 就顯示真實縮減，以便證明 AD 已關（對照 57.160 Leg-1/2 的 `N→N`）。
- **US-5** (closeout): CHANGE-128 + design note 63 + calibration + navigators + AD 關閉。

## 3. Technical Specifications

### 3.0 Architecture (backend-only; NO wire/codegen/frontend/migration/loop.py)

```
EDIT  agent_harness/context_mgmt/compactor/structural.py   — ctor token_counter param + real-count branch + docstring fixes + MHist
EDIT  api/v1/chat/_category_factories.py                    — inject TiktokenCounter into StructuralCompactor (Option A) + MHist
EDIT  tests/unit/agent_harness/context_mgmt/test_compactor_structural.py — +real-count / None-legacy / preclear-parity tests
EDIT  tests/unit/api/test_category_factories.py             — assert counter injected into structural
UNTOUCHED  preclear.py · hybrid.py · chained.py · _abc.py · observation_masker.py · loop.py · sse.py · wire schema · frontend
```

### 3.1 Real re-count branch (US-1) — `structural.py`

- Add `token_counter: TokenCounter | None = None` as the last keyword-only ctor param; store `self.token_counter`.
- Import `TokenCounter` from `agent_harness.context_mgmt.token_counter._abc` (same import preclear uses).
- In Step 5, branch: `token_counter is not None` → real-count (mirror `preclear.py:178-181` exactly: `count(messages=...)` keyword-only, reduction ratio applied to loop-scale `tokens_before`); else → the existing message-count ratio (verbatim).
- `messages_compacted` UNCHANGED (`original_count - len(kept_messages)` — drops only). Both branches produce identical results when nothing is tombstoned (no masker no-op case → ratios agree within int rounding).

### 3.2 Default-on factory injection (US-2) — `_category_factories.py`

- In `make_chat_compactor`, pass `token_counter=TiktokenCounter(model="gpt-4o")` to `StructuralCompactor(...)` (line ~216). Applies to BOTH the bare-hybrid default AND the preclear-chained path.
- No new env lever. `TiktokenCounter` already imported (line 65).

### 3.3 Stale-docstring fix (US-3) — `structural.py`

- Replace the `structural.py:192` inline comment ("token_usage_so_far is approximated; real Loop.run() will re-count via TokenCounter") — the loop does NOT re-count (`loop.py:2282`). New comment states the two branches + that the loop trusts `tokens_after`.
- Update the class docstring point 5 (Day-3.3 masking) to note the real-count-when-injected behaviour.

### 3.x What is explicitly NOT done

- `messages_compacted` mirroring preclear's tombstoned-count (so the marker shows `· N msgs` on pure tombstone instead of `· 0 msgs`) — cosmetic, → §9.
- Upgrading `PreClearCompactor` / `HybridCompactor` / `SemanticCompactor` token accounting — they already real-count or aggregate; untouched.
- Any env lever / per-tenant policy — A is default-on; per-tenant → §9.
- No A/B harness (this is a deterministic correctness fix with an exact expected value, not an efficacy tradeoff — a unit test + drive-through is the evidence, unlike 57.160's masking-mode A/B).

### 3.y Validation (US-1..US-5)

Gates: mypy `src` 400 · run_all 11/11 · pytest 3202+new · Vitest 927 (FE untouched) · mockup 51 (`diff` empty) · black/isort/flake8 clean · LLM-SDK-leak clean. Plus the §3.1 US-4 drive-through (MANDATORY — chat-v2 marker is user-facing).

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/agent_harness/context_mgmt/compactor/structural.py` | EDIT |
| 2 | `backend/src/api/v1/chat/_category_factories.py` | EDIT |
| 3 | `backend/tests/unit/agent_harness/context_mgmt/test_compactor_structural.py` | EDIT |
| 4 | `backend/tests/unit/api/test_category_factories.py` | EDIT |
| — | `backend/src/agent_harness/context_mgmt/compactor/preclear.py` | **UNTOUCHED** |
| — | `backend/src/agent_harness/orchestrator_loop/loop.py` | **UNTOUCHED** |
| — | wire schema / codegen / frontend / migration | **UNTOUCHED** |

## 5. Acceptance Criteria

1. `StructuralCompactor(token_counter=X)` on a tombstoned single-user-turn transcript reports `tokens_after < tokens_before` (real reduction); `StructuralCompactor()` on the same input reports `tokens_after == tokens_before` (proves the fix is the counter).
2. Parity: structural-with-counter's `tokens_after` matches `PreClearCompactor`'s on the same tombstoned input (same ratio-on-loop-scale formula).
3. `token_counter=None` path is byte-identical to pre-57.161 (existing structural tests pass UNCHANGED).
4. Factory injects `TiktokenCounter` into `StructuralCompactor` (test asserts).
5. **Drive-through PASS (MANDATORY, real UI + backend + LLM)** — tool-anchored masking ON + preclear OFF → the 57.159 chat-v2 marker renders a REAL `before→after` reduction (vs 57.160 Leg-1/2's recorded `N→N`); screenshot + observed-vs-intended in progress.md. (NOT gate-only.)
6. `AD-Compaction-Structural-RealTokenCount` CLOSED; CHANGE-128 + design note 63; calibration recorded; navigators + next-phase-candidates updated.

## 6. Deliverables

- [ ] US-1 `token_counter` ctor param + real-count branch (mirror preclear)
- [ ] US-2 factory default-on injection
- [ ] US-3 stale-docstring + class-docstring fix
- [ ] US-4 drive-through PASS (marker surfaces without preclear)
- [ ] US-5 CHANGE-128 + design note 63 + closeout

## 7. Workload Calibration

- Scope class **NEW `compaction-structural-realcount-spike` 0.60** (anchored to the sibling `compaction-tool-anchored-masking-spike` 0.60 (57.160) — same Cat-4 compaction correctness-fix + MANDATORY-drive-through shape; LIGHTER code (a real-count branch mirroring an EXISTING preclear pattern, no new masking mode/A-B harness/corpus) but offset by the SAME fixed drive-through ceremony floor (per the 57.120/160 ceremony-not-code-accelerated insight — a bounded-code + full-ceremony + parent-direct sprint sits ~0.60, not 0.45). If a 2nd `compaction-structural-realcount-spike` lands > 1.20 re-point 0.75; if < 0.7 re-point 0.50).
- **Agent-delegated: no** (parent-direct — a focused Cat-4 correctness fix requiring precise mirror-of-preclear + a compaction drive-through; not a mechanical multi-file port). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~5-5.5 hr (US-1 ~1.5 hr real-count branch + tests · US-2 ~0.3 hr · US-3 ~0.3 hr · US-4 ~2.5 hr drive-through incl. clean restart + compaction staging · US-5 ~1 hr) → class-calibrated commit ~3-3.3 hr (mult 0.60). Day-4 retro Q2 verifies.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| Real-count formula drifts from preclear → inconsistent `tokens_after` between the two compactors | Mirror `preclear.py:178-181` verbatim (ratio-on-loop-scale, not raw count); add a parity unit test (AC-2). |
| Default-on changes the marker numbers for ALL compaction (not just tombstoning) | Intended — the message-count ratio was an approximation; real count is strictly more accurate. Non-tombstoning drops: real-count ≈ message-count within int rounding (both reduce). Documented in CHANGE-128. |
| Drive-through can't reproduce a reduction (compaction doesn't trigger / masker no-ops) | Reuse the EXACT 57.160 Leg-3 staging that DID fire (`CHAT_COMPACTION_TOOL_ANCHORED_MASKING=1` + a low `CHAT_COMPACTION_TOKEN_BUDGET` + a multi-tool single user turn e.g. 6× knowledge_search) — but WITHOUT `CHAT_COMPACTION_PRECLEAR_RATIO` this time; the fix is what makes it surface. |
| Stale `--reload` backend masks the startup-injected counter (Risk Class E) | Clean single-process restart (no `--reload`), env-before-start, confirm sole port owner + startup log; kill orphan spawn-workers via `Win32_Process` PID/PPID/StartTime sweep (57.97 lesson). |
| Test isolation: factory singleton across event loops (Risk Class C) | Factory test constructs fresh; no module-level singleton touched. |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- `messages_compacted` = tombstoned count in the marker (`· N msgs` on pure tombstone) → NEW `AD-Compaction-Structural-TombstoneCount-Marker` (cosmetic follow-on).
- Per-tenant real-count toggle → folds into the existing C3 per-tenant compaction policy seam (`AD-Compaction-Preclear-PerTenant-Phase58`).
- Flip `CHAT_COMPACTION_TOOL_ANCHORED_MASKING` default ON (57.160 carryover, data-gated) — separate decision.
- `AD-Compaction-Marker-Inspector-Trace-Correlate` (57.159 FE carryover) — unrelated FE surface.
