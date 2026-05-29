# Sprint 57.60 Progress

**Sprint**: 57.60 — RateLimits MetaData Cleanup (close `AD-RateLimits-MetaData-Cleanup-Phase58`)
**Branch**: `feature/sprint-57-60-rate-limits-metadata-cleanup` (from main `4ad51828`)
**Class**: `medium-backend` 0.80 / agent-delegated yes / agent-factor `mechanical-pattern-reuse-heavy` 0.30

---

## Day 0 — Plan + Checklist + 三-Prong Verify (2026-05-29)

### Artifacts
- `sprint-57-60-plan.md` v1 (9-section; user-approved 2026-05-29)
- `sprint-57-60-checklist.md` v1
- This progress.md

### Day 0 三-Prong Verify — 14 checks (11 GREEN + 3 NOTABLE/DRIFT + 0 CRITICAL-blocker)

#### Prong 1 — Path Verify
- **D-DAY0-A** ✅ GREEN — `0020_*` does NOT exist (`ls versions | grep 0020` empty); head = `0019_rate_limit_configs`
- **D-DAY0-B** ✅ GREEN — 3 edit-target source files present (`admin/tenants.py`, `middleware/rate_limit.py`, `tool_rate_limit_gate.py`)
- **D-DAY0-C** ✅ GREEN — `rate_limit_config_store.py` present (`project_config_to_item` module-level helper used at all 4 read sites)
- **D-DAY0-D** ✅ GREEN — 57.59 test files present (`test_admin_tenant_rate_limits_table.py`, `test_rate_limit_usage_persistence.py`)

#### Prong 2 — Content Verify
- **D-DAY0-E** ✅ 🔴 CRITICAL GREEN (fallback-removal safety invariant §2.6 R1) — `0019.upgrade()` runs `SELECT id, "metadata" FROM tenants WHERE "metadata" ? 'rate_limits'` **unconditionally** (no flag-gate, no skip). Every tenant carrying parseable items → config rows inserted. Only UNPARSEABLE items ("50 concurrent", malformed, non-positive) are skipped (fail-open) — those have NO enforceable config representation regardless. → removing the meta_data fallback loses no enforceable config. **GO.**
- **D-DAY0-F** ✅ GREEN — 5 removal-site boundaries confirmed:
  - #1 GET `list_tenant_rate_limits` L1389-1396 (`else:` block: meta_raw → DEFAULT); after: `if configs: raw=[...] else: raw=list(DEFAULT_RATE_LIMITS)`
  - #2 usage GET `get_rate_limits_usage` L1601-1606 (else: meta_raw → DEFAULT); same shape as #1
  - #3 middleware `_load_rate_limits` L188-196 (select Tenant + meta_data → `[]`); after: `if configs: return [...]` then `return []`
  - #4 gate `_load_tool_limits` L136-144 (else: select Tenant + meta_data → `{}`); after: `raw = [project_config_to_item(c) for c in configs]` (empty list → empty dict via loop)
  - #5 PUT `upsert_tenant_rate_limits` L1492-1497 (dual-write to meta_data)
- **D-DAY0-G** ⚠️ **DRIFT** (plan §4.4 named only 2 test files) — a **3rd test file** seeds `meta_data["rate_limits"]` + asserts read/write of it: `test_admin_tenant_rate_limits.py` (Sprint 57.48-era):
  - L131 `test_list_rate_limits_applies_tenant_override` — seeds meta_data, asserts GET honours it (will break: GET now → DEFAULT)
  - L163 `test_list_rate_limits_tenant_isolation` — seeds meta_data
  - L224 / L245 / L323-324 — PUT asserts `row.meta_data["rate_limits"] == payload_items` (will break: PUT no longer writes meta_data)
  - **Action**: CONVERT (not delete) — re-point to seed the config table for override tests, and assert PUT writes config table + does NOT write meta_data. Added to plan §5 File Change List + §8 R2 (Day 0 drift annotation). `test_rate_limit_config_migration.py` (57.59) also seeds meta_data BUT tests `0019` in isolation (valid — not converted; does not run `0020`).
  - **Still to enumerate at Day 1**: 57.58-era `test_admin_tenant_rate_limits_usage.py` / `test_rate_limit_middleware.py` / `test_tool_rate_limit_enforce.py` — Day 1 agent greps each for meta_data-seeding + converts any fallback-dependent assertion.
