# Sprint 57.61 — Checklist

Plan: [`sprint-57-61-plan.md`](./sprint-57-61-plan.md)

**Class**: `medium-backend` 0.80 (single-domain backend; NEW Pydantic validator + value-shape predicate + negative tests; frontend verify-only)
**Agent-delegated**: yes (single code-implementer agent)
**Agent-factor**: `mechanical-greenfield-design-decisions` 0.65 (NEW value-shape predicate + 422 envelope; 1st backend-only application)
**Template**: mirrors `sprint-57-60-checklist.md` Day 0-2 structure

---

## Day 0 — Plan + 三-Prong Verify (Prong 3 N/A — no migration)

### 0.1 Plan + Checklist Drafting
- [x] **Draft `sprint-57-61-plan.md` v1** (9-section; PUT-time syntax validation + parser-consistency guard)
- [x] **Draft `sprint-57-61-checklist.md` v1** (this file)
- [x] **User approve plan v1** — gate before Day 0 三-Prong ✅ (approved 2026-05-29; D-points: accept `N concurrent` / defer duplicate-resource / CHANGE record / single agent)

### 0.8 Day 0 三-Prong Verify (Step 2.5 — Content Prong CRITICAL: shared-model + concurrent-default)

#### Prong 1 — Path Verify
- [x] **D-DAY0-A**: `is_recognized_rate_limit_value` does NOT exist yet in `rate_limit_config_store.py` (NEW)
  - Verify: `grep -n "is_recognized_rate_limit_value\|_CONCURRENCY_RE" backend/src/platform_layer/tenant/rate_limit_config_store.py` → empty
- [x] **D-DAY0-B**: `RateLimitsUpsertRequest` has NO existing `field_validator`/`model_validator` (NEW addition)
  - Verify: `grep -n "field_validator\|model_validator" backend/src/api/v1/admin/tenants.py` near `RateLimitsUpsertRequest`
- [x] **D-DAY0-C**: 2 edit-target source files present (`rate_limit_config_store.py`, `api/v1/admin/tenants.py`)
- [x] **D-DAY0-D**: test dir paths — confirm `backend/tests/integration/api/` (US-1) + decide US-2 location (`tests/unit/platform_layer/tenant/` exists? else `tests/integration/...`)
  - Verify: `ls backend/tests/unit/platform_layer/tenant/ 2>/dev/null; ls backend/tests/integration/api/test_admin_tenant_rate_limits*.py`

#### Prong 2 — Content Verify
- [x] **D-DAY0-E** (🔴 CRITICAL — shared-model constraint §2.4): confirm `RateLimitItem` is used by BOTH `RateLimitListResponse` (GET) AND `RateLimitsUpsertRequest` (PUT) → validator MUST go on `RateLimitsUpsertRequest` only
  - Verify: `grep -n "RateLimitItem\|RateLimitListResponse\|RateLimitsUpsertRequest" backend/src/api/v1/admin/tenants.py`
- [x] **D-DAY0-F** (🔴 CRITICAL — concurrent-default §2.3): confirm `DEFAULT_RATE_LIMITS` contains `{"label":"SSE connections","value":"50 concurrent"}` (the non-parsing display value the validator MUST accept)
  - Verify: read `tenants.py:1355-1359` + grep frontend `_fixtures.ts` for `concurrent`
- [x] **D-DAY0-G**: confirm `_VALUE_RE` + `_WINDOW_ALIASES` are reusable (module-private in store) by the new predicate in the SAME module
  - Verify: `grep -n "_VALUE_RE\|_WINDOW_ALIASES\|_LABEL_TO_RESOURCE" backend/src/platform_layer/tenant/rate_limit_config_store.py`
- [x] **D-DAY0-H**: confirm `replace_configs` silent-skip behavior (`if parsed is None: continue`) — the gap being closed (so validation happens BEFORE replace_configs, which keeps its fail-open skip for migration/runtime consistency)
  - Verify: read `rate_limit_config_store.py:181-188`
- [x] **D-DAY0-I** (US-2 premise): confirm counter `_WINDOW_TO_SECONDS` keys == store `_WINDOW_ALIASES` keys (validity agreement)
  - Verify: `grep -n "_WINDOW_TO_SECONDS\|_WINDOW_ALIASES" backend/src/platform_layer/tenant/rate_limit_counter.py backend/src/platform_layer/tenant/rate_limit_config_store.py`
- [x] **D-DAY0-J**: confirm `field_validator` import availability in `tenants.py` (pydantic already imported? Sprint 57.54/57.56 added field_validator elsewhere)
  - Verify: `grep -n "from pydantic import\|field_validator" backend/src/api/v1/admin/tenants.py`

#### Prong 3 — Schema Verify
- [ ] **N/A** — no DB schema change, no migration (pure validation logic); `check_rls_policies` 20 tables unchanged

#### Day 0 Drift Catalog + go/no-go
- [x] **Catalog findings** in `progress.md` Day 0 entry — 10 checks (8 GREEN + 2 NOTABLE; 0 CRITICAL-blocker)
- [x] **Decide go/no-go** — ~0% shift → **GO for Day 1** (all premises confirmed; field_validator already imported = micro-simplification; 0 plan amendments)

### 0.9 Branch + Day 0 commit
- [x] **Create feature branch** `feature/sprint-57-61-rate-limits-syntax-validation` (from main `e71608f0`)
- [x] **Day 0 commit** (plan + checklist + progress.md Day 0 entry) ✅ `6bf23e63`

---

## Day 1 — Implementation (Agent-Delegated: yes — single agent)

