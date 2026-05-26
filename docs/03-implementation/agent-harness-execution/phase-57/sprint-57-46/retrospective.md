# Sprint 57.46 Retrospective — Multi-Domain Bundle (3 AD Closure Wave)

**Date closed**: 2026-05-26
**Branch**: `feature/sprint-57-46-multi-domain-bundle`
**Day 1 commit SHA**: `9ca648bb` (code-implementer agent)
**Day 0.1 commit SHA**: `3fcf8722` (main Claude plan + checklist)
**Phase progress**: V2 22/22 + SaaS Stage 1 3/3 + Phase 57+ Frontend (Phase-2 epic + NEAR-PARITY clean DUAL CLEAN milestone unchanged — Sprint 57.46 is cross-cutting carryover closure, not Phase-2 progress)

---

## Q1 — What went well

1. **3 carryover ADs closed in 1 batched sprint** (vs 3 separate sprints):
   - AD-MockupFidelity-AuditDocSync-Rule codified in `frontend-mockup-fidelity.md` (Track A)
   - AD-TenantSettings-Backend-Schema-Extension shipped (Track B — migration 0018 + Tenant ORM + Pydantic + PATCH + 12 NEW tests)
   - AD-MockupCapture-Method-Resolution resolved (Track C — D-DAY0-5 revelation that `mockup-sweep.mjs` already implements Option B, scope reduced ~1 hr)

2. **Day 0 三-prong ROI continues to validate**: 6 drift findings caught in ~45 min, including the high-value D-DAY0-5 (Track C scope -1 hr) and D-DAY0-1 (test path correction `admin/` → `integration/api/`). Without 三-prong, Track C would have wasted ~1 hr re-implementing Option B from scratch.

3. **Test count delta +12 (156 → 168)** exceeded ≥10 target (+20%):
   - 1 GET defaults + 5 PATCH happy + 1 batch + 4 validator 422 + 1 multi-tenant isolation = 12 tests
   - 168/168 PASSED in 18.21s; 0 regressions; 1 expected schema-shape update (10 → 15 keys in `test_get_tenant_response_shape`)

4. **mypy --strict 0 errors** across 3 modified files; **black + isort + flake8** clean after 3 MHist/comment E501 trims; **alembic 0017 → 0018** applied cleanly to dev DB.

5. **Multi-tenant rule preserved**: D-DAY0-3 audit found Tenant table is intentionally global (per `0009_rls_policies.py:36` — Tenant IS the root, no `tenant_id` self-reference); RLS unchanged. Multi-tenant isolation test added (1 of 12) verifying tenant_a admin JWT cannot PATCH tenant_b.

6. **Code-implementer agent delegation pattern (14th-15th consecutive)** held up under tightened `agent_factor = 0.45`: agent autonomously executed Day 0.8 三-prong → Day 1 all 3 tracks → validation sweep → Day 1 commit + 3 CHANGE records, with iterative lint fixes (E402 import-order + 3 MHist trims) self-corrected.

## Q2 — What didn't go well

1. **Ratio actual/committed-with-agent-factor ~1.60 ABOVE [0.85, 1.20] band by 0.40**:
   - Bottom-up est: ~8.5 hr (plan §6)
   - Class-calibrated commit: ~5.5 hr (mult ~0.65 mixed-multidomain-bundle)
   - Agent-adjusted commit: ~2.5 hr (agent_factor 0.45 — 1st validation)
   - Actual: ~4.0 hr
   - **Ratio: ~1.60 (40% over band upper edge)** = **1st rollback-trigger > 1.20 data point**
   - Per `.claude/rules/sprint-workflow.md` §Active block Rollback rule: "1 sprint with ratio > 1.20 → roll back to 0.65 (single-data-point caution)" → **`agent_factor` 0.45 → 0.65 effective Sprint 57.47+**
   - Root cause: agent_factor 0.45 over-credited the speedup; observed agent speedup was ~2.1× (not the ~5× that drove the activation from 0.55 → 0.45 at Sprint 57.44 retro). Sprint 57.46 was a more complex multi-track sprint with iterative lint cycles + 三-prong overhead, not the pure-mechanical mockup-strict-rebuild pattern that fed Sprint 57.40-44 activation data.

2. **D-DAY0-1 test path drift caught at Day 0.8** (not at plan §5.2 File Change List drafting): plan referenced `backend/tests/api/v1/admin/test_tenants_settings_extension.py` but actual pattern is `backend/tests/integration/api/test_admin_tenant_*.py`. Caught by Prong 1 path verify; required 5-min correction in plan File Change List + checklist Day 1.2 task. Cost ≈ 5 min; benefit caught BEFORE Day 1 code (would have cost ~30 min to retro-fit tests into correct dir).

3. **1 pre-existing AP-4 lint noise** unrelated to Sprint 57.46 scope was noted by agent in 9 V2 lint sweep (`frontend/src/pages/auth/{invite,login,register}` — orthogonal to backend bundle). Not addressed — out of plan scope; logged for future sprint.

