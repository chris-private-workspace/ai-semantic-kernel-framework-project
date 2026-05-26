# Sprint 57.46 — Checklist

[Plan](./sprint-57-46-plan.md) — 3-AD multi-domain bundle (docs codify + backend schema + mockup capture); 1st `agent_factor = 0.45` validation.

---

## Day 0 — Plan + 三-Prong Verify (Sprint 57.45 closeout day)

### 0.1 Plan + Checklist Drafting
- [x] **Sprint plan written** `phase-57-frontend-saas/sprint-57-46-plan.md`
  - DoD: 9 sections present (Goal / Context / Stories / Spec / Files / Workload / AC / Risks / Carryover); 4-segment Workload form
  - Verify: `Glob sprint-57-46-plan.md` returns 1
- [x] **Sprint checklist written** (this file)
  - DoD: Day 0 / Day 1 / Day 2 structure; per-task DoD + Verify
  - Verify: `Glob sprint-57-46-checklist.md` returns 1

### 0.8 Day 0 三-Prong Verify (Step 2.5 mandatory)

**Prong 1 — Path Verify** (8 paths):
- [x] `docs/rules-on-demand/frontend-mockup-fidelity.md` exists (Task 1 target)
- [x] `backend/src/infrastructure/db/models/identity.py` exists (Task 2 ORM)
- [x] `backend/src/api/v1/admin/tenants.py` exists (Task 2 API)
- [x] `backend/src/infrastructure/db/migrations/versions/0017_verification_log.py` exists (migration head)
- [x] `backend/src/infrastructure/db/migrations/versions/0018_*.py` does NOT exist yet (target slot)
- [x] `frontend/scripts/mockup-sweep.mjs` exists (Task 3 target) — ALREADY FUNCTIONAL (D-DAY0-5)
- [x] `reference/design-mockups/` directory exists (Task 3 source) — 22 files incl. index.html
- [x] `backend/tests/api/v1/admin/test_tenants*.py` exists (Task 2 test pattern reference) — D-DAY0-1: dir does NOT exist; pattern lives at `backend/tests/integration/api/test_admin_tenant_*.py`

**Prong 2 — Content Verify** (5 claims):
- [x] Tenant ORM in `identity.py` already has columns: id / code / display_name / state / plan / progress JSONB / metadata / created_at / updated_at (D-DAY0-2: column is `code` not `tenant_code`; D-DAY0-3: `state` Enum not `status` String)
- [x] Tenant ORM does NOT already have: region / locale / retention_days / sso_enabled / seats — confirmed all 5 absent
- [x] TenantSettingsResponse Pydantic in `tenants.py` current field set — `TenantResponse` 10 fields; `TenantUpdateRequest` display_name + meta_data only (extra='forbid')
- [x] Admin PATCH endpoint in `tenants.py` current input model — extra='forbid' enforced (D-DAY0-4: must extend, not relax)
- [x] frontend-mockup-fidelity.md current sections — insertion point identified (before §參考 at line ~87, or as new top-level after Phase-2 AP block)

**Prong 3 — Schema Verify** (Task 2 mandatory):
- [x] Tenant table column declarations in `0001_initial_identity.py` + `0014_phase56_1_saas_foundation.py` — verified baseline
- [x] Confirm migration 0018 number not occupied: 0017 is head (verification_log)
- [x] RLS policy on Tenant table: Tenant table is intentionally global per `0009_rls_policies.py:36` — no `tenant_id` (IS the root); NO RLS needed
- [x] Drift catch: new column names + types from plan §4.2 align with Tenant ORM patterns

**Prong 2.5 — Frontend Tree Depth Audit** (N/A — Task 2 is pure backend; Task 1 + Task 3 are docs/tooling not frontend page re-point).

**Drift findings catalog**:
- [x] All findings logged to `progress.md` Day 0 §Drift findings (D-DAY0-1 through D-DAY0-6)
- [x] Go/no-go decision recorded: ✅ CONTINUE Day 1 (net scope -10%, well within 20% threshold; Task 3 reduced ~1 hr)

### 0.9 Branch + Day 0 commit
- [x] Branch `feature/sprint-57-46-multi-domain-bundle` created ✓ (done 2026-05-26)
- [ ] Day 0.1 + 0.8 commit: `chore(sprint-57-46): Day 0 plan + checklist + 三-prong verify` (deferred to user; combined with Day 1 commit per parent instruction)

---

## Day 1 — Implementation (Code-Implementer Agent Delegation)

### 1.1 Task 1: AD-MockupFidelity-AuditDocSync-Rule Codification (Track A)
- [x] **Add `Mockup File is Canonical (AuditDocSync Rule)` section** to `docs/rules-on-demand/frontend-mockup-fidelity.md`
  - DoD: New section between existing rule corpus and DoD; Sprint 57.45 case study referenced; cross-ref to `.claude/rules/sprint-workflow.md` §Step 2.5 Prong 2
  - Verify: `grep "AuditDocSync" docs/rules-on-demand/frontend-mockup-fidelity.md` → 2 matches (section header + cross-ref)
