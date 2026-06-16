# 38 — chat-v2 Live Multi-Turn Context: Message Persistence + Rehydration (Spike Design Note)

**Purpose**: Extract the verified invariants of the Sprint 57.127 spike — giving the live agent loop a durable per-session Cat-3 `Message` ledger so a follow-up send carries the prior conversation into the LLM request.
**Category / Scope**: 範疇 7 (State Mgmt) + 範疇 1 (Orchestrator Loop) / Phase 57 / Sprint 57.127
**Created**: 2026-06-16
**Last Modified**: 2026-06-16
**Status**: Active (spike-extract — 95%+ verified ratio; all claims carry a file:line + a reproduce command)

> **Modification History**
> - 2026-06-16: Initial creation (Sprint 57.127) — extract from the shipped Approach-A implementation; closes `AD-ChatV2-Live-MultiTurn-Context`

---

## 1. Spike Summary (maps to US-1..US-8)

The 57.126 drive-through surfaced a real product bug: in chat-v2 a follow-up message in an EXISTING session started `loop.run()` with `messages = [system?, new_user]` only — no prior turns — so the LLM could not resolve references ("its population?" → "what does 'it' refer to?"). The `messages` table existed (`models/sessions.py:163-217`) but had **no writer**; `message_events` (57.125/126) persists SSE frames for the replay UI, not Cat-3 `Message` objects for the loop.

This spike wires a NEW provider-neutral `MessageStore` ABC into the main-chat loop. The loop **self-loads** the prior ledger at `run()` start and **persists** the run's user prompt + final answer — so `loop.run()`'s ABC signature is UNCHANGED (no caller ripple) and child loops (no store injected) are unaffected.

**Verified end-to-end** (real Azure gpt-5.2, session `9e89775d`): turn 1 "capital of France?" → "Paris" (`messages_count=4`); turn 2 "its population?" → "Paris has about 2.1 million residents…" (`messages_count=6` = 4 + 2 rehydrated). DB ledger: 4 rows, `sequence_num` 1→4 monotonic.

## 2. Decision Matrix (Approach A vs B vs C — user-picked A, 2026-06-16)

| | **A — `messages` table writer** (PICKED) | B — reconstruct from `message_events` | C — checkpoint-metadata |
|---|---|---|---|
| Fidelity | ✅ verbatim Cat-3 `Message` (incl. tool_calls) | ⚠️ ~80% — SSE frames drop tool/system structure | ✅ verbatim but |
| Storage | ✅ O(N) append-only rows | reuses existing rows | ❌ O(turns²) — re-serialize full history each checkpoint |
| Table | ✅ exists, just needs a writer (`models/sessions.py:163-217`) | exists | bloats `state_snapshots` JSONB |
| Verdict | **PICKED** — the path the `loop.py:244` SPIKE NOTE itself recommends | REJECTED — silent context loss = the `feedback_foundation_slice_verify_against_consumer` trap | REJECTED — quadratic + conflates state snapshot with the message ledger |

**Seam choice**: a new `MessageStore` ABC self-loaded by the loop, NOT a `loop.run(prior_messages=)` param. A `run()` signature change would ripple to `orchestrator_loop/_abc.py` + the router + subagent `fork`/`teammate` callers + every unit test. The injected ABC (bound to `(db, session_id, tenant_id)` at construction, exactly like `DBCheckpointer` at `checkpointer.py:94-150`) keeps `run()` unchanged and is symmetric (reads + writes).

## 3. Verified Invariants (each with a file:line + reproduce)

