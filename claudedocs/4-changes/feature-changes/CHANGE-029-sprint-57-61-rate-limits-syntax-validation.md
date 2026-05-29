# CHANGE-029: RateLimits PUT-time Syntax Validation (Sprint 57.61)

**Date**: 2026-05-29
**Sprint**: 57.61
**Scope**: Cat 9 (admin endpoint validation) + `platform_layer/tenant` (value-shape predicate)
**Change Type**: New Feature (NEW 422 validation contract — not a bug patch; the silent-drop gap is closed by adding a write-time rejection contract)

## Problem

The RateLimits admin write path silently dropped malformed values. `PUT /admin/tenants/{tid}/rate-limits` → `RateLimitsUpsertRequest` → `RateLimitConfigStore.replace_configs` parses each `{label, value}` item via `parse_config_item` and **silently skips** any that return `None` (`if parsed is None: continue`, `rate_limit_config_store.py:184`). So `PUT {"items":[{"label":"API requests","value":"garbage"}]}` returned **200 OK**, but the item was dropped → the next `GET` returned `DEFAULT_RATE_LIMITS` (config table empty) → the admin's setting vanished with no error. A malformed rate limit was indistinguishable from a successful save.

## Root Cause

`replace_configs`'s fail-open skip is correct for the migration/runtime path (an unparseable legacy item has no enforceable representation, so skipping it is safe there). But the **admin write boundary** never validated input before reaching it — there was no write-time contract distinguishing "a value the admin meant to set" from "a value the runtime can't enforce". The gap was a named Phase 58.x carryover (`AD-RateLimits-SyntaxValidation-Phase58`), now easier post-57.59/57.60 (config table has typed `quota`/`window_type` columns; `meta_data` fallback retired).

## Solution

PUT-time validation at the request boundary, 422 on malformed, while leaving `replace_configs`'s fail-open skip intact (migration/runtime consistency).

- **NEW value-shape predicate** (`platform_layer/tenant/rate_limit_config_store.py`): `is_recognized_rate_limit_value(value) -> tuple[bool, str | None]` + module-private `_CONCURRENCY_RE = re.compile(r"^\s*[\d,]+\s+concurrent\s*$", re.IGNORECASE)`. **Reuses** the existing `_VALUE_RE` (L86) + `_WINDOW_ALIASES` (L75) — **no 4th rate-regex copy** (the only NEW pattern is `_CONCURRENCY_RE`). Returns `(True, None)` for an enforceable rate `N / <sec|min|hour|day>` OR a display-only `N concurrent`; `(False, reason)` for empty / unsupported-window / non-positive / non-numeric / unrecognized shape. The predicate is deliberately **broader** than `parse_config_item` (which recognizes only the enforceable rate) because the admin UI legitimately carries the non-enforceable `"50 concurrent"` default — see below.
- **NEW `field_validator("items")`** on `RateLimitsUpsertRequest` (`api/v1/admin/tenants.py:1421` — the **REQUEST** model, **NOT** the shared `RateLimitItem` at L1341 which also feeds GET `RateLimitListResponse` + a 3rd model at L1391; D-DAY0-E). For each item: `label` non-empty AND `is_recognized_rate_limit_value(value)` → on any failure, collect a per-item message (`item[i] (label = value): reason`) and raise `ValueError` → FastAPI returns **422** (`loc: ["body","items"]`). `field_validator` was already imported at L85 (Sprint 57.54/57.56); only the predicate import was new.
- **`"50 concurrent"` round-trip preserved** (the critical edge): `DEFAULT_RATE_LIMITS` (`tenants.py:1355-1359`) carries `{"label":"SSE connections","value":"50 concurrent"}` — display-only, intentionally not time-windowed/not enforced. A naive "reject everything `parse_config_item` returns None for" validator would reject the verbatim load-defaults→edit→save round-trip. `_CONCURRENCY_RE` accepts it; an explicit defaults-round-trip acceptance test guards it.
- **US-2 parser-consistency guard** (`backend/tests/unit/platform_layer/tenant/test_rate_limit_parser_consistency.py`): asserts the three `{label, value}` parse copies agree — for enforceable-rate inputs `parse_config_item` (store) is-not-None ⟺ `parse_rate_limit_item` (counter) is-not-None ⟺ validator rate-branch True; for concurrency inputs the validator accepts but both parsers return None (documented intentional asymmetry — not enforced); for garbage all three reject. Includes an explicit `_WINDOW_TO_SECONDS` (counter) == `_WINDOW_ALIASES` (store) key-set equality assertion so a future edit adding a window to one table only fails loudly.

## Verification

- pytest 1848 → **1887** (+39: 16 US-1 integration + 23 US-2 unit) + 4 skip + 0 regressions
- mypy `src/ --strict` **0 / 317 files** (CI parity backend-ci.yml:152)
- **9/9 V2 lints** green (incl. `check_rls_policies` 20 tables unchanged — no schema change + `check_llm_sdk_leak` 0) / black + isort + flake8 clean
- 0 frontend touched → Vitest 675 unaffected / HEX_OKLCH baseline 48 / mockup-fidelity DUAL CLEAN 22/22 PARITY preserved **17 consecutive sprints 57.45-57.61**
- No Alembic migration (pure validation logic; no schema change)
- Edge cases test-covered: `foo`/`100 bananas`/`concurrent` (shape) / `50 / week` (unsupported window) / `0 / min` + `-5 / min` (non-positive) / `abc / min` (non-numeric) / `` + empty-label → 422; enforceable rate + `N concurrent` + `DEFAULT_RATE_LIMITS` verbatim round-trip → 200 + persisted; GET unaffected; multi-tenant isolation

## Impact

- Backend: the RateLimits write path is now **fail-loud at the boundary** — a malformed value returns 422 with an actionable per-item reason instead of a silent drop on the next GET. Validation is purely additive on the write path (0 existing tests needed conversion).
- Frontend: no functional change. The Sprint 57.57 `useRateLimitsSave` error path already surfaces the mutation error → the 422 message string shows inline (frontend verify-only; nicer per-item field highlighting deferred to `AD-RateLimits-SyntaxValidation-ClientSide-Polish`).
- Phase 58.x RateLimits arc: write path validated (57.57 WRITE + 57.58 RuntimeEnforcement + 57.59 two-table + 57.60 cleanup + **57.61 syntax-validation**). Remaining extensions (Alerting / DuplicateResource / ClientSide-Polish / Parser-Extract) are feature/hygiene, not architectural debt.
- Calibration: `mechanical-greenfield-design-decisions` 0.65 3rd validation (1st backend-only) landed ~0.74 BELOW band → KEEP 0.65 single-data-point caution + NEW `AD-AgentFactor-DesignDecisions-BackendOnly-Variant-Watch` (counterfactual `-port-style` 0.45 → ~1.06 IN band; backend-only validator runs faster than the backend+frontend pair the 0.65 was calibrated on).
- PR: (pending) `feature/sprint-57-61-rate-limits-syntax-validation`
- Commits: `6bf23e63` Day 0 + `093a161d` Day 1 + Day 2 closeout (this record) pending