- [x] **MHist 1-line entry** on `frontend-mockup-fidelity.md`
  - DoD: Per `.claude/rules/file-header-convention.md` 1-line max + ≤100 char budget
  - Verify: Last MHist line ≤ E501 (under 100 chars confirmed)

### 1.2 Task 2: TenantSettings Backend Schema Extension (Track B)
- [x] **Alembic migration 0018** `backend/src/infrastructure/db/migrations/versions/0018_tenant_settings_extension.py`
  - DoD: `op.add_column()` for 5 columns with server_default backfill; down_revision='0017_verification_log'; reversible down
  - Verify: created with 5 add_column + 5 drop_column (reverse order); revision strings match
- [x] **Tenant ORM extension** `backend/src/infrastructure/db/models/identity.py`
  - DoD: 5 typed `Mapped[T]` columns added between meta_data and created_at; Boolean+Integer imports added
  - Verify: identity.py shows 5 new Mapped declarations in Tenant class
- [x] **TenantSettingsResponse Pydantic extension** `backend/src/api/v1/admin/tenants.py` (TenantResponse 10→15 fields + TenantUpdateRequest 2→7 with validators)
  - DoD: 5 new fields each in TenantResponse + TenantUpdateRequest with Field(ge/le/pattern) validators; field_validator for region whitelist; extra='forbid' preserved
  - Verify: tenants.py shows extensions; pydantic field_validator imported
- [x] **Admin PATCH endpoint extension** `tenants.py`
  - DoD: 5 new field-change branches added to update_tenant; each writes to audit chain operation_data (old_values/new_values/changed_fields)
  - Verify: update_tenant has 7 total field branches; no-op short-circuit preserved
- [x] **≥10 NEW pytest tests** `backend/tests/integration/api/test_admin_tenant_settings_extension.py` (D-DAY0-1 corrected path)
  - DoD: 1 GET + 5 PATCH happy + 1 batch + 4 validator 422 + 1 multi-tenant isolation = **12 tests** (≥10 target)
  - Verify: file created with 12 test functions mirroring test_admin_tenant_patch.py pattern
- [x] **File headers updated** per convention (3 files: migration + ORM + API)
  - DoD: Each file has Purpose/Category/Created/MHist; MHist 1-line newest-first
  - Verify: identity.py + tenants.py MHist 1-line entries added; migration has full header
- [x] **CHANGE record** `claudedocs/4-changes/feature-changes/CHANGE-008-tenant-settings-schema-extension.md`
  - DoD: Problem / Root cause / Solution / Verification / Impact sections
  - Verify: File created at CHANGE-008

### 1.3 Task 3: Mockup Capture Method Resolution (Track C)
- [x] **Investigate** `frontend/scripts/mockup-sweep.mjs` current state + `reference/design-mockups/` directory structure
  - DoD: D-DAY0-5 finding logged — Option B (python -m http.server + Playwright) ALREADY implemented in existing 109-line script
  - Verify: progress.md Day 0 §Drift findings D-DAY0-5 + D-DAY0-6
