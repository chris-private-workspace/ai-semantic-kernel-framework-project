# Sprint 57.62 — Plan

**Phase**: 57+ Frontend SaaS / Phase 58.x Portfolio Deeper Extensions
**Sprint**: 57.62 (post-57.61 RateLimits SyntaxValidation)
**Branch**: `feature/sprint-57-62-rate-limits-alerting`
**Class**: `medium-backend` 0.80 (single-domain RateLimits; NEW table + Alembic + RLS + counter detection hook + GET endpoint + frontend alerts surface)
**Agent-delegated**: yes (sequential — Track A backend agent + Track B frontend agent; backend+frontend pair)
**Agent-factor**: `mechanical-greenfield-design-decisions` 0.65 (NEW `rate_limit_alerts` schema design + severity tiers + dedup semantics + frontend alerts UX; **backend+frontend pair** — the shape the 0.65 was calibrated on, 57.56/57.57 IN band)
**Plan version**: v1 — drafted 2026-05-29 Day 0 (pre-三-Prong; grounded in pre-plan Explore reconnaissance)
**Template**: mirrors `sprint-57-61-plan.md` 9-section structure

---

## 1. Sprint Goal

Close **`AD-RateLimits-Alerting-Phase58`** (Sprint 57.57/57.60 carryover) by adding **server-side 80%-threshold usage alerting** that **persists** a record when a tenant's rate-limit usage for a resource crosses 80% of its configured quota — so the breach is captured **even when no admin is watching the live usage card** — and exposes the recent alerts to the admin via a GET endpoint + a QuotasTab alerts surface.

The breach is recorded **once per usage window** (idempotent dedup), with a severity tier (WARNING 80-99% / CRITICAL ≥100% = throttled) and the peak `actual_pct` in that window, mirroring the existing `SLAViolation` log precedent (Sprint 56.3). No SSE / no real-time push (the admin alerts surface reuses the existing 5s usage poll).

After this sprint: a rate-limit breach leaves a durable, deduplicated audit record the admin can review historically — the foundation for later off-page notification (`-Webhook` carryover), without the ~8-12 hr SSE greenfield.

---

## 2. Background & Context

### 2.1 The gap (verified Day 0 pre-plan reconnaissance)

Post-57.58/57.59/57.60, the RateLimits subsystem enforces limits (middleware + Cat 2 gate via `RedisRateLimitCounter`), persists usage (`rate_limits` table write-through), and shows live usage with 70%/90% threshold **colors** in the QuotasTab Live usage Card. But:

- **No breach is ever recorded.** When usage crosses 80%, nothing is persisted — the only signal is a coloured progress bar that exists only while the admin has the page open. Close the tab and the breach is invisible; reopen and you only see the *current* window, not that a prior window peaked.
- **No alerting precedent exists.** Reconnaissance found the SLA Monitor (Sprint 56.3) has a log-only `SLAViolation` table (`metric_type` / `threshold_pct` / `actual_pct` / `severity` MINOR/MAJOR/CRITICAL / `detected_at` / `resolved_at`) but **no delivery** — and nothing analogous for rate limits. `AD-Quotas-Alerting-Phase58` is also still pending. Alert persistence is **greenfield**.

This sprint closes the gap by persisting the breach at the enforcement point.

### 2.2 Reconnaissance findings (grounds the architecture)

