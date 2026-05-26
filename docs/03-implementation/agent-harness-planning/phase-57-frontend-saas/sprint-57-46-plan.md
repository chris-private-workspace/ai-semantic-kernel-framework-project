# Sprint 57.46 — Multi-Domain Bundle (3 AD Closure Wave)

**Phase**: 57+ Frontend SaaS / Cross-cutting carryover closure
**Goal**: Close 3 carryover ADs in one batched sprint — codify mockup-canonical rule + extend TenantSettings backend schema + resolve mockup capture method blocker.
**Branch**: `feature/sprint-57-46-multi-domain-bundle`
**Class**: HYBRID `mixed-multidomain-bundle` (docs/template 0.40 + medium-backend 0.80 + infra/tooling 0.55 + closeout 0.80)
**Date**: 2026-05-26 (Sprint 57.45 Day 3 closeout)
**Prior sprint reference**: Sprint 57.39 (4-domain batched template) + Sprint 57.44 (D-DAY0-4 schema gap source)

---

## 1. Sprint Goal

```
AS sprint leader
I WANT 3 carryover ADs from Phase-2 epic closure (Sprint 57.42-57.45) closed in one batched
   Sprint 57.46 multi-domain bundle
SO THAT we unblock Phase 58+ backend work (Task 2), strengthen mockup-fidelity rule corpus
   (Task 1), and resolve persistent mockup screenshot blocker (Task 3) while generating
   the 1st validation data point under tightened `agent_factor = 0.45` (Sprint 57.44 retro
   Q4 MANDATORY rollback rule).
```

## 2. Background & Context

### 2.1 3 ADs to close

| AD | Source sprint | Scope |
|---|---|---|
| **AD-MockupFidelity-AuditDocSync-Rule** | Sprint 57.45 (NEW carryover) | Codify "mockup file is canonical source; audit-derived docs may carry transcription errors" rule in `docs/rules-on-demand/frontend-mockup-fidelity.md` — prevent future Sprint 57.22-class transcription errors |
| **AD-TenantSettings-Backend-Schema-Extension** | Sprint 57.44 (D-DAY0-4 BLOCKING) | Add NEW columns to Tenant ORM (region / locale / retention_days / sso_enabled / seats) + Alembic 0018 + extend TenantSettingsResponse Pydantic + extend admin PATCH endpoint — unblock fixture-first → real data migration for /tenant-settings |
| **AD-MockupCapture-Method-Resolution** | Sprint 57.43+ (AD-MockupCapture-03 + 04 carried) | Investigate `frontend/scripts/mockup-sweep.mjs` current state + choose method (Option A direct Playwright / Option B static file serve / Option C byte-proxy / Option D real-browser) + implement choice |

### 2.2 Why bundle in one sprint

- All 3 are short (~1-2 hr docs + ~3-5 hr backend + ~1-2 hr tooling = ~6-9 hr bottom-up)
- Independent tracks (zero cross-task dependency) → can be parallel-executed by code-implementer agent
- Single PR → reduces overhead vs 3 separate PRs
- **Validation goal**: 1st `agent_factor = 0.45` data point (Sprint 57.44 retro Q4 rollback rule activated)

### 2.3 `agent_factor = 0.45` 1st validation

Per `.claude/rules/sprint-workflow.md` §Active Agent Delegation Factor Modifier:
- Sprint 57.43 (1st validation at 0.55) ratio ~0.41 BELOW band by 0.44
- Sprint 57.44 (2nd validation at 0.55) ratio ~0.20 BELOW band by ~0.65
- Rollback rule MET → tighten 0.55 → 0.45 effective Sprint 57.45+
- Sprint 57.45 (Path B 0 code change) `agent-delegated: NO` → no validation generated
- **Sprint 57.46 = 1st sprint to validate `agent_factor = 0.45`** (Day 1 ≥80% via code-implementer agent)

If Sprint 57.46 ratio also < 0.7 → propose 0.45 → 0.35 OR Option B per-class sub-class split.
If 0.85-1.20 in band → validate; preserve 0.45 for future agent-delegated sprints.

