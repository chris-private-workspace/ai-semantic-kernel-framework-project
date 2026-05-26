# Sprint 57.54 — Retrospective

**Sprint**: 57.54 — HITLPolicies Admin Write Endpoint + Frontend Edit Mode
**Class**: `medium-backend` 0.80 (7th data point) / `medium-frontend` 0.65 (3rd data point)
**Sub-class** (agent_factor): `mechanical-greenfield` 0.50 — **tier-3 1st validation under NEW sub-class table effective Sprint 57.53+**
**Agent-delegated**: yes — backend Track A + frontend Track B both via code-implementer (sequential)
**Branch**: `feature/sprint-57-54-hitl-policies-full-persistence` (from Sprint 57.53 tip `dc4c1680` per Path A)
**Day 0+1 commit**: `f2f95b11` (14 files / +1933 / -18)
**Date**: 2026-05-26 (Sprint 57.53 closeout same-day continuation)
**Carryover CLOSED**: `AD-AgentFactor-Tier-3-Validation-Sprint-57.54` (Sprint 57.53 carryover; 1st validation now generated under agent-delegated mode)

---

## Q1. What went well

1. **Day 0 三-prong caught critical scope-misframing at plan-drafting time**: original "Phase 58.x = NEW table + Alembic" framing WRONG. Prong 2 content verify revealed table + ORM + RLS + read-only DBHITLPolicyStore + GET endpoint + frontend read hook ALL exist since Sprint 55.3 + 57.48 + 57.49. **True scope = WRITE side only** (single component-pair: backend upsert endpoint + frontend mutation hook + tab edit mode). Caught BEFORE Day 1 work started → 0 wasted effort on duplicate table/ORM/RLS creation. ROI: ~6-8× (saved 1-1.5 hr of mis-directed work; AD-Plan-3 promotion validated again).

2. **Sequential agent delegation pattern (Track A backend → Track B frontend) worked cleanly**: backend track delivered types + endpoint first; frontend track read backend Pydantic shape from admin/tenants.py directly + adapted TypeScript types to match. No type-contract drift detected. Each agent ~25 min wall-clock. 14th + 15th consecutive frontend code-implementer delegation (Sprint 57.40-50 chain extends from 13 to 15).

3. **Sprint 57.12 + 57.53 `§Committed-Row Cleanup Pattern` extends naturally to new test scope**: when `DBHITLPolicyStore.put()` commits via shared test session, agent independently identified the cross-test collision risk + extended existing `_clear_committed_test_tenants()` with `HITL_PUT_%` LIKE sweep. Pattern is now battle-tested across 3 scopes (api, agent_harness, sibling-extension). Validates carryover `AD-Test-Cleanup-Pattern-Shared-Helper` (Sprint 57.53) — agent did the lift WITHIN this sprint instead of waiting for helper extraction.

4. **HEX_OKLCH baseline 47 preserved across edit mode UI**: frontend agent honored mockup-fidelity discipline → 0 NEW hex/oklch literals (reused `--info|--warning|--success|--danger|--btn-primary` via Badge/Card primitives). AP-2 banner intact + AP-4 frontend placeholder lint GREEN.

5. **Plan-time pattern-mirror discipline still working**: `useTenantSettingsSave.ts` (Sprint 57.9) was identified as closest precedent during Day 0; agent delegated frontend track produced verbatim mirror (`useHITLPoliciesSave.ts` 45 lines) without divergence. Demonstrates that single-source precedent files are reliable templates for future mutation hooks.

6. **Test count over-coverage acceptable**: Vitest +10 vs plan +5-8 target — agent justified with "full edit-mode coverage (Edit/Cancel/Save/disabled/error states all individually asserted)". Parent decision: accept; over-coverage > under-coverage for new UI flow. Backend +12 hit exact target (1772 PASS).

## Q2. What didn't go well