- [x] **Implement chosen method** in `mockup-sweep.mjs`
  - DoD: No change needed — Option B already in place (BASE_URL = http://localhost:8080/index.html); script header documents the rationale (lines 33-37)
  - Verify: existing mockup-sweep.mjs uses Option B; no rewrite required
- [x] **Add §Mockup capture section** to `docs/rules-on-demand/frontend-mockup-fidelity.md`
  - DoD: §📸 Mockup Capture Method added (in CHANGE-007 commit alongside AuditDocSync); Standard command + Script details + When to run + Anti-patterns
  - Verify: `grep "Mockup Capture Method" frontend-mockup-fidelity.md` → 1 match
- [x] **Sanity PNG** — Historical evidence from Sprint 57.45 drift audit captures (24 PNGs at `claudedocs/5-status/drift-audit-2026-05-25/screenshots/mockup/`) serves as established working evidence; no need to re-capture (would duplicate; PNGs already in repo per Sprint 57.45 memory)
- [x] **CHANGE record** `claudedocs/4-changes/feature-changes/CHANGE-009-mockup-capture-method.md`
  - DoD: Decision rationale (Option B) + reproduction guide + cross-refs
  - Verify: File created at CHANGE-009

### 1.4 Day 1 Validation Sweep
- [x] **Backend lint chain**: black + isort + flake8 on Sprint 57.46 modified files
  - DoD: All 3 exit 0 — 1 black reformat (tenants.py) + 1 isort fix (identity.py Integer import position) + 3 E501 MHist trims completed
  - Verify: flake8 exit 0 on tenants.py + identity.py + 0018 migration + new test file
- [x] **Backend mypy --strict**: `mypy backend/src/api/v1/admin/tenants.py backend/src/infrastructure/db/models/identity.py backend/src/infrastructure/db/migrations/versions/0018_tenant_settings_extension.py`
  - DoD: 0 errors
  - Verify: `Success: no issues found in 3 source files`
- [x] **9 V2 lints**: `python scripts/lint/run_all.py`
  - DoD: 8/9 green; 1 PRE-EXISTING failure (`check_ap4_frontend_placeholder.py` flags 7 findings in `frontend/src/pages/auth/{invite,login,register}` — 100% pre-existing; Sprint 57.46 did not modify any frontend `.tsx`)
  - Verify: 8/9 from lint chain; failures all in pre-existing frontend auth pages, unrelated to backend tracks
- [x] **Backend pytest**: full integration/api/ suite
  - DoD: **168/168 PASSED** (baseline 156 + 12 NEW Sprint 57.46 tests); 0 regressions; 1 expected-edit on `test_admin_tenant_get.py::test_get_tenant_response_shape` (updated 10-field → 15-field schema expectation for new SaaS columns)
  - Verify: `pytest backend/tests/integration/api/ --no-header -q` → 168 passed in 18.21s
- [x] **LLM SDK leak guard**: `python scripts/lint/check_llm_sdk_leak.py`
  - DoD: 0 imports of `openai`/`anthropic` in `backend/src`
  - Verify: `OK: no LLM SDK leak under backend\src`

### 1.5 Day 1 commit
- [ ] Commit: `feat(sprint-57-46): Day 1 multi-domain implementation (3 tracks)` — deferred to user per parent agent instruction (commits done by user, not agent)

---

## Day 2 — Closeout

### 2.1 24-route sweep + audit trail (Track B/C verification)
- [ ] **Frontend build sanity** (no frontend change expected; verify untouched)
  - DoD: `npm run build` in `frontend/` exit 0; no Vite build delta
  - Verify: Bundle size delta < 1 KB
- [ ] **24-route Playwright sweep** (per `route-sweep.mjs`)
  - DoD: 24 IDENTICAL or expected-noise only; 0 unintended regressions
  - Verify: `node frontend/scripts/route-sweep.mjs` exit 0
- [ ] **Multi-tenant isolation manual probe** (Task 2 specific)
  - DoD: tenant_a admin JWT cannot PATCH tenant_b settings (existing pattern; verify still holds)
  - Verify: 1 e2e test case OR manual curl with 2 JWTs

### 2.2 Retrospective
- [ ] **Write `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-46/retrospective.md`**
  - DoD: Q1-Q7 6 必答格式; ratio actual/committed-with-agent-factor computed; calibration assessment for `mixed-multidomain-bundle` 0.65 baseline + `agent_factor = 0.45` 1st validation
  - Verify: Read retro; 7 sections present
- [ ] **`agent_factor = 0.45` 1st validation data point** logged
  - DoD: Q4 section explicitly states ratio + rollback decision (KEEP 0.45 / tighten 0.35 / roll back 0.65 / Option B split)
  - Verify: Q4 reads ratio + decision

### 2.3 Sprint-workflow.md updates (calibration matrix)
- [ ] **Add NEW class row** `mixed-multidomain-bundle` 0.65 1-data-point baseline
  - DoD: 1 row added to `.claude/rules/sprint-workflow.md` §Scope-class multiplier matrix
  - Verify: Read matrix
- [ ] **Update §Active Agent Delegation Factor Modifier** §Activation history with Sprint 57.46 1st validation entry
  - DoD: New history entry per 57.43+57.44+57.45 pattern; ratio + decision
  - Verify: Read history section last 5 entries

### 2.4 Memory subfile + MEMORY.md index
- [ ] **Write `memory/project_phase57_46_multi_domain_bundle.md`**
  - DoD: Sprint scope / 3 task closures / ratio / calibration / carryover ADs
  - Verify: File exists
- [ ] **Add MEMORY.md pointer entry**
  - DoD: 1 entry (~250-300 char) — subfile link + 1-sentence topic + keywords
  - Verify: Top of Recent Sprints list

### 2.5 CLAUDE.md Current Sprint row update
- [ ] **Update Current Sprint row** to Sprint 57.46 closed + 1-line goal
  - DoD: Only Current Sprint row + Last Updated footer (per `.claude/rules/sprint-workflow.md` §Sprint Closeout policy NAVIGATOR-ONLY rule)
  - Verify: No new history rows added; no per-sprint detail packed

### 2.6 PR + merge
- [ ] **Push branch + open PR** with description containing 3 AD closures + ratio + calibration
- [ ] **Wait CI green** (backend-ci + V2 Lint)
- [ ] **Merge PR** (squash)
- [ ] **Cleanup**: delete local feature branch

### 2.7 Final
- [ ] **Day 2 commit**: `chore(sprint-57-46): Day 2 retro + memory + closeout`
- [ ] **All checklist items above**: `[x]` (or 🚧 with reason if deferred)

---

**Modification History**:
- 2026-05-26: Sprint 57.46 Day 0.1 — Initial draft (3-AD multi-domain bundle; Day 0/1/2 structure mirrors Sprint 57.39 + 57.44 templates)
