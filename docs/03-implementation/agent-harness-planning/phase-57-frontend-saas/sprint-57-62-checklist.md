# Sprint 57.62 — Checklist

Plan: [`sprint-57-62-plan.md`](./sprint-57-62-plan.md)

**Class**: `medium-backend` 0.80 (single-domain RateLimits; NEW table + Alembic + RLS + counter detection hook + GET endpoint + frontend alerts surface)
**Agent-delegated**: yes (sequential — Track A backend agent + Track B frontend agent; 28th + 29th consecutive code-implementer)
**Agent-factor**: `mechanical-greenfield-design-decisions` 0.65 (NEW `rate_limit_alerts` schema + severity tiers + dedup semantics + frontend alerts UX; **backend+frontend pair** — 4th validation in the calibrated pair shape)
**Template**: mirrors `sprint-57-61-checklist.md` Day 0-2 structure

---

## Day 0 — Plan + 三-Prong Verify (Prong 3 APPLIES — NEW `rate_limit_alerts` table)

### 0.1 Plan + Checklist Drafting
- [x] **Draft `sprint-57-62-plan.md` v1** (9-section; persisted alert log + GET + frontend surface; grounded in pre-plan Explore recon)
- [x] **Draft `sprint-57-62-checklist.md` v1** (this file)
- [x] **User approve plan v1** — gate before Day 0 三-Prong ✅ (approved 2026-05-29 全採: Option A persisted log / 2-tier severity / counter-write-through detection / 15s frontend poll / sequential 2-agent / CHANGE-030)

### 0.8 Day 0 三-Prong Verify (Step 2.5 — Content Prong CRITICAL: counter write-through hook site; Schema Prong: new table)

#### Prong 1 — Path Verify
- [x] **D-DAY0-A**: `RateLimitAlert` / `rate_limit_alerts` / `RateLimitAlertStore` do NOT exist yet (NEW)
  - Verify: `grep -rn "RateLimitAlert\|rate_limit_alerts" backend/src/` → empty
- [x] **D-DAY0-B**: `RateLimit` + `RateLimitConfig` ORM present in `api_keys.py` (where new `RateLimitAlert` lands for cohesion)
  - Verify: `grep -n "class RateLimit\|class RateLimitConfig\|TenantScopedMixin" backend/src/infrastructure/db/models/api_keys.py`
- [x] **D-DAY0-C**: `rate_limit_counter.py` present with a write-through method + optional `session_factory` DI (the hook site)
  - Verify: `grep -n "session_factory\|def check_and_increment\|def peek\|write.*through\|on_conflict\|window_start" backend/src/platform_layer/tenant/rate_limit_counter.py`
- [x] **D-DAY0-D**: `GET .../rate-limits/usage` endpoint + `_load_tenant_or_404` present (mirror auth for new alerts GET)
  - Verify: `grep -n "rate-limits/usage\|_load_tenant_or_404\|RateLimitsUsageItem" backend/src/api/v1/admin/tenants.py`
- [x] **D-DAY0-E**: test dir paths — `backend/tests/unit/platform_layer/tenant/` (US-1 store) + `backend/tests/integration/api/` (US-2) + migration-test convention
  - Verify: `ls backend/tests/unit/platform_layer/tenant/ ; ls backend/tests/integration/api/test_admin_tenant_rate_limits*.py ; ls backend/tests/integration/ | grep -i migrat`
- [x] **D-DAY0-F**: frontend `useRateLimitsUsage` + QuotasTab + `usageColorToken` + tokens present (US-3 reuse, 0 new oklch)
  - Verify: `grep -rn "useRateLimitsUsage\|usageColorToken\|var(--warning)\|var(--danger)" frontend/src/features/tenant-settings/`

#### Prong 2 — Content Verify
- [x] **D-DAY0-G** (🔴 CRITICAL — counter hook site §2.4): confirm the EXACT write-through method name + that it holds `session` + `tenant_id` + `resource_type` + `window_type` + `used` + `quota` + `window_start` at the upsert point (where the alert hook rides). Read the method body, not just grep the name.
  - Verify: read `rate_limit_counter.py` write-through method body; confirm all 7 values in scope at the usage-upsert site
- [x] **D-DAY0-H**: confirm the `session_factory` optional-DI wiring pattern (how 57.59 injected it from `main.py`) so the `alert_store` DI mirrors it
  - Verify: `grep -n "session_factory\|RedisRateLimitCounter(" backend/src/api/main.py backend/src/platform_layer/tenant/rate_limit_counter.py`
- [x] **D-DAY0-I**: confirm `SLAViolation` model shape (columns + severity enum) to mirror for `RateLimitAlert`
  - Verify: `grep -n "class SLAViolation\|threshold_pct\|actual_pct\|severity\|MINOR\|MAJOR\|CRITICAL\|resolved_at" backend/src/infrastructure/db/models/sla.py`
