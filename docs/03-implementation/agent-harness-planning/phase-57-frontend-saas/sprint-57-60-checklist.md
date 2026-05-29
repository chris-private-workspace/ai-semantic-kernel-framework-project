# Sprint 57.60 — Checklist

Plan: [`sprint-57-60-plan.md`](./sprint-57-60-plan.md)

**Class**: `medium-backend` 0.80 (single-domain backend cleanup; surgical fallback removal + 1 data-cleanup migration)
**Agent-delegated**: yes (single code-implementer agent — small surgical sprint)
**Agent-factor**: `mechanical-pattern-reuse-heavy` 0.30 (5 near-identical fallback removals; Day 0 may refine to 0.45 `port-style`)
**Template**: mirrors `sprint-57-59-checklist.md` Day 0-2 structure

---

## Day 0 — Plan + 三-Prong Verify

### 0.1 Plan + Checklist Drafting
- [x] **Draft `sprint-57-60-plan.md` v1** (9-section; scope cleanup of 57.59 transitional meta_data layer)
- [x] **Draft `sprint-57-60-checklist.md` v1** (this file)
- [x] **User approve plan v1** — gate before Day 0 三-Prong ✅ (approved 2026-05-29)

### 0.8 Day 0 三-Prong Verify (Step 2.5 mandatory — Content Prong CRITICAL: fallback-removal safety invariant)

#### Prong 1 — Path Verify
- [x] **D-DAY0-A**: `0020_clear_rate_limits_meta_data.py` NOT exist yet (NEW)
  - Verify: `ls backend/src/infrastructure/db/migrations/versions/ | grep 0020` → empty
- [x] **D-DAY0-B**: 3 edit-target source files present (`api/v1/admin/tenants.py`, `platform_layer/middleware/rate_limit.py`, `platform_layer/tenant/tool_rate_limit_gate.py`)
- [x] **D-DAY0-C**: `platform_layer/tenant/rate_limit_config_store.py` present (`_project_config_to_item` = reference for `0020` downgrade inline projection)
- [x] **D-DAY0-D**: 57.59 test files present (`test_admin_tenant_rate_limits_table.py`, `test_rate_limit_usage_persistence.py`)

#### Prong 2 — Content Verify
- [x] **D-DAY0-E** (🔴 CRITICAL — fallback-removal safety invariant §2.6 R1): `0019` `upgrade()` data-migration reads ALL tenants with `meta_data ? 'rate_limits'` unconditionally (no skip / no flag-gate) → confirm every existing config row was migrated to `rate_limit_configs` before removing the fallback
  - Verify: read `0019_rate_limit_configs.py` `upgrade()` data-migration loop
