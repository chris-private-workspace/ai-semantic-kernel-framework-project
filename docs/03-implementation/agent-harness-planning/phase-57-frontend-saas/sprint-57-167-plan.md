# Sprint 57.167 Plan — de-Potemkin: honest MOCK surface + dead Filter control

**Summary**: Clears the **two core Potemkins** the 2026-06-26 reality audit named and the 2026-07-15 re-scan found "原封不動" (0 fixed across a whole sprint cycle). (1) `business_domain_mode` defaults to `"mock"` with **no signal anywhere** — a human reading a business-tool answer in chat-v2 cannot tell fabricated data from real, the audit's "最危險的 mock-as-real". (2) The chat-v2 SessionList **Filter button has no `onClick`** — a dead control on the 主流量. Both fixes are deliberately small; the value is honesty, not capability. Scope decided by user AskUserQuestion 2026-07-23: mock gets **startup log + a `[MOCK]` marker on the tool results** (a log alone leaves the *user* blind — only ops would see it); Filter gets **honest-disable + tooltip** (the mockup itself defines no filter behaviour, so wiring a real filter would mean inventing UI the mockup never specified). **Drive-through MANDATORY** — both surfaces are user-facing. No design note (not a spike; a correctness/honesty fix). CHANGE-136.

**Status**: Approved-to-execute (user picked "先做零成本修復，兩個 Potemkin 一次清掉" 2026-07-23, then the 2 scope options via AskUserQuestion: `log + [MOCK] 標記` + `誠實禁用 + tooltip`)
**Branch**: `feature/sprint-57-167-de-potemkin-honest-surfaces`
**Base**: `main` HEAD `4b3bbcb1` (stale-open backlog audit, PR #396)
**Slice**: standalone de-Potemkin sprint — closes the 2 audit-named Potemkins; NOT part of the engine-debt 7-range program (it is the §9 停損 "insert a grounding / de-Potemkin sprint" move after 2 consecutive pure-engine sprints)
**Scope decisions**: (a) mark at the **`register_all_business_tools` chokepoint**, not in 5 × `mock_executor.py` — one wrapper covers all 18 tools; (b) the wrapper uses `functools.wraps` so the executor's `inspect.signature` **dual-arity** detection still sees the original handler's arity; (c) Filter = `disabled` + `title` tooltip, mockup markup otherwise untouched (no widget deletion — mockup-fidelity 禁止項); (d) NO new wire event / NO migration / NO chat-v2 DEMO badge (that was option C, explicitly declined as beyond "zero-cost").

---

## 0. Background

### The gap (the 2 core Potemkins — reality-audit 6-26 §5, re-scan 7-15 "2（原封不動）")

**Potemkin 1 — `business_domain_mode="mock"` is silent.**
The 18 business-domain tools (patrol / correlation / rootcause / audit / incident) default to an HTTP mock backend. Nothing — not a log line, not the tool output, not the UI — says so. A human who asks the agent about an incident gets a confident, well-formed answer built from fabricated data.

**Potemkin 2 — the SessionList Filter button is dead.**
`SessionList.tsx:159-166` renders a `.btn.ghost` with an icon and an `aria-label`, and **no `onClick`**. Clicking it does nothing, forever.

### Why it matters (the missing capability)

Neither is a missing *feature* — both are **honesty defects**, which is worse: they make the platform look more capable than it is, exactly the AP-4 failure mode V2 exists to avoid. The audit ranks mock-as-real as the single most trust-damaging gap because it silently invalidates the "agent can reach company systems" claim. And a dead control teaches the user their clicks are unreliable.

The 7-15 re-scan is the sharp datum: **both were named on 6-26 and neither was touched in the ~20 sprints since** — attention went to new engine capability instead.

### Root cause (recon code read, file:line; ALL re-verified §checklist 0.1)

| Layer | Reality (on `main` HEAD `4b3bbcb1`) | Anchor |
|-------|----------------------------------|--------|
| mock default | `business_domain_mode: Literal["mock","service"] = "mock"` — comment says "PoC default; backwards-compat" | `core/config/__init__.py:114` |
| mode read | resolved once at registration; nothing logs it | `business_domain/_register_all.py:291` |
| mock pathway | each domain has its own `mock_executor.py` doing plain `httpx` `_post`/`_get` → `resp.json()`; **no marker of any kind** | `business_domain/incident/mock_executor.py:30-40` |
| marker search | `grep "\[MOCK\]|is_mock|mock_marker"` over `business_domain/` + `agent_harness/` → **0 hits** | (grep, 2026-07-23) |
| startup wiring | lifespan already has 5 `_wire_*()` helpers each ending in `logger.info(...)` / `logger.warning(...)` — an established slot | `api/main.py:100-264` |
| Filter control | `<button className="btn ghost" data-size="sm" aria-label={t("chat.session.filter")}>` — **no `onClick`, no `disabled`** | `chat_v2/components/SessionList.tsx:159-166` |
| mockup source | `<Button variant="ghost" size="sm" icon="filter" />` — the **mockup itself defines no behaviour** | `reference/design-mockups/page-chat.jsx:127` |
| i18n | `chat.session` already has a `filter` key; no "unavailable" key | `i18n/locales/{en,zh-TW}/common.json` |

→ The fix must (1) make the mock mode announce itself **both to ops (startup) and to whoever reads the answer (the tool result)**, and (2) make the Filter control's inertness *declared* rather than silent — without deleting a mockup widget or inventing UI the mockup never specified.

### The design (backend: 1 lifespan warning + 1 chokepoint wrapper; frontend: 1 attribute + 1 tooltip + 2 i18n keys)

```
api/main.py
  + _warn_business_domain_mock()          # lifespan, mirrors the 5 _wire_* helpers
      mode == "mock" → logger.warning("api.main: BUSINESS DOMAIN IS MOCK ...")
      mode == "service" → logger.info(...)

business_domain/_register_all.py
  + _MOCK_PREFIX = "[MOCK] "
  + _mark_mock_result(handler)            # functools.wraps → arity preserved
        result = await handler(*args)
        str  → _MOCK_PREFIX + result
        dict → {**result, "_mock": True, <text-ish field prefixed>}
  register_all_business_tools(...):
      after the 5 register_*_tools calls, if mode == "mock":
          for name in <the 18 business tool names newly added>:
              handlers[name] = _mark_mock_result(handlers[name])

chat_v2/components/SessionList.tsx
  Filter <button>  += disabled + title={t("chat.session.filterUnavailable")}
```

**Why the chokepoint, not the 5 `mock_executor.py`**: the executors are 5 files × 2 methods = 10 edit sites and each returns raw `resp.json()` shapes that differ per domain; `register_all_business_tools` is the single place that already knows `mode` and owns all 18 handlers. It also means a future `mode="service"` swap needs **zero** un-marking work.

**Why `functools.wraps` is load-bearing**: `ToolExecutor._handler_takes_context` calls `inspect.signature(handler)` and counts positional params to decide 1-arg vs 2-arg dispatch (`executor.py:316-337`). A naked `async def w(*args)` wrapper would report 0 usable params → `takes_ctx=False` → context-taking handlers would be called with the wrong arity. `functools.wraps` sets `__wrapped__`, which `inspect.signature` follows by default → the original arity is preserved.

### Ground truth (recon head-start — code read on `main` HEAD `4b3bbcb1`; ALL re-verified §checklist 0.1)

- `agent_harness/tools/executor.py:106-109` — `ToolHandler` returns `str | dict[str, Any]`; **both** shapes must be handled by the wrapper.
- `agent_harness/tools/executor.py:316-337` — arity detection counts `POSITIONAL_OR_KEYWORD` / `POSITIONAL_ONLY`; result cached per tool name.
- `business_domain/_register_all.py:127-155` — `register_all_business_tools(registry, handlers, *, mock_url, mode, factory_provider)`; validates `mode`, then calls the 5 `register_*_tools`.
- `api/main.py:100-264` — the 5 `_wire_*()` helpers are the pattern to mirror (fail-open, one log line each).
- `chat_v2/components/SessionList.tsx:150-158` — the sibling "New session" button was itself an un-wired control fixed earlier (FIX-034 comment in-file) → the honest-surface precedent lives in this very component.

**Baselines (57.166 closeout, re-measured 2026-07-23)**: pytest **3271 collected** · Vitest **937** (150 files) · mockup **51** (`styles.css` diff empty) · mypy `src` **400** · run_all **12/12**. Re-verify Day-0.

### STALE / drift findings (Day-0 — EXECUTED 2026-07-23; full detail → progress.md Day-0 table)

- ✅ **D-wrapper-arity** — `executor.py:320` uses `inspect.signature` (follows `__wrapped__`); live proof confirms `functools.wraps` preserves 1-arg/2-arg. Design sound. (Bonus: all 18 handlers are 1-arg today → the 2-arg branch is future-proofing.)
- 🔴 **D-handler-returns-json-string** (was `D-handler-return-shape`) — all 5 domains return `json.dumps(...)`, never `dict`. **Forced the §3.2 design change** (mark inside the JSON, not by prefix).
- 🔴 **D-downstream-json-loads** — `test_business_tools_via_registry.py` `json.loads` the result at 6+ sites → a prefix would break them. Confirms the revision.
- ⚠️ **D-18-tool-names** — exactly 18 handlers added, but all already `mock_`-prefixed → the plan's "nothing says it's mock" premise is **partially wrong** (the name is an accidental signal, rendered by chat-v2's ToolBlock).
- 🔴 **D-toolname-lies-in-service-mode** (NEW) — the same 18 `mock_*` names appear in `mode="service"` (18/18) → the name is a **constant, not a mode signal**, and in production it mislabels REAL data as mock. Strengthens this sprint's mode-derived marker; the rename itself is **out of scope** (changes the LLM-visible tool contract) → §9 + NEW `AD-BusinessTool-Name-Says-Mock-In-Service-Mode`.
- ✅ **D-i18n-key-shape** — `chat.session` symmetric (8 keys) in both locales; safe to add `filterUnavailable`. Edit zh-TW via the Edit tool (shell mangles the UTF-8).
- ✅ **D-mock-tests-assert-exact** — 41 references across 8 files, all field-level not whole-string → compatible with the revised design.

**Go/no-go**: scope shift < 20% (same wrapper shape, different marking mechanism) → **proceed**.

## 1. Sprint Goal

Both audit-named Potemkins are gone: starting the backend in the default configuration **logs a loud MOCK warning**, every business-tool answer that came from the mock backend **carries a `[MOCK]` marker the agent and the human both see**, and the chat-v2 Filter control **declares itself unavailable instead of silently doing nothing**. Proven by gates (mypy `src` 400 · run_all 12/12 · pytest 3271+N · Vitest 937+N · mockup 51 byte-identical) **and a MANDATORY drive-through** on real chat-v2 + real backend + real Azure: a business-tool question renders a visibly `[MOCK]`-marked answer, and the Filter button shows the tooltip + does not respond to clicks. CHANGE-136; no design note.

## 2. User Stories

- **US-1** (mock honesty / ops): 作為維運者，我希望 backend 啟動時就明確告訴我 business domain 跑在 mock 模式，以便我不會把 demo 環境誤當生產環境。
- **US-2** (mock honesty / user): 作為使用 chat 的人，我希望 mock 來源的業務答案自帶 `[MOCK]` 標記，以便我一眼分得出哪些資料是捏造的。
- **US-3** (dead control): 作為使用 chat-v2 的人，我希望 Filter 按鈕誠實顯示「尚未提供」而不是點了沒反應，以便我不會誤以為介面壞掉。
- **US-4** (drive-through, MANDATORY): 作為審查者，我希望這兩項在真 UI + 真後端 + 真 LLM 上被實際走過一遍，以便它們不是又一個 gate-green 的 Potemkin。
- **US-5** (closeout): 作為下一個 session，我希望 CHANGE-136 + retrospective + calibration + navigators 都更新，以便交接不需重新考古。

## 3. Technical Specifications

### 3.0 Architecture (2 backend EDIT + 1 frontend EDIT + 2 i18n EDIT + 3 test files; NO migration / NO wire event / NO CSS / NO `agent_harness/` runtime change)

```
EDIT  backend/src/api/main.py                                  # + _warn_business_domain_mock() in lifespan
EDIT  backend/src/business_domain/_register_all.py             # + _MOCK_PREFIX + _mark_mock_result + apply in mock mode
EDIT  frontend/src/features/chat_v2/components/SessionList.tsx # Filter: + disabled + title
EDIT  frontend/src/i18n/locales/en/common.json                 # + chat.session.filterUnavailable
EDIT  frontend/src/i18n/locales/zh-TW/common.json              # + chat.session.filterUnavailable
NEW   backend/tests/unit/business_domain/test_mock_result_marking.py
EDIT  backend/tests/unit/api/test_main_lifespan.py             # + mock-warning test
EDIT  frontend/tests/unit/chat_v2/components/SessionList.test.tsx
UNTOUCHED  business_domain/*/mock_executor.py (5)              # chokepoint design — no per-domain edits
UNTOUCHED  agent_harness/**                                     # no runtime change; Cat 2 contract unchanged
UNTOUCHED  frontend/src/styles-mockup.css                       # no CSS change → mockup diff stays empty
```

### 3.1 Startup MOCK warning (US-1) — `api/main.py`

- New `_warn_business_domain_mock()` mirroring the 5 existing `_wire_*()` helpers (same shape, same fail-open `try/except`, one log line).
- `mode == "mock"` → `logger.warning` naming it explicitly as fabricated data + how to switch (`BUSINESS_DOMAIN_MODE=service`).
- `mode == "service"` → `logger.info` (so the log positively confirms production mode too — silence must not be ambiguous).
- Called from the lifespan alongside the other wire helpers.

### 3.2 `[MOCK]` result marking (US-2) — `business_domain/_register_all.py`

> **REVISED at Day-0** (audit trail — the drafted design is struck below, not deleted). `D-handler-returns-json-string` + `D-downstream-json-loads` proved all 5 domains return **`json.dumps(...)`** and that 6+ existing integration assertions `json.loads` the result. ~~A `[MOCK] ` string prefix~~ would yield `[MOCK] {"id":…}` = **invalid JSON** and break them. Marking now happens **inside** the JSON.

- `_MOCK_PREFIX = "[MOCK] "` module constant (retained for the non-JSON fallback only).
- `_mark_mock_result(handler)` — `functools.wraps`-decorated passthrough (`*args`) that awaits the original and marks the result:
  - **`str` that parses as a JSON object** (the real path, all 18) → `json.loads` → add `"_mock": true` → `json.dumps` → **still valid JSON**, marker visible to the LLM and to the human in chat-v2's ToolBlock output.
  - `str` that is NOT JSON → `_MOCK_PREFIX + result` (defensive fallback).
  - `dict` → additive `{"_mock": True}`; never drops or reshapes existing keys.
  - anything else (incl. a JSON array / scalar) → returned untouched (defensive; no crash, no shape change).
- Applied in `register_all_business_tools` **only when `mode == "mock"`**, and **only to the tool names the 5 `register_*_tools` calls added** (diff the `handlers` keys before/after → marks exactly the 18, never echo / sandbox / memory / todos).
- `mode == "service"` → zero wrapping → byte-identical to today.

### 3.3 Honest Filter control (US-3) — `SessionList.tsx` + i18n

- Filter `<button>` gains `disabled` + `title={t("chat.session.filterUnavailable")}`; markup, classes and icon otherwise **verbatim** (mockup-fidelity: widget kept, not deleted, not restyled).
- New i18n key `chat.session.filterUnavailable` in **both** `en` and `zh-TW` (symmetric keys — cf. candidate #30).
- An in-file comment records *why* it is disabled rather than wired (the mockup defines no filter behaviour), mirroring the FIX-034 "Honest-surface" comment already in this component.

### 3.x What is explicitly NOT done

- **No chat-v2 DEMO badge / wire event** — that was AskUserQuestion option C, declined as beyond "zero-cost". If wanted later: `AD-BusinessMock-ChatV2-Badge`.
- **No real session filtering** — the mockup specifies no filter UI; inventing a popover would violate the mockup-fidelity 禁止項「自創 i18n copy / widget」. Tracked as `AD-SessionList-Filter-Real-Implementation` (needs a mockup spec first).
- **No flip of `business_domain_mode` to `"service"`** — that is a real migration with DB-backed services behind it, not an honesty fix.
- **No touching the 5 `mock_executor.py`** — chokepoint design (§Scope decisions a).

### 3.y Validation (US-1..US-4)

Gates: mypy `src` 400 · run_all 12/12 · pytest 3271+N · Vitest 937+N · mockup 51 (`diff` empty) · `npm run lint && npm run build` (NO `--silent`) · black/isort/flake8 clean · LLM-SDK-leak clean. Plus the §3.z drive-through (MANDATORY — both surfaces are user-facing).

### 3.z Drive-through (US-4, MANDATORY)

Real chat-v2 + real backend + real Azure `gpt-5.2`, default config (`BUSINESS_DOMAIN_MODE` unset → `mock`):
1. Backend startup log shows the **MOCK warning** (capture the line).
2. Ask the agent a business question that routes to a business tool (e.g. an incident lookup) → the rendered answer / tool output visibly carries **`[MOCK]`**.
3. The SessionList **Filter** button shows the tooltip on hover and does **not** respond to a click (no state change, no console error).
4. Screenshot + observed-vs-intended → progress.md Day 3.

## 4. File Change List

| # | File | Action |
|---|------|--------|
| 1 | `backend/src/api/main.py` | EDIT |
| 2 | `backend/src/business_domain/_register_all.py` | EDIT |
| 3 | `frontend/src/features/chat_v2/components/SessionList.tsx` | EDIT |
| 4 | `frontend/src/i18n/locales/en/common.json` | EDIT |
| 5 | `frontend/src/i18n/locales/zh-TW/common.json` | EDIT |
| 6 | `backend/tests/unit/business_domain/test_mock_result_marking.py` | NEW |
| 7 | `backend/tests/unit/api/test_main_lifespan.py` | EDIT |
| 8 | `frontend/tests/unit/chat_v2/components/SessionList.test.tsx` | EDIT |
| 9 | `claudedocs/4-changes/feature-changes/CHANGE-136-de-potemkin-honest-surfaces.md` | NEW |
| — | `backend/src/business_domain/*/mock_executor.py` (5) | **UNTOUCHED** |
| — | `backend/src/agent_harness/**` | **UNTOUCHED** |
| — | `frontend/src/styles-mockup.css` | **UNTOUCHED** |

## 5. Acceptance Criteria

1. Backend startup in default config emits a `logger.warning` naming business domain as MOCK + the env var to switch; `service` mode emits a positive `logger.info`.
2. Every one of the 18 business tools, in `mode="mock"`, returns a result carrying the `[MOCK]` marker; `mode="service"` returns byte-identical results to today (no wrapper applied).
3. The wrapper preserves handler arity — a 2-arg (context-taking) business handler is still dispatched with its `ExecutionContext` (asserted by a test that drives the REAL `ToolExecutor`, not just the wrapper in isolation).
4. Non-business tools (echo / python_sandbox / memory / write_todos) are **never** marked.
5. The chat-v2 Filter control is `disabled` with a localized tooltip in both `en` and `zh-TW`; the mockup widget markup/classes are otherwise unchanged and `styles-mockup.css` `diff` stays empty.
6. **Drive-through PASS (MANDATORY, real UI + backend + LLM)** — startup MOCK warning captured; a business-tool answer visibly `[MOCK]`-marked in chat-v2; Filter shows tooltip + does not respond to click; screenshot + observed-vs-intended in progress.md. (NOT gate-only.)
7. Both audit Potemkins marked resolved in `5-status/v2-reality-audit-engine-vs-grounding-20260715.md` §5 tracking + `next-phase-candidates.md`; CHANGE-136; calibration recorded; navigators updated.

## 6. Deliverables

- [ ] US-1 startup MOCK warning + lifespan test
- [ ] US-2 `[MOCK]` marking at the registration chokepoint + tests (18 marked / non-business untouched / arity preserved / service mode unchanged)
- [ ] US-3 honest Filter control + 2 i18n keys + Vitest
- [ ] US-4 drive-through PASS (3 legs) + screenshot + observed-vs-intended
- [ ] US-5 CHANGE-136 + retrospective + calibration + navigators + audit-doc Potemkin tracking

## 7. Workload Calibration

- Scope class **NEW `de-potemkin-honest-surface` 0.85** — anchored to the **validated** `chatv2-inspector-existing-field-surface` **0.85** (3 pts, mean ~0.87; its own note: *"a tiny-code + full-ceremony parent-direct sprint sits ~0.85, NOT 0.45-0.55"*), which is exactly this sprint's shape: very little code, full ceremony (plan + checklist + Day-0 + tests + MANDATORY drive-through + closeout), parent-direct. Read + cited from `docs/03-implementation/agent-harness-execution/calibration-matrix.md`. 1st data point.
- **Agent-delegated: no** (parent-direct — small surgical edits across 2 categories + a load-bearing arity subtlety; not mechanical enough to delegate). `agent_factor` 1.0 → 3-segment form.
- Bottom-up est ~4.8 hr (US-1 ~0.4 · US-2 ~1.2 · US-3 ~0.5 · US-4 drive-through ~1.2 · Day-0 + closeout ~1.5) → class-calibrated commit **~4.1 hr** (mult 0.85). Day-4 retro Q2 verifies.

## 8. Dependencies & Risks

| Risk | Mitigation |
|------|------------|
| Wrapper breaks the executor's dual-arity dispatch | `functools.wraps` (sets `__wrapped__`, which `inspect.signature` follows); **D-wrapper-arity** re-verifies the detection mechanism at Day-0; AC-3 asserts it through the REAL `ToolExecutor` |
| `[MOCK] ` prefix breaks existing exact-equality test assertions | **D-mock-tests-assert-exact** greps for them at Day-0; the prefix only applies in `mode="mock"`, so `service`-mode tests are unaffected by construction |
| Marking sweeps in non-business tools registered into the same `handlers` dict | Mark by **key-diff** (before/after the 5 `register_*_tools` calls), not by iterating the whole dict; AC-4 asserts echo/sandbox/memory/todos stay unmarked |
| ~~dict-returning handlers have no obvious text field~~ → **RESOLVED at Day-0**: all 18 return JSON strings; marker is an in-JSON `"_mock": true` key | Day-0 `D-handler-returns-json-string`; §3.2 revised. Residual risk: the key is less eye-catching than a prefix → the drive-through Leg 2 must confirm it is actually *visible* in the chat-v2 ToolBlock output, not merely present in the payload |
| The 18 tool names say `mock_` in BOTH modes (Day-0 `D-toolname-lies-in-service-mode`) → in production the name mislabels real data | Out of scope (renaming changes the LLM-visible tool contract + needs its own drive-through) → NEW `AD-BusinessTool-Name-Says-Mock-In-Service-Mode`. This sprint's marker is **mode-derived**, so it is correct in both modes regardless of the name |
| Stale `--reload` backend hides the startup warning (Risk Class E) | Clean restart, no `--reload`, verify sole live `python.exe` via `Win32_Process`, capture the startup line from the fresh log |
| Drive-through can't reach a business tool from the default persona | 57.166 lever precedent: if the agent won't call one, prompt explicitly by tool name; if still unreachable, record the leg **inconclusive** (NOT a pass) and mark the [MOCK] leg gate-only, per AD-Drive-Through-Acceptance |

## 9. Out of Scope (this sprint; → separate slices / ADs)

- chat-v2 DEMO badge / wire event for mock mode → NEW `AD-BusinessMock-ChatV2-Badge`
- Real session filtering UI → NEW `AD-SessionList-Filter-Real-Implementation` (blocked on a mockup spec)
- Flipping `business_domain_mode` default to `"service"` → the real Phase-2 grounding work (pillar 4)
- **Renaming the 18 `mock_*` tools** (Day-0 `D-toolname-lies-in-service-mode`: the names say mock in `service` mode too) → NEW `AD-BusinessTool-Name-Says-Mock-In-Service-Mode`. Deliberately deferred: the tool name is part of the LLM-visible contract, so a rename changes prompt content + agent behaviour and needs its own drive-through — not a "zero-cost" edit.
- The other grounding pillars (knowledge connector External-Sources / DocTypes) → still the audit §9 首選 next move after this sprint
