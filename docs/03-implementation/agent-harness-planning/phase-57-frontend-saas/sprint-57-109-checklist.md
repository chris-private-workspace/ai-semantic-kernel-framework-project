# Sprint 57.109 — Checklist (C2: compaction cheap tier — `make_chat_compactor(profile.cheap)` retier + `_compaction` cost-ledger attribution (57.82 mirror) + `CHAT_COMPACTION_TOKEN_BUDGET` knob → lowered-budget drive-through)

[Plan](./sprint-57-109-plan.md)

---

## Day 0 — Plan-vs-Repo Verify + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `f4089fd9`) — DONE, catalogued in progress.md D1-D12
- [x] **Prong 1 — path verify**: EDIT files Glob-1 (`handler.py` / `_category_factories.py` / `_contracts/compaction.py` / `compactor/semantic.py` / `compactor/hybrid.py` / `compactor/structural.py` / `orchestrator_loop/loop.py` / `_contracts/events.py` / `api/v1/chat/router.py` / `.env.example`); test suites pinned (5 compaction suites + handler/profile tier tests + router observer tests + billing_outbox tests); design note 24 file path Glob'd (`24-multi-model-profile-design.md`); NO new src files expected
- [x] **Prong 2 — content verify** (D1 verification mirror fully pinned incl. `verification_model`; D3 `_summarise` returns str → return-shape change; D4 hybrid one-site forward; D5 LoopCompleted ×3 ctor sites; D9 TokenUsage = prompt/completion_tokens; D12 quota reconcile mirror fold-in): `ChatResponse` usage/model field names at the compactor seam · `_verification` enqueue payload shape incl. WHAT MODEL it attributes (router.py:683-709 + `LoopCompleted` verification fields — load-bearing for the mirror) · grep ALL `CompactionResult(` constructors (9 src + 2 test, keyword-style) · hybrid construct-vs-forward (hybrid.py:79-174) · verif accumulation idiom (loop.py:2003-2005/:2538-2541/:2607+:2631+:2656) · billing_outbox idempotency key shape (:75-77 — suffix participates) · `_CHAT_TOKEN_BUDGET` consumer sites · `.env` cheap config (commented template only — D11 dt lever) · structural-only compaction enqueues NOTHING (zero-usage guard mirror) · semantic retry path single-count seam (failed attempts raise — no usage to count)
- [x] **Prong 3 — schema verify**: N/A (no DB / no migration — cost_ledger sub_type + billing_outbox suffix are 57.82 infrastructure) — recorded explicitly
- [x] **Catalog drift** findings in progress.md Day 0 (D1-D12 + implications; plan §8 cross-ref)
- [x] **Go/no-go**: GO — D3 (private-method signature) + D12 (one-expression addition) shift scope < 10%

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-109-compaction-cheap-tier` (from `main` `f4089fd9`)

---

## Day 1 — Backend: retier + usage capture (US-1 + US-2 first half) ✅

### 1.1 Compactor cheap retier (US-1)
- [x] **`handler.py:460`**: `make_chat_compactor(profile.cheap)`; §321-327 comment block → three-tier consumer map (loop/prompt=action · verification=cheap 57.97 · compaction=cheap 57.109); MHist 1-line
- [x] **Handler tier-pin test**: the built compactor's semantic client IS the profile's cheap client (mirror the 57.97 verifier-tier test shape) + explicit cheap-unset shares-action-client test (×2 added)
  - DoD: grep `make_chat_compactor(` → sole call site carries `profile.cheap` ✓

### 1.2 `CompactionResult` usage fields + semantic capture (US-2 backend half 1)
- [x] **`_contracts/compaction.py`**: `CompactionResult` += `input_tokens: int = 0` + `output_tokens: int = 0` + `model: str = ""` (frozen, defaulted; MHist 1-line)
- [x] **`semantic.py`**: `_summarise` returns `(text, prompt, completion, model)` (D3 — return-shape change), extracted at the call site into the triggered result (failed attempts raise → only the successful attempt counted)
- [x] **`hybrid.py`**: :166 merged-result forwards semantic's usage fields (D4 — the only LLM-call path); structural/passthrough/failed-fallback keep zeros
- [x] **Unit tests CONVERT/ADD**: semantic usage captured + usage-None zeros · hybrid forward — 0 deletions across the 3 compactor suites
  - DoD: 5 compaction suites green +3 new cases ✓; mypy strict 0 ✓

---

## Day 2 — Backend: accumulator + LoopCompleted + observer + knob (US-2 second half + US-3) ✅

### 2.1 Accumulator → `LoopCompleted` → observer `_compaction` (US-2 backend half 2)
- [x] **`loop.py`** compaction site: ~~accumulator fold~~ → **D-DAY1-1 design correction**: usage rides `ContextCompacted` (+3 server-side dataclass fields; wire untouched) — loop.py diff = ONE yield site; see progress.md D-DAY1-1
- [x] **`_contracts/events.py`**: ~~`LoopCompleted` +3~~ → **`ContextCompacted` +3** per D-DAY1-1 (LoopCompleted has 30+ ctor sites; the event-carrier shape bills EVERY termination path — strictly better); `loop_end`/`context_compacted` WIRE untouched — count 24, no codegen diff ✓
- [x] **`router.py`** observer: accumulates off `ContextCompacted` events (multi-compaction → ONE row) → `compaction_* > 0` → `billing_outbox.enqueue(sub_type_suffix="_compaction", model=<cheap, fallback loop model>)`; zero-usage → NO enqueue (mirror :704-736)
- [x] **Tests ADD** (cost-ledger integration ×4): `_compaction` row at the cheap model name · structural-zero no-enqueue · multi-compaction accumulates into one idempotency key · quota fold (D12)
  - DoD: grep `sub_type_suffix` → loop ""/`_verification`/`_compaction` three-way ✓; run_all 10/10 (count 24) ✓

### 2.2 Budget env knob (US-3)
- [x] **`_category_factories.py`**: `_compaction_token_budget()` env-read (`CHAT_COMPACTION_TOKEN_BUDGET`; default 100_000; non-int/non-positive → default no-crash) + budget threaded to ALL THREE compactors (D13); `.env.example` documents it
- [x] **Unit tests ADD ×7**: env honored + invalid-fallback ×4 + default + sub-compactor threading (appended to the EXISTING `tests/unit/api/test_category_factories.py` — D-DAY1-2 basename-collision lesson)
  - DoD: default path byte-identical (no env set → 100_000) ✓

---

## Day 3 — Full gates + drive-through (US-4) + CHANGE-076 ✅

### 3.1 Full gate sweep
- [x] mypy strict 0/359 · black/isort/flake8 0 (all four, 57.107 lesson) · run_all 10/10 from repo root (count 24; no codegen diff) · full pytest **2477+4skip non-e2e + 8 e2e = 2485 (+23, 0 del)** vs 2462+4skip baseline · FE untouched holds · `loop.py` diff = 1 yield site (D-DAY1-1 carrier shape) · wire schema diff = empty

### 3.2 Drive-through (US-4 — real UI :3007 + fresh no-reload backend + real Azure; zero dev-login; Risk Class E clean restart with BOTH knobs set BEFORE start; sole-owner verified, no orphan spawn-workers) ✅ PASS
- [x] **Tier delta lever confirmed**: `.env` cheap `gpt-5.4-mini` distinct from action `gpt-5.2` (57.97 dt legacy — no tenant policy needed)
- [x] **Compaction triggers live**: keep=1 + budget=2000 + 12-group patrol run + ONE B1 mid-run injection → `context_compacted` **9824→2679 tokens, messages_compacted=8, 3535ms** (a REAL summarize call; D-DAY3-1/2 catalogue why the keep knob was required — semantic was structurally unreachable on the main flow at keep=5)
- [x] **Ledger reality**: billing_outbox `{session}:llm:_compaction` model **`gpt-5.4-mini-2026-03-17`** in=260/out=149 status=done → cost_ledger `azure_openai_gpt-5.4-mini-2026-03-17_compaction_input/_output` $0.000195/$0.0006705 (priced) — CHEAP model, NOT action
- [x] **Quality + non-regression**: post-compaction turn-5 `prompt_built 3411` (from 9824); final answer carries **BLUEFIN** + `verification_passed llm_judge 0.99` + clean `loop_end`; `_compaction` outbox count across the whole dt day = 1 (every default-shape run enqueued NOTHING — D-DAY3-3); memory extraction = gate-level only (no runtime ledger surface; reported honestly)
- [x] Screenshots ×3 + run snapshot in `artifacts/` + observed-vs-intended table in progress.md
  - DoD: ALL legs PASS ✓; no tenant policy modified (env knobs only — process-scoped, gone on next normal restart)

### 3.3 CHANGE-076
- [x] `claudedocs/4-changes/feature-changes/CHANGE-076-compaction-cheap-tier-ledger-attribution.md` (1-page; spike design note NOT required — design-note-24 continuation, §5.5 NOT-apply)

---

## Day 4 — Closeout

### 4.1 Closeout
- [x] retrospective.md Q1-Q7 + calibration (`multi-model-profile-spike` 0.55 2nd data point, ratio ≈1.1-1.2 IN band upper edge; agent-delegated: no) + progress.md final
- [x] Design note 24 edit: "compaction cheap tier" invariant → RESOLVED (extraction half stays open); MHist 1-line
- [x] Navigators: CLAUDE.md Current-Sprint row + Last-Updated; MEMORY.md quality pointer + memory subfile; next-phase-candidates (closes proposal §3.4 C2; C-family 3/3 done; next slice B4 per interleave); sprint-workflow matrix row (2nd data point)
- [x] PR (push + open on user authorization — authorized 2026-06-12; **PR #284**)