- [x] **D-DAY0-J**: confirm the `0019` RLS 2-policy pattern (`tenant_isolation` + `tenant_insert`) to mirror in `0021`
  - Verify: `grep -n "ENABLE ROW LEVEL SECURITY\|tenant_isolation\|tenant_insert\|WITH CHECK" backend/src/infrastructure/db/migrations/versions/0019_rate_limit_configs.py`
- [x] **D-DAY0-K**: confirm `pg_insert` + `on_conflict_do_update` + `func.greatest` import path + usage precedent (57.59 usage upsert)
  - Verify: `grep -n "pg_insert\|on_conflict_do_update\|greatest\|from sqlalchemy" backend/src/platform_layer/tenant/rate_limit_config_store.py backend/src/platform_layer/tenant/rate_limit_counter.py`
- [x] **D-DAY0-L**: confirm QuotasTab existing 2 cards (Rate limits + Live usage) structure so the new Card adds BELOW without touching them
  - Verify: read QuotasTab.tsx card region; confirm Live usage Card boundary

#### Prong 3 — Schema Verify (NEW table)
- [x] **D-DAY0-M**: `TenantScopedMixin` column shape (tenant_id type + FK + any physical-column alias) — so `RateLimitAlert` mirrors `RateLimit` exactly (57.59/57.60 physical-column lesson)
  - Verify: `grep -rn "class TenantScopedMixin\|tenant_id\|mapped_column(" backend/src/infrastructure/db/models/_mixins*.py backend/src/infrastructure/db/models/base*.py`
- [x] **D-DAY0-N**: Alembic head = `0020_clear_rate_limits_meta_data` (down_revision for `0021`); `0021` number not occupied
  - Verify: `ls backend/src/infrastructure/db/migrations/versions/ | sort -V | tail -3`
- [x] **D-DAY0-O**: confirm no physical-column alias trap for the new table's columns (clean new table → ORM attr == physical name; verify `TenantScopedMixin` tenant_id isn't an alias affecting RLS policy SQL)
  - Verify: read `TenantScopedMixin.tenant_id` declaration
- [x] **D-DAY0-P**: `check_rls_policies` current tenant-table count = 20 (→ 21 after `0021`); confirm the lint reads policies from migrations
  - Verify: `python scripts/lint/check_rls_policies.py 2>&1 | tail -5` (current 20/20 green)

#### Day 0 Drift Catalog + go/no-go
- [x] **Catalog findings** in `progress.md` Day 0 entry — 16 checks (13 GREEN + 1 NOTABLE-simplification D-DAY0-G + 3 corrections D-DAY0-E/I/J; 0 CRITICAL-blocker)
- [x] **Decide go/no-go** — net scope shift ≈ **−3%** (dropped `api/main.py` wiring via D-DAY0-G; 3 factual corrections folded) → **GO for Day 1**

### 0.9 Branch + Day 0 commit
- [x] **Create feature branch** `feature/sprint-57-62-rate-limits-alerting` (from main `2d99d626`)
- [x] **Day 0 commit** (plan + checklist + progress.md Day 0 entry) ✅ `79282286`

---

## Day 1 — Implementation (Agent-Delegated: yes — sequential Track A backend → Track B frontend)

### 1.1 US-1 — 80%-threshold detection + persisted alert log (Track A backend)
- [x] **EDIT** `infrastructure/db/models/api_keys.py` — NEW `RateLimitAlert` ORM (`rate_limit_alerts`, `TenantScopedMixin`); `threshold_pct`/`actual_pct` int; severity lowercase `warning`/`critical`; UNIQUE `(tenant_id, resource_type, window_type, window_start)` + CHECK `severity IN ('warning','critical')` + index `(tenant_id, triggered_at)`; MHist
- [x] **NEW** Alembic `0021_rate_limit_alerts.py` (down_revision `0020`) — CREATE table + ENABLE+**FORCE** RLS + 2 policies (`tenant_isolation` USING + `tenant_insert` WITH CHECK; `current_setting('app.tenant_id', true)::uuid` per D-DAY0-J) + CHECK + index
- [x] **NEW** `platform_layer/tenant/rate_limit_alert_store.py` — `ALERT_THRESHOLD_PCT=80` + `_severity` (lowercase) + `maybe_record` (idempotent upsert peak/escalate, returns early < 80 / quota<=0) + `list_recent`; stateless (no ctor state); MHist
- [x] **EDIT** `rate_limit_counter.py` — best-effort `maybe_record` call inside `_write_through` (D-DAY0-G: direct stateless call, session already present; rides existing best-effort block; Risk Class B dual-ignore if mypy diverges); MHist
- [x] ~~**EDIT** `api/main.py` — inject `RateLimitAlertStore`~~ **N/A (D-DAY0-G)**: stateless store + session already in `_write_through` → NO wiring edit needed (scope dropped at Day 0)
- [x] **NEW** `backend/tests/unit/platform_layer/tenant/test_rate_limit_alert_store.py` (~10-12): 80/90/100 → row+severity (lowercase); <80 → none; dedup once-per-window (peak); warning→critical escalation; fail-open no-session/DB-error; multi-tenant isolation
- [x] **Verify**: detection at write-through (not GET); fail-open never breaks enforcement; RLS present