- **D-DAY0-H** ✅ GREEN — `0019` inline parser confirmed: `_LABEL_TO_RESOURCE` (3 entries: api_requests/tool_calls/sse_connections), `_WINDOW_ALIASES` (canonical sec/min/hour/day), value regex `N / unit`. `0020` downgrade inverse `_inline_project(resource_type, window_type, quota)` → `{"label": <reverse-label>, "value": f"{quota} / {window_type}"}`; reverse-label map = invert `_LABEL_TO_RESOURCE` + custom slug `.replace("_"," ").title()` (lossy, dev-only — §8 R3).
- **D-DAY0-I** ✅ GREEN — fallback-terminal asymmetry confirmed: GET (#1) + usage GET (#2) → `DEFAULT_RATE_LIMITS` (display); middleware (#3) → `[]` + gate (#4) → `{}` (enforcement, no phantom defaults). Preserved post-cleanup (only meta_data middle layer dropped).
- **D-DAY0-J** ⚠️ NOTABLE (orphan ripple, Karpathy §3 — clean only this-sprint orphans):
  - GET #1 + usage GET #2: `tenant = await _load_tenant_or_404(...)` becomes value-unused after fallback removal, BUT the **call must stay** (404 contract). → discard binding (`await _load_tenant_or_404(...)` without assignment) — verify no other `tenant.` use in each fn.
  - middleware #3 + gate #4: `select(Tenant)` + `Tenant` import + `scalar_one_or_none` become orphan if no other use → drop import (flake8 F401 will catch).
  - **PUT #5 ripple**: removing dual-write (L1495-97) orphans `await db.flush()` (L1499 — was bumping `tenant.updated_at` via the meta_data mutation) + `await db.refresh(tenant)` (L1517). With no tenant mutation, both are vestigial. Day 1 agent: drop `refresh(tenant)`; keep `replace_configs` + `append_audit` + `commit`; verify `flush` necessity (config rows persisted by `replace_configs`/`commit`).

#### Prong 3 — Schema Verify (data-only migration; 0 new table; no RLS change)
- **D-DAY0-K** ✅ GREEN — head = `0019_rate_limit_configs` → next = `0020`; down_revision for `0020` = `"0019_rate_limit_configs"`
- **D-DAY0-L** ✅ GREEN — `rate_limit_configs` columns (`id, tenant_id, resource_type String(64), window_type String(32), quota Integer, created_at, updated_at`); downgrade SELECT `tenant_id, resource_type, window_type, quota`
- **D-DAY0-M** ✅ 🔴 KEY GREEN (= `AD-Day0-Prong3-Physical-Column-Read`) — tenants JSONB **physical column is `"metadata"`** (ORM `meta_data` via `mapped_column("metadata", ...)` in `identity.py`). `0019` raw SQL already uses `"metadata"`. `0020` raw SQL MUST use `"metadata"`: upgrade `UPDATE tenants SET "metadata" = "metadata" - 'rate_limits' WHERE "metadata" ? 'rate_limits'`; downgrade `jsonb_set("metadata", '{rate_limits}', ...)`.
- **D-DAY0-N** ✅ GREEN — data-only migration (no DDL / no new table) → no RLS policy change; `check_rls_policies` 20 tables unchanged.

### Go/No-Go
**GO for Day 1.** 0 CRITICAL-blocker. Scope shift: +1 test file conversion (`test_admin_tenant_rate_limits.py`, ~+0.5 hr) + PUT flush/refresh orphan cleanup (minor) = **< 20%** → continue with §Risks updated (R2 enumerates, R5 covers orphan ripple). 3 plan micro-amendments applied (§5 +1 test file; §8 R2 drift note; D-DAY0-M physical-column reaffirmed in §4.3).

### Day 0 commit
- (pending) plan v1 + checklist v1 + this progress.md Day 0 entry

---

## Day 1 — Implementation (2026-05-29 — single code-implementer agent `rl-metadata-cleanup`, 26th consecutive)

### US-1 — Remove meta_data read-fallback (4 sites) + PUT dual-write (1 site)
- 5 sites removed (config → terminal, meta_data middle layer dropped):
  - #1 GET `list_tenant_rate_limits` → `config → DEFAULT`; orphan: `tenant =` binding → bare `await _load_tenant_or_404(...)` (404 kept)
  - #2 usage GET `get_rate_limits_usage` → `config → DEFAULT`; `tenant` binding dropped (rest uses `tenant_id`/`RateLimit`)
  - #3 middleware `_load_rate_limits` → `config → []`; orphans cleaned: `select`, `Tenant` imports
  - #4 gate `_load_tool_limits` → `config → {}` (empty list → empty dict via loop); orphans cleaned: `select`, `Tenant` imports
  - #5 PUT `upsert_tenant_rate_limits` → removed 3-line dual-write; dropped `tenant` binding + `db.refresh(tenant)` + redundant `db.flush()` (confirmed `replace_configs` flushes internally; `commit` persists). Audit + `commit` kept.
- Stale `AD-RateLimits-MetaData-Cleanup-Phase58` inline comments/docstrings → past-tense; MHist added to 3 source files.

### US-1 test conversions (Never-Delete honored)
- `test_admin_tenant_rate_limits.py` (57.48): 2 GET-override tests re-seeded to config table; 2 PUT ORM `meta_data` asserts flipped to config-rows + `"rate_limits" not in meta_data`; +1 NEW `test_list_rate_limits_ignores_stale_meta_data`
- `test_admin_tenant_rate_limits_table.py` (57.59): GET-fallback test → asserts DEFAULT (stale meta_data ignored)
- `test_rate_limit_usage_persistence.py` (57.59): middleware-fallback test → asserts `[]`
- `test_admin_tenant_rate_limits_usage.py` (57.58): seeds config table instead of meta_data
- `test_rate_limit_middleware.py` / `test_tool_rate_limit_enforce.py`: NO conversion (monkeypatch `_load_rate_limits` / patch gate read — no meta_data dependency)
- `test_rate_limit_config_migration.py` (57.59): untouched (tests `0019` in isolation — legitimately seeds meta_data)

### US-2 — Alembic `0020` clear stored JSONB + reverse-populate downgrade
- NEW `0020_clear_rate_limits_meta_data.py` (down_revision `0019_rate_limit_configs`): `upgrade()` strips `"metadata" - 'rate_limits'` (idempotent), `downgrade()` reverse-populates via inline `_inline_project` (inverse of `0019._parse_item`; lossy custom labels, dev-only). Dep-light (no store import); physical `"metadata"` column (D-DAY0-M).
- NEW `test_clear_rate_limits_meta_data_migration.py` (7 tests incl. downgrade reverse-populate + round-trip)

### Day 1 deviations / findings
- **`CAST(:items AS jsonb)` NOT `:items::jsonb`**: the `::jsonb` cast shorthand collides with asyncpg named-param parsing (test path); `CAST(...)` is equivalent SQL working under both psycopg (Alembic) + asyncpg. Applied to migration + test. Verified via live `0019→0020→0019→0020` round-trip.
- **`db.flush()` in PUT was redundant** (not needed) — `replace_configs` flushes internally; dropped safely.
- **Pre-existing (not this sprint)**: `mypy --strict .` (whole-dir) reports a duplicate-`conftest` collection error (two `tests/integration/{api,agent_harness}/conftest.py` lack `__init__.py`); present on `main` since Sprint 57.53. **NOT a CI concern** — CI runs `mypy src/ --strict` (backend-ci.yml:152), which is clean (0/317). Flagged as a Phase 58+ candidate, outside this sprint's scope.

### Day 1.3 Validation Sweep — ALL GREEN (parent authoritative)
- pytest **1848 passed / 4 skip** (+8 vs 1840 baseline; 6 new migration tests + 2 new ignore-stale tests; 0 regressions)
- mypy **`src/ --strict` 0 errors / 317 files** (CI parity per backend-ci.yml:152)
- **9/9 V2 lints** green (incl. `check_rls_policies` 20 tables unchanged — data-only migration + `check_llm_sdk_leak`)
- black/isort/flake8 clean (574 files)
- Alembic `up → down → up` clean on live DB
- 0 frontend files touched → Vitest 675 unaffected; HEX_OKLCH baseline 48 unchanged; DUAL CLEAN 22/22 PARITY 16 consec

### Day 1 commit
- (pending — parent commits all Day 1 work after this entry)

## Day 2 — Closeout (pending)
