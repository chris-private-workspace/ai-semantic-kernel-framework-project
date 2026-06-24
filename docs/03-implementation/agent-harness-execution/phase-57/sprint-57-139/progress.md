# Sprint 57.139 Progress — layered compaction (tool-result preclear yield + ACON-band measurement spike)

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-139-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-139-checklist.md)

Closes `AD-Context-Layered-Compaction-ACON` (research #4, Cat 4 — next per canonical order after #6/#3/#8).

---

## Day 0 (2026-06-24) — Plan-vs-Repo Verify (三-prong) + Branch

Branch `feature/sprint-57-139-layered-compaction-spike` from `main` `3bf4a727` (57.138 merge; #330 flip in flight, docs-only).

### Prong 1 — path verify ✅
- 7 NEW files all FREE: `compactor/preclear.py` · `compactor/chained.py` · `scripts/benchmark_layered_compaction.py` · `tests/fixtures/context_mgmt/layered_compaction_cases.yaml` · `tests/unit/scripts/test_benchmark_layered_compaction.py` · `tests/unit/agent_harness/context_mgmt/compactor/test_{preclear,chained}_compactor.py`
- EDIT target `src/api/v1/chat/_category_factories.py` PRESENT.
- compactor test dir does not exist yet → create `tests/unit/agent_harness/context_mgmt/compactor/`.
- CHANGE max = 105 → use **CHANGE-106**. Design note max = 42 → use **43**.

### Prong 2 — content verify (drift table)

| ID | Finding | Implication |
|----|---------|-------------|
| **D-compaction-strategy-wire** | `CompactionStrategy` referenced in `event_wire_schema.py` + `sse.py` + `router.py`; `ContextCompacted` serialized at `sse.py:386-405` (does NOT expose `strategy_used` in its data block, but the enum is on the wire schema). | Adding a `PRECLEAR` enum value would ripple to wire/codegen. **Decision: preclear reuses `CompactionStrategy.STRUCTURAL`** (semantically a structural-family tool clear). Wire UNTOUCHED (count 25). |
| **D-factory-location** | `make_chat_compactor(chat_client)` at `_category_factories.py:143-174`; env helpers `_compaction_token_budget()` (`:116`, `CHAT_COMPACTION_TOKEN_BUDGET`) + `_compaction_keep_recent_turns()` (`:126`, `CHAT_COMPACTION_KEEP_RECENT_TURNS`). All in ONE file (no separate `factory.py` — recon's `factory.py` was a misattribution; Day-0 caught it). | Factory edit is contained to `_category_factories.py`: add `_compaction_preclear_ratio()` helper + preclear branch. |
| **D-tokencounter-default** | `TiktokenCounter(model="gpt-4o")` used in the prompt builder (`:216`); the compactors compare `token_usage_so_far` vs `token_budget` (int), not a counter. | Harness measures with `TiktokenCounter(model="gpt-4o")` for parity. |
| **D-loop-call-site** | Single call site `loop.py:2221 await self._compactor.compact_if_needed(...)`; `self._compactor` injected at `:405` (optional). | `ChainedCompactor` is transparent → **loop.py UNTOUCHED**. |
| **🔴 D-masker-user-anchored** (KEY) | `mask_old_results` anchors the keep-window on **USER message count** (`observation_masker.py:62-66`: `if len(user_indices) <= keep_recent: return unchanged`). The factory docstring (`_category_factories.py:129-134`) explicitly notes the chat main flow runs **ONE user message per loop run** (continuity = Cat 3 memory, not restored history) → the cutoff is unreachable at default 5. | Tool-result masking **NO-OPs in single-send chat**; fires only on rehydrated multi-turn (57.127) / mid-run injection (B1) where the message list has > keep_recent user turns. → (1) corpus MUST be multi-user-turn; (2) drive-through MUST use a rehydrated/multi-turn session; (3) **KEY SPIKE FINDING**: a tool-anchored clear (CC microcompact style, by tool_use_id) is needed to cover single-send → new follow-on `AD-Compaction-ToolAnchored-Preclear-Phase58`. |

### Prong 3 — schema verify
N/A — no new DB table / migration / ORM column.

### D-baselines (re-verify) — pending Day-1 partial gate
Recorded from 57.138 closeout: pytest 2797+5skip · wire 25 · Vitest 915 · mockup 51 · mypy 0/374 · run_all 10/10.

### Go/no-go ✅ PROCEED
Scope-shift < 20% — the D-masker-user-anchored finding SHARPENS the corpus (multi-user-turn) + adds a Phase 58 follow-on AD; it does NOT change the deliverables. The preclear lever still ships (helps the genuinely long-running rehydrated/injected case — the actual ACON target); the single-send limitation is a documented honest finding, not a blocker.

---

## Day 1 (2026-06-24) — PreClearCompactor + ChainedCompactor + factory (US-1, US-3)

**Shipped (3 src + 2 tests)**:
- `compactor/preclear.py` — `PreClearCompactor(Compactor)`: standalone LLM-free tool-result clear; `should_compact` at `preclear_ratio*budget` (0.50, lower than 0.75); reuses `DefaultObservationMasker.mask_old_results`; preserves system+HITL (mirror structural); honest passthrough when nothing masked (the user-anchored NO-OP); `strategy_used=STRUCTURAL` (reuse, no wire enum). **Key fix**: `tokens_after = int(tokens_before * masked/original)` — a REAL token-reduction ratio (vs structural's message-count ratio at `structural.py:192-193`, blind to in-place tombstoning), kept in the loop's token scale so the chained hybrid sees the reduction and can defer semantic.
- `compactor/chained.py` — `ChainedCompactor(Compactor)`: runs children in sequence (preclear→hybrid), threads compacted_state forward, merges `messages_compacted`, carries the last-stage tokens + C2 LLM-usage attribution; empty → ValueError. Transparent to the loop's single `compact_if_needed` call site (loop.py:2221) → loop UNTOUCHED.
- `_category_factories.py` — `_compaction_preclear_ratio()` (`CHAT_COMPACTION_PRECLEAR_RATIO`, valid (0,1) else 0=OFF) + `make_chat_compactor` branch: ratio>0 → `ChainedCompactor([PreClearCompactor(TiktokenCounter(gpt-4o)), hybrid])`; unset → bare `HybridCompactor` (DEFAULT byte-identical).
- `test_compactor_preclear.py` (8) + `test_compactor_chained.py` (7) — FLAT path per existing convention (test-path drift caught: existing compactor tests are `test_compactor_<name>.py`, not a `compactor/` subdir).

**Gate**: mypy src 376 (0) · black/isort/flake8 clean · v2 lints (`scripts/lint/run_all.py` from repo root) 10/10 incl. check_llm_sdk_leak · 15 new + 34 existing compactor/factory tests pass.

**Note**: factory wire (US-3) pulled into Day 1 (it's the natural home of the preclear branch). Day 2 = harness + corpus + harness tests + real-Azure run.

## Day 2 (2026-06-24) — Measurement harness + corpus + real-Azure run (US-2)

**Shipped**:
- `scripts/benchmark_layered_compaction.py` (Cat 4 eval, mirrors benchmark_sandbox_escape.py) — `load_cases / build_transcript (spec→Messages) / measure_case (L0 raw / L1 tool-clear-only via PreClearCompactor / L2 structural / L3 hybrid-semantic) / build_report / report_to_markdown / _amain (RUN_AZURE_INTEGRATION-gated L3) / main`. Measures with a REAL `TiktokenCounter(gpt-4o)` (NOT the compactor's internal message-count approximation).
- `tests/fixtures/context_mgmt/layered_compaction_cases.yaml` — 6 specs spanning tool-heavy→text-heavy + a single-turn NO-OP demo.
- `tests/unit/scripts/test_benchmark_layered_compaction.py` (13, importlib idiom) — load/transcript/measure(L0/L1/L2)/report + L1==L2 invariant + single-turn NO-OP + no-L3 invariant.

**A/B result (real Azure, 6 cases × cheap tier)**:
| metric | value |
|--------|-------|
| mean tool_clear_reduction | **33.72% → IN ACON band [26-54%]** ✅ |
| mean semantic_reduction | 40.65% |
| semantic_deferred_rate | **66.67%** (4/6) |
| preclear_recommended | **True** |

Per-case tool_clear%: tool-heavy-long 55.83 · tool-heavy-mid 34.20 · balanced 36.81 · text-heavy 11.05 · rehydrated-deep 64.44 · single-turn-noop **0.00** (user-anchored NO-OP demo).

**Verdict (evidence-first, same shape as #136/#138)**: the FREE, LLM-free tool-clear layer reclaims **33.72%** on average (IN the ACON band), capturing **~83%** (33.72/40.65) of the TOTAL compaction yield the expensive semantic layer reaches — and tool-clear alone defers semantic in **2/3** of cases. The semantic LLM layer earns its cost mainly on prose-heavy transcripts (text-heavy: tool-clear 11% → semantic 34.6%, +23pp). **Recommendation: keep default OFF; ship the preclear as a selectable env opt-in** (the win is composition-dependent + the user-anchored masker NO-OPs single-send chat). Report → `artifacts/layered_compaction_report.{md,json}`.

**Notable**: L1 == L2 in every case — the synthetic corpus has unique tool args (no retries), so structural's dedup drops nothing → masking IS structural's entire value here. Honest: on real conversations with retries, structural adds dedup beyond tool-clear; this corpus isolates the masking layer.

**Gate**: mypy src 376 (0) · run_all 10/10 · pytest 2825 +5skip (+28: 8 preclear + 7 chained + 13 harness) · black/isort/flake8 clean · LLM-SDK-leak clean. (mypy `scripts/` not in gate scope — `import yaml` stub, same as existing benchmark_sandbox_escape.py.)

## Day 3 (2026-06-24) — Drive-through (US-4) — chat-v2, real Azure gpt-5.2

Clean restart (Risk Class E): no python pre-start, :8000 free, :3007 node (frontend) untouched. dev-login jamie@acme.com·operator·acme-prod.

**ARM A — preclear ON** (`CHAT_COMPACTION_PRECLEAR_RATIO=0.5` + `CHAT_COMPACTION_TOKEN_BUDGET=2000` + `CHAT_COMPACTION_KEEP_RECENT_TURNS=2`, env set BEFORE startup → `make_chat_compactor` returns `ChainedCompactor([PreClearCompactor, hybrid])`):
- 3 real-LLM turns all completed + rendered: T1 "TCP three-way handshake" → SYN/SYN-ACK/ACK; T2 "TLS 1.3 handshake" → completed; T3 "compare + QUIC" → QUIC answer. **No-regression**: chat behaves identically with the preclear chain active. Screenshot `dt-57139-preclear-on-no-regression.jpeg`.
- LLM calls: gpt-5.2 ×3 (action-tier answers) + gpt-5.4-mini ×3 (cheap-tier verification, 1/turn). **Compaction semantic did NOT fire** (cheap count == turn count = no extra summarize call) even at 3 turns / budget 2000 — plain chat stayed under the trigger.

**ARM B — default OFF** (env UNSET → `make_chat_compactor` returns the bare `HybridCompactor`, byte-identical pre-57.139): restart → "capital of Japan?" → "Tokyo" → completed. Default path unchanged. Screenshot `dt-57139-default-off-unchanged.jpeg`.

**Honest CATCH = the harness, UI = no-regression + chain wiring** (同 57.136/138 "兩者結合"): the preclear masking yield is NOT UI-triggerable on plain chat — (a) the masker is user-anchored (needs > keep_recent user turns), (b) it masks `role="tool"` results, of which plain Q&A has NONE, and (c) chat single-send context stayed under budget even at 3 turns (the documented "normal chat doesn't trigger compaction" reality). The 33.72%-in-band yield + 2/3 semantic-deferral are proven by the **harness** (Day 2), NOT claimed from the UI. The UI proves the lever is wired into the main flow and chat is unaffected (no-regression) + the default is byte-identical.

**Note**: a `sessions_pkey` duplicate-key on the 2nd send is a PRE-EXISTING best-effort `create_session` INSERT race (`router.py:368`, caught, chat unaffected — all turns completed) — unrelated to preclear.

## Day 4 (2026-06-24) — CHANGE-106 + design note 43 + closeout

_(in progress)_
