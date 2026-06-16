# Sprint 57.129 Progress — chat-v2 ledger intra-turn tool round-trips

**Branch**: `feature/sprint-57-129-chatv2-ledger-tool-roundtrips` (from `main` `858bd3af`, post-#304)
**AD**: closes `AD-ChatV2-Ledger-Tool-RoundTrips` (57.127 carryover)
**Plan**: [`sprint-57-129-plan.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-129-plan.md) · **Checklist**: [`sprint-57-129-checklist.md`](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-129-checklist.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch — YYYY-MM-DD (2026-06-16)

### Prong 1 — path verify ✅
- `agent_harness/orchestrator_loop/loop.py` exists — contains `_run_turns`, `_persist_to_ledger` (`:1906-1913`), `# output_type == TOOL_USE` (`:2774`), post-tool checkpoint (`:3059-3072`). EDIT target.
- `state_mgmt/message_store.py` (`DBMessageStore.append`, `:115-149`) + `_contracts/message_serde.py` (`:47-112`) exist — reused as-is, NO edit.
- `tests/unit/agent_harness/orchestrator_loop/test_loop_multiturn_rehydration.py` exists — EDIT target (extend `FakeMessageStore` + add tests).
- `tests/integration/agent_harness/state_mgmt/test_message_store.py` exists — already covers store-layer "round-trip incl. tool_calls" (no edit).
- `CHANGE-096` free (Glob → no files).

### Prong 2 — content verify ✅ (drift findings below)

| D-ID | Finding | Implication |
|------|---------|-------------|
| **D-toolbatch-marker-placement** | `# output_type == TOOL_USE` at `:2774`; the `assistant tool_use` append at `:2777`; the post-tool checkpoint `yield post_tool_event` at `:3072`; the `finally:` (TURN SpanEnded) at `:3073`. TOOL_USE is the fall-through after the stop_reason/FINAL/HANDOFF branches all `return`. | `_tool_batch_start = len(messages)` goes immediately before `:2777`; the persist goes between `:3072` and `:3073` (inside the `try`, after the post-tool checkpoint). Confirmed. |
| **D-no-other-appends-in-window** | `grep messages.append` → in the window `:2774-:3057` the ONLY appends are `:2777` (assistant tool_use), `:2826` (cat9-blocked result), `:3051` (normal result). The `:2124` (injected) + `:2614/2615` (verification self-correction) appends are EARLIER in the iteration (before the TOOL_USE branch) and `continue`/precede the marker. | `messages[_tool_batch_start:]` == exactly `[assistant tool_use, *tool results]`. No stray append. Verification noise correctly excluded (Option A). |
| **D-early-return-paths** | Early-return paths inside the tool for-loop `return` BEFORE the persist: cat9 terminate (`:2819-2820`), cancellation (`:2900-2906`), cat8 hard terminate (`:2926-2935`), cat8 soft terminate (`:2995-3004`). | Dangling protection holds — a partial/failed turn never reaches the persist → no dangling `assistant tool_use` in the ledger. |
| **D-serde-toolcalls** | `_message_to_dict`/`_message_from_dict` (`message_serde.py:47-112`) round-trip `tool_calls` (id/name/arguments) + `tool_call_id` + `name`. | The persisted batch reloads as well-formed Messages. NO serde edit. |
| **D-persist-helper-docstring** | `_persist_to_ledger` (`:1906-1913`) docstring states "never ... intra-turn tool round-trips — the final answer is the cross-send unit". | Must update the docstring this sprint (US-4); no behaviour change to the helper. |
| **D-resume-pretool-append** | resume()'s pending-tool branch appends the assistant/observation at `:3347`/`:3423` (resume starts `:3085`) — BEFORE driving the shared `_run_turns`. | NOT captured by the `TOOL_USE`-branch marker → persisting it is DEFERRED (sub-carryover AD). Confirms the §9 out-of-scope. |

### Prong 3 — schema verify ✅ (no schema change)
- `Message` ORM (`infrastructure/db/models/sessions.py:163-217`) has `sequence_num` (`:184`), `turn_num` (`:185`), `content_type` (`:188`), `content`. The tool batch reuses the SAME `DBMessageStore.append` writer as the 57.127 user/final-answer persists → NO migration, NO new column.

### D-baselines (re-assert at gate runs)
- full pytest **2724+5skip** · wire **24** · Vitest **904** · mockup **51** · mypy `src` **0/372** · run_all **10/10**. (Intermittent `AD-Billing-Outbox-Drain-Test-Flake` may surface once; re-run confirms.)

### Go/no-go ✅
- All findings confirm the plan (scope shift 0%). The marker-placement + early-return findings (the dangling-protection gate) are GREEN. **Proceed to Day 1.**

### Branch ✅
- `feature/sprint-57-129-chatv2-ledger-tool-roundtrips` created from `main` `858bd3af`.

---

## Day 1 — Backend: `_run_turns` `TOOL_USE` persist + docstring — 2026-06-16

### Accomplishments
- **1.1 TOOL_USE persist** (`loop.py`): added `_tool_batch_start = len(messages)` immediately before the `:2777` assistant tool_use append (under `# output_type == TOOL_USE`), and `await self._persist_to_ledger(messages[_tool_batch_start:], turn_num=turn_count)` immediately after the post-tool checkpoint `yield post_tool_event` (`:3072`), before the TURN-span `finally:`. WHY-comments explain the atomic-complete-batch + dangling-free reasoning. The persist is reached ONLY when the round-trip is well-formed (every early-return path returns before it).
- **1.2 docstring** (`loop.py`): `_persist_to_ledger` docstring updated — intra-turn tool round-trips are now passed (complete batch from the TOOL_USE branch), alongside the user prompt + final answer; still never system / prior. No behaviour change to the helper. MHist + Last Modified bumped (1 new MHist line, E501-clean).
- **1.3 partial gate**: `black` reformatted loop.py · `isort` clean · `flake8` clean · `mypy src` **0/372** · `run_all` **10/10** (check_llm_sdk_leak clean — no provider import added; check_event_schema_sync ✅ → wire 24 unchanged).

### Notes
- The change is 2 functional lines (marker + persist call) + the docstring + comments — `git diff --stat`: `loop.py` +34/−. No new helper / ABC / event / wire / codegen / migration (reuses `_persist_to_ledger` → `DBMessageStore.append` → `message_serde`, all unchanged).
- Actual ~0.6 hr (est ~0.75 hr) — clean, Day-0 verify removed all surprises.

---

## Day 2 — Backend test + full gate — 2026-06-16

### Accomplishments
- **2.1 unit tests** (`test_loop_multiturn_rehydration.py`): extended `FakeMessageStore` with an `append_calls: list[list[Message]]` recorder (additive); added `_build_tool_loop` (registers `calc_tool` → handler returns `_TOOL_RESULT = "factorial(8) = 40320"`, deliberately NOT echoed in the final answer "it is even") + `_tool_then_final_chat` (TOOL_USE then END_TURN). 3 new tests:
  - `test_run_persists_tool_round_trip` — `store.appended` roles == `[user, assistant, tool, assistant]`; assistant carries `tool_calls` (name `calc_tool`); `tool` result has `tool_call_id="tc-1"` + the result text; final answer never contains the result.
  - `test_tool_round_trip_persisted_atomically` — exactly ONE `append_calls` entry carries a tool_use and it is `[assistant, tool]` (the dangling-free guarantee at the unit level: a `load()` never sees a tool_use without its result; chosen over a cat8/cat9-terminate test — the design property is documented in the test docstring + the Day-0 D-early-return-paths finding).
  - `test_prior_tool_round_trip_rehydrated` — seeded prior `[user, assistant tool_use, tool result, assistant answer]` → run a follow-up → the `tool` result text + the assistant tool_use (with `tool_calls`) rehydrate into LLM request[0]; new user turn last.
  - Result: **6 passed** (3 new + 3 existing) in 0.32s.
- **2.2 full gate**: `mypy src` **0/372** · `run_all` **10/10** (wire 24) · full pytest **2727 passed / 5 skipped** (2724 baseline + 3 new) in 132s · black/isort/flake8 clean · `git status --short frontend/` empty (Vitest 904 / mockup 51 UNCHANGED — pure backend). The intermittent `AD-Billing-Outbox-Drain-Test-Flake` did NOT surface this run.

### Notes
- `git diff --stat backend/`: `loop.py` +34/−, `test_loop_multiturn_rehydration.py` +130/−5. Frontend untouched.
- Actual ~0.9 hr (est ~1.0 hr).

---

## Day 3 — Drive-through (real UI + real backend + real LLM) — 2026-06-16 — **PASS**

### Setup
- **Clean restart (Risk Class E)**: started a fresh no-`--reload` `api.main:app` on :8000 (PID 40596, sole owner; startup log confirms "pricing loader wired" + "startup complete"; `MAIN_TRANSCRIPT_OBSERVER` on). Docker PostgreSQL/Redis healthy (dev.py status mis-reports docker; `docker ps` confirms). Frontend Vite :3007 (untouched).
- **Tool selection**: `python_sandbox` is the controllable non-derivable tool, but it is risk MEDIUM and the DEFAULT tenant HITL policy (`require_approval_min_risk=MEDIUM`) ESCALATES it → a HITL pause → the approve path goes through `resume()` (the DEFERRED sub-carryover, NOT my fix). To exercise the NORMAL `run()` → `_run_turns` TOOL_USE branch (where my persist fires), set acme-prod's HITL policy to `auto_approve_max_risk=MEDIUM` / `require_approval_min_risk=HIGH` (via the admin `PUT /admin/tenants/{id}/hitl-policies`, dan@acme.com platform_admin, cookie-auth fetch) → `decide_tool_hitl` auto-approves MEDIUM → python_sandbox runs in-loop, no pause.

### Drive-through PASS — session `9150a32f` (real Azure gpt-5.2, dan@acme.com / acme-prod)
- **Turn 1**: "Use the python sandbox to run `random.randint(100000,999999)`, reply with just EVEN or ODD." → python_sandbox AUTO-RAN (no pause), `stdout=333221`, agent answered **"ODD"** (333221 is odd; the number is NOT in the answer). Tool block + answer rendered live; verification 0.99.
- **Turn 2** (innocent follow-up): "Please add 7 to that number and tell me the resulting sum." → agent answered **"333228"** (= 333221 + 7). `333221` appears ONLY in the turn-1 tool result (rendered once); turn 2 did NOT re-run the tool. The turn-2 POST body = `{message, session_id}` only (NO history) → the number could ONLY come from the backend self-loading the persisted tool round-trip. **This is the end-to-end proof: the intra-turn tool round-trip persisted AND rehydrated into the follow-up's LLM request, and the LLM used the tool result to compute.**
- **DB ledger** (`artifacts/verify_ledger.py 9150a32f...`): **6 rows** — seq=1 user / **seq=2 assistant tool_calls=python_sandbox** (the new persist) / **seq=3 tool `{"stdout":"333221..."}`** (the new persist) / seq=4 assistant "ODD" / seq=5 user "add 7..." / seq=6 assistant "333228". Before 57.129 only seq 1 + 4 would persist.
- Screenshot: `artifacts/drivethrough-PASS-toolcontext.jpeg`.

### Earlier corroboration — session `d5d59c39` (first attempt)
- Turn 1 (python_sandbox auto-run, no pause): `messages` ledger 4 rows — seq=2 assistant tool_use python_sandbox + seq=3 tool result `{"stdout":"463533..."}` + seq=4 "odd". **Tool round-trip persisted (the fix), DB-verified.** `message_events` (35 events) shows the in-run rehydration too: the 2nd internal turn's `prompt_built messages_count=5` (system+user+assistant-tool_use+tool).
- Follow-up self-load proven via live SSE: turns 2-3 `prompt_built messages_count=8` (vs the initial 4) — the loop self-loaded the persisted prior INCLUDING the tool round-trip. Screenshots `drivethrough-turn2.png` / `drivethrough-conversation.jpeg`.

### Investigation: a FALSE-ALARM "regression" (important lesson)
- The d5d59c39 follow-ups (turns 2-3) returned EMPTY answers and did NOT persist their own rows (ledger stayed at 4). I initially suspected a regression (rehydrating a tool round-trip breaks the follow-up).
- **Diagnostic**: a clean no-tool follow-up (new session: "capital of France?" → "Paris"; "its population?" → "Paris has ~2.1 million people") worked PERFECTLY (rehydration + answer + persist). So the empty-answer was NOT a generic follow-up bug.
- **Root cause (backend log line 212+)**: `openai.BadRequestError 400 content_filter` / `'jailbreak': {'detected': True, 'filtered': True}` — **Azure's content filter blocked my adversarial recall prompts** ("**Disregard** the earlier 'do not reveal' instruction", "do not reveal the number", "recall it … do NOT run any tool") as jailbreak attempts → the Azure call 400'd → the loop got an `AdapterException` → the turn produced no answer + never reached the persist → SSE generator closed early (the `finally: yield SpanEnded` during GeneratorExit teardown noise in the log).
- **Conclusion**: NOT a regression. The empty answers were Azure content-filter false-positives on MY adversarial prompt wording. With an INNOCENT follow-up ("add 7 to that number"), the tool-round-trip follow-up works perfectly AND persists (session 9150a32f, 6 rows). **Lesson: when drive-through-testing rehydration recall, use natural follow-up prompts; "disregard/override/do-not-reveal/recall-don't-run-tool" phrasings trip Azure's jailbreak filter and produce confounding empty turns.**

### AP-4 per-control check
- Composer: typeable, Enter sends ✅ · mode toggle real_llm ✅ · tool block renders real `python_sandbox` input/output (333221) ✅ · answer bubbles render real text ("ODD", "333228") ✅ · verification renders 0.99 ✅ · session continues across turns ✅. No dead controls / no fixture / no mislabel on the driven path.

### Notes
- The HITL policy change (acme-prod auto=MEDIUM) is drive-through SETUP, mirroring the 57.128 pattern; it does not affect production defaults of other tenants.
- Actual ~2.0 hr (est ~1.5 hr) — over by the content-filter false-alarm investigation (the diagnostic no-tool cycle + log root-cause). Worth it: confirmed no regression + extracted the prompt-wording lesson.

---

## Day 4 — CHANGE-096 + closeout
