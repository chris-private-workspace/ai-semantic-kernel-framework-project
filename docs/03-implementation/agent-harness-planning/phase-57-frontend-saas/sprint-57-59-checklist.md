# Sprint 57.59 — Checklist

Plan: [`sprint-57-59-plan.md`](./sprint-57-59-plan.md)

**Class**: `mixed-multidomain-bundle` 0.65 (tier-2; DB schema + service + 4 re-points)
**Agent-delegated**: yes (sequential code-implementer agents)
**Agent-factor**: `mixed-multidomain-bundle-mechanical` 0.65 (tier-3 **2nd validation**)
**Template**: mirrors `sprint-57-58-checklist.md` Day 0-2 structure

---

## Day 0 — Plan + 三-Prong Verify

### 0.1 Plan + Checklist Drafting
- [x] **Draft `sprint-57-59-plan.md` v1** (9-section; scope C1 two-table split locked per user 2026-05-28)
- [x] **Draft `sprint-57-59-checklist.md` v1** (this file)
- [x] **User approve plan v1 + checklist v1** — gate before Day 0 三-Prong ✅ (approved 2026-05-28)

### 0.8 Day 0 三-Prong Verify (Step 2.5 mandatory — Schema Verify CRITICAL this sprint)

#### Prong 1 — Path Verify
- [x] **D-DAY0-A**: `rate_limit_configs` migration file NOT exist yet (NEW)
  - Verify: `ls backend/src/infrastructure/db/migrations/versions/ | grep rate_limit_configs` → empty
- [x] **D-DAY0-B**: `platform_layer/tenant/rate_limit_config_store.py` NOT exist (NEW)
- [x] **D-DAY0-C**: `RateLimitConfig` ORM NOT exist in `api_keys.py` (only `RateLimit` usage table exists)
  - Verify: `grep -n "class RateLimitConfig\b" backend/src/infrastructure/db/models/api_keys.py` → empty
- [x] **D-DAY0-D**: Sprint 57.58 files present (re-point targets): `rate_limit.py`, `rate_limit_counter.py`, `tool_rate_limit_gate.py`, `admin/tenants.py` rate-limit endpoints

#### Prong 2 — Content Verify
- [x] **D-DAY0-E**: `parse_rate_limit_item()` signature + return shape (Sprint 57.58)
  - Verify: `grep -n "def parse_rate_limit_item" backend/src/platform_layer/tenant/rate_limit_counter.py` + read body
- [x] **D-DAY0-F**: exact `meta_data["rate_limits"]` stored shape (confirm `{label, value}` per Sprint 57.58 D-DAY1-1; read Pydantic `RateLimitItem` body NOT just grep — per `AD-Day0-Prong2-Nested-Shape-Read` lesson)
- [x] **D-DAY0-G**: existing `RateLimit` usage ORM full schema (cols + unique + RLS) to confirm usage-table reuse fit
- [x] **D-DAY0-H**: `RateLimitConfigStore` precedent — `_PLAN_QUOTA_RESOURCE_WHITELIST` + projection helpers (Sprint 57.56) + `RateLimitConfigStore` vs existing store patterns
- [x] **D-DAY0-I**: Redis counter `check_and_increment` body (where to add write-through) + window_start computation

#### Prong 3 — Schema Verify (CRITICAL — new table + data migration)
- [x] **D-DAY0-J**: Alembic head number — `ls backend/src/infrastructure/db/migrations/versions/ | sort -V | tail -3` → next available NN
- [x] **D-DAY0-K**: RLS policy pattern from `0009_rls_policies.py` (`tenant_isolation_*` USING clause) to mirror for `rate_limit_configs`
- [x] **D-DAY0-L**: `TenantScopedMixin` columns (tenant_id type + FK) to match config table
- [x] **D-DAY0-M**: existing `rate_limits` table migration `0006` — column types + unique + FK to mirror config table styling
- [x] **D-DAY0-N**: migration import-weight — can `parse_rate_limit_item` be imported in Alembic migration OR must inline? (Alembic dep-light rule)
- [x] **D-DAY0-O**: data migration query — how to read `tenants.meta_data` JSONB in raw SQL (`meta_data ? 'rate_limits'` operator availability)

#### Day 0 Drift Catalog + go/no-go
- [x] **Catalog findings** in `progress.md` Day 0 entry — 15 checks (12 GREEN + 3 NOTABLE + 1 minor; 0 CRITICAL)
- [x] **Decide go/no-go** — ~5% shift → **GO for Day 1** (3 plan v1.1 micro-amendments: window_end + RLS double-policy + inline parse)

### 0.9 Branch + Day 0 commit
- [x] **Create feature branch** `feature/sprint-57-59-rate-limits-potemkin-migration` (from main `5736e0a4`)
- [ ] **Day 0 commit** (plan + checklist + progress.md)

---

## Day 1 — Implementation (Agent-Delegated: yes — sequential)

### 1.1 US-1 — NEW config table + ORM + Alembic + data migration (agent `rl-config-table`) ✅ COMPLETE
- [x] **NEW** `RateLimitConfig` ORM in `api_keys.py` + `__all__` ✅
- [x] **EDIT** `infrastructure/db/models/__init__.py` — export ✅
- [x] **NEW** Alembic `0019_rate_limit_configs.py` — CREATE + unique + FK CASCADE + RLS (2 policies: isolation USING + insert WITH CHECK) + inline-parse data migration + downgrade DROP ✅
- [x] **NEW** `test_rate_limit_config_migration.py` (6 tests) ✅
- [x] **Verify**: migration up/down/up clean (head 0019) + `check_rls_policies` PASS (20 tables) + pytest US-1 green ✅