---

## 3. User Stories

### US-1: AD-MockupFidelity-AuditDocSync-Rule Codification

```
AS a future frontend sprint AI assistant working drift audit / Phase-2 re-point work
I WANT a documented rule stating "mockup file is canonical source — when audit-derived
   docs claim X but mockup source shows Y, mockup wins" in frontend-mockup-fidelity.md
SO THAT future Sprint 57.22-class transcription errors (audit's NEAR-PARITY verdict
   contradicted by mockup-file content) are detected at Day 0 Prong 2 grep, not at
   Day 3+ closeout overrule (Sprint 57.45 evidence).
```

**Acceptance**:
- New section in `docs/rules-on-demand/frontend-mockup-fidelity.md` codifying the rule
- Sprint 57.45 case study referenced as concrete evidence
- Cross-reference to `.claude/rules/sprint-workflow.md` §Step 2.5 Prong 2 (content verify methodology)
- File header MHist 1-line entry per `.claude/rules/file-header-convention.md`

### US-2: AD-TenantSettings-Backend-Schema-Extension

```
AS a backend engineer working on /tenant-settings page real-data migration
I WANT TenantSettingsResponse Pydantic + Tenant ORM extended with the 5 missing columns
   (region / locale / retention_days / sso_enabled / seats) plus admin PATCH endpoint
   supporting their mutation
SO THAT frontend /tenant-settings page (Sprint 57.44 fixture-first locked-in scope) can
   switch from `_fixtures.ts` static data to real backend API, unblocking Phase 58+ work.
```

**Acceptance**:
- Alembic migration `0018_tenant_settings_extension.py` creating 5 new columns with sensible defaults
- Tenant ORM (`backend/src/infrastructure/db/models/identity.py`) extended with 5 typed columns
- TenantSettingsResponse Pydantic model extended with 5 fields
- Admin PATCH endpoint accepts 5 new fields (with permission check)
- Multi-tenant rule preserved: all queries filtered by tenant_id; RLS policy unchanged (Tenant table is admin-only, no per-user tenant_id)
- pytest backend tests verifying GET/PATCH for 5 new fields (≥10 NEW tests)
- mypy --strict 0 errors
- File headers updated per convention

### US-3: AD-MockupCapture-Method-Resolution

```
AS a frontend sprint AI assistant running mockup vs production visual comparison
I WANT the mockup screenshot capture method documented + implemented (chosen from
   Options A/B/C/D per AD-MockupCapture-03+04) so visual comparison is reproducible
SO THAT future mockup-fidelity / drift-audit work can capture authoritative mockup PNGs
   programmatically, replacing the persistent "MOCKUP not captured" blocker.
```

**Acceptance**:
- `frontend/scripts/mockup-sweep.mjs` updated with chosen method + inline rationale comment
- `docs/rules-on-demand/frontend-mockup-fidelity.md` §Mockup capture section added with method + reproduction command
- 1 test run capturing at least 1 mockup PNG (sanity check)
- File header MHist 1-line entry

---

## 4. Technical Specification

### 4.1 Task 1: AD-MockupFidelity-AuditDocSync-Rule (docs codification)

**Target**: `docs/rules-on-demand/frontend-mockup-fidelity.md`

**Add new section** (after existing rule corpus, before DoD):

