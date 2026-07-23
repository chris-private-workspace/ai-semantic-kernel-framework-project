# CHANGE-136: de-Potemkin — honest MOCK surface + honest dead Filter control

**Date**: 2026-07-23
**Sprint**: 57.167
**Scope**: `business_domain` (aggregator) + `api/main` lifespan + chat-v2 frontend — backend + FE (NO migration / NO wire event / NO `agent_harness/` runtime change)

## Problem

The 2026-06-26 reality audit named **two core Potemkins**; the 2026-07-15 re-scan found both **原封不動** (`核心 Potemkin 2 → 2, 0 修`) after ~20 sprints.

1. **`business_domain_mode` defaults to `"mock"` and said so nowhere.** The 18 business tools (patrol / correlation / rootcause / audit / incident) answer from a fabricated HTTP backend. A `grep` for `[MOCK]` / `is_mock` / `mock_marker` across `business_domain/` + `agent_harness/` returned **0 hits** — nothing in the logs, the payloads, or the UI distinguished invented data from real. The audit ranked this the most trust-damaging gap because it silently invalidates the "the agent can reach company systems" claim.
2. **The chat-v2 SessionList Filter button was dead.** `SessionList.tsx:159-166` rendered a `.btn.ghost` with an icon and an `aria-label` and **no `onClick`** — clicking it did nothing, forever, on the 主流量.

Neither is a missing feature. Both are **honesty defects** — the AP-4 failure mode V2 exists to avoid.

## Root Cause

1. `business_domain_mode` is read once at registration (`_register_all.py:291`) and never surfaced. Each domain's `mock_executor.py` does a plain `httpx` call and returns `resp.json()` — no provenance travels with the payload. The startup lifespan had 5 `_wire_*()` helpers that each log their outcome, but nothing reported the business-domain mode.
2. The Filter button was a **faithful port of a mockup element that itself defines no behaviour** (`reference/design-mockups/page-chat.jsx:127` = `<Button variant="ghost" size="sm" icon="filter" />`). The port was correct; what was missing was declaring the resulting inertness.

## Solution

Scope chosen by user AskUserQuestion (2026-07-23): **`log + [MOCK] 標記`** and **`誠實禁用 + tooltip`**.

**1. Startup warning** (`api/main.py`) — new `_warn_business_domain_mock()` mirroring the 5 `_wire_*()` helpers (fail-open, one log line), called from the lifespan. `mock` → `logger.warning` naming the 5 domains as FABRICATED **and** the way out (`BUSINESS_DOMAIN_MODE=service`); `service` → `logger.info` positive confirmation, so a *broken* warning is never indistinguishable from production.

**2. Result marking at the registration chokepoint** (`business_domain/_register_all.py`) — `_mark_mock_result()` wraps handlers by **key-diff** (snapshot `set(handlers)` before the 5 `register_*_tools`, wrap only the delta) and **only when `mode == "mock"`**. Chosen over editing the 5 `mock_executor.py` because this is the one place that already knows `mode` and owns all 18 handlers; a future `service` swap then needs zero un-marking work.

Two load-bearing details:
- **`functools.wraps` is not cosmetic.** `ToolExecutorImpl` picks 1-arg vs 2-arg dispatch from `inspect.signature` (`executor.py:320`), which follows `__wrapped__`. A naked `async def w(*args)` would report 0 positional params and silently strip a context-taking handler's `ExecutionContext`.
- **Marking is inside the JSON, not a string prefix.** Day-0 found all 5 domains return `json.dumps(...)` and that integration tests `json.loads` the result at 6+ sites — `[MOCK] {...}` would be invalid JSON. `_marked_payload()` adds `"_mock": true` to a dict, and to **every dict element of a list**; scalars and non-JSON strings degrade (prefix / untouched) rather than corrupt.

**3. Honest Filter control** (`SessionList.tsx` + 2 i18n keys) — `disabled` + `title={t("chat.session.filterUnavailable")}`, markup / classes / icon otherwise verbatim. Disabled rather than wired because inventing a filter UI the mockup never specified would breach the mockup-fidelity 禁止項「自創 widget」; deleting the widget would breach the widget-deletion ban. Real filtering needs a mockup spec first → `AD-SessionList-Filter-Real-Implementation`.

## Verification

- **Gate**: mypy `src` **400/0** · `run_all` **12/12** · backend pytest **3278 passed**, 6 skipped (baseline 3271 → **+13**) · Vitest **939** (baseline 937 → **+2**) · mockup **51**, `styles.css` diff **empty** · `npm run lint && npm run build` clean (NO `--silent`) · black / isort / flake8 + LLM-SDK-leak clean.
- **New tests** — `test_mock_result_marking.py` (11): marker lands + payload stays valid JSON · every original key preserved · `service` mode wraps **nothing** · key-diff never touches a co-registered `echo_tool` (asserted by object **identity**) · **arity preserved through the REAL `ToolExecutorImpl`** (a 2-arg handler still receives its `ExecutionContext`) · 1-arg still dispatches · array-of-objects marks every element · array-of-scalars / non-JSON / dict shapes degrade sensibly. Plus `test_main_lifespan.py` (+2: mock warns and names the escape hatch; service confirms positively and does not warn) and `SessionList.test.tsx` (+2: disabled + localized tooltip; click moves no state).
- **Drive-through PASS** (real chat-v2 + real backend + real Azure `gpt-5.2`, default config, `mock_services` on :8001):
  - Leg 1 — the fresh startup log carries the WARNING verbatim.
  - Leg 2 — the chat-v2 ToolBlock output shows **10** `"_mock": true` (one per incident object) with every original field intact and the payload still `json.loads`-able.
  - Leg 3 — the Filter control is `disabled` with `title="Session filtering is not available yet"`, and after the locale toggle `title="工作階段篩選功能尚未提供"` / `aria-label="篩選"` — resolving live in **both** locales, not just in the JSON.
  - Screenshot: `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-167/artifacts/sprint-57-167-drivethrough-mock-marker.png`.

### ⚠️ The drive-through caught a real bug that all 9 green tests missed

Run 1 rendered **zero** markers. `mock_incident_list` returns a **bare JSON array**, and the first implementation deliberately skipped arrays — encoded as a *passing* test (`test_json_array_left_untouched`). The Day-0 probe had verified handlers return `json.dumps(result)` but never checked the type of `result`. So **every `*_list` / `*_query` tool would have shipped unmarked with a fully green gate.** Fixed by `_marked_payload()` marking each dict element of a list (array shape preserved); the misleading test was replaced by one that names the drive-through as its provenance.

## Impact

- Both audit-named Potemkins are closed. Behaviour changes **only** in `mock` mode (the default); `mode="service"` wraps nothing → byte-identical to pre-57.167, asserted by a test.
- Tool payloads stay valid JSON and keep every original field — existing `json.loads` consumers are unaffected.
- **Not done (deliberate)**: a chat-v2 DEMO badge on the answer bubble (AskUserQuestion option C, declined as beyond "zero-cost") → `AD-BusinessMock-ChatV2-Badge`. The marker is visible in the tool-output block, which needs the Loop/Inspector panel open.
- **New finding, out of scope**: the 18 tools are named `mock_*` in **`service` mode too** (Day-0 `D-toolname-lies-in-service-mode`, 18/18) — in production the *name* would mislabel real data. Renaming changes the LLM-visible tool contract, so it needs its own sprint → `AD-BusinessTool-Name-Says-Mock-In-Service-Mode`.