4. **Day 0.1 + 0.8 commit deferred** to combine with Day 1 commit (per agent instruction): minor checklist §0.9 deviation; should have been separate `chore(sprint-57-46): Day 0` commit for cleaner audit trail (parent's call, not agent's fault).

## Q3 — What we learned (generalizable lessons)

1. **`agent_factor = 0.45` is too aggressive for multi-track bundles**: the 0.45 activation evidence (Sprint 57.40-44) came from 5 consecutive single-domain `mockup-strict-rebuild` sprints with predictable mechanical port patterns. Multi-domain bundles with iterative lint cycles + 三-prong overhead show smaller agent speedup (~2.1× observed vs ~5× implied by 0.45). **Future sprint plans should classify Day 1 work by sub-class**: single-domain mechanical → 0.45; multi-domain mixed-bundle → 0.65 (effectively the new rollback target).

2. **D-DAY0-5 pattern — "feature already implemented" discovery**: Track C found `mockup-sweep.mjs` already implements Option B with full Playwright + python -m http.server pattern documented in script header. Pattern lesson: **Day 0.8 Prong 2 content-verify must read target tool/script files in full BEFORE drafting plan §4 spec sections**, not just grep for absence of feature. Would have saved Sprint 57.43-44's repeated "AD-MockupCapture-03+04 deferred" carryover entries — Track C was already solved 23 sprints ago and the carryover was a documentation gap, not a feature gap.

3. **D-DAY0-1 pattern — "test path convention drift"**: future sprints touching test paths should add to Day 0 三-prong Prong 1 a 2-line `glob backend/tests/integration/**/test_admin_tenant_*.py` + `glob backend/tests/api/v1/admin/*.py` comparison; pattern drift between sprint memories and actual repo is common (V2 had a refactoring wave that moved tests; subsequent plans inherit outdated path memory).