| Finding | Evidence (file:line — Day 0 三-Prong will re-confirm) | Implication |
|---------|-------------------------------------------------------|-------------|
| Counter knows `count` vs `limit` at increment | `rate_limit_counter.py` `check_and_increment(...limit)` ~L422-482 (`if count <= limit` ~L455) | 80% can be detected at the enforcement point, not just on admin poll |
| Counter already DB-writes per increment | 57.59 write-through to `rate_limits` usage table (window upsert `on_conflict_do_update used=GREATEST`) via optional `session_factory` DI | The alert upsert rides the SAME existing DB-write path — no new hot-path roundtrip class |
| GET usage endpoint exists | `tenants.py` `GET /admin/tenants/{tid}/rate-limits/usage` → `RateLimitsUsageItem {resource, window, limit, current, reset_at}` ~L1551-1650 | New alerts GET endpoint mirrors this shape/auth |
| Frontend already polls + has threshold colors | `useRateLimitsUsage` `refetchInterval: 5000`; QuotasTab `usageColorToken(pct)` 70/90 thresholds | Alerts surface reuses the poll + `var(--warning)`/`var(--danger)` tokens — 0 new oklch |
| SSE is greenfield | only the agent-loop `LoopEvent` SSE exists (`chat/sse.py`); NO admin SSE channel | Option A (persisted log + poll) chosen over Option C (SSE push ~8-12 hr) |
| Tables + next migration | `rate_limits` (usage) + `rate_limit_configs` (config) in `api_keys.py`; head = `0020_clear_rate_limits_meta_data` | NEW `rate_limit_alerts` table → Alembic **`0021`** |

### 2.3 Architecture decision (user-locked Day 0) + why `-design-decisions` 0.65

**Option A — Persisted alert log + GET** (user-selected at AskUserQuestion gate 2026-05-29, over Option B client-banner-only and Option C SSE-push). The carryover's literal "SSE 80% threshold" was de-scoped because reconnaissance proved the "SSE infra ~80% from prior sprints" premise false (only the agent-loop stream exists; an admin SSE channel is ~8-12 hr greenfield, ~3× the budget).

The agent-factor is `mechanical-greenfield-design-decisions` 0.65 (NOT `-port-style` 0.45) because this is genuine NEW design: the `rate_limit_alerts` schema (column set + dedup key), the severity-tier mapping, the once-per-window upsert/escalation semantics, and the frontend alerts UX. **It is a backend+frontend pair** — the exact shape the 0.65 sub-class was calibrated on (57.56=1.02 + 57.57=1.15 IN band), so it is the natural 4th validation that complements 57.61's backend-only outlier (which landed ~0.74 BELOW; see `AD-AgentFactor-DesignDecisions-BackendOnly-Variant-Watch`).

### 2.4 Detection-hook placement constraint