1. **D-DAY0-1 Glob false-negative**: Day 0 Prong 1 Globbed `__tests__/HITLPoliciesTab.test.tsx` → returned 0 results → checklist marked "CREATE NEW". Actual repo convention is `frontend/tests/unit/<feature>/` mirror layout (not co-located `__tests__/`). Existing `tests/unit/tenant-settings/tabs/HITLPoliciesTab.test.tsx` had 6 tests already; agent correctly adapted at Day 1. Day 0 finding was Glob-pattern-mismatch, not absence-of-tests. **Lesson 1**: Day 0 Prong 1 file-path glob should query repo's actual test layout convention; recommend grep first for any `*.test.tsx?` file containing component name vs assuming `__tests__/` pattern.

2. **Plan §6 bottom-up estimate likely too generous**: Plan estimated 3.5 hr bottom-up; actual Day 0+1 (~1.92 hr) BEFORE Day 2 closeout. Even with ~0.5-0.7 hr Day 2 estimate, total sprint will be ~2.4-2.6 hr ≈ 70% of bottom-up. Pattern: my Day 0 三-prong + plan drafting (~50 min) was longer than plan's 18 min estimate due to content-verify discovery; agent execution was ~50 min vs plan's 90+78=168 min (much faster — speedup ~3.4×). **Lesson 2**: Day 0 三-prong cost ~30 min higher than estimated when content verify surfaces misframing; offset by agent speedup. Net: ratio still above band by 0.17 — single-data-point caution rule applies.

3. **`pg_insert.on_conflict_do_update` is repo first-usage (D-DAY0-13 NOTABLE)**: pattern needed import + careful `set_` clause for `updated_at` rotation (server_default only fires on INSERT, not on conflict-update path). Agent handled correctly + documented in put() docstring. **Lesson 3**: PostgreSQL dialect-specific patterns need explicit docs comment about server_default vs explicit set_ clause behavior; future devs may hit this.

4. **Plan §3 US-2 Acceptance "Vitest +5-8" target was too tight**: full edit-mode coverage needs separate tests for Edit-toggle / Cancel-reset / Save-call-mutation / Save-disabled-while-pending / Save-error-display = 5 tab tests + 3 hook tests + 2 service tests = 10 minimum. Agent over-shipped by 2-5 vs plan; in retrospect plan target should have been +8-12. **Lesson 4**: estimate Vitest test count by listing state transitions × assertions, not by "feel"; full coverage of new UI flow with N states usually needs ~N edge-case tests + 2-3 service/hook unit tests.

## Q3. What we learned (generalizable lessons for future sprints)

### Lesson 1: Day 0 Prong 1 file-glob should query repo's actual test convention
- **Context**: D-DAY0-1 marked "NEW required" via Glob `__tests__/HITLPoliciesTab.test.tsx`; actual file existed at `tests/unit/tenant-settings/tabs/HITLPoliciesTab.test.tsx`
- **Codification**: Add to `.claude/rules/sprint-workflow.md §Step 2.5 Prong 1` (Path Verify): when checking existence of test files, glob ALL conventional patterns (`__tests__/<name>.test.*` OR `<dirname>/tests/**/<name>.test.*` OR `<name>.test.*` co-located); never single-pattern glob for test files unless repo's test layout is known
- **Future AD candidate**: `AD-Day0-Prong1-Test-Glob-Multi-Pattern` (NEW)

### Lesson 2: Phase 58.x WRITE-side pattern is reusable for FeatureFlags/Quotas/RateLimits
- **Context**: Sprint 57.54 pattern = (backend) `pg_insert.on_conflict_do_update` upsert + Pydantic write schema + PUT endpoint reusing `_load_tenant_or_404` + `_session_factory_from` + `_project_*_to_items` projection + 12 pytest tests; (frontend) mirror of `useTenantSettingsSave` + service func PUT + edit mode tab + 10 Vitest tests
- **Codification**: When Sprint 57.55+ ships FeatureFlags WRITE / Quotas WRITE / RateLimits WRITE, the same shape applies; agent can mechanically copy/adapt. Each subsequent sprint should drop to `mechanical-pattern-reuse-heavy` 0.30 (≥ 4 mechanical repetitions) IF batched 4-track; OR stay `mechanical-greenfield` 0.50 if single domain at a time.
- **Future AD candidate**: `AD-Phase58-Persistence-WriteSide-Pattern-Template` (NEW; codify the pattern in `claudedocs/4-changes/feature-changes/CHANGE-024` template)