### 1.2 US-2 — Recent-alerts GET endpoint (Track A backend cont.)
- [x] **EDIT** `api/v1/admin/tenants.py` — NEW `RateLimitAlertItem` + `RateLimitAlertsResponse` + `GET /admin/tenants/{tid}/rate-limits/alerts?limit=N` (default 20, cap 100, newest-first); reuse `_load_tenant_or_404`; MHist
- [x] **NEW** `backend/tests/integration/api/test_admin_tenant_rate_limits_alerts.py` (~4-6): auth/404; empty list; ordering newest-first; limit cap 100; multi-tenant isolation
- [x] **Verify**: GET reads via `alert_store.list_recent`; tenant A cannot read tenant B's alerts

### 1.3 US-3 — QuotasTab recent-alerts surface (Track B frontend)
- [x] **NEW** `useRateLimitsAlerts.ts` hook (TanStack; `refetchInterval` ~15000) + `fetchRateLimitsAlerts` service func + alert TS types
- [x] **EDIT** `QuotasTab.tsx` — NEW "Recent alerts" Card BELOW Live usage Card (resource · peak % · severity badge `var(--warning)`/`var(--danger)` · time + empty state); existing Rate limits Card + Live usage Card UNCHANGED (scope guard); 0 new oklch
- [x] **NEW** Vitest (~8-10): hook fetch/empty/error; alerts list render + severity colors; empty state; 2 existing cards unchanged scope-guard
- [x] **Verify**: HEX_OKLCH baseline 48 unchanged (grep); existing cards bit-for-bit

### 1.4 Day 1 Validation Sweep — ALL GREEN
- [x] **pytest full**: 1887 → **1907** (+20) (US-1 ~10-12 + US-2 ~4-6; 0 regressions)
- [x] **mypy `src/ --strict`**: 0 / 319 files (CI parity backend-ci.yml:152)
- [x] **9/9 V2 lints** (`check_rls_policies` **20 → 21** tables incl. new `rate_limit_alerts` + `check_llm_sdk_leak`)
- [x] **Alembic** live `0021` up→down→up clean
- [x] **Vitest** 675 → ~685+ ; tsc 0 ; ESLint clean ; Vite build
- [x] **HEX_OKLCH baseline 48** + DUAL CLEAN 22/22 PARITY 18 consec
- [x] **LLM SDK leak 0** + black/isort/flake8 clean

### 1.5 Day 1 commit(s)
- [ ] **Commit Day 1 work** (Track A + Track B; 1 or 2 commits)

---

## Day 2 — Closeout (parent assistant)

### 2.1 Final Validation Sweep
- [ ] **Re-run Day 1.4 checks** sanity
- [ ] **mockup-fidelity DUAL CLEAN 22/22 PARITY 18 consecutive 57.45-57.62** (frontend alerts Card 0 new oklch)

### 2.2 Retrospective (Q1-Q6; Q7 N/A SKIP — feature ship NOT spike)
- [ ] **NEW** `retrospective.md` (Q1-Q6 + calibration `mechanical-greenfield-design-decisions` 0.65 4th validation pair-shape + `medium-backend` 0.80 13th + AD closure)

### 2.3 sprint-workflow.md updates
- [ ] MHist 1-line + `medium-backend` 0.80 13th data point + `mechanical-greenfield-design-decisions` 0.65 4th validation (pair shape) data point

### 2.4 PROMOTIONS (check thresholds)
- [ ] Confirm whether any AD reaches codify threshold (likely none new)

### 2.5 Memory + index
- [ ] **NEW** `memory/project_phase57_62_rate_limits_alerting.md` (user-home)
- [ ] **EDIT** `memory/MEMORY.md` — quality pointer

### 2.6 CLAUDE.md (navigator-only)
- [ ] Current Sprint row + Last Updated footer

### 2.7 next-phase-candidates.md
- [ ] Sprint 57.62 Carryover section: Alerting CLOSED + carryovers (Webhook / Ack-Mute / Quotas-Alerting template / 57.61 hygiene / BackendOnly-Variant-Watch continues)

### 2.8 CHANGE-030 record
- [ ] **NEW** `CHANGE-030-sprint-57-62-rate-limits-alerting.md` (feature — NEW alerting + table)

### 2.9 PR + merge (user action)
- [ ] Push branch + open PR (title: `feat(rate-limits, sprint-57-62): 80%-threshold usage alerting — persisted log + GET — close AD-RateLimits-Alerting-Phase58`)
- [ ] Wait CI (5 required green) → user merge → branch cleanup

### 2.10 Final closeout
- [ ] Day 2 commit (all docs)
- [ ] Verify working tree clean on main after merge
- [ ] Mark Sprint 57.62 CLOSED in next-phase-candidates.md

---

## Open items / 🚧 Deferred (updated end of Day 0 三-Prong)

(Only `[ ]` → `[x]` allowed; never delete unchecked. 🚧 markers acceptable with reason.)