```markdown
## 🛡️ Mockup File is Canonical (AuditDocSync Rule)

When an audit-derived document (audit-report.md, drift-audit, NEAR-PARITY/CATASTROPHIC
verdict) claims component X has property Y, but the mockup source file shows property Z:

**Mockup file wins. Audit doc is updated to match mockup, not the reverse.**

### Why this rule exists

Audit docs are derived artifacts (human transcription from mockup screenshots + page-level
read-through). Transcription errors propagate forward: once Sprint N's audit doc states
"tab order is A/B/C/D", Sprint N+1, N+2, ... all cite that audit doc without re-checking
the mockup source. Sprint 57.45 evidence: audit row 9 stated /chat-v2 Inspector tabs
should be "Run/Tools/Memory/Verify" but mockup `page-chat.jsx:378-381` shows
"Turn/Trace/Memory/Tree" — audit was transcription error from Sprint 57.22, propagated
forward 23 sprints unchallenged until Path B re-check.

### Day 0 Prong 2 enforcement

Every drift-audit / Phase-2 re-point Day 0 Prong 2 grep MUST include:

1. Read the mockup source file directly (e.g. `reference/design-mockups/page-*.jsx`)
2. Compare against audit-doc claim using grep
3. If discrepancy → audit doc is wrong; update audit doc to match mockup; investigate
   when transcription error was introduced

### Audit doc update protocol

When audit doc transcription error discovered:
- Add inline note: `<!-- Sprint XX.Y Day 0 Prong 2: row N claim was transcription error -->`
- Update verdict (e.g. NEAR-PARITY → PARITY) if mockup matches production
- Cross-reference Sprint XX.Y retrospective for full root cause analysis
- Log NEW carryover AD if pattern indicates broader audit-corpus integrity gap

See `.claude/rules/sprint-workflow.md` §Step 2.5 Prong 2 for content-verify methodology.
```

### 4.2 Task 2: TenantSettings Backend Schema Extension

**Target files**:
- `backend/src/infrastructure/db/models/identity.py` — Tenant ORM
- `backend/src/infrastructure/db/migrations/versions/0018_tenant_settings_extension.py` — NEW migration
- `backend/src/api/v1/admin/tenants.py` — TenantSettingsResponse + PATCH endpoint
- `backend/tests/api/v1/admin/test_tenants_settings_extension.py` — NEW tests (≥10)

**New columns** (per Sprint 57.44 D-DAY0-4):

| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `region` | `VARCHAR(32)` | NOT NULL | `'global'` | Regional setting (apac/emea/americas/global) |
| `locale` | `VARCHAR(16)` | NOT NULL | `'en-US'` | BCP-47 locale code |
| `retention_days` | `INTEGER` | NOT NULL | `90` | Data retention policy (GDPR-relevant) |
| `sso_enabled` | `BOOLEAN` | NOT NULL | `FALSE` | Identity/SSO toggle |
| `seats` | `INTEGER` | NOT NULL | `5` | Plan seat limit |

**Migration 0018**:
- `op.add_column()` for each of 5
- `op.execute()` to backfill existing rows with defaults
- `down_revision = '0017'`
- Down migration: `op.drop_column()` for each

**Pydantic TenantSettingsResponse extension**:
- Add 5 fields with appropriate types
- Update PATCH input model

**PATCH endpoint extension**:
- Accept 5 new optional fields (partial update)
- Audit log entry for each field change (existing pattern)
- Permission check: admin role only (existing)

**Tests** (≥10 NEW):
- GET tenant settings returns 5 new fields with defaults
- PATCH region updates region + audit log entry
- PATCH locale updates locale
- PATCH retention_days with negative value → 422
- PATCH sso_enabled = true → updates
- PATCH seats = 0 → 422 (must be ≥1)
- PATCH all 5 fields at once → batch update
- Multi-tenant isolation preserved (tenant_a PATCH cannot affect tenant_b)
- mypy --strict 0 errors
- isort + black + flake8 clean

### 4.3 Task 3: Mockup Capture Method Resolution

**Investigation** (Day 0.8):
- Read `frontend/scripts/mockup-sweep.mjs` current state
- Identify what's blocking mockup PNG capture
- Compare Options A (direct Playwright on mockup HTML) / B (static file serve via python -m http.server) / C (byte-proxy from page-*.jsx) / D (real browser via headless Chrome)

**Decision criteria**:
- Option A: simplest if mockup is renderable standalone HTML/JSX
- Option B: works for static `reference/design-mockups/index.html` if present
- Option C: requires JSX → HTML transpile step
- Option D: most accurate but slowest