### Lesson 3: `pg_insert.on_conflict_do_update` upsert with `updated_at` rotation
- **Context**: D-DAY0-13 NOTABLE — repo first usage of this PostgreSQL pattern
- **Codification**: Pattern: `pg_insert(Row).values(...).on_conflict_do_update(index_elements=["<unique_col>"], set_={..., "updated_at": func.now()}).returning(Row)` — `set_["updated_at"]` MUST be explicit because `server_default=func.now()` only applies on INSERT path; UPDATE path needs explicit assignment
- **Reuse**: When other admin endpoints add upsert semantics (FeatureFlags / Quotas / RateLimits / Identity write side), this pattern is the canonical reference

### Lesson 4: Vitest test count estimation = (UI state transitions) × (assertion types)
- **Context**: Plan §3 US-2 estimated +5-8 Vitest; actual +10 needed for full edit-mode coverage
- **Codification**: When estimating frontend test counts for a NEW UI flow, list:
  - State transitions (e.g. Edit toggle ON / Cancel toggle OFF / Save call / Save success / Save error)
  - Per state: assertions about visible elements + mutation calls + cache invalidation
  - Each state-assertion pair ≈ 1 test
  - Plus 2-3 unit tests for service func (happy + error paths) + mutation hook (happy + invalidate + error)
- Sprint 57.54 case: 5 tab states + 3 hook tests + 2 service tests = 10 minimum; planning target should match (not +5-8 estimate)

## Q4. Calibration

### `mechanical-greenfield` 0.50 — **TIER-3 1ST VALIDATION** (PRIMARY)

- Bottom-up est: ~3.5 hr
- Class-calibrated commit (`medium-backend` 0.80): ~2.8 hr
- Agent-adjusted commit (`agent_factor 0.50`): **~1.4 hr (~84 min)**
- **Actual Day 0+1 wall-clock**: ~115 min (Day 0 三-prong + plan/checklist drafting + Track A agent + Track B agent + cross-track validation + progress writes)
- Day 2 closeout estimate (this section + memory subfile + sprint-workflow.md + CLAUDE.md + next-phase-candidates + CHANGE-024 + commit + PR): ~45-60 min
- **Estimated Total Sprint Wall-Clock**: ~160-175 min ≈ **~2.7-2.9 hr**

**Ratio computations**:
- actual_total / agent_factor_committed = ~2.8 / 1.4 ≈ **~2.0** ABOVE band [0.85, 1.20] by ~0.8
- Day 0+1 only: 1.92 / 1.4 ≈ **1.37** ABOVE band by 0.17 (sub-validation focus; Day 2 inflates further)
- actual_total / class_committed = ~2.8 / 2.8 ≈ **~1.0** ✅ IN BAND middle (`medium-backend` 0.80 class baseline holds cleanly)
- actual_total / bottom_up = ~2.8 / 3.5 ≈ **~0.80** (bottom-up was 25% generous; multiplier 0.80 well-calibrated for human-pace; agent speedup partially absorbs this but not fully when greenfield work has irreducible complexity)

**Decision per Sprint 57.52 retro Q4 single-data-point caution rule**: **KEEP `mechanical-greenfield` 0.50**. 1 data point > 1.20 → 1st rollback-trigger candidate. **Flag Sprint 57.55+ for 2nd validation**: if also > 1.20 → propose 0.50 → 0.65 lift in Sprint 57.55 retro Q4; if < 0.7 → propose tier-4 refinement (extreme-mechanical sub-class 0.30).