### 1.2 US-2 — Config store + re-point GET/PUT (agent `rl-config-table`) ✅ COMPLETE
- [x] **NEW** `rate_limit_config_store.py` (`RateLimitConfigStore`: list_configs / replace_configs / _project_config_to_item) ✅
- [x] **EDIT** `admin/tenants.py` — GET/PUT re-point (fallback meta_data; API shape UNCHANGED; audit preserved; transitional dual-write D-DAY1-2) ✅
- [x] **NEW** `test_admin_tenant_rate_limits_table.py` (9 tests) ✅
- [x] **Verify**: pytest US-2 green + existing rate-limit tests preserved ✅

### 1.3 US-3 — Re-point middleware/gate/usage + Redis write-through (agent `rl-runtime-repoint`) ✅ COMPLETE
- [x] **EDIT** `rate_limit.py` — `_load_rate_limits` config table (fallback meta_data) ✅
- [x] **EDIT** `tool_rate_limit_gate.py` — config read from table ✅
- [x] **EDIT** `rate_limit_counter.py` — write-through (window_start+window_end upsert `used=GREATEST`) + `_recover_from_table` + optional `session_factory` DI ✅
- [x] **EDIT** `api/main.py` — inject `get_session_factory` into counter ✅
- [x] **EDIT** `admin/tenants.py` — usage GET table-backed (Redis peek + table fallback) ✅
- [x] **NEW** `test_rate_limit_usage_persistence.py` (6 tests) ✅
- [x] **EDIT** `agent_harness/conftest.py` — `RATE_USAGE_%` sweep ✅

### 1.4 Day 1 Validation Sweep — ALL GREEN
- [x] **pytest full**: 1819 → **1840** (+21; plan target +15) + 0 regressions ✅
- [x] **mypy --strict**: 0 errors ✅
- [x] **9/9 V2 lints** (incl. `check_rls_policies` 20 tables + `check_llm_sdk_leak`) ✅
- [x] **Vitest 675 unchanged** (0 frontend files touched — API shapes preserved) ✅
- [x] **HEX_OKLCH baseline 48** + DUAL CLEAN 22/22 PARITY 15 consec ✅
- [x] **LLM SDK leak 0** ✅
- [x] **AP-4 closed**: `rate_limits` usage table now written (`pg_insert`) + queried (recovery/usage GET) ✅

### 1.5 Day 1 commit
- [ ] **Commit all Day 1 work**
  - Message: `feat(rate-limits, sprint-57-59): two-table split — rate_limit_configs + activate rate_limits usage table (close AP-4 Potemkin)`

---

## Day 2 — Closeout (parent assistant)

### 2.1 Final Validation Sweep
- [ ] **Re-run Day 1.4 checks** sanity
- [ ] **mockup-fidelity DUAL CLEAN 22/22 PARITY 15 consecutive 57.45-57.59**

### 2.2 Retrospective (Q1-Q6; Q7 N/A SKIP — refactor/migration NOT spike)
- [ ] **NEW** `agent-harness-execution/phase-57/sprint-57-59/retrospective.md` (Q1-Q6 + calibration ratio + AP-4 closure note)

### 2.3 sprint-workflow.md updates
- [ ] MHist 1-line + `mixed-multidomain-bundle` 0.65 SCOPE 3rd data point + `mixed-multidomain-bundle-mechanical` 0.65 tier-3 2nd validation (§Active block)

### 2.4 PROMOTIONS (SKIP-eligible)
- [ ] Confirm 0 PROMOTION-CANDIDATE reach 3-data-point threshold (or codify `AD-Day0-Prong2-Nested-Shape-Read` if 57.59 = 2nd data point)

### 2.5 Memory + index
- [ ] **NEW** `memory/project_phase57_59_rate_limits_potemkin_migration.md` (user-home `.claude/projects/.../memory/`)
- [ ] **EDIT** `memory/MEMORY.md` — quality pointer ~250-300 char

### 2.6 CLAUDE.md (navigator-only)
- [ ] Current Sprint row + Last Updated footer

### 2.7 next-phase-candidates.md
- [ ] Sprint 57.59 Carryover section: `AD-RateLimits-Potemkin-Migration-Phase58` CLOSED + AP-4 closed + NEW `AD-RateLimits-MetaData-Cleanup-Phase58`

### 2.8 REFACTOR-003 record
- [ ] **NEW** `claudedocs/4-changes/refactoring/REFACTOR-003-sprint-57-59-rate-limits-potemkin-migration.md`

### 2.9 PR + merge (user action)
- [ ] Push branch + open PR (title: `feat(rate-limits, sprint-57-59): RateLimits two-table split — close AP-4 Potemkin (Phase 58.x deeper extensions 2/5)`)
- [ ] Wait CI (5 required green) → user merge → branch cleanup

### 2.10 Final closeout
- [ ] Day 2 commit (all docs)
- [ ] Verify working tree clean on main after merge
- [ ] Mark Sprint 57.59 CLOSED in next-phase-candidates.md

---

## Open items / 🚧 Deferred (updated end of Day 0 三-Prong)

(Only `[ ]` → `[x]` allowed; never delete unchecked. 🚧 markers acceptable with reason.)
