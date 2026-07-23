# Sprint 57.167 — Checklist (de-Potemkin: honest MOCK surface + dead Filter control)

[Plan](./sprint-57-167-plan.md)

---

## Day 0 — Plan-vs-Repo Verify (三-prong) + Branch

### 0.1 Three-prong Day-0 verify (against `main` HEAD `4b3bbcb1`)
- [x] **Prong 1 — path verify**: `api/main.py` · `business_domain/_register_all.py` · `chat_v2/components/SessionList.tsx` · `i18n/locales/{en,zh-TW}/common.json` · `tests/unit/api/test_main_lifespan.py` · `tests/unit/chat_v2/components/SessionList.test.tsx` all exist; NEW `tests/unit/business_domain/test_mock_result_marking.py` free; `CHANGE-136` free
- [x] **Prong 2 — content verify** (drift → progress.md):
  - [x] **D-wrapper-arity** ✅ `inspect.signature` confirmed; wraps preserves arity (live proof) — re-read `executor.py:316-337`: arity detection must be `inspect.signature` (follows `__wrapped__`), NOT `__code__.co_argcount` (does NOT) → decides whether `functools.wraps` suffices
  - [x] **D-handler-return-shape** 🔴 all 5 domains return `json.dumps(...)` (str, never dict) → forced §3.2 design change — sample the 18 registered business handlers: count `str` vs `dict` returns; if `dict`, identify the human-readable text field per domain
  - [x] **D-18-tool-names** ⚠️ exactly 18, but ALL already `mock_`-prefixed (+ NEW `D-toolname-lies-in-service-mode`: same names in `service` mode) — capture the exact key set the 5 `register_*_tools` add (key-diff before/after) so marking never touches echo / python_sandbox / memory / write_todos
  - [x] **D-mock-tests-assert-exact** ✅ 41 refs / 8 files, field-level not whole-string; but `json.loads` at 6+ sites → confirms in-JSON marking — grep business-domain tests for exact-equality assertions on handler output that a `[MOCK] ` prefix would break
  - [x] **D-i18n-key-shape** ✅ symmetric 8 keys both locales — confirm `chat.session` nesting + that `en` / `zh-TW` are symmetric before adding `filterUnavailable`
- [x] **Prong 3 — schema verify**: N/A (no DB table / migration / ORM change)
- [x] **D-baselines** — pytest **3271** · Vitest **937** (150 files) · mockup **51** (`diff` empty) · mypy `src` **400** · run_all **12/12**
- [x] **Catalog drift** — progress.md Day-0 table
- [x] **Go/no-go** — <20% shift (same wrapper shape, revised marking mechanism) → proceed. — scope-shift % → proceed / revise / abort

### 0.2 Branch
- [x] `git checkout -b feature/sprint-57-167-de-potemkin-honest-surfaces` (from `main` `4b3bbcb1`)

---

## Day 1 — Mock honesty: startup warning + result marking (US-1 / US-2)

### 1.1 Startup MOCK warning
- [x] **`_warn_business_domain_mock()` in the lifespan, mirroring the 5 `_wire_*()` helpers**
  - DoD: `mode=="mock"` → `logger.warning` naming fabricated data + `BUSINESS_DOMAIN_MODE=service` as the switch; `mode=="service"` → `logger.info` positive confirmation; fail-open `try/except` like its siblings
  - Verify: `grep -n "_warn_business_domain_mock" backend/src/api/main.py`

### 1.2 `[MOCK]` marking at the registration chokepoint
- [x] **`_MOCK_PREFIX` + `_mark_mock_result(handler)` + key-diff application in `register_all_business_tools`**
  - DoD (**revised per Day-0 D-handler-returns-json-string**): `functools.wraps` preserves arity; JSON-object `str` → `json.loads` + `"_mock": true` + `json.dumps` (**stays valid JSON** — a prefix would break the 6+ `json.loads` integration assertions); non-JSON `str` → `[MOCK] ` prefix fallback; `dict` → additive `_mock`; other shapes untouched; applied ONLY when `mode=="mock"` and ONLY to the key-diff set (the 18)
  - Verify: `grep -n "_MOCK_PREFIX\|_mark_mock_result" backend/src/business_domain/_register_all.py`

### 1.3 Backend tests
- [x] **`test_mock_result_marking.py` (NEW) + lifespan-warning test**
  - 18 business tools marked in `mock` mode / non-business tools NEVER marked
  - `mode="service"` → zero wrapping, results byte-identical
  - **arity preserved through the REAL `ToolExecutor`** (a 2-arg handler still receives its `ExecutionContext`) — AC-3
  - dict-shaped result keeps every original key
  - Verify: `python -m pytest backend/tests/unit/business_domain/test_mock_result_marking.py backend/tests/unit/api/test_main_lifespan.py -q`

### 1.x Partial gate
- [x] `mypy src` (400) + `black/isort/flake8` on the 2 touched backend files

---

## Day 2 — Honest Filter control + full gate (US-3)