**Root cause analysis (1st validation > 1.20)**:
- Sprint 57.40-44 mockup-strict-rebuild ratios under 0.60 baseline were ~0.18-0.41 (deep below band) because work was pure mechanical port (read mockup → translate to React; no design decisions)
- Sprint 57.54 is single greenfield NEW feature (backend upsert design + Pydantic write schema decisions + frontend edit-mode UX design); per-component-pair complexity inherently higher than port work
- The 0.50 baseline from `mechanical-greenfield` may have been calibrated against port-style work; true greenfield NEW feature work shows ~2x speedup vs human, not ~5x speedup seen for pure mechanical port
- Sub-class refinement candidate: split `mechanical-greenfield` into `mechanical-greenfield-port-style` (0.45) vs `mechanical-greenfield-design-decisions` (0.65) — but defer to 2nd-3rd data point evidence

### `medium-backend` 0.80 — **7TH DATA POINT** (post-confound-resolution tracking)

- Data points: 55.5=1.14 / 55.6=0.92 / 57.47=0.16 / 57.48=0.11 / 57.50=0.27 / 57.53=0.83 / **57.54=~1.0 (estimated total)**
- 7-pt mean: ~0.63 (improvement from 6-pt 0.57)
- Last 3 (57.50=0.27 + 57.53=0.83 + 57.54=~1.0): only 1/3 < 0.7 → **lower-trigger NOT MET** (need 3+ consecutive < 0.7)
- **Decision**: **KEEP `medium-backend` 0.80** per 3-sprint window rule
- 57.53 prediction "6th cleaner signal under human factor" + 57.54 1.0 IN BAND middle confirm class baseline is well-calibrated when confound stripped at sub-class layer

### `medium-frontend` 0.65 — **3RD DATA POINT** (continuing Sprint 57.49 carryover tracking)

- Data points: 57.13=0.95-1.0 / 57.49=0.064 / **57.54=TBD (frontend-only sub-portion)**
- Frontend track wall-clock: ~25 min; bottom-up est for frontend track: ~1.3 hr → ratio frontend track only = 25/78 ≈ 0.32 BELOW band by 0.53
- However: frontend track confound resolved by tier-2 sub-class split (mechanical-greenfield 0.50 sub-class applies to the whole sprint, not separately to frontend)
- 3-pt mean (95/0.064/0.32) ≈ 0.46 — below band edge; pattern persists
- **Decision**: **KEEP `medium-frontend` 0.65 baseline** per 3-sprint window rule (3 data points within rule window; if Sprint 57.55+ adds 4th and shows pattern continues → AD-medium-frontend-Baseline-Recalibration becomes actionable)
- Carryover `AD-medium-frontend-Baseline-Recalibration` continues open for Sprint 57.55+ 4th data point

## Q5. Top 3 carryover candidates for Sprint 57.55+

1. **`AD-AgentFactor-Tier-3-Validation-Sprint-57.55`** (NEW; renumbered from Sprint 57.54 carryover successfully closed) — need 2nd validation under `mechanical-greenfield` 0.50; agent-delegated single-domain NEW component-pair work; if also > 1.20 → propose 0.50 → 0.65 lift OR tier-4 refinement; candidate substrate: another Phase 58.x persistence WRITE side (FeatureFlags / Quotas / RateLimits) using same pattern as Sprint 57.54

2. **Phase 58.x WRITE-side portfolio continuation** — 3 remaining: `AD-TenantSettings-FeatureFlags-Backend-Persistence-WriteSide` + `AD-TenantSettings-Quotas-Backend-Persistence-WriteSide` + `AD-TenantSettings-RateLimits-Backend-Persistence-WriteSide`. All can use Sprint 57.54 pattern as template (pg_insert.on_conflict_do_update + Pydantic write + mutation hook + edit mode); if batched 4-track → `mechanical-pattern-reuse-heavy` 0.30 sub-class candidate; if single domain at a time → continue `mechanical-greenfield` 0.50 2nd validation

