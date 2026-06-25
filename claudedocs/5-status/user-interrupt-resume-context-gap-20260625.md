# User-Initiated Stop → Continue Loses Context (Interrupt-Resume Durability Gap)

**Purpose**: Document a verified harness gap — when a user STOPS a running chat turn mid-execution and then types "continue", the agent has no memory of what it was doing — plus the CC blueprint for the fix and a root-cause analysis of why the gap was missed by prior CC-parity / pause-resume analyses.
**Category / Scope**: Cat 1 (Orchestrator Loop) + Cat 7 (State Mgmt) + chat-v2 ; cross-cutting durability
**AD ID**: `AD-UserStop-Resume-Context` (candidate; Phase 58+)
**Created**: 2026-06-25
**Last Modified**: 2026-06-25
**Status**: Active — verified gap, registered as candidate (NOT yet scheduled)

> **Modification History**
> - 2026-06-25: Initial creation — drive-through-verified gap + CC blueprint + root-cause of the miss

---

## 0. TL;DR — the item

**Symptom**: In chat-v2, if you send a message, let the agent run, **hit Stop mid-run**, then type **"continue"**, the agent does not know what it was doing — it replies "Continue from what, exactly?". It DOES still remember earlier *completed* turns, but the interrupted run is gone.

**Verdict (drive-through verified, not paper)**: This is **real amnesia about the interrupted run**, not "the backend quietly finished". A turn that is stopped mid-execution persists **nothing** to the `messages` ledger — not its answer, not even the user's prompt for that run — because the ledger writes are committed only when the streamed request finishes normally, and a client disconnect rolls the whole request transaction back.

