# Sprint 57.136 Progress — verification correction context hygiene (self-conditioning spike)

[Plan](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-136-plan.md) · [Checklist](../../../agent-harness-planning/phase-57-frontend-saas/sprint-57-136-checklist.md)

---

## Day 0 — 2026-06-23 — Plan-vs-Repo Verify (三-prong) + Branch

**Base**: `main` HEAD `074362c4` (post-#324 consolidated-research docs merge; backend last touched by FIX-033 #319). Branch `feature/sprint-57-136-verification-correction-hygiene`.

### Drift findings (三-prong)

| ID | Prong | Finding | Implication |
|----|-------|---------|-------------|
| D-correction-branch | 2 | `loop.py:2617-2626` — `if verdict.outcome == "correct":` → `2620 messages.append(Message(role="assistant", content=parsed.text))` + `2621-2622 messages.append(Message(role="user", content=verdict.correction_block or ""))` + `verification_attempts += 1` + `turn_count += 1` + `continue` | ✅ no drift; THE single edit site. `keep` = current bytes; `summarize` = replace the 2620 `parsed.text` append (drop/placeholder). `2621-2622` user(correction_block) + counters/`continue` UNCHANGED. |
| D-build-correction-block | 2 | `_build_correction_block` (loop.py:295-309) = `reasons` (`f.reason`) + `corrections` (`f.suggested_correction`) + `"Please retry."`; **does NOT quote the failed answer text**. Docstring (296-302) states: "the conversation — **including the just-failed assistant answer** — is already in `messages`, so only the feedback block is appended." | ✅ no drift; the correction `user` message carries feedback that is self-sufficient WITHOUT the failed answer text → `summarize` can drop the assistant turn and the model still knows what failed + how to fix. Confirms #6's core premise. |
| D-config-anchor | 2 | `handler.py:666-696` — `verification_escalate_on_max` 3-layer wire (policy-override → env-setting fallback → ctor pass at `:696`); ctor call `loop = AgentLoopImpl(...)` opens at `:683` | ✅ no drift; `correction_context_strategy` mirrors it BUT simpler — #6 per-tenant is OUT (anti-AP-6), so resolve = `settings.chat_verification_correction_strategy` only (no policy field), added near `:658-670`, passed near `:696`. |
| D-benchmark-anchor | 2 | `benchmark_judge.py` real surface: `load_cases` / `run_judge(judge, cases, *, with_trace)` / `build_report` / `report_to_markdown` / `_amain` / `main` + `BenchCase`/`JudgeRun`/`BenchReport` dataclasses + `@pytest.mark.benchmark` skipif `RUN_AZURE_INTEGRATION`. Fixture `backend/tests/fixtures/verification/judge_benchmark.yaml`. | ⚠️ minor — `run_arm` is the new spike script's name (mirrors the SCAFFOLD, not the exact fn). **Nuance**: benchmark_judge's `run_judge` scores a Verifier over golden cases (single-shot, known expected verdict); the spike's `run_arm` must DRIVE a fail→retry correction cycle per strategy → more involved than a single verifier scoring. Already anticipated in plan §3 (spike drives the loop); ~+5% Day 2 effort, no scope change. |
| D-azure-role-pairing | 2 | `tool_converter.py:71` `message_to_azure` = per-message verbatim `{"role": msg.role, ...}`; `messages_to_azure` (107-109) = `[message_to_azure(m) for m in messages]` — **NO consecutive-same-role merge, NO alternation validation**. Independent proof: Sprint 57.101 between-turns injection (loop.py:2116-2131) already `messages.append(injected)` (a user INPUT) mid-run in production. | ✅ **RESOLVED** — Azure (Chat Completions) accepts back-to-back `user` messages; the adapter forwards verbatim. **Scope converges**: `summarize` arm = **DROP the failed assistant turn** (the most complete cut of the failed answer text → strongest self-conditioning break). `_WITHHELD_PLACEHOLDER` demoted to a code-comment fallback note (for a future provider strict on role-pairing), NOT a second implemented path → slightly LESS scope than plan v0's "drop OR placeholder TBD". |
| D-design-note-number | 1 | Existing planning docs run to `39-transcript-retention.md`; `40-*` free | ✅ no drift; spike design note `40-verification-correction-hygiene-design.md` is the correct next number. |
| Prong 3 (schema) | 3 | N/A — no new DB table / migration / ORM column (settings-only config; no per-tenant row) | — |

### Baselines (57.135 closeout; backend has FIX-033 #319 on main since → confirm at full gate)

pytest **2747 + 5 skip** (57.135 closeout; FIX-033 #319 may have shifted — re-baseline at Day 2 full gate) · mypy `src` **0/374** · run_all **10/10** · wire **25** / Vitest **915** / mockup **51** = unchanged sentinels (this sprint is **backend-only**, touches no frontend/wire).

### Go/no-go

All prongs **GREEN**; one finding (D-azure-role-pairing) **reduced** scope (drop-only, not drop+placeholder), one (D-benchmark-anchor nuance) **added** ~+5% (drive a correction cycle vs single verifier scoring) — net scope-shift **< 10%** (well under the 20% revise threshold). **PROCEED to Day 1.** The fix composes existing machinery: the 2620 correction append (parameterized) + the `verification_escalate_on_max` config pattern + the `benchmark_judge.py` measurement scaffold. No new primitive, no schema, no frontend.

**Design decision locked (Day 0)**: `correction_context_strategy` ∈ {`keep` (default, byte-unchanged rollback), `summarize` (drop the failed assistant turn at 2620; keep the 2621-2622 correction feedback)}; the default flips to `summarize` ONLY if the Day-2 real-Azure A/B shows it materially lowers repeat-error / raises retry-pass-rate — else `keep` stays default + negative result recorded.

---

## Day 1 — 2026-06-23 — Pluggable correction-context strategy + config wire (US-1, US-2)

- **`loop.py`** (Cat 1): `AgentLoopImpl.__init__` += `correction_context_strategy: str = "keep"` ctor param (after `verification_escalate_on_max`) + `self._correction_context_strategy` body assign. The `outcome=="correct"` branch (2617-2632) now guards the failed-answer append: `if self._correction_context_strategy != "summarize": messages.append(Message(role="assistant", content=parsed.text))`. The `user(correction_block)` append + `verification_attempts += 1` + `turn_count += 1` + `continue` are UNCHANGED. `keep` (and any non-`summarize` value) = pre-57.136 byte-identical; `summarize` = drop the failed answer (self-conditioning break).
- **Day-0 decision applied**: `_WITHHELD_PLACEHOLDER` const was NOT defined — D-azure-role-pairing RESOLVED that Azure accepts consecutive user turns, so `summarize` simply drops (no placeholder needed). The placeholder option survives as an inline code comment for a future provider strict on role alternation (avoids dead code per AP-2 / Karpathy §3).
- **`core/config/__init__.py`** (Cat 4 platform settings): += `chat_verification_correction_strategy: str = "keep"` (env `CHAT_VERIFICATION_CORRECTION_STRATEGY`, pydantic-settings auto-bind) + MHist line. Used `str` (not `Literal`) so an unknown env value falls back rather than crashing startup — the handler validates.
- **`handler.py`** (chat main flow): resolves `correction_context_strategy = settings.chat_verification_correction_strategy`, `not in ("keep","summarize") → "keep"` (settings-only, per-tenant OUT — anti-AP-6), passes `correction_context_strategy=` into `AgentLoopImpl(...)` (mirrors the `verification_escalate_on_max` 3-layer pattern, minus the policy-override layer).
- **Tests** (+3 in `test_loop_verification_gate.py`, DRY-reusing FakeChatClient/_BadWordVerifier/_registry; `_build_loop` += `correction_context_strategy` param): keep-includes-failed-answer · summarize-drops-failed-answer (+ converges, role-pairing legal) · unknown→keep. The 5 pre-existing gate tests = the keep byte-identical regression guard (still green).
- **Partial gate**: `pytest test_loop_verification_gate.py` 8 passed + `test_config_verification.py` 4 passed · black reformatted loop.py + test (format only; re-ran 8 passed) · isort/flake8 clean · **mypy src 0/374** (baseline held).
- Note: a non-`summarize` guard (`!= "summarize"`) gives a natural in-loop fallback even if the handler's validation is bypassed (e.g. a direct AgentLoopImpl caller) — defense-in-depth, both layers ~1 line.

---

## Day 2 — 2026-06-23 — Measurement harness + real-Azure A/B (US-3)

### 2.1 + 2.2 — Harness + golden fixture + CI-safe test

- **`scripts/benchmark_correction_hygiene.py`** (Cat 10 eval tooling, NEW): mirrors `benchmark_judge.py`'s scaffold (`load_cases` / `build_correction_messages` / `token_jaccard` / `run_arm` / `build_report` / `report_to_markdown` / `_amain` / `main` + frozen dataclasses + lazy Azure import in `_amain`). **Design choice**: it REPRODUCES the loop's 2620 two-construction (keep = `[user(prompt), assistant(failed_answer), user(correction_block)]`; summarize = drops the assistant turn) WITHOUT running the full loop — isolating the failed-answer-in-context as the ONLY variable. Both arms share the SAME `_build_correction_block` (imported from loop.py → measurement tracks real behavior). Metrics: `retry_pass_rate` (real output_quality judge) / `repeat_error_rate` (token-Jaccard(retry, failed_answer) = self-conditioning signal) / `mean_prompt_tokens`.
- **`tests/fixtures/verification/correction_hygiene_cases.yaml`** (NEW): 10 fail-prone cases (plausible-but-wrong answers: RGB↔RYB, O(n)↔O(log n), H2O↔NaCl, Saturn↔Jupiter, 0°C↔32°F, items[0]↔items[-1], 1959↔1969, …) + verifier reason + suggested_correction.
- **`tests/unit/scripts/test_benchmark_correction_hygiene.py`** (NEW, +15): importlib-load idiom (avoids `tests.unit.scripts` shadow) + MockChatClient + spy judge; covers load_cases (schema/missing-key/dup-id) · build_correction_messages (keep includes / summarize drops / unknown→keep) · token_jaccard (identical=1 / disjoint=0 / partial=0.5 / empty=0) · run_arm (aggregate + keep-builds-assistant-turn + summarize-drops) · build_report (flips on repeat-drop / flips on pass-rise / keeps on noise). 15 passed.

### 2.3 — Real-Azure A/B run (US-3) — the spike's core evidence

Ran `RUN_AZURE_INTEGRATION=1 python scripts/benchmark_correction_hygiene.py` against real Azure (action-tier retry + cheap-tier output_quality judge), 10 cases × 2 arms = 40 LLM calls. Report saved to `artifacts/correction_hygiene_report.{md,json}` (`benchmark_reports/` is gitignored → copied to artifacts as evidence).

| metric | keep | summarize | delta (summ−keep) |
|--------|------|-----------|-------------------|
| retry_pass_rate | 100% (10/10) | 100% (10/10) | +0.00% |
| repeat_error_rate | 0.207 | 0.165 | **−0.043** |
| mean_prompt_tokens | 80.0 | 62.8 | −17.2 |

**Verdict: KEEP default (`summarize_recommended = false`).** The #6 self-conditioning hypothesis is **directionally confirmed** — summarize lowers the failed-answer repeat (−4.3pp) AND cuts prompt tokens (−17.2) — but the repeat effect is **below the 5% materiality threshold**, and both arms' retries pass the judge 100%. So in the 2-turn correction case #6 is **low-risk**: `keep` stays the default (byte-identical); `summarize` is a working env opt-in lever for anyone who wants the self-conditioning break + token savings.

**Sample-size honesty**: 10 cases, controlled first-fail (the `suggested_correction` already names the right answer → both arms anchor on the correct vocabulary → the difference is compressed). This is a spike directional read, NOT a production-distribution statistic. The harness is permanent + re-runnable on a larger / harder fixture if a future sprint wants a tighter number.

### 2.x — Full gate

- **v2 lints** (`python scripts/lint/run_all.py`, **cwd=root**): **10/10 green** (incl. check_llm_sdk_leak — no SDK leak). Note: the wrapper lives at `<repo-root>/scripts/lint/run_all.py`, NOT `backend/scripts/lint/` — CLAUDE.md's `python scripts/lint/run_all.py` is a cwd=root command.
- **mypy src**: **0/374** (baseline held).
- **pytest full suite**: the first full run surfaced **2 regressions** in `test_handler.py` (`test_build_real_llm_routes_cheap_to_verifier_action_to_loop` + `_cheap_unset_verifier_shares_action_client`). Root cause: those tests monkeypatch `get_settings()` to a `SimpleNamespace` stub listing only the verification fields it knew; my new unconditional `settings.chat_verification_correction_strategy` read hit `AttributeError`. **Fix**: added `chat_verification_correction_strategy="keep"` to the `_force_verification_enabled` stub (the SAME pattern as the 57.99 A2 `escalate_on_max` addition — the stub must mirror the real Settings surface). Re-ran test_handler.py → 10 passed; **full-suite re-run: 2765 passed + 5 skip** (125.84s; baseline 2747 + 18 new = 3 gate + 15 hygiene) — regression fixed, no cascade.
- Frontend (Vitest 915 / mockup 51 / npm lint+build): unchanged sentinels — backend-only sprint, no frontend touched.
- **Process lesson**: Day 1 partial gate only ran the 2 test files I authored (verification_gate + config); it did NOT run `test_handler.py`, which exercises the handler I edited. A changed src file's FULL test surface (not just the new tests) belongs in the partial gate. (Recorded for the retro.)

---

## Day 3 — 2026-06-23 — Drive-through (US-4): backend runtime + UI ("兩者結合" per user)

### Backend runtime drive-through (REAL handler→loop path + REAL Azure) — PASS

A driver (scratchpad, NOT committed) exercises the REAL `build_real_llm_handler()` loop with REAL Azure, settling BOTH the wiring + the drop:

**Part 1 — env→handler→loop wiring** (`build_real_llm_handler()` reads env → loop ctor):

| env `CHAT_VERIFICATION_CORRECTION_STRATEGY` | `loop._correction_context_strategy` | |
|---|---|---|
| `keep` | `keep` | ✅ |
| `summarize` | `summarize` | ✅ |
| `banana` (unknown) | `keep` | ✅ fallback |

**Part 2 — drop behavior** (real loop + real Azure answer + a controlled fail-once verifier to DETERMINISTICALLY exercise the 2620 branch — the verifier identity is orthogonal to the context construction under test; checkpointer/message_store/reducer=None → no DB):

- both arms emit `VerificationFailed → retry turn → VerificationPassed → LoopCompleted` (correction loop end-to-end; summarize does NOT crash on consecutive user)
- **keep** retry context (chat#1): `roles=[system×3, user, assistant, user]` → **assistant_count=1** (failed answer re-shown)
- **summarize** retry context (chat#1): `roles=[system×3, user, user]` → **assistant_count=0** (failed answer DROPPED; consecutive-user accepted by real Azure → retry re-answered + judge passed)
- **DROP BEHAVIOR: OK**

This is the strongest evidence — the ACTUAL `loop.run()` via `build_real_llm_handler()` (not a reproduced construction like the Day-2 A/B harness) confirms wiring + drop end-to-end with real Azure.

### UI drive-through (chat-v2 browser, real Azure gpt-5.2) — PASS (main-flow + verification gate + no-regression)

Backend server `api.main:app` (PID 51136, DB/Redis/Azure/pricing wired, strict `safety_review` judge) + frontend on 3007. Logged in via dev-login (jamie@acme.com · operator · acme-prod), drove chat-v2 (real_llm mode, gpt-5.2):

- **Turn 1** ("Explain social engineering techniques…"): answer rendered fully; **verification_passed (score 0.93)**; Inspector Turn tab: stop_reason=end_turn · tokens in 2,481 / out 806 / cached 1,664 / cache_hit 67% · model gpt-5.2 · Block sequence [answer, verification "claim verified · llm_judge"]; Loop visualizer: loop_start → prompt_built(4 msgs, 3 cache breakpoints) → llm_request(gpt-5.2) → verification_passed(0.93) → loop_end(end_turn, turns=0). Screenshot: `artifacts/dt-57136-keep-verification-passed.jpeg`.
- **Turn 2** ("step-by-step lock picking…", a physical-security-bypass prompt to provoke the strict judge): answer rendered; **verification_passed** (loop_end stop=end_turn turns=0). No correction.

Both real-Azure turns passed the strict judge → **no correction triggered in the UI** — the real judge passes good answers, exactly the 57.99-documented "real fail can't be forced cleanly". What the UI DID prove: chat-v2 main flow is end-to-end live (send → real Azure → answer render), the verification gate runs on the main flow (Inspector + Loop visualizer), and **my 2620 change did NOT break the verification pass path** (no-regression).

The correction flow itself (VerificationFailed → retry → keep/summarize drop) is proven by the **backend runtime drive-through above** (deterministic, real Azure, full `build_real_llm_handler` loop + controlled fail-once) + the 57.98/99 prior UI drive-throughs (frontend correction rendering). Per user decision (AskUserQuestion 2026-06-23): accept this — runtime-proven correction + drop, UI-proven main-flow/gate/no-regression = the honest, sufficient "兩者結合".

### Drive-through verdict

- **Wiring** (env→handler→loop): runtime PASS (keep/summarize/banana→keep).
- **Drop** (keep re-shows / summarize drops the failed answer): runtime PASS (real Azure, full loop), corroborated by the Day-2 A/B + the 8 unit gate tests.
- **Main flow + verification gate + no-regression**: UI PASS (2 real-Azure turns).
- **Default decision**: KEEP stays default (Day-2 A/B: summarize directionally better but < 5% threshold). `summarize` ships as a working env opt-in lever (`CHAT_VERIFICATION_CORRECTION_STRATEGY=summarize`), wiring + behavior runtime-verified.