4. **3-AD bundle pattern works well for small (~1-2 hr each) independent tracks** when:
   - Tasks have zero cross-dependency (Track A docs / Track B backend / Track C tooling)
   - Each ≤ 4 hr bottom-up (single PR doesn't get unwieldy)
   - Validation sweep is shared (single lint chain + pytest + alembic upgrade head)
   - Agent can parallel-process via sequential tool use within same agent session

## Q4 — Audit Debt deferred + Calibration decisions

### `agent_factor` rollback decision (MANDATORY per rollback rule)

**Sprint 57.46 ratio ~1.60 > 1.20 → ROLL BACK `agent_factor` 0.45 → 0.65 effective Sprint 57.47+**

This is the **1st rollback-trigger > 1.20** data point under tightened 0.45 baseline. Per `.claude/rules/sprint-workflow.md` §Active Agent Delegation Factor Modifier Rollback rule:
- "1 sprint with ratio > 1.20 → roll back to 0.65 (single-data-point caution)"
- Sprint 57.47+ plans MUST use `agent_factor = 0.65` in 4-segment Workload calculation
- If Sprint 57.47 also > 1.20 → roll back further to 1.0 (drop modifier entirely)
- If Sprint 57.47 < 0.7 → tighten back to 0.55

The activation at 0.55 → 0.45 (Sprint 57.44 retro) was driven by 2 consecutive `mockup-strict-rebuild` < 0.7 readings. That class is single-domain + highly-mechanical; Sprint 57.46 multi-domain bundle is structurally different (3 independent tracks + iterative validation cycles). Future calibration should track sub-class agent_factor separately when 3-sprint window evidence accumulates.

### NEW class baseline opens

**`mixed-multidomain-bundle` 0.65** — 1st app Sprint 57.46 ratio actual/bottom-up = 4.0/8.5 = **0.47**; ratio actual/committed (excluding agent_factor) = 4.0/5.5 = **0.73** BELOW [0.85, 1.20] band by 0.12 (close to lower edge).
- Class definition: multi-domain bundle with ≥2 independent tracks (docs + backend + tooling combinations); agent-delegated Day 1
- KEEP 0.65 baseline per `When to adjust` 3-sprint window rule (1-data-point insufficient)
- Pending 2-3 sprint validation; if 2nd+3rd app also ratio < 0.7 → propose 0.65 → 0.55 lift

### Carryover ADs (for Sprint 57.47+ pickup)

1. **🔴 `AD-AdminTenants-Backend-Schema-Extension`** (still BLOCKING Phase 58+) — Sprint 57.43 D-DAY0-6 source; 5 of 9 admin tenant LIST columns missing (region/locale/retention_days/sso_enabled/seats); admin TENANT-SETTINGS subset closed in Sprint 57.46 but ADMIN-TENANTS LIST/INDEX still pending (separate scope — list view uses different aggregation columns)

2. **`AD-AgentFactor-Sub-Class-Calibration`** (NEW from Sprint 57.46 retro Q3 lesson 1) — propose splitting agent_factor by Day 1 work shape: `mechanical-single-domain` 0.45 (mockup-strict-rebuild evidence) vs `mixed-multidomain-bundle` 0.65 (Sprint 57.46 evidence); validate over 3-5 sprint window before promoting

3. **`AD-Frontend-AP4-Pre-Existing-Lint`** (NEW) — pre-existing AP-4 in `frontend/src/pages/auth/{invite,login,register}` noted by Sprint 57.46 V2 lint sweep; orthogonal to backend bundle; ~30 min cleanup sprint candidate

4. **`AD-Day0-Prong2-Tool-Script-Full-Read`** (NEW from Sprint 57.46 Q3 lesson 2) — codify rule "Day 0.8 Prong 2 must read tool/script files in full, not just grep for absence, when plan spec section claims new feature implementation"; fold into `.claude/rules/sprint-workflow.md` §Step 2.5 Prong 2 next revision

5. **`AD-MockupCapture-Frontend-Visual-Diff-Pipeline`** (DEFERRED to Phase 58+) — current `mockup-sweep.mjs` Option B works for screenshot capture but no automated visual-diff pipeline (frame compare / SSIM / pixel diff) integrated; manual eye-ball still required for fidelity verdict; future infra sprint candidate

### NOT carried (closed in Sprint 57.46)

- ✅ AD-MockupFidelity-AuditDocSync-Rule (closed via Track A codification)
- ✅ AD-TenantSettings-Backend-Schema-Extension (closed via Track B; **note**: tenant-settings subset only; admin-tenants LIST is separate AD-AdminTenants-Backend-Schema-Extension still pending)
- ✅ AD-MockupCapture-Method-Resolution (closed via Track C — D-DAY0-5 revelation; AD-MockupCapture-03+04 historical carryovers superseded)
- ✅ AD-Sprint-Plan-Agent-Delegation-Factor-Sprint-57.46-FirstValidation (closed via this retro Q4 rollback decision)

## Q5 — Next steps (rolling planning §6 — candidate list only, NOT specific assignments)

Per rolling planning §6 (do NOT pre-write Sprint 57.47 plan), candidate directions for Sprint 57.47+:

1. **`AD-AdminTenants-Backend-Schema-Extension`** 🔴 BLOCKING — ~3-5 hr backend schema extension for admin tenant LIST view (5 missing columns), mirroring Sprint 57.46 Track B pattern (now well-internalized agent-delegated pattern); high pattern-reuse ROI
2. **`AD-AgentFactor-Sub-Class-Calibration`** validation — track sub-class agent_factor across Sprint 57.47 (under rolled-back 0.65) + Sprint 57.48 to gather 3-data-point window
3. **`AD-Frontend-AP4-Pre-Existing-Lint`** cleanup — ~30 min low-priority hygiene
4. **Phase 58+ Tier 1 IaC + DR drill** — strategic infra wave (~15-20 hr standalone sprint)
5. **`AD-MockupCapture-Frontend-Visual-Diff-Pipeline`** — ~5-8 hr infra/tooling sprint
6. **Pause session** — DUAL CLEAN milestone (Sprint 57.45) + 3-AD closure wave (Sprint 57.46) is a natural extended break point

## Q6 — Solo-dev policy validation

- ✅ enforce_admins=true preserved; admin cannot push directly to main
- ✅ review_count=0 (solo dev) preserved per 53.2 permanent policy
- ✅ 4 active required CI checks: backend-ci + V2 Lint expected on PR (no docs-only paths-filter exception since Track B touches `backend/src/**`)
- ✅ Conventional commit format: Day 0.1 `chore(sprint-57-46)` + Day 1 `feat(sprint-57-46)` + Co-Authored-By line preserved
- ✅ No `--no-verify` / `--force` / `--admin` bypass used

## Q7 — N/A SKIP

Per Sprint 57.8-57.45 precedent: Q7 is reserved for design-note 8-Point Quality Gate verification on **spike** sprints. Sprint 57.46 is a **carryover-closure bundle** (not a spike); no design note required. Track A's AuditDocSync rule is a `.claude/rules/`-adjacent operational rule in `docs/rules-on-demand/`, not a `agent-harness-planning/` spike-extract design note. Skipping Q7 is precedent-consistent.

---

## Calibration Summary

| Metric | Value |
|---|---|
| Class | `mixed-multidomain-bundle` 0.65 (NEW 1st app baseline) |
| `agent_factor` applied | 0.45 (tightened 2026-05-26 per Sprint 57.44 retro) |
| Bottom-up est | ~8.5 hr |
| Class-calibrated commit | ~5.5 hr |
| Agent-adjusted commit | ~2.5 hr |
| Actual | ~4.0 hr |
| ratio actual/bottom-up | 0.47 |
| ratio actual/class-committed | 0.73 (BELOW band by 0.12, close to lower edge) |
| **ratio actual/committed-with-agent-factor** | **~1.60 ABOVE band by 0.40 = 1st rollback-trigger > 1.20** |
| `agent_factor` rollback decision | **0.45 → 0.65 effective Sprint 57.47+** (single-data-point caution) |
| Cumulative consecutive code-implementer delegations | 14th+15th (across Day 0.8 + Day 1) |

---

**Modification History**:
- 2026-05-26: Sprint 57.46 Day 2 closeout — Initial retrospective (3-AD multi-domain bundle; `agent_factor 0.45` 1st validation rollback to 0.65 triggered)
