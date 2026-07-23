# Sprint 57.167 Retrospective — de-Potemkin: honest MOCK surface + dead Filter control

**Date**: 2026-07-23 · **Branch**: `feature/sprint-57-167-de-potemkin-honest-surfaces` · **Base**: `main` `4b3bbcb1`

---

## Q1 — What shipped

Both Potemkins the reality audit named on 2026-06-26 — and found untouched on the 2026-07-15 re-scan — are closed:

1. **Mock honesty**: a startup `logger.warning` naming the 18 business tools as FABRICATED + the env var to switch, **and** a `"_mock": true` marker on every mock-sourced tool result, applied by a `functools.wraps` wrapper at the `register_all_business_tools` key-diff chokepoint, mode-gated so `service` wraps nothing.
2. **Dead control**: the chat-v2 SessionList Filter button is `disabled` with a localized tooltip instead of silently no-op'ing — the widget kept verbatim (the mockup itself defines no filter behaviour, so wiring one would breach 「自創 widget」 and deleting it would breach the widget-deletion ban).

Backend 2 files + FE 1 + 2 i18n + 3 test files. No migration, no wire event, no `agent_harness/` change. CHANGE-136; no design note (a correctness/honesty fix, not a spike).

## Q2 — Estimate accuracy / calibration

- Plan: bottom-up ~4.8 hr → class-calibrated commit **~4.1 hr** (NEW class `de-potemkin-honest-surface` **0.85**, `Agent-delegated: no` → `agent_factor` 1.0, 3-segment).
- Actual ≈ **5.0–5.2 hr** → ratio ≈ **1.22–1.27**, marginally **over** the [0.85, 1.20] band.
- **Where it went**: Day 0/1/2 landed essentially on estimate. The overshoot is entirely Day 3 — the drive-through found a real bug (below), which cost a fix + new tests + a backend restart + a re-drive (~+0.6 hr). That is the drive-through **working as designed**, not an estimation failure: the alternative was shipping a broken feature on a green gate.
- **Verdict**: **KEEP 0.85** as the class anchor (1st data point, edge-over). The 0.85 correctly priced the tiny-code + full-ceremony shape; what it does not price is "the mandatory drive-through finds something". If a 2nd `de-potemkin-*` also lands > 1.20 with the same cause, re-point to **1.0** rather than blaming estimation.

## Q3 — What went well / key lesson

- **The drive-through earned its mandate — again, and harder than usual.** 9/9 unit tests green, mypy clean, 12/12 lints, and the feature was **completely non-functional for every `*_list` tool**. `mock_incident_list` returns a bare JSON array; my wrapper skipped arrays — and I had written that skip as a *passing test* (`test_json_array_left_untouched`), so the suite actively **certified the bug**. Only opening the real UI and looking for the marker exposed it.
- **The generalizable lesson: a Day-0 probe that verifies the *call shape* is not the same as verifying the *value shape*.** I confirmed all 5 domains `return json.dumps(result)` and concluded "always a JSON string" — true but insufficient; I never checked what `result` itself was. One extra line in the probe (decode a sample and print `type(parsed)`) would have caught it before a single line of the wrapper was written.
- **Day-0 Prong 2 still paid twice**: it forced the in-JSON marking design (a prefix would have produced invalid JSON and broken 6+ existing `json.loads` assertions), and it surfaced `D-toolname-lies-in-service-mode` — the 18 tools are named `mock_*` in `service` mode too, i.e. in production the name would mislabel **real** data. That is a bug nobody had noticed, found by reading adjacent code rather than by the task itself.
- The chokepoint design held: one wrapper, 18 tools, zero per-domain edits, and a future `service` swap needs no un-marking.

## Q4 — What to improve next

- **Extend the Day-0 probe habit from signatures to values.** When a plan's design branches on a payload's *type*, decode a real sample at Day 0. Cheap; would have removed this sprint's entire overshoot.
- **Treat "a test that encodes the intended non-behaviour" as a smell.** `test_json_array_left_untouched` was written confidently and was wrong. When a test asserts that a feature *doesn't* apply somewhere, that is exactly the branch to check against reality before trusting it.
- The `_mock` marker lives in the tool-output block, so a user must open the Loop/Inspector panel to see it. Honest, but not maximally visible → `AD-BusinessMock-ChatV2-Badge` (user already declined this as beyond zero-cost; re-offer when a mock-mode UI surface is wanted).

## Q5 — Anti-pattern self-check

| AP | Verdict |
|----|---------|
| AP-2 Side-track | ✅ both changes sit on the 主流量 (lifespan + the registration path the chat handler uses + the chat-v2 sidebar) |
| AP-3 Cross-directory scatter | ✅ 2 backend files, 1 FE component, 2 i18n — the chokepoint design avoided 5 × `mock_executor.py` edits |
| **AP-4 Potemkin** | ✅ **this sprint exists to remove two of them** — and the drive-through prevented shipping a third (a marker that marked nothing for `*_list` tools) |
| AP-6 Speculative abstraction | ✅ one small helper + one wrapper; no new class / flag / config |
| AP-8 PromptBuilder bypass | N/A — no LLM call added |
| AP-11 Version suffix / misleading naming | ✅ none added. ⚠️ **found (pre-existing, out of scope)**: the 18 `mock_*` tool names are wrong in `service` mode → `AD-BusinessTool-Name-Says-Mock-In-Service-Mode` |

v2 lints **12/12**.

## Q6 — Carryover

- **NEW `AD-BusinessTool-Name-Says-Mock-In-Service-Mode`** — the 18 tool names are `mock_*` in **both** modes (18/18 verified); in production the name mislabels real data. A rename changes the LLM-visible tool contract → needs its own sprint + drive-through.
- **NEW `AD-BusinessMock-ChatV2-Badge`** — surface mock mode on the chat-v2 answer bubble (wire event + FE badge), so the marker does not require opening the Inspector.
- **NEW `AD-SessionList-Filter-Real-Implementation`** — real session filtering; blocked on a mockup spec (the mockup defines no filter UI).
- **NEW `AD-Day0-Probe-Value-Shape-Not-Just-Call-Shape`** — codify Q4's lesson into the Day-0 procedure (`docs/rules-on-demand/day0-plan-verify.md` Prong 2) if a 2nd sprint hits the same class of miss.

## Q7 — Gate summary

mypy `src` **400/0** · `run_all` **12/12** · backend pytest **3278 passed**, 6 skipped (**+13**) · Vitest **939** (**+2**) · mockup **51**, `styles.css` diff empty · `npm run lint && npm run build` clean (NO `--silent`) · black / isort / flake8 + LLM-SDK-leak clean · **drive-through PASS** (3 legs, after the array fix).