**Recommended path** (per Sprint 57.43 AD-MockupCapture-03 note): **Option B** (static file serve) — `reference/design-mockups/` is renderable as static HTML via `python -m http.server` per `CLAUDE.md` §Frontend Mockup-Fidelity Hard Constraint already-documented "Playwright 截圖 mockup（`python -m http.server`）vs production, 1440×900".

**Implementation**:
- Update `mockup-sweep.mjs` to:
  - Start `python -m http.server` on port 4173 (or detect already running)
  - Playwright navigate to `http://localhost:4173/reference/design-mockups/page-<name>.html` (if HTML build exists) OR fall back to JSX-render approach
  - Capture 1440×900 PNG to `claudedocs/screenshots/mockup-<name>.png`
- Add usage section to `frontend-mockup-fidelity.md`
- Add 1 sanity test run capturing 1 PNG

---

## 5. File Change List

### New files
- `backend/src/infrastructure/db/migrations/versions/0018_tenant_settings_extension.py`
- `backend/tests/api/v1/admin/test_tenants_settings_extension.py`
- `claudedocs/4-changes/feature-changes/CHANGE-XXX-tenant-settings-schema-extension.md`
- `claudedocs/4-changes/feature-changes/CHANGE-XXX-mockup-capture-method.md`
- `claudedocs/4-changes/feature-changes/CHANGE-XXX-mockup-fidelity-auditdocsync-rule.md`

### Modified files
- `docs/rules-on-demand/frontend-mockup-fidelity.md` (Task 1 + Task 3 doc section)
- `backend/src/infrastructure/db/models/identity.py` (Task 2 — Tenant ORM +5 columns)
- `backend/src/api/v1/admin/tenants.py` (Task 2 — TenantSettingsResponse + PATCH)
- `frontend/scripts/mockup-sweep.mjs` (Task 3 — method implementation)

### Untouched (drift verify)
- `frontend/src/features/tenant-settings/_fixtures.ts` (Sprint 57.44 fixture stays; migration is additive — fixtures align defaults)
- All Sprint 57.44 frontend tenant-settings components (zero frontend code change in Sprint 57.46)

---

## 6. Workload

**Bottom-up est**: ~8.5 hr
- Task 1 (docs codification): 1.5 hr
- Task 2 (backend schema + migration + tests): 4 hr
- Task 3 (mockup capture investigate + impl): 1.5 hr
- Day 0 三-prong: 0.5 hr
- Day 2 closeout + retro + memory + commit: 1 hr

**Class-calibrated commit** (HYBRID weighted blend):
- docs/template ~25% × 0.40 = 0.10
- medium-backend ~50% × 0.80 = 0.40
- infra/tooling ~15% × 0.55 = 0.0825
- closeout ~10% × 0.80 = 0.08
- = **0.66 mid-band** ≈ 0.65 HYBRID class multiplier
- 8.5 × 0.65 = **~5.5 hr committed**

**Agent-adjusted commit** (under `agent_factor = 0.45`):
- 5.5 × 0.45 = **~2.5 hr agent-adjusted**
- Day 1 ≥80% via code-implementer agent → `agent-delegated: yes` triggers

**4-segment form** (per `.claude/rules/sprint-workflow.md` §Active Agent Delegation Factor Modifier):
> Bottom-up est ~8.5 hr → class-calibrated commit ~5.5 hr (mult ~0.65) → agent-adjusted commit ~2.5 hr (`agent_factor` 0.45)

**`agent_factor = 0.45` 1st validation goal**:
- Sprint 57.46 retro Q4 will compute ratio actual/committed-with-agent-factor
- Predicted bullseye if 0.45 calibrated correctly: ~1.0 (i.e. actual ~2.5 hr)
- Per rollback rule "2 sprints with ratio < 0.7 → tighten to 0.35 OR Option B per-class split"
- Sprint 57.46 is 1st of 3-sprint window evaluation

---

## 7. Acceptance Criteria