### 2.1 Filter control + i18n
- [x] **`disabled` + `title` tooltip on the Filter button; `chat.session.filterUnavailable` in en + zh-TW**
  - DoD: markup / classes / icon otherwise verbatim (widget NOT deleted, NOT restyled); in-file comment records why disabled-not-wired (mockup defines no behaviour); keys symmetric across both locales
  - Verify: `grep -n "filterUnavailable" frontend/src/features/chat_v2/components/SessionList.tsx frontend/src/i18n/locales/*/common.json`

### 2.2 Frontend test
- [x] **`SessionList.test.tsx` — Filter is disabled + carries the localized tooltip**
  - DoD: asserts `disabled` + `title`; a click produces no state change / no throw
  - Verify: `cd frontend && npx vitest run tests/unit/chat_v2/components/SessionList.test.tsx`

### 2.x Full gate
- [x] mypy `src` 400 · run_all 12/12 · backend pytest 3271+N · Vitest 937+N · `npm run lint && npm run build` clean (NO `--silent`) · mockup 51 (`diff` empty) · black/isort/flake8 clean · LLM-SDK-leak clean

---

## Day 3 — Drive-through (US-4) — real UI + real backend + real LLM
_(MANDATORY — both surfaces are user-facing.)_

### 3.1 Clean restart (Risk Class E)
- [x] Kill all stale uvicorn reloader + spawn-workers; verify sole live `python.exe` via `Win32_Process` (PID/PPID/StartTime); start WITHOUT `--reload`, default config (`BUSINESS_DOMAIN_MODE` unset)

### 3.2 Drive-through (MANDATORY — NOT gate-only)
- [x] **Leg 1 — startup MOCK warning** visible in the fresh backend log (capture the line verbatim)
- [x] **Leg 2 — `[MOCK]` marker (real UI)** — ⚠️ run 1 showed **0** markers → drive-through found `mock_incident_list` returns a bare JSON **array** which the wrapper skipped (a passing unit test encoded the bug); fixed via `_marked_payload` (mark every dict element) → re-run: **10** `"_mock": true`. Original DoD:: ask a business question routing to a business tool → the tool result / answer rendered in chat-v2 visibly carries `[MOCK]`; if the agent won't call a business tool, prompt it by tool name; if STILL unreachable → record **inconclusive** (NOT a pass) + label that leg gate-only
- [x] **Leg 3 — Filter control (real UI)** — verified in BOTH locales live (en tooltip + 繁中 `工作階段篩選功能尚未提供`). Original DoD:: hover shows the localized tooltip; click does nothing (no state change, no console error) — the AP-4 per-control walk
- [x] Screenshot + observed-vs-intended → progress.md Day 3

---

## Day 4 — CHANGE-136 + closeout

### 4.1 CHANGE-136
- [x] **`CHANGE-136-de-potemkin-honest-surfaces.md`** (gap + fix + drive-through PASS + both Potemkins closed)

### 4.2 Closeout
- [x] retrospective.md Q1-Q7 + calibration (ratio ~1.22-1.27 edge-OVER → KEEP 0.85, cause = the drive-through FINDING a bug, not mis-estimation) (NEW `de-potemkin-honest-surface` 0.85, 1st data point; flag if ratio out of band → re-point)
- [x] calibration-matrix.md row (358 chars, hygiene lint green; narration → calibration-log §1) — skeleton was, ≤ 1 line ~250 chars (narration → calibration-log §1 ONLY): `| \`de-potemkin-honest-surface\` | 0.85 | n/a (1 pt) | KEEP pending validation (57.167 1st pt ratio ~<Y> <IN/OVER> band; anchored to chatv2-inspector-existing-field-surface 0.85 — tiny-code + full-ceremony + mandatory drive-through; if a 2nd lands >1.20 → 1.0; → calibration-log §1) |`
- [x] Final gate sweep (re-run AFTER the Day-3 array fix): mypy 400 · run_all 12/12 · pytest **3278** (+13) · Vitest **939** (+2) · mockup 51 · build/lint clean — mypy · run_all · pytest · Vitest · mockup · build · lint · LLM-SDK-leak
- [x] Navigators (+ shipped-archive block + pointer-index row): CLAUDE.md Current-Sprint + Last-Updated · MEMORY.md pointer + subfile · next-phase-candidates (**both Potemkins resolved** + 2 NEW ADs: `AD-BusinessMock-ChatV2-Badge` + `AD-SessionList-Filter-Real-Implementation`) · calibration-matrix.md row
- [x] **Audit-doc tracking** — §5 rows #1+#2 marked 修復 + an honest note that **#3-#7 five dead controls REMAIN** (out of this sprint's scope): original DoD: mark the 2 Potemkins resolved in `5-status/v2-reality-audit-engine-vs-grounding-20260715.md` §5 (this is the live tracking surface the audit itself points at — distinct from rewriting its dated §7 numbers)
- [x] Anti-pattern self-check (retro Q5): AP-2/3/4/6/8/11 → violations; v2 lints 12/12
- [ ] **Commit** → ⏳ PR push + open → CI → merge: PENDING USER CONFIRMATION → post-merge status flip after gh-verified MERGED