1. **Provider-neutral ABC** — `MessageStore(ABC)` at `state_mgmt/_abc.py:64` (`load()` `:81`, `append(messages, *, turn_num)` `:86`). Imports only Cat-3 `Message`; no DB/provider import. Verify: `python scripts/lint/run_all.py` (check_llm_sdk_leak green).
2. **DB impl, tenant-scoped** — `DBMessageStore` at `state_mgmt/message_store.py:74`; `load()` (`:93`) = `select(MessageRow).where(session & tenant).order_by(sequence_num)` (`:102`) → `_message_from_dict`; `append()` (`:115`) seeds `sequence_num` from `MAX+1` (`:143`) inside a best-effort `begin_nested()` SAVEPOINT (`:122`); `db is None` → `[]`/no-op. Verify: `pytest tests/integration/agent_harness/state_mgmt/test_message_store.py -q` (5 pass).
3. **Serde relocated (circular-import safety)** — `_message_to_dict` (`_contracts/message_serde.py:47`) / `_content_block_to_dict` (`:71`) / `_message_from_dict` (`:85`) moved out of `loop.py` so `state_mgmt` imports the leaf, not the heavy loop. `loop.py` imports them; `messages_from_metadata` stays in `loop.py`. Verify: `mypy src` 0/372.
4. **Loop self-load** — `run()` (`loop.py:1915`): `prior = await self._message_store.load() if self._message_store is not None else []` (`:1932`); `messages = list(prior)`; system reconstructed (NEVER persisted); user appended. ctor `message_store` param `:328`, assigned `:410`. Verify: `test_loop_multiturn_rehydration.py::test_run_rehydrates_prior_into_llm_request`.
5. **Persist points (de-risked)** — `_persist_to_ledger` helper at `loop.py:1906`; the user prompt persisted at run start (`:1941`, turn 0); the final answer persisted at the 2 end_turn sites (`:2689` stop_reason terminator, `:2721` FINAL branch). System + prior NEVER re-persisted. Verify: `test_loop_multiturn_rehydration.py::test_run_persists_user_prompt_and_final_answer`.
6. **Multi-tenant 鐵律** — `load`/`append` filter by the bound `tenant_id`; a cross-tenant load → `[]`. Verify: `test_message_store.py::test_cross_tenant_load_returns_empty`.
7. **Wiring (main loop only)** — `make_chat_message_store(db, session_id, tenant_id)` (`api/v1/chat/_category_factories.py`, None-guard) injected by `build_handler` (`api/v1/chat/handler.py`) onto the main chat loop; subagent child loops get none. Verify: `test_message_store.py::test_factory_none_guard` + the drive-through.
8. **No `run()` signature change / no migration / pure backend** — `loop.run()` ABC unchanged; `messages_default`/`message_events_default` partitions exist (`0028`) → no migration; wire 24, Vitest 904, mockup 51 unchanged.
9. **End-to-end (drive-through)** — turn 1 `messages_count=4` → turn 2 `messages_count=6` (+2 rehydrated); answer resolves "its"→Paris; ledger 4 rows seq 1→4. Reproduce: `progress.md` Day 3 + `artifacts/verify_ledger.py` + the 2 screenshots.

## 4. Cross-Category Contracts (17.md single-source)

- **`MessageStore` ABC** — registered in `17-cross-category-interfaces.md` § registry table (範疇 7, sibling to `Checkpointer`). Owner: 範疇 7. `load() -> list[Message]` / `append(messages, *, turn_num)`. No new SSE event, no new wire type (wire count stays 24). Consumes the Cat-3 `Message` contract (`_contracts/chat.py`).

## 5. Open Invariants (deferred — NOT verified in this spike)

- **Intra-turn tool round-trips** — only the user prompt + final answer are persisted this slice; assistant/tool messages WITHIN a turn are not in the ledger. → `AD-ChatV2-Ledger-Tool-RoundTrips` (deferred; avoids the dangling-tool_call risk the simpler 2-point persist sidesteps).
- **`metadata` round-trip** — the shared serde does NOT round-trip `Message.metadata` (local bookkeeping flags like `{"hitl"}`/`{"compacted_summary"}`) — same limitation as the proven HITL-resume path. Not sent to the LLM → no context impact; only local compaction/prompt-builder tagging.
- **Resume-path message persistence** — the resume flow's transcript persistence is a pre-existing 57.125 gap → `AD-ChatV2-Resume-Transcript-Persistence`.
- **`turn_num` always 0** — each send is its own `run()` starting at turn 0; cross-send ordering is via `sequence_num` (correct/monotonic). `turn_num` as a cross-send counter is cosmetic; not fixed this slice.
- **Backfill for pre-57.127 sessions** — graceful degrade to `prior=[]`; no backfill tool.
- **`message_events` / `messages` consolidation** — the dual-ledger is intentional (different consumers); a future canonical-ledger AD.
- **pg_partman partition automation** — the systemic fix for all partitioned tables (infra AD).
- **`model` / `tokens_*` on message rows** — null this slice (YAGNI).

## 6. Rollback / Fallback

- The store is **optional + best-effort**: `message_store=None` (any non-chat / child loop) → today's single-turn behavior, no persistence. `load`/`append` are best-effort (SAVEPOINT + swallow) → a DB hiccup degrades to `prior=[]`, never breaks a send.
- To revert: drop the `message_store=` injection in `build_handler` (1 line) → the loop stops loading/persisting (behavior reverts to pre-57.127); the `messages` rows already written are harmless (no reader without the injection). Estimated revert: <30 min. No migration to undo (no schema change).

## 7. References

- `CHANGE-094-chatv2-live-multiturn-context.md` — change record
- `progress.md` (Sprint 57.127) Day 0 (三-prong drift) + Day 3 (drive-through)
- `17-cross-category-interfaces.md` — `MessageStore` contract registration
- `memory/feedback_foundation_slice_verify_against_consumer.md` — why Approach B (lossy reconstruction) was rejected
- 57.125/126 (`message_events` persistence + replay) — the sibling ledger this spike does NOT reuse for the live loop
- `01-eleven-categories-spec.md` §範疇 7 (State Mgmt) / §範疇 1 (Orchestrator Loop)