| # | Criterion | Verify |
|---|---|---|
| AC-1 | frontend-mockup-fidelity.md AuditDocSync rule section added with Sprint 57.45 case study | grep `AuditDocSync` in target file → ≥1 match |
| AC-2 | Tenant ORM has 5 NEW columns (region/locale/retention_days/sso_enabled/seats) | grep target columns in `identity.py` → 5 matches |
| AC-3 | Alembic 0018 migration created + applied locally | `alembic upgrade head` succeeds; `alembic current` shows 0018 |
| AC-4 | TenantSettingsResponse Pydantic + PATCH endpoint extended | grep 5 new fields in `tenants.py` |
| AC-5 | ≥10 NEW pytest tests covering GET/PATCH for 5 new fields + multi-tenant isolation | pytest count delta ≥ 10 |
| AC-6 | mypy --strict 0 errors | `mypy backend/src` → 0 errors |
| AC-7 | Backend lint clean (black + isort + flake8) | `black . && isort . && flake8 .` → exit 0 |
| AC-8 | 9 V2 lints all green | `python scripts/lint/run_all.py` → 9/9 |
| AC-9 | LLM SDK leak guard: 0 imports | existing CI lint |
| AC-10 | mockup-sweep.mjs updated with chosen method + inline rationale | Read file; verify method + comment |
| AC-11 | frontend-mockup-fidelity.md mockup-capture section added | grep section header |
| AC-12 | 1 sanity mockup PNG captured | file exists at expected path |
| AC-13 | File headers updated per convention (MHist 1-line) | grep MHist entries newest-first |
| AC-14 | 3 CHANGE-XXX records under `claudedocs/4-changes/feature-changes/` | ls dir; 3 NEW files |
| AC-15 | Day 0 三-prong report logged in progress.md Day 0 section | Read progress.md |

---

## 8. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| **Risk class B — cross-platform mypy `unused-ignore`** | Medium | Use `# type: ignore[X, unused-ignore]` dual-code pattern per `.claude/rules/code-quality.md` |
| Tenant ORM column type mismatch (D-DAY0 Prong 3 schema-grep catch) | Medium | Day 0.8 Prong 3 verify against `0014_phase56_1_saas_foundation.py` (Tenant table source) before drafting migration |
| Mockup capture: no static HTML build exists for mockups | Medium-High | Investigate `reference/design-mockups/` structure during Day 0.8; if no HTML build → fall back Option C (JSX→HTML transpile) OR document Option D for Phase 58+ |
| Audit doc transcription rule too abstract → future AI ignores | Low | Include Sprint 57.45 concrete case study in rule text; cross-reference Day 0 Prong 2 grep methodology |
| Multi-tenant rule violation in test fixture | Low | All tests must inject tenant_id; use existing `make_admin_jwt` helper |
| Migration 0018 backfill failure on prod-sized data | Low (dev only) | Migration is local dev only; defaults are safe (NOT NULL with sensible defaults backfilled in same statement) |
| **`agent_factor = 0.45` over-corrects** → ratio > 1.20 | Medium | 1st validation; per rollback rule single > 1.20 → roll back to 0.65 |
| **`agent_factor = 0.45` under-corrects** → ratio < 0.7 | Medium | If 2nd consecutive (Sprint 57.46 + 57.47) < 0.7 → tighten to 0.35 OR Option B per-class split |

---

## 9. Carryover ADs (for next sprint pickup)

If Sprint 57.46 closes cleanly, carryover ADs are:

- `AD-AdminTenants-Backend-Schema-Extension` (still BLOCKING Phase 58+) — Sprint 57.43 D-DAY0-6 source; 5 of 9 admin tenant list columns missing (NOT this sprint's scope; Sprint 57.46 closes /tenant-settings subset only)
- Potential NEW from Sprint 57.46 Day 0 三-prong findings
- `agent_factor = 0.45` calibration trend (track in `sprint-workflow.md` §Active block)

---

**Modification History**:
- 2026-05-26: Sprint 57.46 Day 0.1 — Initial draft (3-AD multi-domain bundle; closes 3 carryover ADs from Sprint 57.42-45 wave; 1st `agent_factor = 0.45` validation)