### 1.1 US-1 — PUT-time syntax validation (422 instead of silent drop)
- [x] **EDIT** `rate_limit_config_store.py` — NEW `_CONCURRENCY_RE` + `is_recognized_rate_limit_value(value) -> tuple[bool, str|None]` (reuses `_VALUE_RE` + `_WINDOW_ALIASES`); MHist
- [x] **EDIT** `api/v1/admin/tenants.py` — NEW `field_validator("items")` on `RateLimitsUpsertRequest` (label non-empty + `is_recognized_rate_limit_value`) → ValueError → 422 per-item reason; import; MHist
- [x] **NEW** `test_admin_tenant_rate_limits_syntax_validation.py` (~8-10): garbage/unsupported-window/`0 / min`/empty/non-numeric/empty-label → 422; rate + `N concurrent` + DEFAULT round-trip → 200 + persisted; multi-tenant; GET unaffected
- [x] **Verify**: validator on `RateLimitsUpsertRequest` only (GET regression test green); DEFAULT_RATE_LIMITS verbatim round-trip → 200

### 1.2 US-2 — Parser-consistency guard
- [x] **NEW** `test_rate_limit_parser_consistency.py` (~4-6 matrix): RATE_OK → store/counter not-None + validator True; RATE_BAD+GARBAGE → all reject; CONCURRENCY → validator True + store/counter None (documented asymmetry); every window alias covered
- [x] **Verify**: test fails loudly if counter/store window-alias keys diverge

### 1.3 Day 1 Validation Sweep — ALL GREEN
- [x] **pytest full**: 1848 → **1887** (+39: 16 US-1 integration + 23 US-2 unit; 0 regressions)
- [x] **mypy `src/ --strict`**: 0 errors / 317 files (CI parity backend-ci.yml:152)
- [x] **9/9 V2 lints** (incl. `check_rls_policies` 20 tables unchanged + `check_llm_sdk_leak`)
- [x] **Vitest 675 unchanged** (0 frontend files touched)
- [x] **HEX_OKLCH baseline 48** + DUAL CLEAN 22/22 PARITY 17 consec
- [x] **LLM SDK leak 0** + black/isort/flake8 clean

### 1.4 Day 1 commit
- [x] **Commit all Day 1 work** ✅ `093a161d`

---

## Day 2 — Closeout (parent assistant)

### 2.1 Final Validation Sweep
- [x] **Re-run Day 1.3 checks** sanity ✅ (mypy `src/ --strict` 0/317 + 9/9 V2 lints + git diff confirms only 2 backend src files vs main, 0 frontend; full pytest 1887 Day-1.3 authoritative, source byte-identical to `093a161d`)
- [x] **mockup-fidelity DUAL CLEAN 22/22 PARITY 17 consecutive 57.45-57.61** (0 frontend touched)

### 2.2 Retrospective (Q1-Q6; Q7 N/A SKIP — feature ship NOT spike)
- [x] **NEW** `retrospective.md` (Q1-Q6 + calibration `mechanical-greenfield-design-decisions` 0.65 3rd validation 1st backend-only ~0.74 BELOW band KEEP + AD closure; Q7 N/A SKIP 10th consecutive)

### 2.3 sprint-workflow.md updates
- [x] MHist 1-line 57.61 entry + `medium-backend` 0.80 12th data point (~0.48; 12-pt mean ~0.62) + `mechanical-greenfield-design-decisions` 0.65 3rd validation (1st backend-only ~0.74 BELOW band) appended to agent_factor sub-class line

### 2.4 PROMOTIONS (check thresholds)
- [x] Confirmed: **no AD reaches codify threshold** this sprint — Prong promotions already codified 57.57+57.60; the 2 NEW ADs (`AD-AgentFactor-DesignDecisions-BackendOnly-Variant-Watch` + `AD-AgentDelegate-DevStack-Precheck`) are single-data-point

### 2.5 Memory + index
- [x] **NEW** `memory/project_phase57_61_rate_limits_syntax_validation.md` (user-home)
- [x] **EDIT** `memory/MEMORY.md` — quality pointer (prepended above 57.60 entry)

### 2.6 CLAUDE.md (navigator-only)
- [x] Current Sprint row (L73) + Last Updated footer (L628) → 57.61

### 2.7 next-phase-candidates.md
- [x] Sprint 57.61 Carryover section + `**Updated**:` header (57.60 demoted to `**Previous Updated**:`): SyntaxValidation CLOSED + 6 carryovers (Alerting / DuplicateResource / ClientSide-Polish / Parser-Extract / BackendOnly-Variant-Watch / DevStack-Precheck; Tier-3 0.45 defers Sprint 57.62)

### 2.8 CHANGE-029 record
- [x] **NEW** `CHANGE-029-sprint-57-61-rate-limits-syntax-validation.md` (feature — NEW 422 validation contract)

### 2.9 PR + merge (user action)
- [ ] Push branch + open PR (title: `feat(rate-limits, sprint-57-61): PUT-time syntax validation — close AD-RateLimits-SyntaxValidation-Phase58`)
- [ ] Wait CI (5 required green) → user merge → branch cleanup

### 2.10 Final closeout
- [x] Day 2 commit (all docs) ✅ `e1b9c2ff` (7 in-repo docs; memory user-home outside repo)
- [ ] Verify working tree clean on main after merge
- [ ] Mark Sprint 57.61 CLOSED in next-phase-candidates.md

---

## Open items / 🚧 Deferred (updated end of Day 0 三-Prong)

(Only `[ ]` → `[x]` allowed; never delete unchecked. 🚧 markers acceptable with reason.)