3. **`AD-medium-frontend-Baseline-Recalibration` continues** — Sprint 57.49 + 57.54 are 2nd + 3rd data points; 3-pt mean ~0.46 below band; if Sprint 57.55+ adds 4th data point and pattern persists < 0.7 → propose `medium-frontend` 0.65 → 0.50 lift

**Additional NEW carryovers** (Day 1 lessons codification candidates):
- `AD-Day0-Prong1-Test-Glob-Multi-Pattern` (NEW; Q3 Lesson 1 — codify multi-pattern test file glob in §Step 2.5 Prong 1)
- `AD-Phase58-Persistence-WriteSide-Pattern-Template` (NEW; Q3 Lesson 2 — codify Sprint 57.54 pattern as template for next 3 Phase 58.x persistence WRITE sprints)
- `AD-Sub-Class-Greenfield-Port-vs-Design-Refinement` (CONDITIONAL; Q4 root cause analysis — split `mechanical-greenfield` 0.50 into port-style vs design-decisions sub-classes if 2-3 consecutive > 1.20 patterns surface)

**Pending from Sprint 57.53 carryover** (deferred):
- `AD-Plan-Workload-AgentDelegation-Explicit-Field-Codification` — Sprint 57.54 successfully filled the field at plan time (Plan §6 + §1 explicit "Agent-delegated: yes" line); per US-3 acceptance, defer codification to Sprint 57.55+ after 1-2 more data points validate the pattern works at plan time. If Sprint 57.55 plan also fills field cleanly → ready to codify into `sprint-workflow.md §Workload Calibration §Four-segment form` as MANDATORY field.
- `AD-Test-Cleanup-Pattern-Shared-Helper` — Sprint 57.54 Track A naturally extended Sprint 57.12 + 57.53 trail by adding `HITL_PUT_%` LIKE sweep to existing `_clear_committed_test_tenants()`; the helper extraction (separate `tests/common/cleanup.py` or similar) is still deferred to Phase 58.x; pattern is now battle-tested across 3 scopes
- `AD-MediumBackend-AICadence-Recalibration` — Sprint 57.54 7th data point at ratio ~1.0 IN BAND middle (cleaner signal); pattern continues to validate `medium-backend` 0.80 + sub-class layer confound resolution; no action this sprint

## Q6. Solo-Dev Policy Validation

- Branch protection `enforce_admins=true` + `review_count=0` (solo-dev policy permanent since Sprint 53.2)
- 4 required CI checks: Backend E2E + Frontend E2E + Lint+Type+Test PG16 + v2-lints
- PR will be opened at Day 2.8; user merge via GitHub UI when CI green
- Sprint 57.53 PR #203 GitHub Actions degraded_performance status TBD at Day 2.8 time; if still degraded → Sprint 57.54 PR likely also affected; touch `.github/workflows/backend-ci.yml` header if needed (Sprint 53.2.5 workaround precedent)
- No `--admin` bypass + no `--no-verify` used; standard solo-dev workflow

## Q7. Design Note Extract — N/A SKIP

Sprint 57.54 is a feature ship (Phase 58.x WRITE side for HITLPolicies), NOT a spike sprint. Per Sprint 57.10 + 57.47-53 precedent: feature ship sprints do not produce spike-extract design notes. Lesson 2 in Q3 (Phase 58.x WRITE-side pattern reusability) is the closest equivalent to a "pattern codification document" — but it lives in this retrospective + the planned CHANGE-024 record (per CLAUDE.md `4-changes/` convention), NOT as a new `agent-harness-planning/` design doc.

---

**Modification History**:
- 2026-05-26: Sprint 57.54 Day 2 closeout — Q1-Q7 6必答 format (Q7 N/A SKIP per feature-ship precedent); `mechanical-greenfield` 0.50 1st validation ratio ~1.37 ABOVE band by 0.17 (single-data-point caution KEEP); `medium-backend` 0.80 7th data point ~1.0 IN BAND middle (KEEP); `medium-frontend` 0.65 3rd data point continues tracking; 3 NEW carryover ADs + 3 Sprint 57.53 carryovers continue