- [x] **D-DAY0-F**: exact fallback block shape + line numbers at 4 read sites (#1 GET L1390-91 / #2 usage GET L1602 / #3 middleware L188-193 / #4 gate L136-141) + dual-write block (#5 PUT L1492-97); confirm removal boundaries
- [x] **D-DAY0-G**: enumerate ALL tests seeding `meta_data["rate_limits"]` (so none break silently)
  - Verify: `grep -rn "meta_data.*rate_limits\|rate_limits.*meta_data" backend/tests/`
- [x] **D-DAY0-H**: `_inline_parse` in `0019` (label→resource_type + "N / unit"→quota,window_type) → derive inverse `_inline_project` (resource_type,window_type,quota → {label, value "N / unit"}) for `0020` downgrade
- [x] **D-DAY0-I**: `DEFAULT_RATE_LIMITS` shape (`tenants.py:1354`) + confirm GET display paths fall to DEFAULT while enforcement paths (middleware/gate) fall to `[]` (asymmetry preserved)
- [x] **D-DAY0-J**: orphan check (Karpathy §3) — after fallback removal, is the `tenant`/`meta_data` ORM fetch still referenced at each of the 4 read sites + PUT? (drop only orphans THIS sprint creates)

#### Prong 3 — Schema Verify (data-only migration — no new table, no RLS change)
- [x] **D-DAY0-K**: Alembic head — `ls backend/src/infrastructure/db/migrations/versions/ | sort -V | tail -3` → confirm head = `0019` → next = `0020`
- [x] **D-DAY0-L**: `rate_limit_configs` columns (`tenant_id, resource_type, window_type, quota`) for the `0020` downgrade reverse-projection SELECT
- [x] **D-DAY0-M**: JSONB ops availability — `meta_data - 'rate_limits'` (minus-key) for upgrade + `jsonb_set` for downgrade; confirm pattern precedent (Sprint 57.56 quota_overrides `dict()` ORM path or raw SQL elsewhere)
- [x] **D-DAY0-N**: no RLS policy change (data-only migration, 0 new table) → `check_rls_policies` 20 tables unchanged

#### Day 0 Drift Catalog + go/no-go
- [x] **Catalog findings** in `progress.md` Day 0 entry — 14 checks (11 GREEN + 3 NOTABLE/DRIFT + 0 CRITICAL-blocker)
- [x] **Decide go/no-go** — ≤20% shift → **GO for Day 1** (3 plan micro-amendments: §4.3 physical-column `"metadata"` + §5 +1 test file `test_admin_tenant_rate_limits.py` + §8 R2 drift note)

### 0.9 Branch + Day 0 commit
- [x] **Create feature branch** `feature/sprint-57-60-rate-limits-metadata-cleanup` (from main `4ad51828`)
- [x] **Day 0 commit** (plan + checklist + progress.md Day 0 entry) ✅ `621afe72`

---

## Day 1 — Implementation (Agent-Delegated: yes — single agent)

### 1.1 US-1 — Remove meta_data read-fallback (4 sites) + PUT dual-write (1 site)
- [x] **EDIT** `api/v1/admin/tenants.py` — remove GET fallback (#1) → config → DEFAULT; orphan `tenant` binding → bare `await _load_tenant_or_404(...)`
- [x] **EDIT** `api/v1/admin/tenants.py` — remove usage GET fallback (#2) → config → DEFAULT; `tenant` binding dropped
- [x] **EDIT** `api/v1/admin/tenants.py` — remove PUT dual-write (#5) → config write only; dropped `tenant` binding + `db.refresh` + redundant `db.flush`; audit + commit kept
- [x] **EDIT** `platform_layer/middleware/rate_limit.py` — `_load_rate_limits` remove fallback (#3) → config → `[]`; dropped orphan `select`/`Tenant` imports
- [x] **EDIT** `platform_layer/tenant/tool_rate_limit_gate.py` — `_load_tool_limits` remove fallback (#4) → config → `{}`; dropped orphan `select`/`Tenant` imports
- [x] **EDIT** file-header MHist (3 source files) + inline AD comments → past-tense (AD now closed)
- [x] **CONVERT** `test_admin_tenant_rate_limits_table.py` — fallback-path assertion → config-only (DEFAULT)
- [x] **CONVERT** `test_rate_limit_usage_persistence.py` — middleware-fallback assertion → config-only (`[]`)
- [x] **CONVERT (Day 0 D-DAY0-G drift)** `test_admin_tenant_rate_limits.py` (57.48) — 2 GET-override → config table; 2 PUT meta_data asserts → config-rows + `"rate_limits" not in meta_data`; +1 NEW `test_list_rate_limits_ignores_stale_meta_data`
- [x] **CONVERT** `test_admin_tenant_rate_limits_usage.py` (57.58) — seeds config table instead of meta_data
- [x] **NEW** ignore-stale-meta_data pytest: seed meta_data + empty config → GET returns DEFAULT (not meta_data) + PUT does not write meta_data
- [x] **Verify**: pytest US-1 green + API shapes unchanged

### 1.2 US-2 — Alembic `0020` clear stored JSONB + reverse-populate downgrade
- [x] **NEW** `0020_clear_rate_limits_meta_data.py` — upgrade strips `"metadata" - 'rate_limits'` (idempotent, physical column) + downgrade inline `_inline_project` `rate_limit_configs` → `meta_data["rate_limits"]`; `CAST(:items AS jsonb)` (asyncpg compat); dep-light
- [x] **NEW** `test_clear_rate_limits_meta_data_migration.py` (7 tests): upgrade clears key + idempotent + downgrade reverse-populates + multi-tenant + round-trip
- [x] **Verify**: migration `up → down → up` clean on live DB (head `0020`) + `check_rls_policies` 20 tables unchanged

### 1.3 Day 1 Validation Sweep — ALL GREEN
- [x] **pytest full**: 1840 → **1848** (+8; 0 regressions)
- [x] **mypy `src/ --strict`**: 0 errors / 317 files (CI parity per backend-ci.yml:152)
- [x] **9/9 V2 lints** (incl. `check_rls_policies` 20 tables + `check_llm_sdk_leak`)
- [x] **Vitest 675 unchanged** (0 frontend files touched — API shapes preserved)
- [x] **HEX_OKLCH baseline 48** + DUAL CLEAN 22/22 PARITY 16 consec
- [x] **LLM SDK leak 0** + black/isort/flake8 clean

### 1.4 Day 1 commit
- [x] **Commit all Day 1 work** ✅ `416c9f84`

---

## Day 2 — Closeout (parent assistant)

### 2.1 Final Validation Sweep
- [x] **Re-run Day 1.3 checks** sanity ✅ (pytest 1848 / mypy src 0/317 / 9/9 V2 lints / black-isort-flake8 clean / Alembic up→down→up clean)
- [x] **mockup-fidelity DUAL CLEAN 22/22 PARITY 16 consecutive 57.45-57.60** ✅ (0 frontend touched)

### 2.2 Retrospective (Q1-Q6; Q7 N/A SKIP — refactor/cleanup NOT spike)
- [x] **NEW** `retrospective.md` ✅ (Q1-Q6 + calibration `mechanical-pattern-reuse-heavy` 0.30 1st forward application ~1.09 IN BAND + AD closure)

### 2.3 sprint-workflow.md updates
- [x] MHist 1-line + `medium-backend` 0.80 11th data point (~0.33; KEEP) + `mechanical-pattern-reuse-heavy` 0.30 §Active block forward-application data point (~1.09 IN BAND; KEEP)

### 2.4 PROMOTIONS (Prong codify — both confirmed 2 data points)
- [x] Codified BOTH into `sprint-workflow.md §Step 2.5`: Prong 2 +1 row `Claimed-but-nested-shape-mismatch` (`AD-Day0-Prong2-Nested-Shape-Read`; 57.58+57.59) + Prong 3 +1 row `Physical-column-vs-ORM-alias` (`AD-Day0-Prong3-Physical-Column-Read`; 57.59+57.60)

### 2.5 Memory + index
- [x] **NEW** `memory/project_phase57_60_rate_limits_metadata_cleanup.md` (user-home) ✅
- [x] **EDIT** `memory/MEMORY.md` — quality pointer ✅

### 2.6 CLAUDE.md (navigator-only)
- [x] Current Sprint row + Last Updated footer ✅

### 2.7 next-phase-candidates.md
- [x] Updated line (demote 57.59 → Previous) + NEW §57.60 Carryover section: MetaData-Cleanup CLOSED + 2 PROMOTIONS + carryovers (SyntaxValidation / Alerting / Tier-3 0.45 deferred 57.61 / NEW AD-Mypy-WholeDir-Conftest-Collision) ✅

### 2.8 REFACTOR-004 record
- [x] **NEW** `REFACTOR-004-sprint-57-60-rate-limits-metadata-cleanup.md` ✅

### 2.9 PR + merge (user action)
- [ ] Push branch + open PR (title: `refactor(rate-limits, sprint-57-60): retire transitional meta_data fallback + dual-write — close AD-RateLimits-MetaData-Cleanup-Phase58`)
- [ ] Wait CI (5 required green) → user merge → branch cleanup

### 2.10 Final closeout
- [ ] Day 2 commit (all docs)
- [ ] Verify working tree clean on main after merge
- [ ] Mark Sprint 57.60 CLOSED in next-phase-candidates.md

---

## Open items / 🚧 Deferred (updated end of Day 0 三-Prong)

(Only `[ ]` → `[x]` allowed; never delete unchecked. 🚧 markers acceptable with reason.)
