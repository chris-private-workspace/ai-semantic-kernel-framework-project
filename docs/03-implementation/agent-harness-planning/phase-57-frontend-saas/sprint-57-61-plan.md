# Sprint 57.61 — Plan

**Phase**: 57+ Frontend SaaS / Phase 58.x Portfolio Deeper Extensions
**Sprint**: 57.61 (post-57.60 RateLimits MetaData Cleanup)
**Branch**: `feature/sprint-57-61-rate-limits-syntax-validation`
**Class**: `medium-backend` 0.80 (single-domain backend; NEW Pydantic validator + value-shape predicate + comprehensive negative tests; frontend verify-only)
**Agent-delegated**: yes (single code-implementer agent — small backend-only sprint)
**Agent-factor**: `mechanical-greenfield-design-decisions` 0.65 (NEW value-shape predicate + 422 envelope design; backend-only application — see §2.3)
**Plan version**: v1 — drafted 2026-05-29 Day 0 (pre-三-Prong)
**Template**: mirrors `sprint-57-60-plan.md` 9-section structure

---

## 1. Sprint Goal

Close **`AD-RateLimits-SyntaxValidation-Phase58`** (Sprint 57.60 carryover) by adding **PUT-time syntax validation** to the RateLimits admin write path, so a malformed rate-limit `value` returns a clear **422** instead of being **silently dropped** by `replace_configs` (which currently `if parse is None: continue` skips unparseable items → the admin gets 200 OK but the row vanishes on the next GET).

The validator distinguishes three value classes:

- **Enforceable rate** `N / <sec|min|hour|day>` (e.g. `"100 / min"`, `"1,000 / hour"`) → ACCEPT
- **Display-only concurrency** `N concurrent` (e.g. `"50 concurrent"` — the `DEFAULT_RATE_LIMITS` SSE row; intentionally not time-windowed, not enforced) → ACCEPT (preserves the load-defaults → edit → save round-trip)
- **Malformed / unsupported** — garbage (`"foo"`), unsupported window (`"50 / week"` — looks like a rate but the window is not enforced), non-positive quota (`"0 / min"`), empty value, empty label → REJECT **422** with a per-item reason

Plus a **parser-consistency guard** (US-2): a test asserting the three parse copies (admin store `parse_config_item`, runtime counter `parse_rate_limit_item`, and the new validator predicate) agree on validity, so a future edit to one window-alias table can't make the PUT accept an item the runtime gate silently can't enforce.

After this sprint: the admin can no longer save a rate limit that would be silently ignored; the failure is surfaced at write time with an actionable message.

---

## 2. Background & Context

### 2.1 The silent-drop gap (verified this sprint Day 0 探勘)

Post-57.60, the RateLimits write path is: `PUT /admin/tenants/{tid}/rate-limits` → `RateLimitsUpsertRequest` (Pydantic, `extra="forbid"`, `items: list[RateLimitItem]`) → `RateLimitConfigStore.replace_configs(tenant_id, items)` → config rows in `rate_limit_configs`.

`replace_configs` (`rate_limit_config_store.py:162-200`) parses each `{label, value}` item via `parse_config_item` and **silently skips** any that return `None` (`if parsed is None: continue`, L184). So:

- `PUT {"items":[{"label":"API requests","value":"garbage"}]}` → **200 OK**, but the item is dropped → next `GET` returns `DEFAULT_RATE_LIMITS` (config table empty) → the admin's setting vanished with no error.

This is the gap `AD-RateLimits-SyntaxValidation-Phase58` closes: validate at PUT-time, 422 on malformed, so the silent drop becomes a visible rejection.

### 2.2 The three-parser landscape + validity agreement (de-risks US-2)

There are three copies of the `{label, value}` parse logic (intentional — the migration must be dep-light per Sprint 57.59 D-DAY0-N):

| Parser | File | Output | Purpose |
|--------|------|--------|---------|
| `parse_rate_limit_item` / `parse_rate_limit_value` | `rate_limit_counter.py:165-203` | `ParsedRateLimit(resource, limit, window_seconds)` | runtime enforcement (middleware + Cat 2 gate) |
| `parse_config_item` | `rate_limit_config_store.py:105-131` | `(resource_type, window_type, quota)` | admin store persist |
| `_parse_item` (inline) | `0019_rate_limit_configs.py` | `(resource_type, window_type, quota)` | migration seed (frozen snapshot) |

