# Sprint 57.60 — Plan

**Phase**: 57+ Frontend SaaS / Phase 58.x Portfolio Deeper Extensions
**Sprint**: 57.60 (post-57.59 RateLimits Potemkin Migration)
**Branch**: `feature/sprint-57-60-rate-limits-metadata-cleanup`
**Class**: `medium-backend` 0.80 (single-domain backend cleanup; surgical fallback removal + 1 data-cleanup migration)
**Agent-delegated**: yes (≥80% Day 1 via code-implementer; single agent — small surgical sprint)
**Agent-factor**: `mechanical-pattern-reuse-heavy` 0.30 (5 near-identical fallback-removal sites = ≥4 mechanical repetitions; Day 0 三-Prong may refine — see §2.3)
**Plan version**: v1 — drafted 2026-05-29 Day 0 (pre-三-Prong)
**Template**: mirrors `sprint-57-59-plan.md` 9-section structure

---

## 1. Sprint Goal

Close **`AD-RateLimits-MetaData-Cleanup-Phase58`** (Sprint 57.59 carryover §9) by **removing the transitional `tenant.meta_data["rate_limits"]` read-fallback + PUT dual-write** that Sprint 57.59 retained as migration safety, now that the `rate_limit_configs` table has been the source of truth across 1 sprint cycle:

- **Remove the meta_data read-fallback** at the 4 RateLimits read paths (GET config / usage GET / middleware `_load_rate_limits` / Cat 2 gate `_load_tool_limits`) — read chain becomes `rate_limit_configs` → (display default OR empty), dropping the meta_data middle layer
- **Remove the PUT dual-write** (`upsert_tenant_rate_limits` no longer mirror-writes `meta_data["rate_limits"]`; writes config table only)
- **Clear the stored JSONB**: NEW Alembic `0020` strips the now-redundant `rate_limits` key from every tenant's `meta_data` (data already migrated to `rate_limit_configs` by Sprint 57.59 `0019`); downgrade reverse-populates from the config table for reversibility
- **Preserve `DEFAULT_RATE_LIMITS`** (display default for un-configured tenants — NOT transitional, out of cleanup scope) and **API response shapes** (frontend untouched)

After this sprint: RateLimits config has a single source of truth (`rate_limit_configs`); the meta_data JSONB path is fully retired; 0 transitional fallback branches remain in the subsystem.

---

## 2. Background & Context

### 2.1 What Sprint 57.59 left (verified this sprint Day 0 探勘)

Sprint 57.59 split RateLimits into two tables (config `rate_limit_configs` + usage `rate_limits`) and re-pointed all read/write paths to them, but **deliberately retained `meta_data["rate_limits"]` as a transitional read-fallback + kept the PUT dual-write** (per 57.59 plan §2.6 backward-compat safety) so any not-yet-migrated tenant or reader stayed consistent for one validation cycle. The fallback sites (located Day 0 探勘 2026-05-29):

| # | Site | File:line (57.59 baseline) | Type |
|---|------|----------------------------|------|
| 1 | `list_tenant_rate_limits` (GET config) | `api/v1/admin/tenants.py:1390-1391` | read-fallback: config empty → `meta_data["rate_limits"]` → `DEFAULT_RATE_LIMITS` |
| 2 | `get_rate_limits_usage` (usage GET) | `api/v1/admin/tenants.py:1602` | read-fallback: config empty → meta_data → DEFAULT |
| 3 | `_load_rate_limits` (middleware) | `platform_layer/middleware/rate_limit.py:188-193` | read-fallback: config empty → meta_data → `[]` (no enforcement) |
| 4 | `_load_tool_limits` (Cat 2 gate) | `platform_layer/tenant/tool_rate_limit_gate.py:136-141` | read-fallback: config empty → meta_data → `[]` |
| 5 | `upsert_tenant_rate_limits` (PUT) | `api/v1/admin/tenants.py:1492-1497` | dual-write: write config table **and** `meta_data["rate_limits"]` |

