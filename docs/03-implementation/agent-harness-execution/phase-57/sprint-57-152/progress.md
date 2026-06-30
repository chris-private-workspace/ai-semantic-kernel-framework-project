# Sprint 57.152 Progress — combine post-send extract + summarize into one LLM call

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-152-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-152-checklist.md)

---

## Day 0 — 2026-06-30 — Plan-vs-Repo Verify (三-prong) + Branch

Branch `feature/sprint-57-152-memory-combined-formation` from `main` HEAD `a6e8d586` (Sprint 57.151 flip PR #357 merged).

### Three-prong verify (against `main` HEAD `a6e8d586`)

**Prong 1 — path verify**: PASS
- NEW absent: `formation.py`, `test_formation.py`, `CHANGE-119-*`, design note `55-*` — all 0 results.
- EDIT present: extraction.py / session_summarizer.py / memory/__init__.py / handler.py / router.py / core/config/__init__.py / check_promptbuilder_usage.py / test_memory_auto_extract.py / test_handler.py — all OK.
- Numbers free: highest CHANGE = 118 (→ 119 free); highest design note = 54 (→ 55 free).

**Prong 2 — content verify**: PASS (drift table below)

| Finding | What | Implication |
|---------|------|-------------|
| D-write-facts-session-id | `extract_session_to_user` (`extraction.py:79-129`) — `session_id` param is UNUSED in the write loop | `write_facts` need not take `session_id` (only tenant_id/user_id/items/trace_context) — confirmed clean extraction |
| D-ctx-field-rename | `ctx.extractor` / `ctx.summarizer` / `ChatMemoryExtractContext(` used in `router.py:442,496,681,706-720` + `test_memory_auto_extract.py:20,54-59,83-138` + `test_handler.py:21,156-157` | rename to `former` → update these sites (expected test maintenance for a behavior change, NOT deletion) |
| D-allowlist-formation | `check_promptbuilder_usage.py:54-62` already allowlists `extraction.py` + `session_summarizer.py` | add `agent_harness/memory/formation.py` Day-1 (same category, 57.151 precedent) |
| D-profile-gate | `_maybe_auto_extract` (`router.py:706`) reads `profile()` gated on `extractor is not None and user_id is not None` | becomes `former.wants_user_facts and user_id is not None` |

**Prong 3 — schema verify**: N/A (no DB table / migration / ORM column change this sprint).

**D-baselines** (documented; re-verify at final gate): pytest 3042 · wire 26 · Vitest 922 · mockup 51 · mypy 0/396 · run_all 11/11.

**Go/no-go**: scope-shift ~0% (all findings match the plan's pre-recon). PROCEED to Day 1.

---

## Day 1 — 2026-06-30 — Worker + dispatch extraction (US-1/2/3)

- **`MemoryExtractor.write_facts`** extracted from `extract_session_to_user` (the content/confidence/clamp/`source="auto_extract"` loop verbatim); `extract_session_to_user` now ends `return self.write_facts(...)`. Behavior-preserving — `test_extraction.py` (9) green untouched.
- **`SessionSummarizer.store_summary`** extracted from `summarize_and_store` (the blank-guard + `upsert_summary` verbatim); `summarize_and_store` now ends `store_summary(...)`. Behavior-preserving — `test_session_summarizer.py` (6) green untouched.
- **`MemoryFormationWorker`** (`formation.py`): `_form_combined` (ONE combined prompt with facts/summary sections conditioned on wired collaborators + the known-facts dedup block → ONE `chat()` → tolerant combined-JSON parse → `write_facts` + `store_summary`); `_form_separate` (delegate to the 2 full methods — env fallback); `wants_user_facts` property; own render/parse/coerce helpers (small self-contained; pre-existing identical helpers in extraction/summarizer NOT refactored per Karpathy §3 surgical). Exported in `memory/__init__.py`.
- **`chat_memory_combined_formation: bool = True`** flag (env `CHAT_MEMORY_COMBINED_FORMATION`); AP-8 allowlist += `formation.py`.
- **`test_formation.py`** (10): combined 1-call writes both · `combined=False` → 2 delegate calls · only-extractor / only-summarizer one-section · no-user skips facts forms summary · empty/no-collaborator no-op · `_build_prompt` section+known-block · `_parse_combined` shapes.
- Gate: black/isort/flake8 clean (fixed 1 docstring E501 + 2 test E501 + handler.py F401/F811 by dropping the now-unused TYPE_CHECKING MemoryExtractor/SessionSummarizer imports — the late runtime imports + dataclass `former` cover it). AP-8 0 violations.

## Day 2 — 2026-06-30 — Rewiring + test updates (US-4)

- **handler.py**: `ChatMemoryExtractContext` `{extractor, summarizer}` → `{former: MemoryFormationWorker}`; `build_chat_memory_extractor` builds the worker (`combined=settings.chat_memory_combined_formation`), still None when both feature flags off.
- **router.py**: `_maybe_auto_extract` loads ledger once → `profile()` known_facts gated on `former.wants_user_facts and user_id is not None` → ONE `await former.form(...)`.
- **test updates**: `test_memory_auto_extract.py` → `_StubFormer` (records `form()` + `wants_user_facts`); `test_handler.py` cheap-tier assertion → `ctx.former._chat_client`.
- **Full gate**: mypy `src` 0/397 (+1 formation.py) · run_all **11/11** (incl. llm_sdk_leak + AP-8 formation.py allowlisted) · backend pytest **3053 passed / 6 skip** (+11: test_formation +10, test_memory_auto_extract +1) · black/isort/flake8 clean.

## Day 3 — 2026-06-30 — Drive-through (real chat-v2 + real Azure gpt-5.2)

Risk Class E clean restart: killed stale 57.151 backend PID 61048; started fresh no-reload 57.152 backend PID 47908 (sole :8000 owner, 23:17). Frontend vite on :3007 (node, untouched). dev-login dan@acme.com (acme-prod, admin).

**Leg 1 — combined formation (THE sprint change) = STRONG PASS.** One send: "Hi, I'm Marcus and I lead the Payments Platform team. We're migrating our session store from Redis to DynamoDB. We decided to use a write-through cache during the cutover. Open question: TTL-based expiry vs explicit invalidation." Agent answered fully (TTL-default + read-time expiry + hybrid recommendation). DB inspector (`artifacts/db-evidence-combined-formation.txt`) — session `73a909fe`:
- **summary half** (`memory_session_summary`, updated `15:20:30`): Redis→DynamoDB / TTL-vs-invalidation summary + 3 `key_decisions` (write-through cache during cutover; prefer TTL; explicit invalidation only must-revoke-now) + 3 `unresolved_issues`.
- **facts half** (`memory_user [auto_extract]`, **same `15:20:30` timestamp**): conf 0.99 "Marcus's team is migrating its session store from Redis to DynamoDB" + conf 0.98 "The session-store cutover will use a write-through cache."
- **Both halves at the SAME `15:20:30` timestamp** = ONE combined background call (the unit test proves `chat_call_count == 1`; the DB proves both halves landed together). The agent's in-loop discretionary `memory_write` (source `None`, 15:20:07) of "Marcus leads the Payments Platform team" was dedup-upserted by the auto_extract at 15:20:30 (created stays 15:20:07, updated → 15:20:30) — 57.150 dedup coexists with combined formation.

**Leg 2 — recall injection (read path, UNCHANGED this sprint).** NEW session, "do you remember who I am and what we were working on?" Inspector memory-read trace confirms the new session's PromptBuilder injected BOTH halves the combined call wrote: `profile()` read the Marcus user facts + `recent_sessions()` read `memory_session_summary:73a909fe` (the Redis/TTL summary). So the combined-formation outputs flow into recall. The agent's FINAL ANSWER hit two PRE-EXISTING carryovers (NOT 57.152 regressions — this sprint only changed the write path):
- **cross-sprint dan identity conflict**: dan's `user_id` accumulated both 57.149's "Chris/Project Aurora/billing" facts and Leg-1's "Marcus/Payments/Redis" facts → the model synthesized the older Chris/Aurora identity. Artifact of reusing the `dan` dev identity across sprints with different fictional personas, not a formation bug.
- **`AD-Verification-Judge-Memory-Inject-Blind`** (57.149 carryover): the in-loop judge sees only the conversation trace (not injected memory) → REJECTed the recall as "fabrication" → coached retry produced an "I don't have prior context" answer. Known carryover, judge-blind to memory injection.

Verdict: **the sprint's change (combine extract+summarize into one call) is STRONG PASS** (Leg 1: both halves from one call, same timestamp; unit test call-count==1). Recall injection confirmed (Leg 2 trace). Recall final-answer quality is gated by pre-existing carryovers unchanged by this sprint; 57.151's own drive-through already proved clean recall on the unchanged read path. Screenshots: `artifacts/sprint-57-152-leg1-combined-formation.png` + `sprint-57-152-leg2-recall-injection.png`.

---
