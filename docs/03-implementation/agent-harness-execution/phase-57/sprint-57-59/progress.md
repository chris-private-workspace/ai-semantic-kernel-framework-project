# Sprint 57.59 — Progress

**Goal**: Close AP-4 Potemkin via C1 two-table split — NEW `rate_limit_configs` + activate `rate_limits` usage table (`AD-RateLimits-Potemkin-Migration-Phase58`)
**Class**: `mixed-multidomain-bundle` 0.65 (SCOPE 3rd data point)
**Agent-factor**: `mixed-multidomain-bundle-mechanical` 0.65 (tier-3 **2nd validation**)
**Start date**: 2026-05-28

Plan: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-59-plan.md`
Checklist: `docs/03-implementation/agent-harness-planning/phase-57-frontend-saas/sprint-57-59-checklist.md`

---

## Day 0 — 2026-05-28

### Today's Accomplishments

- Plan v1 + checklist v1 drafted (9-section mirror 57.58); user approved 2026-05-28
- Branch `feature/sprint-57-59-rate-limits-potemkin-migration` created from main `5736e0a4`
- Day 0 三-Prong Verify executed (Path + Content + **Schema verify** — new table + data migration)

### Drift findings (15 checks — 12 GREEN + 3 🆕 NOTABLE + 1 🔴 minor; NO CRITICAL)

#### Prong 1 — Path Verify (all GREEN)

- ✅ **D-DAY0-A**: `0019_rate_limit_configs.py` not exist (Alembic head = `0018_tenant_settings_extension.py` → next = **0019**)
- ✅ **D-DAY0-B**: `platform_layer/tenant/rate_limit_config_store.py` NOT exist (Glob 0 results)
- ✅ **D-DAY0-C**: `RateLimitConfig` ORM NOT exist (`api_keys.py` `__all__ = ["ApiKey", "RateLimit"]`)
- ✅ **D-DAY0-D**: Sprint 57.58 re-point targets present (`rate_limit_counter.py` has `parse_rate_limit_item` + `RedisRateLimitCounter` + `check_and_increment` L200 + `peek` L248)

#### Prong 2 — Content Verify (GREEN + nested-shape lesson applied)

- ✅ **D-DAY0-E**: `parse_rate_limit_item(item: object) -> ParsedRateLimit | None` (L158) — parses `{label, value}` dict, returns `ParsedRateLimit` (resource/limit/window) or None (skip)
- ✅ **D-DAY0-F**: `RateLimitItem(BaseModel)` (`tenants.py:1333`) = `{label: str, value: str}` + `model_config = ConfigDict(from_attributes=True)` — confirmed by READING the Pydantic body (per `AD-Day0-Prong2-Nested-Shape-Read` lesson, NOT just grep)
- ✅ **D-DAY0-G** (see NOTABLE below): `RateLimit` usage ORM full schema read
- ✅ **D-DAY0-I**: `check_and_increment` (L200) + `peek` (L248) — write-through hook sites confirmed

#### Prong 3 — Schema Verify (CRITICAL prong; 3 NOTABLE)

- ✅ **D-DAY0-J**: Alembic head `0018` → next = **0019** (no collision)
- ✅ **D-DAY0-L**: `TenantScopedMixin` provides `tenant_id` + FK; `RateLimit` uses it → `RateLimitConfig` mirrors
- ✅ **D-DAY0-M**: `rate_limits` 0006 schema = the ORM (covered by D-DAY0-G)
- ✅ **D-DAY0-O**: data migration uses PostgreSQL JSONB `meta_data ? 'rate_limits'` key-existence operator (supported)

#### 🆕 NOTABLE / 🔴 findings

**🆕 D-DAY0-G — `rate_limits` usage table has `window_end` too (plan only mentioned `window_start`)**
- Full schema: `id` + `resource_type`(VARCHAR64) + `window_type`(VARCHAR32) + `quota`(Integer) + `used`(Integer default 0) + `window_start`(timestamptz NOT NULL) + **`window_end`(timestamptz NOT NULL)** + unique `(tenant_id, resource_type, window_type, window_start)` + index `idx_rate_limits_lookup (tenant_id, resource_type, window_end DESC)`
- **Implication**: US-3 Redis write-through must populate BOTH `window_start` AND `window_end` (window_end = window_start + window_seconds). Plan §4.5 updated to note window_end.

**🆕 D-DAY0-K — RLS in 0009 uses TWO policies per table (loop-based)**
- Pattern: `CREATE POLICY tenant_isolation_{tbl} ... USING (...)` + `CREATE POLICY tenant_insert_{tbl} ... WITH CHECK (...)` (both, for SELECT/UPDATE/DELETE isolation + INSERT check)
- **Implication**: 0019 migration adds BOTH `tenant_isolation_rate_limit_configs` (USING) + `tenant_insert_rate_limit_configs` (WITH CHECK) inline. `check_rls_policies` V2 lint expects this.

**🔴 D-DAY0-N — inline `parse_rate_limit_item` in Alembic migration (do NOT import)**
- `parse_rate_limit_item` lives in `rate_limit_counter.py` which imports Redis types (module-level). Importing the module into an Alembic migration risks pulling heavy/unstable deps.
- **Resolution**: INLINE the parse logic (label→resource_type + value→quota/window_type) directly in the 0019 migration `upgrade()`. Alembic migrations are historical snapshots — should be dep-light + stable even if app code later changes. Day 1 US-1 agent inlines.

### Scope shift assessment

- 0 CRITICAL; 3 NOTABLE refinements (window_end column + RLS double-policy + inline parse) = ~5% scope detail, NOT scope change
- **Go for Day 1** (≤20% shift; risks noted in plan §8)

### Plan v1.1 micro-amendments (audit trail)

1. §4.5 write-through: populate `window_end` (= window_start + window_seconds) in addition to window_start
2. §4.2 migration: add BOTH RLS policies (isolation USING + insert WITH CHECK) per 0009 pattern; migration number = **0019**
3. §4.2 migration: INLINE parse logic (do not import `parse_rate_limit_item`); dep-light Alembic convention

---

## Day 1 — 2026-05-28

### US-1 + US-2 — config table + ORM + migration + GET/PUT re-point (agent `rl-config-table`; 24th consecutive code-implementer)

✅ COMPLETE — 4 NEW + 4 EDIT; pytest 1819 → **1834** (+15); mypy 0; **`check_rls_policies` PASS (20 tables, +1)**; migration up/down/up clean (head `0019`).

**NEW**: `0019_rate_limit_configs.py` (CREATE + 2 RLS policies + inline-parse data migration) / `platform_layer/tenant/rate_limit_config_store.py` (`RateLimitConfigStore`) / `test_rate_limit_config_migration.py` (6 tests) / `test_admin_tenant_rate_limits_table.py` (9 tests)
**EDIT**: `api_keys.py` (+`RateLimitConfig` ORM + `__all__`) / `models/__init__.py` (export) / `admin/tenants.py` (GET/PUT re-point) / `api/conftest.py` (`RATE_LIMIT_CONFIG_%` sweep)

- `RateLimitConfig`: id (PgUUID) + tenant_id (FK CASCADE via TenantScopedMixin) + resource_type(64) + window_type(32) + quota(Int) + created/updated_at + unique `(tenant_id, resource_type, window_type)`
- Migration `0019`, `down_revision = "0018_tenant_settings_extension"` (verified)
- Data migration: additive; inline `_parse_item` mirrors `parse_rate_limit_item` (_LABEL_TO_RESOURCE + value regex + window aliases); de-dups last-wins; skips unparseable; meta_data NOT modified
- GET fallback chain: config table → meta_data → DEFAULT_RATE_LIMITS; PUT `replace_configs` (source of truth) + transitional dual-write to meta_data + audit preserved; API `{label,value}` shape UNCHANGED

### US-3 — runtime re-point + usage-table write-through (agent `rl-runtime-repoint`; 25th consecutive code-implementer)

✅ COMPLETE — 1 NEW + 6 EDIT; full suite 1834 → **1840** (+6); mypy 0; 9/9 V2 lints; `check_llm_sdk_leak` PASS (Cat 2 seam neutral). **AP-4 CLOSED**.

**EDIT**: `rate_limit_counter.py` (write-through + `_recover_from_table` + `window_type_for_seconds` + optional `session_factory` ctor) / `rate_limit.py` (`_load_rate_limits` config table) / `tool_rate_limit_gate.py` (config table) / `admin/tenants.py` (usage GET table-backed) / `api/main.py` (inject `get_session_factory`) / `test_rate_limit_middleware.py` (autouse monkeypatch-restore fixture; assertions preserved) / `agent_harness/conftest.py` (`RATE_USAGE_%` sweep)
**NEW**: `test_rate_limit_usage_persistence.py` (6 tests)

- Counter DB session: optional `session_factory` DI (None = pure-Redis dev/unit; main.py injects); singleton self-acquires session + sets RLS context
- window_start = floor(now to window boundary); window_end = window_start + window_seconds; upsert via `pg_insert.on_conflict_do_update` (`used = GREATEST`) — same-window requests update ONE row
- Write-through best-effort/fail-open (Redis decision taken BEFORE DB I/O; errors log + continue)
- Recovery: Redis cache miss → `_recover_from_table` replays still-open-window `used` from table

### Day 1 Drift findings

- **🔴 D-DAY1-1**: tenants JSONB physical column is `metadata` (ORM attr `meta_data` aliases via `mapped_column("metadata", ...)`); migration raw SQL fixed to quoted `"metadata"` (agent caught via live migration failure)
- **🆕 D-DAY1-2**: transitional **dual-write** on PUT — config table = source of truth + meta_data kept in sync until cleanup sprint (`AD-RateLimits-MetaData-Cleanup-Phase58`); sensible transition safety beyond plan's "fallback-read-only"
- **🆕 D-DAY1-3**: `SET LOCAL app.tenant_id = $1` bind-param fails under asyncpg → `SELECT set_config('app.tenant_id', :tid, true)` (per `correction_loop.py` precedent)
- **🆕 D-DAY1-4**: counter is a singleton (not request-scoped) → self-acquires session via `session_factory` + sets own RLS context per write/read

### Day 1 Validation Sweep — ALL GREEN

| Gate | Result |
|------|--------|
| pytest | 1819 → **1840** (+21; plan target +15) + 4 skip + 0 regressions ✅ |
| mypy --strict | 0 errors ✅ |
| 9 V2 lints | 9/9 green (incl. `check_rls_policies` 20 tables + `check_llm_sdk_leak`) ✅ |
| Frontend | 0 files touched (API shapes preserved) → Vitest 675 unaffected ✅ |
| HEX_OKLCH | baseline 48 unchanged (0 frontend change) ✅ |
| LLM SDK leak | 0 ✅ |
| **AP-4 closure** | `rate_limits` usage table now written (`pg_insert`) + queried (recovery/usage GET) ✅ |
| mockup-fidelity | DUAL CLEAN 22/22 PARITY 15 consec 57.45-57.59 ✅ |

### Day 1 Workload tracking

- US-1+US-2 agent (`rl-config-table`): ~12 min wall-clock (duration 718s) — 24th consecutive
- US-3 agent (`rl-runtime-repoint`): ~14 min wall-clock (duration 844s) — 25th consecutive
- Parent supervisory + validation + progress/checklist: ~25 min
- **Day 1 total**: ~50 min wall-clock

### Day 0 Workload tracking

- Plan v1 + checklist v1 drafting: ~45 min (parent)
- Day 0 三-Prong (parallel Glob/Grep/Read + Alembic head check): ~20 min (parent)
- **Total Day 0**: ~65 min parent; on track vs ~1.0 hr §6 estimate

