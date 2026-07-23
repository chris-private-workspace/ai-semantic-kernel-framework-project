# Sprint 57.167 Progress — de-Potemkin: honest MOCK surface + dead Filter control

## Day 0 — 2026-07-23 — Plan-vs-Repo Verify (三-prong)

### Baselines (measured on `main` HEAD `4b3bbcb1`)
- pytest: **3271 collected**
- Vitest: **937 passed** (150 files)
- mockup: **51** hex baseline · `diff reference/design-mockups/styles.css frontend/src/styles-mockup.css` **empty**
- mypy `src`: **400**
- run_all: **12/12 green**

### Prong 1 — path verify
All 7 EDIT targets exist; both NEW paths (`test_mock_result_marking.py`, `CHANGE-136`) free. **0 drift.**

### Prong 2 — content verify

| ID | Finding | Implication |
|----|---------|-------------|
| **D-wrapper-arity** ✅ | `executor.py:320` uses `inspect.signature(handler)` (NOT `__code__.co_argcount`). Live proof: a `functools.wraps`-decorated `async def w(*a)` reports the ORIGINAL arity — 1-arg → `takes_ctx=False`, 2-arg → `takes_ctx=True` | Plan's `functools.wraps` design is **sound**. Also measured: all 18 business handlers are currently **1-arg** (`call`) — so the 2-arg path is future-proofing, not a live requirement |
| **D-18-tool-names** ⚠️ **MAJOR** | The key-diff returns exactly **18** handlers — but every name is **already `mock_`-prefixed** (`mock_incident_get`, `mock_patrol_schedule`, …) | Partially falsifies the plan's premise "nothing says it's mock": the tool NAME is a signal today, and chat-v2's ToolBlock renders it. **BUT see the next row** — the signal is unreliable |
| **D-toolname-lies-in-service-mode** 🔴 **MAJOR / NEW** | Registering with `mode="service"` yields **the same 18 `mock_*` names** (18/18). The name is a **constant, not a mode signal** | In production (`service`), REAL DB-backed results would be labelled `mock_*` — the lie runs the *opposite* way. This **strengthens** the case for a mode-derived marker (the sprint's actual fix) and surfaces a NEW naming defect (AP-11) that is **out of scope** here (renaming changes the LLM-visible tool contract) → NEW `AD-BusinessTool-Name-Says-Mock-In-Service-Mode` |
| **D-handler-returns-json-string** 🔴 **MAJOR — design change** | All 5 domains return **`json.dumps(result)`** (patrol 8 · correlation 6 · rootcause 6 · audit 6 · incident 10 return sites) — i.e. a **JSON string**, never a `dict` | A `[MOCK] ` string prefix would produce `[MOCK] {"id":…}` = **invalid JSON**. Plan §3.2's prefix-the-string design must change → mark **inside** the JSON |
| **D-downstream-json-loads** 🔴 confirms the above | `tests/integration/business_domain/test_business_tools_via_registry.py` does `json.loads(result.content)` at **6+ sites** | A prefix would break these tests AND any real JSON consumer. Confirms the revised design is required, not merely preferable |
| **D-i18n-key-shape** ✅ | `chat.session` keys are **symmetric** across `en` / `zh-TW` (8 keys each); `filter` exists (`"Filter"` / 繁中) | Safe to add `filterUnavailable` to both. Note: edit the zh-TW JSON with the Edit tool, not shell — the console mangles the UTF-8 on read |
| **D-mock-tests-assert-exact** ✅ | 41 test references to the `mock_*` tool names across 8 files | Covered by the revised design: injecting a JSON key keeps `json.loads` working; the affected assertions check specific payload fields, not whole-string equality |

### Design change adopted at Day-0 (audit trail preserved — plan §3.2 revised, not silently)

**Was** (plan as drafted): `str` result → `"[MOCK] " + result`.
**Now**: parse the JSON string → add `"_mock": true` → re-dump. Keeps the payload **valid JSON** (so `json.loads` consumers and the 6+ existing integration assertions keep working) while the marker stays visible to both the LLM and the human reading the tool output in chat-v2. Non-JSON strings keep the `[MOCK] ` prefix as a defensive fallback; `dict` results get an additive `_mock` key.

### Go/no-go

Scope shift **< 20%** — the fix's shape is unchanged (one wrapper at the `register_all_business_tools` chokepoint, mode-gated, arity-preserving); only the *marking mechanism* changed (JSON-key injection instead of string prefix), which the Day-0 evidence forced. Two new out-of-scope findings logged as carryover ADs. → **proceed to Day 1**.

## Day 1-2 — 2026-07-23 — Implementation + full gate

### Implemented

**US-1 startup warning** (`api/main.py`) — `_warn_business_domain_mock()` mirroring the 5 `_wire_*()` helpers (fail-open, one log line), called from the lifespan after `_wire_billing_outbox()`. `mock` → `logger.warning` naming the 5 domains as FABRICATED + `BUSINESS_DOMAIN_MODE=service` as the way out; `service` → `logger.info` positive confirmation (silence must not be ambiguous — otherwise a *broken* warning is indistinguishable from production).

**US-2 result marking** (`business_domain/_register_all.py`) — `_MOCK_KEY`/`_MOCK_PREFIX` + `_mark_mock_result()` (`functools.wraps`), applied by **key-diff** (`_before = set(handlers)` snapshot before the 5 `register_*_tools`, wrap only the delta) and only when `mode == "mock"`. Marking is **in-JSON** per the Day-0 revision: JSON-object string → `json.loads` + `"_mock": true` + `json.dumps`; non-JSON string → `[MOCK] ` prefix; `dict` → additive key; JSON array/scalar → untouched.

**US-3 honest Filter** (`SessionList.tsx` + 2 i18n) — `disabled` + `title={t("chat.session.filterUnavailable")}`; markup/classes/icon verbatim; an in-file comment records *why disabled rather than wired* (the mockup defines no filter behaviour → wiring one would breach 「自創 widget」; deleting it would breach the widget-deletion ban). New symmetric key in `en` + `zh-TW`.

### Tests (+13)

- **NEW `test_mock_result_marking.py` (9)** — marker lands + payload stays valid JSON · every original key preserved · `service` mode wraps NOTHING · key-diff never touches a co-registered `echo_tool` (asserted by **object identity**) · **arity preserved through the REAL `ToolExecutorImpl`** (a 2-arg handler still receives its `ExecutionContext` — the load-bearing case) · 1-arg still dispatches · dict/non-JSON/array shapes degrade sensibly.
- **`test_main_lifespan.py` (+2)** — mock mode warns (and names the escape hatch); service mode confirms positively and does NOT warn.
- **`SessionList.test.tsx` (+2)** — Filter is `disabled` + carries the localized tooltip; clicking it moves no state (the AP-4 dead-control walk).

### Gate

| Gate | Result |
|------|--------|
| mypy `src` | **400**, no issues (1 self-inflicted `unused-ignore` found + removed) |
| run_all | **12/12** |
| backend pytest | **3276 passed**, 6 skipped (baseline 3271 collected → **+11**) |
| Vitest | **939** (baseline 937 → **+2**) |
| mockup fidelity | **51**, `styles.css` diff **empty** |
| `npm run lint && npm run build` | clean (NO `--silent`) |
| black / isort / flake8 · LLM-SDK-leak | clean |

## Day 3 — 2026-07-23 — Drive-through (real UI + real backend + real LLM) — **PASS (after a real fix)**

### Setup (Risk Class E)
Killed the stale backend; `Win32_Process` confirmed a **sole** live `python.exe` before each run; started WITHOUT `--reload`, **default config** (`BUSINESS_DOMAIN_MODE` unset → `mock`). Also started `mock_services` on :8001 (the business tools' HTTP backend). Frontend Vite :3007, real Azure `gpt-5.2`, jamie@acme.com.

### 🔴 The drive-through caught a real gap the green gate could not

**Run 1** ended with the agent answering from `mock_incident_list` — and **`_mock` appeared nowhere on the page**.

Root cause: `mock_incident_list` returns a **bare JSON array** (`[{...}, {...}]`), and the Day-1 wrapper deliberately left arrays untouched — I had even written that as a *passing* test (`test_json_array_left_untouched`). My Day-0 probe verified handlers return `json.dumps(result)` but never checked the type of `result` itself. So **every `*_list` / `*_query` tool shipped unmarked while 9/9 unit tests were green** — a textbook gate-green≠works.

**Fix**: extracted `_marked_payload()` — a dict gains the key; a **list marks every dict element** (array shape preserved, still `json.loads`-able); scalars / lists-of-scalars stay untouched. `test_json_array_left_untouched` was replaced by `test_json_array_of_objects_marks_every_element` (which names the drive-through as its provenance) + 2 more shape tests → **11 tests**.

### Legs (after the fix, backend restarted)

| Leg | Verified | Result |
|-----|----------|--------|
| **1 — startup warning** | fresh backend log, default config | ✅ `WARNING api.main: BUSINESS DOMAIN IS MOCK — the 18 business tools (patrol/correlation/rootcause/audit/incident) return FABRICATED data from the mock backend, not real systems. Tool results are marked with "_mock": true. Set BUSINESS_DOMAIN_MODE=service …` |
| **2 — `_mock` marker (real UI)** | chat-v2 ToolBlock output, real Azure `gpt-5.2` | ✅ **10 occurrences** of `"_mock": true` — one per incident object, e.g. `[{"id": "inc_003", …, "created_at": "2026-04-30T08:00:00Z", "_mock": true}, {"id": "inc_001", …, "_mock": true}, …]`. Payload still valid JSON; every original field intact |
| **3 — Filter control (real UI)** | live DOM, both locales | ✅ `disabled=""` + `title="Session filtering is not available yet"`; mockup classes (`btn ghost` / `data-size="sm"`) + icon unchanged. Locale toggle → `title="工作階段篩選功能尚未提供"`, `aria-label="篩選"` — the key resolves live in **both** locales, not just in the JSON file |

### Observed vs intended

| | Intended | Observed |
|---|---|---|
| ops signal | startup names mock + the way out | exact warning present at WARNING level ✅ |
| user signal | fabricated results visibly marked in chat-v2 | `"_mock": true` on every returned object ✅ (**only after the array fix** — run 1 showed 0) |
| payload safety | stays valid JSON, no field lost | `json.loads`-able array; all original fields present ✅ |
| dead control | declares itself instead of silently no-op'ing | disabled + localized tooltip, widget otherwise verbatim ✅ |

Screenshot: `artifacts/sprint-57-167-drivethrough-mock-marker.png`.

### Honest note
Leg 2's marker is visible **in the tool-output block**, which the user must have the Loop/Inspector panel open to read. It is NOT a badge on the answer bubble — that was AskUserQuestion option C, declined as beyond "zero-cost" → `AD-BusinessMock-ChatV2-Badge`.

### Remaining
- Day 4: CHANGE-136 + closeout.