**Validity AGREES across the live two** (Day 0 探勘): both use the identical `_VALUE_RE` regex; counter `_WINDOW_TO_SECONDS` keys = store `_WINDOW_ALIASES` keys = `{sec, second, min, minute, hour, hr, day}`; both require quota/limit > 0 + non-empty label. So an item parses in the store ⟺ it parses in the counter. The US-2 guard encodes this so a future divergence (e.g. someone adds `"week"` to one table only) is caught by a test, not by a tenant silently losing enforcement.

### 2.3 The `"50 concurrent"` critical edge case + why `-design-decisions` 0.65

`DEFAULT_RATE_LIMITS` (`tenants.py:1355-1359`) includes `{"label": "SSE connections", "value": "50 concurrent"}` — a **display-only** value that intentionally does NOT parse to an enforceable rate (no time window). The runtime skips it (nothing to enforce); the admin UI shows it.

A naive validator that rejects everything `parse_config_item` returns `None` for would **reject `"50 concurrent"`** → breaking the natural admin flow: GET the defaults → edit one row → PUT the whole list (including the unchanged `"50 concurrent"`). So the validator needs a **broader "recognized value shape" predicate** than the enforceable-rate parser:

- accept `N / <known-window>` (enforceable) **and** `N concurrent` (display-only)
- reject everything else (with a reason)

This broader predicate is **genuine NEW design** (not a port of `parse_config_item`), which is why the agent-factor is `mechanical-greenfield-design-decisions` 0.65 rather than `-port-style` 0.45. **Note (backend-only application)**: the tier-4 `-design-decisions` 0.65 sub-class was framed around a backend-Pydantic + frontend-UX component-pair (Sprint 57.56/57.57). This sprint is **backend-only** (frontend verify-only); the "design decisions" here are the value-shape predicate + the 422 error envelope + the accept/reject asymmetry, substituting for the usual frontend-UX-design portion. 3rd data point for `-design-decisions` 0.65; flag retro Q4 to note the backend-only variant (if it lands far from band, consider whether backend-only design warrants a distinct factor).

### 2.4 `RateLimitItem` is a SHARED model (validator placement constraint)

`RateLimitItem` (`tenants.py:1341-1345`) is used by BOTH `RateLimitListResponse` (GET response) AND `RateLimitsUpsertRequest` (PUT request, `items: list[RateLimitItem]`). A strict validator must therefore go on the **request model** (`RateLimitsUpsertRequest` — a `field_validator("items")` or `model_validator`), **NOT** on the shared `RateLimitItem` (which would also validate GET responses + reject the `DEFAULT_RATE_LIMITS` projection). Day 0 三-Prong Prong 2 confirms the sharing before code.

### 2.5 Sprint 57.60 carryover chain