**Why it matters**: This is one of the most visible "feels broken vs Claude Code" behaviors. CC handles exactly this case well (it is even called out verbatim in CC's source as "user clicks Stop seconds after send").

**Status**: NOT a feature that exists. Registered as candidate `AD-UserStop-Resume-Context`. See §6 for proposed spike scope.

---

## 1. The symptom (precise scenario)

1. User: "ok, what action you can execute or do for me in this session?"
2. Agent starts running (generating / tool use).
3. User **hits Stop** mid-run (the chat-v2 Stop button).
4. User: "continue".
5. Agent: "What do you want to continue with? / Continue from what, exactly?" — it has no record of the interrupted work.

The frontend Stop button is a **client-side abort only** ([`useLoopEventStream.ts:149-152`](../../frontend/src/features/chat_v2/hooks/useLoopEventStream.ts) — `abortRef.current?.abort()` + `setStatus("cancelled")`); it does **not** call the cancel API. So "Stop" just closes the browser's SSE connection.

---

## 2. Verified evidence (drive-through + DB ledger inspection, 2026-06-25)

Reproduced against the **real running backend + real Azure gpt-5.2**, inspecting the `messages` ledger directly via the DB (`ipa_v2`), per the project's Drive-Through Acceptance rule (gate/curl is not enough).

**Experiment**: (a) one quick *completing* send to establish prior context, (b) a long-generation send **stopped at 3s mid-run** (same session), (c) a "continue" send.

| Step | Action | `messages` ledger result |
|------|--------|--------------------------|
| #0 | "give me Demo A / Demo B" → **completes** | ✅ **2 rows** persisted (user + assistant) |
| #1 | long essay, **STOP at 3s** (loop was at `llm_request`, awaiting the LLM) | ❌ ledger **stays at 2 rows** — polled 40s, **0 new rows**: the interrupted run wrote NOTHING (no answer, no prompt) |
| #2 | "continue" | loaded only the #0 context → agent: **"What should I continue from — do you want two more demo ideas, or to expand Demo A/B?"** |

**Key findings**:
1. A **completed** turn persists to the ledger and IS rehydrated on the next send (the agent remembers "Demo A/B") — i.e. cross-turn rehydration (Sprint 57.127 `DBMessageStore`) works for completed turns.
2. A turn **stopped mid-run** persists **nothing**. The backend does not run to completion after the client disconnects (40s of polling → no new rows), AND the persistence is deferred.
3. Even the **turn-0 user-prompt persist** — which [`loop.py:1974-1977`](../../backend/src/agent_harness/orchestrator_loop/loop.py) explicitly comments is meant to survive "*even if the run fails before an answer*" — does **NOT** survive a mid-run disconnect. The append uses `begin_nested()` (SAVEPOINT) on the request's DB session, and the outer commit is deferred to stream-end; a disconnect rolls it back. **This is a latent bug: intent ≠ behavior.**

(Honesty: I could not fully distinguish "loop cancelled on disconnect" vs "loop ran but its commit failed against the dead request txn". The outcome is identical — nothing persisted — so it does not change the conclusion.)

This exactly reproduces the user's screenshot: the agent half-remembered ("the two demos above" ≈ "Demo A/B") because earlier completed turns persisted, but had zero record of the interrupted task.

---

## 3. How Claude Code does it (the blueprint)

Verified against the deobfuscated CC source at `reference/claude-code-source-cdoe/src`. Four principles:

1. **User message is persisted + flushed synchronously BEFORE the LLM call.** [`QueryEngine.ts:436-463`](../../reference/claude-code-source-cdoe/src/QueryEngine.ts) — interactive mode does `await recordTranscript(messages)` + `flushSessionStorage()` before entering the query loop. The comment is almost written for our bug:
   > *"If the process is killed before that (e.g. **user clicks Stop in cowork seconds after send**), the transcript is left with only queue-operation entries; … --resume fails with 'No conversation found'. Writing now makes the transcript resumable from the point the user message was accepted, **even if no API response ever arrives**."*
   Cost is noted: "~4ms on SSD".

2. **The interrupt is RECORDED as a message.** `INTERRUPT_MESSAGE = '[Request interrupted by user]'` / `'[Request interrupted by user for tool use]'` ([`utils/messages.ts:207-209`](../../reference/claude-code-source-cdoe/src/utils/messages.ts)); inserted on abort via `createUserInterruptionMessage()` ([`query.ts:1046-1050`, `1501-1505`](../../reference/claude-code-source-cdoe/src/query.ts)). Incomplete tool_uses get synthetic tool_results via `yieldMissingToolResultBlocks()` ([`query.ts:123, 984, 1025`](../../reference/claude-code-source-cdoe/src/query.ts)) so the transcript never holds a `tool_use` without its result.

3. **Resume = replay the full transcript** (incl. the interrupt marker + partial assistant + synthetic tool_results). `loadFullLog()` + `buildConversationChain()` walk the `parentUuid` chain (`utils/sessionStorage.ts`); restored into the message array before the next LLM call → the model sees everything, including "you were interrupted here".

4. **Single in-process cooperative abort.** ESC → `abortController.abort('interrupt')`; the query loop, on abort, yields the partial + marker + synthetic results, then the same process records them. There is no "client disconnect tears down a half-written server transaction" failure mode (CC is a local CLI).

---

## 4. The fix direction — close the last two miles on the architecture we already have

The project's core philosophy is **already the same as CC's** — "the ledger on disk/DB is the source of truth; replay it on run start". `DBMessageStore.load()` at [`loop.py:1959`](../../backend/src/agent_harness/orchestrator_loop/loop.py) IS the equivalent of CC's `buildConversationChain`. The gaps are two disciplines CC has and we don't:

| CC mechanism | V2 current state | Fix needed |
|--------------|------------------|-----------|
| User msg committed + flushed **before** the LLM call | turn-0 persist is in a deferred-commit SAVEPOINT → rolls back on disconnect | Commit the user-prompt ledger write in its **own immediate transaction** (mirror the early `db.commit()` already done for the sessions row at [`router.py:384`](../../backend/src/api/v1/chat/router.py)) |
| Per-message **incremental** persist as the turn streams | persists at completion boundaries, committed at stream-end | Commit each ledger append in its **own short transaction**, not the request-scoped txn that dies on disconnect |
| Stop writes `[Request interrupted by user]` + synthetic tool_results | Stop writes **nothing** | On cancel/disconnect: write a synthetic interrupt marker + synthetic tool_results for pending tools, committed via a **fresh DB session** (not the dead request txn) |
| Stop = in-process cooperative AbortController | Stop = browser closes SSE; server request torn down with no cleanup | Stop button calls **`POST /sessions/{id}/cancel`** (already exists, [`router.py:1167`](../../backend/src/api/v1/chat/router.py)); server cancel-handler runs the persistence cleanup above |
| Transcript replay on resume | `DBMessageStore.load()` already replays ✅ | No change — just needs the above to actually contain the data |

This is **not new architecture** — it is adding CC's "persist immediately + record the interrupt" discipline onto the ledger-replay we already built.

> Note: this is distinct from Sprint 57.88 durable **HITL pause-resume** (deferred ESCALATE → `state_snapshots` checkpoint → `POST /resume`). That handles an *approval* pause and is correct. A *user-initiated stop* is a different trigger (a hard abort, no checkpoint) and is the case that has no handling today.

---

## 5. Root cause — why was this missed by A/B/C and the research analyses?

It was missed not because nobody looked at interrupt/resume, but because of **how the comparison was framed**. Four compounding reasons:

1. **The comparison was scoped to the HARD problem and declared victory.** The CC pause-resume blueprint ([`cc-source-blueprint-pause-resume-phases-20260608.md`](cc-source-blueprint-pause-resume-phases-20260608.md) §2.2, §5) analyzed *durable mid-loop resume* (restoring exact loop phase / in-flight tool state), correctly found **CC does not do that** ("`/resume` 是重載對話…非 mid-loop resume"), and concluded the project's HITL 57.88 is **ahead of CC** ("Durable pause-resume — CC 完全沒有 … 57.88 純自研,方向對"). This created false confidence that "resume is handled — better than CC, even".

2. **It dismissed the very mechanism that matters.** CC's "reload the conversation transcript" was framed as the *inferior* thing ("= 重載對話, 非 mid-loop resume"). But that transcript-replay is **exactly what the user-stop→continue case needs**, and it is the thing CC does *robustly* (immediate persist + interrupt-as-message). The analysis treated the needed mechanism as trivial and moved on.

3. **The parity check box-checked at the mechanism level, not the UX level.** The CC-parity doc ([`agent-harness-cc-parity-20260607.md`](agent-harness-cc-parity-20260607.md) row #2) marks **"Interrupt & cancellation ✅"** (anchor `termination.py CANCELLED + asyncio`, category "—" = not a gap). True at the mechanism level — the run *can* be cancelled — but "can cancel ✅" is **not** "can continue-with-context after cancel". Nobody asked the follow-up question. This is precisely the gate-vs-drive-through trap the project's own rules warn about ([`memory/feedback_drive_through_over_paper_metrics.md`](../../memory/feedback_drive_through_over_paper_metrics.md)).

4. **HITL-pause and user-stop were never separated, and the user-stop path was never drive-through-tested.** Sprint 57.88 covered the HITL ESCALATE pause (and it was drive-through verified — it works). Because "resume" was marked done via that path, the *user-stop* variant (a different code path producing a hard abort) was never separately scoped. The capability drive-through ([`chat-v2-agent-loop-capability-drivethrough-20260618.md`](chat-v2-agent-loop-capability-drivethrough-20260618.md)) drove HITL pause-resume but not "user stops mid-run → continue". The durability bug (§2.3) is invisible to static analysis — only a real drive-through + DB inspection surfaces it.

**One-line root cause**: the analyses compared the *hardest* form of resume (mid-loop state) and concluded we were ahead of CC, while the *simplest, most user-visible* form (continue after a user stop) was box-checked as "cancellation ✅" and never driven — so the durability gap underneath it stayed invisible.

This also reinforces the "守住不要動" guard in [`next-phase-candidates.md`](../1-planning/next-phase-candidates.md) ("Durable, governable HITL pause … heavier than CC … don't simplify") — that guard is correct for the HITL case, but it should NOT be read as "all interrupt/resume is covered". The user-stop case is a separate, open item.

---

## 6. Recommendation

Register as candidate `AD-UserStop-Resume-Context` (done — see [`next-phase-candidates.md`](../1-planning/next-phase-candidates.md) §Net-new). When selected, a thin spike sprint, scoped:

- **US-1 — fix the latent durability bug**: commit the turn-0 user-prompt ledger write immediately (own transaction), so a mid-run stop preserves at least the question. (Closes the §2.3 intent≠behavior bug independent of everything else.)
- **US-2 — record the interrupt**: Stop button → `POST /sessions/{id}/cancel`; server cancel-handler persists a synthetic `[interrupted]` marker + synthetic tool_results for pending tools, via a fresh DB session.
- **US-3 — incremental commit**: each ledger append in its own short transaction (not the request-scoped txn).
- **US-4 — drive-through**: real UI + real backend + real LLM — stop mid-run → continue → assert the agent knows what it was doing (and the ledger contains the interrupt marker).

Evidence-first per project discipline: US-1 is a confirmed bug (fix directly); US-2/US-3 should be validated by the US-4 drive-through before being treated as done.

---

## 7. References

- **Verified evidence**: this doc §2 (drive-through DB experiment, 2026-06-25)
- **CC blueprint**: `reference/claude-code-source-cdoe/src/QueryEngine.ts:436-463`, `utils/messages.ts:207-209`, `query.ts:1046-1050/1501-1505/123`, `utils/sessionStorage.ts` (loadFullLog / buildConversationChain)
- **Prior analyses where this was missed** (cross-referenced back to this doc):
  - [`agent-harness-cc-parity-20260607.md`](agent-harness-cc-parity-20260607.md) row #2 "Interrupt & cancellation ✅"
  - [`cc-source-blueprint-pause-resume-phases-20260608.md`](cc-source-blueprint-pause-resume-phases-20260608.md) §2.2 / §5
- **Related shipped work**: Sprint 57.127 (`DBMessageStore` cross-turn rehydration), Sprint 57.88 (durable HITL pause-resume — different trigger)
- **Candidate registry**: [`next-phase-candidates.md`](../1-planning/next-phase-candidates.md) §Net-new — `AD-UserStop-Resume-Context`