Detection must fire at the **enforcement point** (the counter's per-increment write-through), NOT in the GET usage endpoint — else a breach during a window when no admin is polling is never recorded (the entire point of persistence). The counter already has the optional `session_factory` DI (57.59) and already upserts the usage row each increment; the alert upsert rides there, **best-effort / fail-open** (an alerting failure must never break enforcement or the request). Day 0 三-Prong Prong 2 will confirm the exact write-through method name/location before the hook is added.

LLM-neutrality is unaffected — `RedisRateLimitCounter` is `platform_layer` (not `agent_harness`); the alert store is a sibling `platform_layer/tenant/` module (same layer as `rate_limit_config_store.py`).

### 2.5 Dedup + severity semantics (NEW design)

- **Dedup**: one alert row per `(tenant_id, resource_type, window_type, window_start)` — i.e. **once per usage window**. `ON CONFLICT (...) DO UPDATE` keeps the row, updates `actual_pct = GREATEST(existing, new)` + `used = excluded.used` + escalates `severity`; `triggered_at` stays at first trigger (the breach's first-crossing time). So a window that flaps over 80% repeatedly leaves exactly one row tracking the peak.
- **Threshold**: module constant `ALERT_THRESHOLD_PCT = 80`. Fire when `used/quota*100 >= 80`.
- **Severity**: `WARNING` (80 ≤ pct < 100) / `CRITICAL` (pct ≥ 100 = quota hit / throttled). 2-tier (vs SLAViolation's 3-tier MINOR/MAJOR/CRITICAL) because rate-limit semantics have a clean "approaching vs throttled" split; noted as a deliberate divergence (D-point).

### 2.6 Sprint 57.61 carryover chain

- `AD-RateLimits-Alerting-Phase58` (this sprint's primary)
- `AD-RateLimits-DuplicateResource-Validation` / `-SyntaxValidation-ClientSide-Polish` / `-Parser-Extract-Shared-Predicate` (NOT this sprint — independent hygiene/feature)
- `AD-AgentFactor-DesignDecisions-BackendOnly-Variant-Watch` — this sprint is a backend+**frontend** pair, so it does NOT generate the 2nd backend-only data point (the watch continues to await a backend-only `-design-decisions` sprint); but it DOES give the 4th *pair-shape* validation
- `AD-AgentFactor-Tier-3-MixedBundle-Mechanical-Tighten-0.45-Validation-Sprint-57.62` (DEFERS again — single-domain, not a multi-track bundle)
- `AD-AgentPrompt-CrossPlatform-Mypy-Warning` — **APPLIES this sprint** (the counter hook touches `rate_limit_counter.py` which already deals with Redis/asyncpg; the agent prompt must flag Risk Class B dual-ignore)
- `AD-Mypy-WholeDir-Conftest-Collision` (CONTINUES — Phase 58+)

### 2.7 Class baseline tracking

- `medium-backend` 0.80 — 13th data point (12-pt mean ~0.62; informational)
- `mechanical-greenfield-design-decisions` 0.65 — 4th validation, **back to backend+frontend pair shape** (57.56=1.02 + 57.57=1.15 pair IN band; 57.61=0.74 backend-only BELOW). A pair-shape IN-band reading here reinforces the R6 hypothesis (backend-only is the outlier).

---

## 3. User Stories

### US-1: 80%-threshold detection + persisted alert log

**As a** platform operator
**I want** a durable record whenever a tenant's rate-limit usage crosses 80% of quota
**So that** breaches are captured even when no admin is watching, and I can review them historically.

**Acceptance**:
- NEW `RateLimitAlert` ORM (`rate_limit_alerts` table, in `api_keys.py` alongside `RateLimit` + `RateLimitConfig`; `TenantScopedMixin`): `resource_type` / `window_type` / `threshold_pct` / `actual_pct` / `used` / `quota` / `severity` / `window_start` / `triggered_at`; UNIQUE `(tenant_id, resource_type, window_type, window_start)`; index `(tenant_id, triggered_at DESC)`.
- NEW Alembic `0021_rate_limit_alerts.py` (down_revision `0020_clear_rate_limits_meta_data`): CREATE table + 2 RLS policies (`tenant_isolation` + `tenant_insert`, mirroring the `0019` pattern) + the index.
- NEW `RateLimitAlertStore` (`platform_layer/tenant/rate_limit_alert_store.py`): `maybe_record(session, tenant_id, resource_type, window_type, used, quota, window_start)` — computes pct, returns early if `< ALERT_THRESHOLD_PCT`, else idempotent upsert (`pg_insert ... on_conflict_do_update` peak/escalate per §2.5); `list_recent(session, tenant_id, limit)` newest-first.
- Counter hook: `RedisRateLimitCounter` write-through path calls `alert_store.maybe_record(...)` after the usage upsert, **best-effort / fail-open** (try/except, never raises into enforcement); gated by the existing optional `session_factory` (no session → skip silently).
- `ALERT_THRESHOLD_PCT = 80` module constant; severity tiers WARNING/CRITICAL per §2.5.
- ~10-12 NEW pytest: detection at 80/90/100 → row created with correct severity; below 80 → no row; once-per-window dedup (2 crossings same window → 1 row, peak tracked); escalation WARNING→CRITICAL on same window; fail-open when `session_factory` is None / DB error; multi-tenant isolation; RLS policy present.

### US-2: Recent-alerts GET endpoint

**As a** tenant administrator
**I want** to fetch recent rate-limit alerts for a tenant
**So that** I can see which resources breached 80% and when.

**Acceptance**:
- NEW `GET /admin/tenants/{tid}/rate-limits/alerts?limit=N` (default N=20, cap 100) → `RateLimitAlertsResponse {items: list[RateLimitAlertItem]}`; `RateLimitAlertItem {resource, window, threshold_pct, actual_pct, used, quota, severity, window_start, triggered_at}` newest-first.
- Reuses `_load_tenant_or_404` + tenant scoping (mirror the usage GET endpoint auth).
- ~4-6 NEW pytest: auth/404; empty list when no alerts; ordering newest-first; limit cap; multi-tenant isolation (tenant A can't read tenant B's alerts).

### US-3: QuotasTab recent-alerts surface (frontend)

**As a** tenant administrator
**I want** the QuotasTab to show recent breaches
**So that** I notice a resource hit 80% without staring at the live bars.

**Acceptance**:
- NEW `useRateLimitsAlerts` hook (TanStack Query; same 5s poll OR a lighter 15-30s interval — alerts are not as time-critical as live usage) hitting the new endpoint.
- NEW "Recent alerts" surface in QuotasTab (below the Live usage Card): a compact list of recent breaches (resource · peak % · severity badge · window time), reusing existing tokens (`var(--warning)` WARNING / `var(--danger)` CRITICAL; `.card` / badge styles) — **0 new oklch** (HEX_OKLCH baseline 48 unchanged). Empty state when no alerts. Existing Rate limits Card + Live usage Card **UNCHANGED** (scope guard).
- ~8-10 NEW Vitest: hook fetch/empty/error; list render with severity colors; empty state; scope-guard the 2 existing cards unchanged.

---

## 4. Technical Specification

### 4.1 `RateLimitAlert` ORM (`infrastructure/db/models/api_keys.py`)

```python
class RateLimitAlert(Base, TenantScopedMixin):
    __tablename__ = "rate_limit_alerts"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    # tenant_id via TenantScopedMixin
    resource_type: Mapped[str] = mapped_column(String(64))
    window_type: Mapped[str] = mapped_column(String(16))
    threshold_pct: Mapped[int]                 # the configured threshold that fired (80)
    actual_pct: Mapped[int]                    # peak pct in this window (GREATEST on conflict)
    used: Mapped[int]
    quota: Mapped[int]
    severity: Mapped[str] = mapped_column(String(16))   # 'warning' | 'critical' (lowercase + CHECK — mirror SLAViolation; D-DAY0-I)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint("tenant_id", "resource_type", "window_type", "window_start",
                         name="uq_rate_limit_alerts_window"),
        CheckConstraint("severity IN ('warning', 'critical')", name="ck_rate_limit_alerts_severity"),
        Index("ix_rate_limit_alerts_tenant_recent", "tenant_id", "triggered_at"),  # DESC in query
    )
```

> **Day 0 三-Prong corrections folded** (audit trail in progress.md): `threshold_pct`/`actual_pct` stay `int` (rate-limit pct integer-grained — deliberate divergence from SLAViolation `Numeric(8,4)`); severity lowercase `warning`/`critical` + CHECK (D-DAY0-I); RLS SQL uses `current_setting('app.tenant_id', true)::uuid` + `FORCE` (D-DAY0-J); the alert hook needs NO ctor DI / NO `api/main.py` edit (D-DAY0-G — stateless store, session already in `_write_through`).

### 4.2 Alembic `0021_rate_limit_alerts.py`

down_revision `0020_clear_rate_limits_meta_data`. `upgrade()`: `op.create_table("rate_limit_alerts", ...)` + the unique constraint + index + 2 RLS policies via raw `op.execute`:
```sql
ALTER TABLE rate_limit_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE rate_limit_alerts FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_rate_limit_alerts ON rate_limit_alerts
    USING (tenant_id = current_setting('app.tenant_id', true)::uuid);
CREATE POLICY tenant_insert_rate_limit_alerts ON rate_limit_alerts
    FOR INSERT WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
```
(D-DAY0-J: matches the `0019` 2-policy pattern exactly — `FORCE` + the `, true` missing_ok arg.)
`downgrade()`: drop policies + table. (`check_rls_policies` lint: 20 → **21** tables.)

### 4.3 `RateLimitAlertStore` (`platform_layer/tenant/rate_limit_alert_store.py`)

```python
ALERT_THRESHOLD_PCT = 80

def _severity(pct: int) -> str:
    return "critical" if pct >= 100 else "warning"   # lowercase + CHECK (D-DAY0-I)

class RateLimitAlertStore:
    async def maybe_record(self, session, tenant_id, resource_type, window_type,
                           used: int, quota: int, window_start) -> None:
        if quota <= 0:
            return
        pct = int(used / quota * 100)
        if pct < ALERT_THRESHOLD_PCT:
            return
        stmt = pg_insert(RateLimitAlert).values(
            tenant_id=tenant_id, resource_type=resource_type, window_type=window_type,
            threshold_pct=ALERT_THRESHOLD_PCT, actual_pct=pct, used=used, quota=quota,
            severity=_severity(pct), window_start=window_start,
        ).on_conflict_do_update(
            constraint="uq_rate_limit_alerts_window",
            set_=dict(actual_pct=func.greatest(RateLimitAlert.actual_pct, pct),
                      used=used, severity=case(...escalate...)),
        )   # triggered_at NOT updated (keeps first-crossing time)
        await session.execute(stmt)

    async def list_recent(self, session, tenant_id, limit: int = 20): ...
```

### 4.4 Counter hook (`platform_layer/tenant/rate_limit_counter.py`)

**Hook site CONFIRMED Day 0 (D-DAY0-G)**: `_write_through(self, ..., limit, ...)` (`rate_limit_counter.py:265`) — already guards `if self._session_factory is None: return` (L282), opens the session, computes `window_start` (L289), and upserts `pg_insert(RateLimit)` (L298-311) with `used` + `limit` (= the quota snapshot). All 7 values are in scope at the upsert. The whole method is already best-effort ("any DB error logs + continues"). So the alert call rides there directly — **NO ctor DI, NO `api/main.py` edit** (the `RateLimitAlertStore` is stateless; the counter imports + calls it within the existing session):
```python
# inside _write_through, after the RateLimit usage upsert (still in the same best-effort block):
await maybe_record_rate_limit_alert(session, tenant_id, resource, window_type,
                                    used=used, quota=limit, window_start=window_start)
# (maybe_record returns early when pct < ALERT_THRESHOLD_PCT; the surrounding
#  _write_through try/except already makes alerting fail-open — never breaks enforcement)
```
Risk Class B: `rate_limit_counter.py` deals with Redis/asyncpg → the backend agent prompt flags the dual-ignore `# type: ignore[X, unused-ignore]` pattern if mypy diverges cross-platform.

### 4.5 GET endpoint (`api/v1/admin/tenants.py`)

```python
class RateLimitAlertItem(BaseModel):
    resource: str; window: str; threshold_pct: int; actual_pct: int
    used: int; quota: int; severity: str
    window_start: datetime; triggered_at: datetime
class RateLimitAlertsResponse(BaseModel):
    items: list[RateLimitAlertItem]

@router.get("/admin/tenants/{tenant_id}/rate-limits/alerts")
async def get_rate_limits_alerts(tenant_id, limit: int = Query(20, le=100), db=...):
    await _load_tenant_or_404(db, tenant_id)
    rows = await alert_store.list_recent(db, tenant_id, limit)
    return RateLimitAlertsResponse(items=[_project_alert(r) for r in rows])
```

### 4.6 Frontend (`tenant-settings`)

- NEW `frontend/src/features/tenant-settings/hooks/useRateLimitsAlerts.ts` (TanStack; `refetchInterval` ~15000) + service func.
- NEW types `RateLimitAlertItem` / `RateLimitAlertsResponse`.
- QuotasTab: NEW "Recent alerts" Card below Live usage Card — list of `{resource · actual_pct% · severity badge · relative time}`; severity badge `var(--warning)`/`var(--danger)`; empty state "No recent alerts"; reuse `.card` / `.bar-track`-adjacent styles; **0 new oklch**.

### 4.7 Verification

- ~22-28 NEW tests (US-1 ~10-12 pytest + US-2 ~4-6 pytest + US-3 ~8-10 Vitest)
- pytest 1887 → ~1900+; Vitest 675 → ~685+
- mypy `src/ --strict` 0 / tsc 0 / **9/9 V2 lints** (`check_rls_policies` 20 → **21** tables) / 0 SDK leak
- Alembic live `0021` up→down→up clean
- frontend: ESLint clean / Vite build / HEX_OKLCH baseline 48 unchanged → DUAL CLEAN 22/22 PARITY **18 consec**; existing 2 cards bit-for-bit unchanged

### 4.8 Risk mitigation

| Risk | Mitigation |
|------|-----------|
| Alert write breaks enforcement (hot path) | best-effort try/except fail-open; gated by optional DI (no session → skip) |
| Alert spam (row per request over 80%) | once-per-window dedup via UNIQUE upsert; ≤1 row per `(tenant,resource,window,window_start)` |
| Detection in GET endpoint misses unwatched windows | detection at counter write-through (enforcement point), NOT the GET poll (§2.4) |
| RLS missing on new table → lint fail | `0021` adds 2 policies (isolation + insert); `check_rls_policies` 21 tables |
| Cross-platform mypy on counter edit | Risk Class B — agent prompt flags dual-ignore `# type: ignore[..., unused-ignore]` |
| Frontend new oklch literal | reuse `var(--warning)`/`var(--danger)`; HEX_OKLCH baseline 48 grep-checked Day 1 |

---

## 5. File Change List

### Backend (NEW + EDIT)

**NEW**:
- `backend/src/infrastructure/db/migrations/versions/0021_rate_limit_alerts.py`
- `backend/src/platform_layer/tenant/rate_limit_alert_store.py`
- `backend/tests/integration/api/test_admin_tenant_rate_limits_alerts.py` (US-2 GET ~4-6)
- `backend/tests/unit/platform_layer/tenant/test_rate_limit_alert_store.py` (US-1 detection/dedup/severity ~10-12)
- `backend/tests/integration/api/test_rate_limit_alerts_migration.py` (0021 up/down + RLS; D-DAY0-E: migration tests live in `integration/api/` — `test_rate_limit_config_migration.py` convention, NOT `integration/db/`)

**EDIT**:
- `backend/src/infrastructure/db/models/api_keys.py` — NEW `RateLimitAlert` ORM; MHist
- `backend/src/platform_layer/tenant/rate_limit_counter.py` — best-effort alert hook in `_write_through` (direct stateless call, NO ctor DI per D-DAY0-G); Risk Class B dual-ignore if mypy diverges; MHist
- `backend/src/api/v1/admin/tenants.py` — NEW alerts GET endpoint + Pydantic models; MHist

> ~~`backend/src/api/main.py` — inject RateLimitAlertStore~~ **DROPPED (D-DAY0-G)**: the alert store is stateless + `_write_through` already holds the session → no wiring edit needed.

### Frontend (NEW + EDIT)

**NEW**:
- `frontend/src/features/tenant-settings/hooks/useRateLimitsAlerts.ts`
- `frontend/tests/unit/tenant-settings/useRateLimitsAlerts.test.ts(x)` + QuotasTab alerts tests (Day 0 Prong 1 confirms test layout)

**EDIT**:
- `frontend/src/features/tenant-settings/services/...Service.ts` — `fetchRateLimitsAlerts`
- `frontend/src/features/tenant-settings/types.ts` — alert types
- `frontend/src/features/tenant-settings/components/tabs/QuotasTab.tsx` — NEW Recent alerts Card (existing 2 cards UNCHANGED)

### Sprint artifacts (Day 0 + Day 2)

- `sprint-57-62-plan.md` (this) + `sprint-57-62-checklist.md`
- `agent-harness-execution/phase-57/sprint-57-62/progress.md` + `retrospective.md`
- `memory/project_phase57_62_rate_limits_alerting.md` (user-home)
- `claudedocs/4-changes/feature-changes/CHANGE-030-sprint-57-62-rate-limits-alerting.md`

---

## 6. Workload

**Agent-delegated: yes** (sequential — Track A backend agent + Track B frontend agent; 28th + 29th consecutive code-implementer)

**Bottom-up est ~6.75 hr** → class-calibrated commit ~5.4 hr (mult 0.80 `medium-backend`) → **agent-adjusted commit ~3.5 hr** (`agent_factor` 0.65 `mechanical-greenfield-design-decisions`)

| Task | Bottom-up | Class-calibrated | Agent-adjusted |
|------|-----------|-----------------|---------------|
| Day 0 三-Prong (Path + Content + Schema for new table) + plan | 0.9 hr | 0.9 hr | 0.9 hr (parent) |
| US-1: table + ORM + Alembic 0021 + RLS + alert store + counter hook + ~10-12 tests | 3.5 hr | 2.8 hr | 1.8 hr |
| US-2: alerts GET endpoint + ~4-6 tests | 1.0 hr | 0.8 hr | 0.5 hr |
| US-3: frontend alerts Card + hook + ~8-10 Vitest | 1.5 hr | 1.2 hr | 0.8 hr |
| Day 1 validation sweep | 0.4 hr | 0.4 hr | parent |
| Day 2 closeout | 0.6 hr | 0.6 hr | 0.6 hr (parent) |
| **Total** | **~6.75 hr** | **~5.4 hr** | **~3.5 hr** |

Validation threshold: `actual/agent-adjusted` in [0.85, 1.20]; tier-4 `mechanical-greenfield-design-decisions` 0.65 **4th validation, back to backend+frontend pair shape** (57.56=1.02 + 57.57=1.15 pair IN band; 57.61=0.74 backend-only BELOW). If this pair-shape app lands IN band → reinforces R6 (backend-only is the outlier).

---

## 7. Acceptance Criteria

### Functional
- [ ] Usage crossing 80% at the enforcement point → 1 persisted `rate_limit_alerts` row (correct severity WARNING; ≥100% → CRITICAL)
- [ ] Below 80% → no row
- [ ] Same window crossing twice → exactly 1 row, `actual_pct` = peak, severity escalates, `triggered_at` = first crossing
- [ ] Alert write failure / no session → enforcement unaffected (fail-open)
- [ ] `GET /admin/tenants/{tid}/rate-limits/alerts` → recent newest-first, limit cap 100, 404 on unknown tenant
- [ ] Multi-tenant isolation: tenant A cannot read/own tenant B's alerts (endpoint + RLS)
- [ ] QuotasTab shows recent alerts (resource · peak % · severity badge · time) + empty state; existing 2 cards unchanged

### Quality
- [ ] pytest 1887 → ~1900+ (NO regressions); Vitest 675 → ~685+
- [ ] mypy `src/ --strict` 0 / tsc 0 / **9/9 V2 lints** (`check_rls_policies` **21** tables) / 0 SDK leak
- [ ] Alembic `0021` live up→down→up clean
- [ ] HEX_OKLCH baseline 48 / DUAL CLEAN 22/22 PARITY **18 consec**

### Process
- [ ] Day 0 三-Prong (Path + Content + **Schema** — new table `0021`)
- [ ] Prong 2 confirms exact counter write-through method/site before the hook + the `session_factory` DI pattern
- [ ] Prong 3 confirms `0020` head + RLS 2-policy pattern + `TenantScopedMixin` column shape
- [ ] Sequential 2-agent delegation (Track A backend → Track B frontend); Risk Class B flagged in the backend agent prompt (counter edit)
- [ ] Day 2 closeout (retro Q1-Q6 + memory + CLAUDE.md + next-phase + CHANGE-030)
- [ ] PR + CI green + merge

---

## 8. Risks

| # | Risk | Class | Mitigation |
|---|------|-------|-----------|
| R1 | Alert write in counter breaks enforcement / adds latency | Logic / Perf | best-effort try/except fail-open; rides the existing 57.59 usage-upsert DB write (no new roundtrip class); optional DI gate |
| R2 | Alert spam (row per over-80% request) | Logic | once-per-window UNIQUE upsert; ≤1 row per window; `actual_pct` peak-tracks |
| R3 | Detection in GET poll misses unwatched windows | Logic | detection at counter write-through, NOT GET (§2.4) — the core reason Option A persists |
| R4 | RLS missing on new table → `check_rls_policies` fail | Security | `0021` adds 2 policies (isolation + insert); Prong 3 verifies the `0019` 2-policy pattern |
| R5 | Cross-platform mypy on `rate_limit_counter.py` edit | Tooling (Risk Class B) | agent prompt flags dual-ignore `# type: ignore[X, unused-ignore]` |
| R6 | Frontend introduces a new oklch literal | Mockup-fidelity | reuse `var(--warning)`/`var(--danger)`; Day 1 HEX_OKLCH grep (baseline 48) |
| R7 | `mechanical-greenfield-design-decisions` 0.65 4th validation (pair shape) lands out of band | Calibration | 4th data point; pair shape is the calibrated one (57.56/57.57 IN band) — an IN-band reading reinforces R6 (backend-only outlier); BELOW/ABOVE → retro Q4 reassesses |
| R8 | Severity 2-tier vs SLAViolation 3-tier inconsistency | Design | deliberate (rate-limit "approaching vs throttled" semantics); D-point §9.2; documented in CHANGE-030 |

---

## 9. Carryover ADs (for Sprint 57.63+ pickup)

| ID | Status | Notes |
|----|--------|-------|
| `AD-RateLimits-Alerting-Webhook-Phase58` | NEW (deferred) | off-page delivery (Slack/PagerDuty/email webhook) built on the `rate_limit_alerts` table this sprint creates; ~3-4 hr + external integration |
| `AD-RateLimits-Alert-Acknowledge-Mute` | NEW (deferred) | admin ack / snooze-24h on an alert row (SLAViolation has `resolved_at`; rate-limit alerts could mirror); ~1-2 hr |
| `AD-Quotas-Alerting-Phase58` | CARRYOVER | the Quotas analogue — this sprint's `rate_limit_alerts` + store pattern is the reusable template (`AD-Phase58-Persistence-WriteSide-Pattern-Template` extends to alerting) |
| `AD-RateLimits-DuplicateResource-Validation` / `-SyntaxValidation-ClientSide-Polish` / `-Parser-Extract-Shared-Predicate` | CARRYOVER | 57.61 hygiene/feature carryovers (independent) |
| `AD-AgentFactor-DesignDecisions-BackendOnly-Variant-Watch` | CONTINUES | 57.62 is a pair (not backend-only) → still awaiting a 2nd backend-only `-design-decisions` data point |
| `AD-AgentFactor-Tier-3-MixedBundle-Mechanical-Tighten-0.45-Validation-Sprint-57.63` | DEFERS | single-domain; awaits next genuine multi-track bundle |
| `AD-AgentPrompt-CrossPlatform-Mypy-Warning` / `AD-Mypy-WholeDir-Conftest-Collision` | CONTINUES | R5 applies this sprint (counter edit); whole-dir mypy unaffected (CI runs `mypy src/`) |

---

**Plan v1 status**: drafted 2026-05-29 Day 0 (pre-Day 0 三-Prong Verify; grounded in pre-plan Explore reconnaissance); awaiting user approval before checklist v1 + Day 0 三-Prong execution.

**Open user decision points** (Day 0 approval gate):
1. **Confirm scope** — Option A persisted alert log (counter write-through detection → idempotent `rate_limit_alerts` upsert + GET endpoint + QuotasTab alerts surface). NO SSE; reuse polling.
2. **Severity tiers** — 2-tier WARNING (80-99%) / CRITICAL (≥100% throttled) vs mirroring SLAViolation 3-tier MINOR/MAJOR/CRITICAL. (Recommended: 2-tier — cleaner rate-limit semantics.)
3. **Detection location** — counter write-through (enforcement point; catches unwatched windows) vs GET-poll-only (simpler but misses unwatched windows). (Recommended: write-through — it's the whole point of persistence.)
4. **Frontend alerts poll interval** — reuse 5s (matches live usage) vs lighter 15-30s (alerts less time-critical). (Recommended: 15s — alerts aren't sub-5s critical; lighter load.)
5. **Agent delegation** — sequential Track A backend + Track B frontend (mirror 57.54-57.57) vs single agent. (Recommended: sequential 2-agent.)
6. **Change record** — CHANGE-030 (NEW alerting feature). (Recommended: CHANGE — new capability + new table.)