Comments at these sites already name the cleanup AD explicitly (e.g. `rate_limit.py:172` "removed by AD-RateLimits-MetaData-Cleanup-Phase58"; `tenants.py:1479-1481` dual-write removal note) — the 57.59 author pre-marked the exact removal targets.

### 2.2 What stays (NOT in cleanup scope)

- ✅ **`DEFAULT_RATE_LIMITS`** (`tenants.py:1354`) — the 3-item display default shown in the admin UI for tenants with no config row; this is the intended steady-state fallback for the **GET display** path (un-configured tenant still shows editable defaults). It is NOT the transitional meta_data layer. KEEP.
- ✅ **Enforcement empty-config behaviour** — middleware + Cat 2 gate return `[]` (no enforcement) when config is empty; they never used `DEFAULT_RATE_LIMITS` (enforcement must not apply phantom defaults). After cleanup they still return `[]` on empty config — only the meta_data middle layer is dropped.
- ✅ **`RateLimitConfigStore`** (`rate_limit_config_store.py`) — already pure config-table CRUD (no meta_data inside); the fallback lives only in the 5 caller sites above. No store change.
- ✅ **`parse_rate_limit_item()`** / projection helpers — unchanged.

### 2.3 Why `medium-backend` 0.80 + `mechanical-pattern-reuse-heavy` 0.30

- **Scope class `medium-backend` 0.80**: single-domain backend with a DB data-migration + service-layer surgical edits + test updates (no frontend functional change). Matches the `medium-backend` class shape (DB + service).
- **Agent-factor `mechanical-pattern-reuse-heavy` 0.30**: the dominant work is **5 near-identical fallback-removal edits** (≥ 4 mechanical repetitions of the same `if config-empty: read meta_data` block) + a reverse-mirror of the Sprint 57.59 `0019` data-migration pattern. This is removal/repetition, not greenfield design.
- **Caveat (Day 0 may refine)**: removal sprints don't map cleanly onto the tier-4 sub-class table (built around creation/port). The reverse-populate downgrade + test conversions add non-repetitive work that tempers the "pattern-reuse-heavy" rating. If Day 0 三-Prong shows the non-repetitive portion dominates, refine to `mechanical-greenfield-port-style` 0.45. Provisionally 0.30 since 5 repetitive removals are the bulk.
- **Does NOT validate** `mixed-multidomain-bundle-mechanical` 0.45 — that carryover (`AD-AgentFactor-Tier-3-MixedBundle-Mechanical-Tighten-0.45-Validation-Sprint-57.60`) expected a multi-track bundle; this is single-domain, so the tightened-0.45 1st validation defers to the next genuine multi-track bundle sprint (see §9).

### 2.4 Sprint 57.59 carryover chain