- `AD-RateLimits-SyntaxValidation-Phase58` (this sprint's primary)
- `AD-RateLimits-Alerting-Phase58` (NOT this sprint — SSE 80% threshold)
- `AD-AgentFactor-Tier-3-MixedBundle-Mechanical-Tighten-0.45-Validation-Sprint-57.61` (DEFERS again — this sprint is single-domain, not a multi-track bundle)
- `AD-AgentPrompt-CrossPlatform-Mypy-Warning` / `AD-Mypy-WholeDir-Conftest-Collision` (Phase 58+ candidates; this sprint does NOT touch Redis/asyncpg stubs)

### 2.6 Class baseline tracking

- `medium-backend` 0.80 — 12th data point (11-pt mean ~0.63; informational)
- `mechanical-greenfield-design-decisions` 0.65 — 3rd validation (57.56=1.02 + 57.57=1.15 both IN band; this is the 1st backend-only application)

---

## 3. User Stories

### US-1: PUT-time RateLimits syntax validation (422 instead of silent drop)

**As a** tenant administrator
**I want** a clear error when I save a malformed rate limit
**So that** my setting is never silently dropped and I know exactly what to fix.

**Acceptance**:
- NEW `is_recognized_rate_limit_value(value) -> tuple[bool, str | None]` predicate in `rate_limit_config_store.py` (reuses `_VALUE_RE` + `_WINDOW_ALIASES`; adds `_CONCURRENCY_RE` for the `N concurrent` display pattern). Returns `(True, None)` for enforceable rate OR display-only concurrency; `(False, reason)` otherwise (empty / unsupported-window / non-positive / non-numeric / unrecognized shape).
- NEW `field_validator("items")` (or `model_validator`) on `RateLimitsUpsertRequest` (`tenants.py`) that, for each item, checks `label` non-empty AND `is_recognized_rate_limit_value(value)` → on any failure raises `ValueError` → FastAPI returns **422** with a per-item message (index + label + value + reason).
- Validator goes on the **request model only** (NOT shared `RateLimitItem`).
- `DEFAULT_RATE_LIMITS` round-trip preserved: PUT-ing the 3 defaults verbatim (incl. `"50 concurrent"`) → **200 OK** (no false reject).
- ~8-10 NEW pytest: each malformed shape → 422 (no-slash garbage / unsupported window `"50 / week"` / `"0 / min"` / `""` / empty label / non-numeric `"abc / min"`); valid rate + concurrency + defaults round-trip → 200; multi-tenant isolation unaffected; the persisted config matches (valid items reach `rate_limit_configs`).

### US-2: Parser-consistency guard (prevent silent-enforcement drift)

**As a** platform maintainer
**I want** a test asserting the admin-store, runtime-counter, and validator parsers agree on validity
**So that** a future edit to one window-alias table can't let the PUT accept a rate the runtime gate silently won't enforce.

**Acceptance**:
- NEW test (`test_rate_limit_parser_consistency.py`) over a shared input matrix asserting:
  - for **enforceable-rate** inputs: `parse_config_item is not None` ⟺ `parse_rate_limit_item is not None` ⟺ `is_recognized_rate_limit_value()[0] is True` (rate branch)
  - for **concurrency** inputs (`"N concurrent"`): validator accepts (display-only) BUT both parsers return `None` (documented intentional asymmetry — not enforced)
  - for **garbage** inputs: all three reject
- The matrix covers every window alias (sec/second/min/minute/hour/hr/day) + thousands separators + the concurrency pattern + representative garbage.
- Test fails loudly if `_WINDOW_TO_SECONDS` (counter) and `_WINDOW_ALIASES` (store) keys diverge.

---

## 4. Technical Specification

### 4.1 NEW value-shape predicate (`rate_limit_config_store.py`)

```python
# Display-only concurrency pattern (e.g. "50 concurrent") — recognized + accepted
# by the admin validator but NOT enforceable (no time window), so the runtime
# parsers skip it. Kept here next to parse_config_item so the {label,value} domain
# logic stays in one module (no 4th regex copy beyond this one new pattern).
_CONCURRENCY_RE = re.compile(r"^\s*[\d,]+\s+concurrent\s*$", re.IGNORECASE)

# Public so the RateLimitsUpsertRequest validator (tenants.py) + tests reuse it.
def is_recognized_rate_limit_value(value: str) -> tuple[bool, str | None]:
    """Validate an admin-supplied rate-limit display value.

    Accepts: enforceable rate 'N / <sec|min|hour|day>' OR display-only 'N concurrent'.
    Rejects everything else with a human reason. Broader than parse_config_item
    (which only recognizes the enforceable rate) because the admin UI legitimately
    carries the non-enforceable 'N concurrent' default (DEFAULT_RATE_LIMITS SSE row).
    """
    v = (value or "").strip()
    if not v:
        return False, "value is empty"
    m = _VALUE_RE.match(v)
    if m:
        raw_quota, raw_window = m.group(1), m.group(2).lower()
        if raw_window not in _WINDOW_ALIASES:
            return False, f"unsupported window '{m.group(2)}' (supported: sec, min, hour, day)"
        try:
            quota = int(raw_quota.replace(",", ""))
        except ValueError:
            return False, "quota is not a number"
        if quota <= 0:
            return False, "quota must be a positive number"
        return True, None
    if _CONCURRENCY_RE.match(v):
        return True, None  # display-only; not time-windowed, not enforced
    return False, "value must be 'N / <sec|min|hour|day>' or 'N concurrent'"
```

### 4.2 Validator on `RateLimitsUpsertRequest` (`tenants.py`)

```python
from platform_layer.tenant.rate_limit_config_store import is_recognized_rate_limit_value

class RateLimitsUpsertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[RateLimitItem] = Field(default_factory=list, description=...)

    @field_validator("items")
    @classmethod
    def _validate_items(cls, items: list[RateLimitItem]) -> list[RateLimitItem]:
        errors: list[str] = []
        for i, item in enumerate(items):
            if not item.label.strip():
                errors.append(f"item[{i}]: label is required")
            ok, reason = is_recognized_rate_limit_value(item.value)
            if not ok:
                errors.append(f"item[{i}] ({item.label!r} = {item.value!r}): {reason}")
        if errors:
            raise ValueError("; ".join(errors))
        return items
```

FastAPI wraps the `ValueError` into a **422** `detail` entry (`loc: ["body","items"]`, `msg: "Value error, item[0] (...): ..."`). The Sprint 57.57 frontend `useRateLimitsSave` error path already surfaces the mutation error → the 422 message string is shown inline (frontend verify-only; §5).

### 4.3 US-2 consistency guard

`test_rate_limit_parser_consistency.py` iterates a matrix:

```
RATE_OK      = ["1 / sec", "100 / min", "1,000 / minute", "50 / hour", "9 / hr", "1 / day", "10 / second"]
RATE_BAD     = ["50 / week", "0 / min", "-5 / min", "abc / min", "100 /", "/ min", "100", ""]
CONCURRENCY  = ["50 concurrent", "1,000 concurrent", "5 CONCURRENT"]
GARBAGE      = ["foo", "100 bananas", "concurrent", "min / 100"]
```

Assertions: RATE_OK → all three recognize (store/counter not-None, validator True); RATE_BAD + GARBAGE → store/counter None AND validator False; CONCURRENCY → validator True but store/counter None (documented asymmetry).

### 4.4 Verification

- ~12-16 NEW pytest (US-1 ~8-10 + US-2 ~4-6 matrix assertions)
- pytest baseline 1848 → ~1860+
- mypy `src/ --strict` 0 / 9/9 V2 lints (`check_rls_policies` 20 tables unchanged — no schema change) / 0 SDK leak
- 0 frontend functional change → Vitest 675 unaffected / HEX_OKLCH baseline 48 / DUAL CLEAN 22/22 PARITY 17 consec
- No Alembic migration (no schema change)

### 4.5 Risk mitigation

| Risk | Mitigation |
|------|-----------|
| Validator rejects the `"50 concurrent"` default → breaks load-edit-save | `_CONCURRENCY_RE` accepts it; explicit defaults-round-trip test (US-1 acceptance) |
| Validator placed on shared `RateLimitItem` → breaks GET | Day 0 Prong 2 confirms sharing; validator on `RateLimitsUpsertRequest` only |
| 422 message not surfaced in UI | Sprint 57.57 `useRateLimitsSave` error path shows mutation error; frontend verify-only (manual check) |
| 4th parser drift | predicate reuses store `_VALUE_RE` + `_WINDOW_ALIASES` (no new rate regex; only `_CONCURRENCY_RE`); US-2 guard locks store⟺counter validity |
| Over-strict rejects a value the runtime WOULD enforce | predicate's rate branch mirrors `parse_config_item` exactly (same regex + alias table); US-2 guard proves equivalence |

---

## 5. File Change List

### Backend (NEW + EDIT)

**NEW**:
- `backend/tests/integration/api/test_admin_tenant_rate_limits_syntax_validation.py` (~8-10 US-1 422/200 tests)
- `backend/tests/unit/platform_layer/tenant/test_rate_limit_parser_consistency.py` (~4-6 US-2 matrix tests) — *(Day 0 Prong 1 confirms the unit test dir path; may be `tests/integration/...` if no unit tree for this module)*

**EDIT**:
- `backend/src/platform_layer/tenant/rate_limit_config_store.py` — NEW `is_recognized_rate_limit_value` predicate + `_CONCURRENCY_RE`; MHist
- `backend/src/api/v1/admin/tenants.py` — NEW `field_validator("items")` on `RateLimitsUpsertRequest` + import; MHist

### Frontend (verify-only; no functional change expected)

- Confirm `useRateLimitsSave` mutation error path surfaces the 422 message in the QuotasTab RateLimits Card edit mode (Sprint 57.57). No code change for MVP; nicer per-item highlighting deferred to carryover.

### Sprint artifacts (Day 0 + Day 2)

- `sprint-57-61-plan.md` (this) + `sprint-57-61-checklist.md`
- `agent-harness-execution/phase-57/sprint-57-61/progress.md` + `retrospective.md`
- `memory/project_phase57_61_rate_limits_syntax_validation.md`
- `claudedocs/4-changes/feature-changes/CHANGE-0XX-sprint-57-61-rate-limits-syntax-validation.md` (feature — NEW validation behavior; not a refactor — see §9 D-point)

---

## 6. Workload

**Agent-delegated: yes** (single code-implementer agent — small backend-only sprint)

**Bottom-up est ~5.25 hr** → class-calibrated commit ~4.2 hr (mult 0.80 `medium-backend`) → **agent-adjusted commit ~2.7 hr** (`agent_factor` 0.65 `mechanical-greenfield-design-decisions`)

| Task | Bottom-up | Class-calibrated | Agent-adjusted |
|------|-----------|-----------------|---------------|
| Day 0 三-Prong (Path + Content; Schema N/A) + plan | 0.75 hr | 0.75 hr | 0.75 hr (parent) |
| US-1: predicate + validator + ~8-10 negative tests | 2.5 hr | 2.0 hr | 1.3 hr |
| US-2: parser-consistency guard matrix test | 1.0 hr | 0.8 hr | 0.5 hr |
| Day 1 validation sweep | 0.4 hr | 0.4 hr | parent |
| Day 2 closeout | 0.6 hr | 0.6 hr | 0.6 hr (parent) |
| **Total** | **~5.25 hr** | **~4.2 hr** | **~2.7 hr** |

Validation threshold: `actual/agent-adjusted` in [0.85, 1.20]; tier-4 `mechanical-greenfield-design-decisions` 0.65 3rd validation (57.56=1.02 + 57.57=1.15 IN band) — if this 1st backend-only application lands far from band, retro Q4 considers a backend-only variant note.

---

## 7. Acceptance Criteria

### Functional
- [ ] Malformed value (garbage / unsupported window / non-positive / non-numeric / empty) → PUT 422 with per-item reason
- [ ] Empty label → 422
- [ ] Enforceable rate (`N / sec|min|hour|day`) → 200 + persisted to `rate_limit_configs`
- [ ] Display-only `N concurrent` → 200 (accepted, not enforced)
- [ ] `DEFAULT_RATE_LIMITS` verbatim round-trip (incl. `"50 concurrent"`) → 200 (no false reject)
- [ ] Validator on `RateLimitsUpsertRequest` only; GET unaffected
- [ ] Parser-consistency guard: store ⟺ counter validity for rates; concurrency asymmetry documented; garbage all-reject
- [ ] Multi-tenant isolation unaffected

### Quality
- [ ] pytest 1848 → 1860+ (NO regressions)
- [ ] mypy `src/ --strict` 0 / 9/9 V2 lints / 0 SDK leak
- [ ] HEX_OKLCH baseline 48 / DUAL CLEAN 22/22 PARITY 17 consec / Vitest 675 unchanged
- [ ] No Alembic migration (no schema change)

### Process
- [ ] Day 0 三-Prong (Path + Content; Schema N/A — no migration)
- [ ] Prong 2 confirms `RateLimitItem` shared between GET/PUT + the `"50 concurrent"` default present
- [ ] Single code-implementer agent delegation
- [ ] Day 2 closeout (retro Q1-Q6 + memory + CLAUDE.md + next-phase + CHANGE-0XX)
- [ ] PR + CI green + merge

---

## 8. Risks

| # | Risk | Class | Mitigation |
|---|------|-------|-----------|
| R1 | Validator rejects `"50 concurrent"` → breaks load-edit-save round-trip | Logic / UX | `_CONCURRENCY_RE` accepts; explicit defaults-round-trip acceptance test (the single most important negative-of-the-negative case) |
| R2 | Validator on shared `RateLimitItem` → breaks GET / DEFAULT projection | Logic | Day 0 Prong 2 confirms sharing; validator on `RateLimitsUpsertRequest` only; GET regression test |
| R3 | 4th parser copy drift | Code hygiene | predicate reuses store `_VALUE_RE` + `_WINDOW_ALIASES`; only NEW regex is `_CONCURRENCY_RE`; US-2 guard locks store⟺counter |
| R4 | Over-strict: rejects a value the runtime WOULD enforce (false 422) | Logic | rate branch mirrors `parse_config_item` exactly; US-2 guard proves store⟺counter⟺validator-rate equivalence |
| R5 | 422 message not surfaced in admin UI | Frontend | Sprint 57.57 `useRateLimitsSave` error path shows it; frontend verify-only manual check; nicer highlighting → carryover |
| R6 | `mechanical-greenfield-design-decisions` 0.65 3rd validation (1st backend-only) lands out of band | Calibration | 3rd data point; if far from band, retro Q4 notes a backend-only variant (vs the 57.56/57.57 backend+frontend pair) |
| R7 | Duplicate (resource_type, window_type) in payload still silently last-wins de-duped | Logic (deferred) | OUT of MVP scope; the dedup is defensible (last-wins); surfacing it as 422 → carryover `AD-RateLimits-DuplicateResource-Validation` |

---

## 9. Carryover ADs (for Sprint 57.62+ pickup)

| ID | Status | Notes |
|----|--------|-------|
| `AD-RateLimits-Alerting-Phase58` | CARRYOVER | SSE 80%-threshold usage alerts; pairs with the activated `rate_limits` usage table; SSE infra ~80% from prior sprints; ~3-4 hr |
| `AD-RateLimits-DuplicateResource-Validation` | NEW (deferred) | PUT-time 422 on two payload items resolving to the same (resource_type, window_type) — currently silent last-wins dedup; ~1 hr |
| `AD-RateLimits-SyntaxValidation-ClientSide-Polish` | NEW (deferred) | mirror the value-shape predicate in TS for inline client-side validation + per-item field highlighting (UX polish; risks a 5th parser copy — weigh carefully); ~2 hr |
| `AD-RateLimits-Parser-Extract-Shared-Predicate` | NEW (deferred) | extract the window-alias table to ONE source the counter + store reference (migration stays dep-light inline); removes the 2-live-copy smell the US-2 guard currently watches; ~2-3 hr |
| `AD-AgentFactor-Tier-3-MixedBundle-Mechanical-Tighten-0.45-Validation-Sprint-57.62` | DEFERS | awaits next genuine multi-track `mixed-multidomain-bundle` sprint (57.61 is single-domain) |
| `AD-AgentPrompt-CrossPlatform-Mypy-Warning` / `AD-Mypy-WholeDir-Conftest-Collision` | CONTINUES | Phase 58+ (this sprint does NOT touch Redis/asyncpg stubs nor `mypy .` whole-dir) |

---

**Plan v1 status**: drafted 2026-05-29 Day 0 (pre-Day 0 三-Prong Verify); awaiting user approval before checklist v1 + Day 0 三-Prong execution.

**Open user decision points** (Day 0 approval gate):
1. **Confirm scope** — PUT-time value-shape validation (accept enforceable rate + `N concurrent`; reject garbage/unsupported-window/non-positive/empty) + parser-consistency guard. KEEP free-form labels (NO whitelist, per Sprint 57.57 D-DAY0-C/D).
2. **`"N concurrent"` acceptance** — confirm display-only concurrency values are ACCEPTED (required for the defaults round-trip), not rejected. (Recommended: accept.)
3. **Duplicate-resource detection** — IN scope (422 on same resource+window) OR deferred carryover? (Recommended: defer — last-wins dedup is defensible; keep MVP tight.)
4. **Change record type** — CHANGE-0XX (NEW validation behavior = feature) vs FIX (silent-drop is arguably a bug). (Recommended: CHANGE — it adds a new 422 contract, not just a bug patch.)
5. **Agent delegation** — single code-implementer agent (small backend-only) vs parent-direct. (Recommended: single agent.)