- `AD-RateLimits-MetaData-Cleanup-Phase58` (this sprint's primary)
- `AD-RateLimits-SyntaxValidation-Phase58` / `AD-RateLimits-Alerting-Phase58` (RateLimits deeper extensions; NOT this sprint)
- `AD-Day0-Prong3-Physical-Column-Read` + `AD-Day0-Prong2-Nested-Shape-Read` (each now 2 data points after 57.58/57.59 — candidate for codify this sprint Day 2; see §9)
- `AD-AgentFactor-Tier-3-MixedBundle-Mechanical-Tighten-0.45-Validation-Sprint-57.60` (defers — see §2.3)

### 2.5 Class baseline tracking

- `medium-backend` 0.80 — 11th data point (10-pt mean 0.66; last-3 mean ~0.72; informational this sprint — single-domain cleanup is a clean human/agent baseline)
- `mechanical-pattern-reuse-heavy` 0.30 agent_factor — validation data point (Sprint 57.49 retroactive was the prior signal; this is the 1st deliberate forward application)

### 2.6 Backward-compat + safety (data-cleanup migration sensitivity)

- **Read-path correctness invariant**: removing the meta_data fallback is safe **only because** `0019` already migrated every `meta_data["rate_limits"]` row into `rate_limit_configs`. Day 0 三-Prong Prong 2 MUST confirm `0019`'s data-migration is unconditional (no skipped tenants) before removing the fallback — else un-migrated tenants would silently lose config.
- **`0020` is additive cleanup, reversible**:
  - `upgrade()`: for each tenant where `meta_data ? 'rate_limits'`, strip the key (`meta_data = meta_data - 'rate_limits'`); config table is untouched (already authoritative).
  - `downgrade()`: reverse-populate — read each tenant's `rate_limit_configs` rows → inline-project back to `{label, value}` list → write `meta_data["rate_limits"]`. Makes the migration symmetric so a downgrade past `0020` then `0019` still has meta_data. Reverse-projection is **lossy for custom labels** (canonical slug ≠ original display string) — acceptable since downgrade is a dev-only operation (§8 R3).
- **Migration dep-light** (Sprint 57.59 D-DAY0-N rule): do NOT import `rate_limit_config_store` / `rate_limit_counter` (Redis dep) into the migration — INLINE the projection. Alembic migrations are frozen historical snapshots.
- **Down past `0019`**: `0019.downgrade()` already drops `rate_limit_configs` and falls back to retained meta_data; `0020`'s reverse-populate restores meta_data first, so the `0019` fallback still resolves. Order-correct.

---

## 3. User Stories

### US-1: Remove transitional meta_data read-fallback + PUT dual-write

**As a** platform maintainer
**I want** the RateLimits read/write paths to use `rate_limit_configs` as the sole source (no meta_data middle layer)
**So that** there is one authoritative config store and no silent divergence between the table and stale JSONB.

**Acceptance**:
- Remove the meta_data read-fallback at all 4 read sites (§2.1 #1-#4): read chain becomes `rate_limit_configs` → `DEFAULT_RATE_LIMITS` (GET display paths #1, #2) / `rate_limit_configs` → `[]` (enforcement paths #3, #4)
- Remove the PUT dual-write (§2.1 #5): `upsert_tenant_rate_limits` writes `RateLimitConfigStore.replace_configs` only; `append_audit("tenant_rate_limits_upsert")` unchanged
- Update file-header MHist + the inline "removed by AD-RateLimits-MetaData-Cleanup-Phase58" comments (the AD is now closed — comments either deleted with the block or updated)
- API response shapes UNCHANGED (`{label, value}` items) — frontend untouched
- Update affected Sprint 57.59 tests: convert "config empty → meta_data fallback" assertions to "config empty → DEFAULT (display) / empty (enforcement)"; **do not delete** tests — re-point assertions to the new steady-state behaviour (per Never-Delete-Tests rule)
- ~2-4 NEW/converted pytest asserting no-meta_data-read (seed meta_data["rate_limits"] + empty config table → GET returns DEFAULT not the meta_data value; PUT does not write meta_data)

### US-2: Data-cleanup migration `0020` (clear stored JSONB) + reverse-populate downgrade

**As a** platform operator
**I want** the redundant `meta_data["rate_limits"]` JSONB stripped from all tenants
**So that** no stale config blob lingers after the table became authoritative.

**Acceptance**:
- NEW Alembic `0020_clear_rate_limits_meta_data.py` (Day 0 Prong 3 confirms head = `0019` → next = `0020`):
  - `upgrade()`: strip `rate_limits` key from each tenant's `meta_data` (`meta_data - 'rate_limits'`); idempotent (tenants without the key are no-ops); config table untouched
  - `downgrade()`: inline-project `rate_limit_configs` rows → `{label, value}` → write `meta_data["rate_limits"]` (reversibility; lossy for custom labels per §2.6)
- Migration is dep-light (inline projection; no service/Redis import — Sprint 57.59 D-DAY0-N rule)
- ~3-4 NEW pytest in a migration test (upgrade clears key on seeded tenant + idempotent on un-seeded + downgrade reverse-populates from config rows + multi-tenant isolation preserved)
- Down-migration verified: `0020` up → down restores meta_data; full `up → down → up` clean

---

## 4. Technical Specification

### 4.1 Read-fallback removal (4 sites — surgical deletion)

Each site currently has a 3-tier chain `config → meta_data → terminal`. Remove the meta_data tier:

| Site | Before | After |
|------|--------|-------|
| `tenants.py:1366` `list_tenant_rate_limits` GET | config → meta_data (L1390-91) → DEFAULT (L1396) | config → DEFAULT |
| `tenants.py:1571` `get_rate_limits_usage` usage GET | config → meta_data (L1602) → DEFAULT | config → DEFAULT |
| `rate_limit.py:166` `_load_rate_limits` | config → meta_data (L188-193) → `[]` | config → `[]` |
| `tool_rate_limit_gate.py` `_load_tool_limits` | config → meta_data (L136-141) → `[]` | config → `[]` |

For the enforcement paths (#3, #4) the `tenant`/`meta_data` ORM load may become unused after fallback removal → drop the now-dead `tenant` fetch + its imports if no longer referenced (grep-verify per Day 0 Prong 2; Karpathy §3 — clean the orphan **I create**, not pre-existing dead code).

### 4.2 PUT dual-write removal (`tenants.py:1456` `upsert_tenant_rate_limits`)

Remove L1492-1497 (the `new_meta = dict(tenant.meta_data or {}); new_meta["rate_limits"] = new_items; tenant.meta_data = new_meta` block). PUT now does: `RateLimitConfigStore.replace_configs(tenant_id, items)` + `append_audit(...)` only. The `tenant` ORM object is still needed for audit/`_load_tenant_or_404` — verify it isn't orphaned.

### 4.3 Alembic `0020_clear_rate_limits_meta_data.py`

```python
def upgrade():
    conn = op.get_bind()
    # Strip the now-redundant rate_limits key (config lives in rate_limit_configs since 0019).
    # JSONB minus-key operator; only touches tenants that carry the key (idempotent).
    # Day 0 D-DAY0-M: tenants JSONB physical column is "metadata" (ORM meta_data is an
    # alias via mapped_column("metadata", ...)); 0019 raw SQL uses "metadata" — 0020 must too.
    conn.execute(text('UPDATE tenants SET "metadata" = "metadata" - \'rate_limits\' '
                      'WHERE "metadata" ? \'rate_limits\''))

def downgrade():
    # Reversibility: reverse-populate meta_data["rate_limits"] from the config table.
    # INLINE projection (dep-light — no rate_limit_config_store import; Sprint 57.59 D-DAY0-N).
    # Lossy for custom labels (canonical resource_type → display label); acceptable (dev-only).
    conn = op.get_bind()
    rows = conn.execute(text("SELECT tenant_id, resource_type, window_type, quota "
                             "FROM rate_limit_configs ORDER BY tenant_id, resource_type"))
    by_tenant: dict = {}
    for r in rows:
        item = _inline_project(r.resource_type, r.window_type, r.quota)  # → {"label":..,"value":"N / unit"}
        by_tenant.setdefault(r.tenant_id, []).append(item)
    for tenant_id, items in by_tenant.items():
        conn.execute(text('UPDATE tenants SET "metadata" = jsonb_set('
                          'COALESCE("metadata", \'{}\'::jsonb), \'{rate_limits}\', :items::jsonb) '
                          'WHERE id = :tid'), {"items": json.dumps(items), "tid": tenant_id})
```

> **Note (Day 0 D-DAY0-M physical-column — `AD-Day0-Prong3-Physical-Column-Read`)**: the tenants JSONB column is physically named `"metadata"`; the ORM exposes it as `meta_data` via `mapped_column("metadata", ...)` in `identity.py`. `0019` raw SQL already uses `"metadata"` — `0020` raw SQL MUST match (this was Sprint 57.59 D-DAY1-1; codified now).
> **Note (Day 0 D-DAY0-N rule reaffirmed)**: `_inline_project` is the inverse of `0019`'s `_inline_parse`; keep it local to the migration. The live projection (`RateLimitConfigStore._project_config_to_item`) is NOT imported (dep-light frozen snapshot).
> **Note (RLS in migration)**: data-only migration (no DDL, no new table) → no RLS policy changes; `check_rls_policies` unaffected (20 tables unchanged).

### 4.4 Test updates (per Never-Delete-Tests rule)

- `test_admin_tenant_rate_limits_table.py` (57.59) — any test seeding `meta_data["rate_limits"]` + asserting GET reads it → re-point to assert GET returns `DEFAULT_RATE_LIMITS` (config empty) and meta_data is ignored. Any "PUT dual-writes meta_data" assertion → flip to "PUT does NOT write meta_data".
- `test_rate_limit_usage_persistence.py` (57.59) — middleware/usage meta_data-fallback assertions → re-point to config-table-only.
- NEW `test_clear_rate_limits_meta_data_migration.py` — `0020` up clears key / idempotent / downgrade reverse-populates / multi-tenant.
- Day 0 Prong 2 MUST enumerate every test that seeds `meta_data["rate_limits"]` (grep `meta_data.*rate_limits` in `backend/tests/`) so none silently break.

### 4.5 Verification

- pytest baseline 1840 → ~1842-1846 (net: + migration tests, ± converted fallback tests)
- mypy --strict 0 / 9/9 V2 lints (incl. `check_rls_policies` 20 tables unchanged) / 0 SDK leak
- HEX_OKLCH baseline 48 / DUAL CLEAN 22/22 PARITY 16 consec (0 frontend touched)
- Vitest 675 unchanged / Vite build clean
- Migration `up → down → up` clean (head `0020`)

---

## 5. File Change List

### Backend (NEW + EDIT)

**NEW**:
- `backend/src/infrastructure/db/migrations/versions/0020_clear_rate_limits_meta_data.py` (Day 0 Prong 3 confirms number; data-cleanup upgrade + reverse-populate downgrade)
- `backend/tests/integration/api/test_clear_rate_limits_meta_data_migration.py` (~3-4 migration tests)

**EDIT**:
- `backend/src/api/v1/admin/tenants.py` — remove read-fallback (GET #1 L1390-91 + usage GET #2 L1602) + PUT dual-write (#5 L1492-97); update header MHist + inline AD comments
- `backend/src/platform_layer/middleware/rate_limit.py` — `_load_rate_limits` remove meta_data fallback (#3 L188-193); drop orphaned tenant fetch if unused
- `backend/src/platform_layer/tenant/tool_rate_limit_gate.py` — `_load_tool_limits` remove meta_data fallback (#4 L136-141)
- `backend/tests/integration/api/test_admin_tenant_rate_limits.py` — **(Day 0 D-DAY0-G drift)** 57.48-era; converts GET-honours-meta_data (L131/163) + PUT-writes-meta_data (L224/245/323) assertions → config-table steady-state (no delete)
- `backend/tests/integration/api/test_admin_tenant_rate_limits_table.py` — re-point fallback-path assertions (no delete)
- `backend/tests/integration/agent_harness/test_rate_limit_usage_persistence.py` — re-point fallback-path assertions (no delete)
- 57.58-era (`test_admin_tenant_rate_limits_usage.py` / `test_rate_limit_middleware.py` / `test_tool_rate_limit_enforce.py`) — Day 1 agent greps each for meta_data-seeding; convert any fallback-dependent assertion (no delete)

### Frontend (verify-only)

- Confirm `useRateLimits` / `useRateLimitsSave` / `useRateLimitsUsage` + QuotasTab unchanged (API shapes preserved — no field change)

### Sprint artifacts (Day 0 + Day 2)

- `sprint-57-60-plan.md` (this) + `sprint-57-60-checklist.md`
- `agent-harness-execution/phase-57/sprint-57-60/progress.md` + `retrospective.md`
- `memory/project_phase57_60_rate_limits_metadata_cleanup.md`
- `claudedocs/4-changes/refactoring/REFACTOR-004-sprint-57-60-rate-limits-metadata-cleanup.md` (refactor — transitional-code removal + data cleanup, not a feature)

---

## 6. Workload

**Agent-delegated: yes** (≥80% Day 1 via code-implementer; single agent — small surgical sprint)

**Bottom-up est ~7 hr** → class-calibrated commit ~5.6 hr (mult 0.80 `medium-backend`) → **agent-adjusted commit ~1.7 hr** (`agent_factor` 0.30 `mechanical-pattern-reuse-heavy`)

| Task | Bottom-up | Class-calibrated | Agent-adjusted |
|------|-----------|-----------------|---------------|
| Day 0 三-Prong (Path + Content + Schema verify) + plan | 0.75 hr | 0.75 hr | 0.75 hr (parent) |
| US-1: remove 5 fallback/dual-write sites + convert affected tests | 3 hr | 2.4 hr | 0.7 hr |
| US-2: migration `0020` + reverse downgrade + migration tests | 2.5 hr | 2.0 hr | 0.6 hr |
| Day 1 validation sweep | 0.4 hr | 0.4 hr | parent |
| Day 2 closeout | 0.6 hr | 0.6 hr | 0.6 hr (parent) |
| **Total** | **~7.25 hr** | **~5.6 hr** | **~1.7 hr** |

Validation threshold: `actual/agent-adjusted` in [0.85, 1.20]; < 0.7 OR > 1.20 → `mechanical-pattern-reuse-heavy` 0.30 single-data-point caution (this is the 1st deliberate forward application — KEEP unless a 2nd data point also breaches).

---

## 7. Acceptance Criteria

### Functional
- [ ] 4 read-fallback sites read `rate_limit_configs` only (meta_data middle layer removed); GET display → DEFAULT, enforcement → `[]` on empty config
- [ ] PUT writes config table only (no meta_data dual-write); audit unchanged
- [ ] `0020` upgrade strips `meta_data["rate_limits"]` from all tenants (idempotent)
- [ ] `0020` downgrade reverse-populates meta_data from config table
- [ ] Migration `up → down → up` clean (head `0020`)
- [ ] API response shapes UNCHANGED; frontend QuotasTab + 3 hooks unchanged + green
- [ ] No orphaned `tenant`/meta_data ORM fetch left behind (Karpathy §3 — only orphans this sprint creates)

### Quality
- [ ] pytest 1840 → 1842+ (NO regressions; converted tests still pass)
- [ ] mypy --strict 0 / 9/9 V2 lints (`check_rls_policies` 20 tables unchanged) / 0 SDK leak
- [ ] HEX_OKLCH baseline 48 / DUAL CLEAN 22/22 PARITY 16 consec
- [ ] Vitest 675 unchanged / Vite build clean

### Process
- [ ] Day 0 三-Prong (Path + Content + Schema verify — data migration in scope)
- [ ] Prong 2 confirms `0019` data-migration unconditional (fallback-removal safety invariant §2.6)
- [ ] Prong 2 enumerates all tests seeding `meta_data["rate_limits"]`
- [ ] Single code-implementer agent delegation
- [ ] Day 2 closeout artifacts (retro Q1-Q6 + memory + CLAUDE.md + next-phase + REFACTOR-004)
- [ ] PR + CI green + merge

---

## 8. Risks

| # | Risk | Class | Mitigation |
|---|------|-------|-----------|
| R1 | Un-migrated tenant loses config when fallback removed | DB migration / Logic | Day 0 Prong 2 MUST verify `0019` data-migration is unconditional (every `meta_data ? 'rate_limits'` tenant inserted config rows); only remove fallback after confirming. `0020` strips meta_data only AFTER config is authoritative. |
| R2 | Hidden test seeds `meta_data["rate_limits"]` + breaks silently | Testing | **Day 0 D-DAY0-G DRIFT confirmed**: `test_admin_tenant_rate_limits.py` (57.48-era) seeds meta_data + asserts GET/PUT read/write it (L131/163/224/245/323) → added to §5; 57.58-era 3 files Day 1 grep-enumerate. Convert (no delete). `test_rate_limit_config_migration.py` excluded (tests 0019 in isolation). |
| R3 | `0020` downgrade reverse-projection lossy for custom labels | Schema | Acceptable — downgrade is dev-only; canonical slug round-trip preserves enforcement semantics (quota/window), only the display label string may differ; documented in migration docstring |
| R4 | Down past `0020` then `0019` loses config entirely | DB migration | `0020.downgrade()` reverse-populates meta_data first → `0019.downgrade()` fallback still resolves; order-correct (R verified by `up→down→up` test on a 2-migration window) |
| R5 | Orphaned `tenant` ORM fetch left after fallback removal | Code hygiene | Grep-verify each edited site post-removal; drop unused fetch + imports (Karpathy §3, only this-sprint orphans) |
| R6 | Alembic head number drift | Schema | Day 0 Prong 3: `ls migrations/versions | sort -V | tail -3` confirms next = `0020` |
| R7 | `mechanical-pattern-reuse-heavy` 0.30 mis-fit (removal ≠ template repetition) | Calibration | 1st deliberate forward application; if actual/agent-adjusted < 0.7 OR > 1.20 → Day 2 retro Q4 refine to 0.45 `port-style` (single-data-point caution) |
| R8 | Cross-platform mypy on edited service files (Risk Class B) | Tooling | Edited files don't touch Redis/asyncpg stubs (the 57.59 hotfix site `rate_limit_counter.py` is NOT edited here); low risk — but run mypy --strict before push |

---

## 9. Carryover ADs (for Sprint 57.61+ pickup)

| ID | Status | Notes |
|----|--------|-------|
| `AD-RateLimits-SyntaxValidation-Phase58` | CARRYOVER | Now easier post-split (config table has typed `quota`/`window_type`); PUT-time validation; ~2-3 hr |
| `AD-RateLimits-Alerting-Phase58` | CARRYOVER | SSE 80% threshold; pairs with usage table; ~3-4 hr (SSE infra ~80% from prior sprints) |
| `AD-AgentFactor-Tier-3-MixedBundle-Mechanical-Tighten-0.45-Validation-Sprint-57.61` | DEFERS | 57.60 is single-domain (not multi-track) → tightened-0.45 1st validation defers to next genuine `mixed-multidomain-bundle` sprint |
| `AD-Day0-Prong3-Physical-Column-Read` + `AD-Day0-Prong2-Nested-Shape-Read` | CODIFY-CANDIDATE | Each now 2 data points (57.58 + 57.59) — codify into `sprint-workflow.md §Step 2.5` Drift Class table this sprint Day 2 if scope allows, else carry |
| `AD-medium-frontend-Baseline-Recalibration` / `AD-MediumBackend-AICadence-Recalibration` / `AD-Test-Cleanup-Pattern-Shared-Helper` | CONTINUES | Phase 58+ |
| `AD-AgentPrompt-CrossPlatform-Mypy-Warning` | CANDIDATE | Agent prompts touching Redis/asyncpg should flag Risk Class B + suggest dual-ignore (57.59 CI failure lesson) |

---

**Plan v1 status**: drafted 2026-05-29 Day 0 (pre-Day 0 三-Prong Verify); awaiting user approval before checklist v1 + Day 0 三-Prong execution.

**Open user decision points** (Day 0 approval gate):
1. **Confirm scope** — remove 5 transitional sites (4 read-fallback + 1 dual-write) + `0020` data-cleanup migration (reverse-populate downgrade) + test conversions; KEEP `DEFAULT_RATE_LIMITS` display default
2. **Reverse-populate downgrade** — confirm worth the ~10 lines for reversibility (vs forward-only no-op downgrade with documented data-loss-on-downgrade); recommended: reverse-populate (symmetric, low cost)
3. **Codify Prong-2/3 Drift Class rows this sprint** — both ADs hit 2 data points; fold into `sprint-workflow.md` Day 2, or carry to 57.61? (recommend fold-in — cheap, both validated)
4. **Agent delegation** — single code-implementer agent (small surgical sprint) vs parent-direct; recommend single agent
5. **REFACTOR-004** — classify as REFACTOR (transitional-code removal + data cleanup) — confirm
