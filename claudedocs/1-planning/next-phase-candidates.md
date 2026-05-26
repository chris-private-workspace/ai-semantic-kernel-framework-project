# Next Phase 候選 (Phase 57.22+)

**Purpose**: Open items / pending decisions / carryover ADs accumulated from prior sprint retrospectives. Single-source for "what could be next sprint". CLAUDE.md / MEMORY.md no longer carry this list per §Sprint Closeout policy ([`.claude/rules/sprint-workflow.md`](../../.claude/rules/sprint-workflow.md)).

**Selection Rule**: User explicitly selects → draft plan kicks off Sprint XX.Y; otherwise items wait here indefinitely until selected or archived.

**Updated**: 2026-05-26 (Sprint 57.50 closed — single-track 1-hr hygiene closes `AD-TenantSettings-IdentityFixture-Cleanup` via Option A fixture-projection (mirror Sprint 57.48 Track D RateLimits); **2nd validation `mechanical-single-domain` 0.45 ratio 0.58 → 2nd consec < 0.7 → ROLLBACK RULE MET → Option B tier-2 ESCALATED ACTIVATED**: NEW `mechanical-pattern-reuse-heavy` 0.30 + `mechanical-greenfield` 0.50 effective Sprint 57.51+ (parallel Sprint 57.38+57.48 precedent); 3 ADs closed (#73 + #74 + IdentityFixture-Cleanup); 4 NEW carryover ADs (#75 + #76 + #81 + AD-Stale-Docstring-Karpathy-3); 22nd consecutive code-implementer delegation; mockup-fidelity DUAL CLEAN 22/22 PARITY preserved.)

**Previous Updated**: 2026-05-26 (Sprint 57.43-57.49 batch closed; 4-sprint window landed via 14 ADs total — Phase-2 epic + NEAR-PARITY **DUAL CLEAN milestone 22/22 PARITY** reached Sprint 57.45; Phase 58+ Backend Schema Extension COMPLETE for TenantSettings 6-tab + admin-tenants LIST; Phase 58+ Frontend Real-Data Migration COMPLETE for /tenant-settings + /admin-tenants Members; Sprint 57.48 Option B sub-class split ACTIVATED.)

**Previous Updated**: 2026-05-25 (Sprint 57.42 closed; Option A `agent_factor = 0.55` ACTIVATED — later SUPERSEDED Sprint 57.48 via Option B sub-class split.)

---

## 🆕 Sprint 57.50 Carryover (2026-05-26 — TenantSettings Identity Fixture Cleanup; Option B Tier-2 ESCALATION)

Sprint 57.50 (`AD-TenantSettings-IdentityFixture-Cleanup`) ✅ **CLOSED**: single-track 1-hr hygiene migrates `IDENTITY_FIXTURE` 4 fields to real backend via Option A fixture-projection (mirror Sprint 57.48 Track D RateLimits exactly).

### Sprint scope

- **Backend**: NEW `GET /admin/tenants/{tenant_id}/identity` + `TenantIdentityResponse` Pydantic (4 fields: provider/scim_enabled/allowed_domains/mfa_required) + `DEFAULT_IDENTITY` constant + 7 NEW pytest tests (217→224); auth `require_admin_platform_role` (mirror sibling HITL/FF/Quotas/RateLimits)
- **Frontend**: NEW `fetchTenantIdentity` single-record service func + NEW `useTenantIdentity` TanStack Query hook + GeneralTab.tsx Identity Card refactor (4 Badge rows via hook with shape adapters bool→"enabled"/"disabled" / list→", ".join / bool→"required"/"optional") + softened BackendGapBanner copy per D-DAY0-9 + `_fixtures.ts` DANGER_OPS only (~50 lines) + 9 NEW Vitest tests (598→607) across 4 test files
- **Day 0 三-prong**: 9 drift findings (7 GREEN + 1 GREEN+ D-DAY0-8 SEATS_FIXTURE already removed + 1 YELLOW D-DAY0-9 BackendGapBanner copy pre-flag); ROI ~5-7×
- **Sequential agent delegation**: Backend agent ~4.1 min + Frontend agent ~6.7 min = ~11 min total agent wall-clock; 22nd consecutive code-implementer delegation
- **Validation chain**: pytest +7 / mypy --strict 0 / black + isort + flake8 clean / Vitest +9 / ESLint 0 / tsc 0 / Vite build 3.45s / 9/9 V2 lints GREEN / LLM SDK leak 0

### 🎯 Structural calibration event (Sprint 57.50 retro Q4)

**Ratio actual/committed-with-agent-factor ~0.58 BELOW [0.85, 1.20] band by 0.27 = 2nd consecutive < 0.7 under `mechanical-single-domain` 0.45 sub-class** (Sprint 57.49 = 0.14 + Sprint 57.50 = 0.58; mean 0.36; **4× variance bimodal NOT Gaussian**).

Rollback rule "2 sprints < 0.7 → tighten" MET — flat tighten 0.45 → 0.35 REJECTED (doesn't address variance root cause). **Decision: ACTIVATE Option B tier-2 refinement** (parallel Sprint 57.38 `-simple/-with-extras` + Sprint 57.48 Option B precedent).

**Active tier-2 sub-class table** (effective Sprint 57.51+):

| Tier-2 sub-class | `agent_factor` | Activation criterion | Evidence base |
|------------------|---------------|----------------------|---------------|
| `mechanical-pattern-reuse-heavy` | **0.30** | ≥ 4 mechanical repetitions of same template in 1 sprint | Sprint 57.49 retroactive (5-tab+1-drawer; ratio 0.21 under 0.30 vs 0.14 under 0.45) |
| `mechanical-greenfield` | **0.50** | Single NEW component-pair; < 4 mechanical repetitions | Sprint 57.50 retroactive (1-endpoint+1-hook+1-refactor; ratio 0.54 under 0.50 vs 0.58 under 0.45) |
| `mixed-multidomain-bundle` | 0.65 | 3+ independent tracks with context-switching | Sprint 57.46 (UNCHANGED from Sprint 57.48 Option B) |
| `partial` | 0.75 | 20-79% via agent (linear interpolation) | — |
| `human` | 1.0 | < 20% via agent | — |

Tier-2 split reduces 4.1× → 2.6× variance spread; both classes still below band globally (bottom-up estimates also generous). See `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier` for full formula + rollback rule reset + tracking discipline.

### `medium-backend` 0.80 5th data point

- 5-pt: 55.5=1.14 / 55.6=0.92 / 57.47=0.16 / 57.48=0.11 / 57.50=0.27
- 5-pt mean **0.52** (last-3 mean 0.18) — last 3 all < 0.7 BUT all agent-delegated
- **KEEP 0.80 per confound-resolved-by-sub-class-split discipline**; 6th data point Sprint 57.51+ under tier-2 will be cleaner signal

### 3 ADs closed this sprint

- ✅ #73 **`AD-AgentFactor-Sub-Class-Validation-Sprint-57.50`** — via 2nd validation ratio 0.58 + ROLLBACK RULE MET
- ✅ #74 **`AD-AgentFactor-Tier-2-Refinement-Proposal`** — via Q4 ACTIVATION (mechanical-pattern-reuse-heavy 0.30 + mechanical-greenfield 0.50)
- ✅ **`AD-TenantSettings-IdentityFixture-Cleanup`** (Sprint 57.49 carryover) — Identity Card now consumes real backend

### 🆕 4 NEW carryover ADs (Sprint 57.51+ candidates)

80. 🆕 **`AD-AgentFactor-Tier-2-Sub-Class-Validation-Sprint-57.51`** — 1st validation needed under tier-2 sub-class table. Sprint 57.51 will naturally generate either `pattern-reuse-heavy` 0.30 OR `greenfield` 0.50 data point depending on work shape.

81. 🆕 **`AD-TenantSettings-Identity-Persistence-Phase58`** Phase 58.x — full SSO admin schema: dedicated `tenant_identity` table + admin PATCH endpoint + audit chain WORM + tenant_overrides → real table migration. Mirrors `AD-TenantSettings-RateLimits-Persistence` (#79) pattern.

82. 🆕 **`AD-Plan-Risk-ORM-File-Path-Reference-Style`** — Plan §8 Risks ORM file path references should use 09-db-schema-design.md Group references (e.g. "identity.py per Group 1 Identity & Tenancy") not table_name.py speculation. D-DAY0-2 lesson: Tenant ORM lives in `identity.py` not `tenant.py`. Codify in plan template + sprint-workflow.md §Step 1 risk class catalog. ~30 min `chore(rules)` micro-sprint.

83. 🆕 **`AD-Stale-Docstring-Karpathy-3-Cleanup-Pattern`** — Treat docstring claims as "code" for Day 0 三-prong Prong 2 content verify. D-DAY0-8 lesson: Sprint 57.49 _fixtures.ts docstring referenced SEATS_FIXTURE which Sprint 57.49 already removed; stale comment caught Day 0. Generalize: docstring claims grep-verified against repo reality, not just at MHist entry creation time. ~15-30 min `chore(rules)` codification.

### Carryover from prior sprints (continuing)

- **`AD-Lint-Detector-Code-Aware-Masking-Rule`** (Sprint 57.48 carryover) — `.claude/rules/` codification still pending; recommended Sprint 57.51+ scope per user direction. ~1-2 hr `audit-cycle / docs / template` 0.40 class.
- **`AD-medium-frontend-Baseline-Recalibration`** (Sprint 57.49 carryover) — 3rd data point pending under tier-2 sub-class confound-cleared table; happens organically at next medium-frontend sprint.
- **`AD-MockupCapture-Frontend-Visual-Diff-Pipeline`** (Phase 58+ deferred) — carryover continues.
- **`AD-TenantSettings-RateLimits-Persistence`** (Phase 58.x deferred) — carryover continues; pair with new #81 `AD-TenantSettings-Identity-Persistence-Phase58`.

### Top 3 next-sprint candidates (post Sprint 57.50)

1. 🥇 **`AD-Lint-Detector-Code-Aware-Masking-Rule`** ~1-2 hr (`audit-cycle / docs / template` 0.40 class; codifies Sprint 57.48 D-DAY0-6 lesson into `.claude/rules/`; original Sprint 57.50 plan candidate (b) for follow-up)
2. **`AD-Plan-Risk-ORM-File-Path-Reference-Style`** ~30 min (#82 micro-sprint; quick `chore(rules)` codification)
3. **Pause** — Natural break point after 6 consecutive sprints (57.45-50) cleanly closed + DUAL CLEAN milestone preserved + tier-2 ESCALATION just landed (let 1-2 sprints validate tier-2 before more carryover work)

---

## 🆕 Sprint 57.43-57.49 Carryover Batch (2026-05-26 — Phase-2 Epic DUAL CLEAN + Phase 58+ Backend Schema Extension + Frontend Migration Wave)

4-sprint window closes **14 ADs total** + introduces **7 new carryover ADs**. Per-sprint detail single-source = `memory/project_phase57_4{3,4,5,6,7,8,9}_*.md` subfile + `docs/03-implementation/agent-harness-execution/phase-57/sprint-57-XX/retrospective.md`.

### Milestones reached

- **Sprint 57.43** (PR `12af6060` later `34c5ad1c` merge): `/admin-tenants` Tenants table full mockup-fidelity rebuild closes drift audit 2026-05-25 #1 priority CATASTROPHIC (4th of 5 original). 5 NEW components + _fixtures.ts 8 TENANTS verbatim + 6 orphan delete Karpathy §3 + 33 NEW Vitest tests +312-560% over target + 24-route sweep cleanest of Phase-2 epic. `frontend-mockup-strict-rebuild` 0.60 9th data point + **1st validation under newly ACTIVATED `agent_factor = 0.55`** ratio ~0.41 BELOW band by 0.44 = 1st rollback-trigger data point → KEEP 0.55 single-data-point caution.
- **Sprint 57.44** (PR squash merge): `/tenant-settings` 6-tab full rebuild closes Phase-2 epic FULL CLEAN (5th of 5 original CATASTROPHIC). 7 NEW components + 1 REWRITE + _fixtures.ts verbatim port + 4 orphan delete + 50 NEW Vitest tests +287% over +12 target. `frontend-mockup-strict-rebuild` 0.60 10th data point ratio ~0.20 = **2nd rollback-trigger data point → MANDATORY tighten `agent_factor` 0.55 → 0.45 effective Sprint 57.45+**. 🎉 **Phase-2 epic FULL CLEAN milestone (21 PARITY + 1 NEAR-PARITY + 0 CATASTROPHIC)**.
- **Sprint 57.45** (PR #195): 🎉 **Phase-2 Epic + NEAR-PARITY DUAL CLEAN milestone (22/22 PARITY)** — `/chat-v2` Inspector tab NEAR-PARITY closed via Path B audit overrule (Day 0 Prong 2 grep proved audit row 9 was Sprint 57.22 transcription error; canonical mockup `page-chat.jsx:378-381` `Turn/Trace/Memory/Tree` matched production exactly). 0 code change docs-only closure. `frontend-refactor-mechanical 0.80` 3rd data point + `agent_factor` 1st validation NOT generated (Path B 0 code change → `agent-delegated: NO` → `agent_factor = 1.0`).
- **Sprint 57.46** (PR #196 `034846f3`): 3-AD multi-domain bundle — AuditDocSync rule codified + Tenant ORM +5 cols Alembic 0018 + 12 NEW pytest tests + mockup capture D-DAY0-5 already-implemented Option B revelation -1 hr scope. NEW class `mixed-multidomain-bundle` 0.65 1-data-point baseline opens. `agent_factor = 0.45` 1st validation ratio ~1.60 ABOVE band by 0.40 → **ROLLBACK to 0.65** effective Sprint 57.47+ per single-data-point caution.
- **Sprint 57.47** (PR #197 `12f97635`): Phase 58+ Backend Schema Extension — 🔴 BLOCKING `AD-AdminTenants-Backend-Schema-Extension` closed (TenantListItem 7→12 fields + region filter + 12 NEW pytest tests) + TenantSettings 6-tab Day 0.8b audit + MEMBERS cheapest tab impl (8 NEW pytest tests incl. CRITICAL multi-tenant isolation). `agent_factor = 0.65` 1st validation ratio ~0.27 = 1st < 0.7 → KEEP single-data-point caution.
- **Sprint 57.48** (PR #198 `c451f584`): **5-track wave** (largest single-sprint AD closure of Phase 57+: **5 ADs**) — HITLPolicies (DBHITLPolicyStore projection) + FeatureFlags (JSONB tenant_overrides) + Quotas (PlanQuota projection) + RateLimits (Option A fixture-projection) + AP-4 lint detector false-positive fix → **9/9 V2 lints GREEN restored** (was 8/9 since Sprint 57.46). 29 NEW pytest tests +132% over target. `agent_factor = 0.65` 2nd validation ratio ~0.17 = 2nd consec < 0.7 → **ROLLBACK RULE MET → Option B sub-class split ESCALATED ACTIVATED** (parallel Sprint 57.38 `-simple/-with-extras` precedent).
- **Sprint 57.49** (PR #199 `33e9f2aa`): Dual-track frontend migration wave — TenantSettings 5-tab fixture→hook via 5 NEW TanStack Query hooks + 5 NEW service functions + per-tab adapter projection D-DAY0-1 pattern + AdminTenants TenantMembersDrawer NEW with slide-over. 37 NEW Vitest tests +264% over target. **24× pattern-reuse speedup observed (highest of 21 consecutive code-implementer delegations)**. NEW sub-class `mechanical-single-domain` 0.45 1st validation ratio ~0.14 → KEEP single-data-point caution.

### Structural calibration event (Sprint 57.48 retro Q4 — escalation)

`agent_factor` evolved from single coefficient to sub-class table via Option B structural split. Single-coefficient pendulum 0.55 → 0.45 → 0.65 → 0.45 inadequate to capture Day 1 work shape variance (Sprint 57.46 multi-track 2.1× speedup vs Sprint 57.40-44 single-domain 5× speedup).

**Active sub-class table** (effective Sprint 57.49+):

| Sub-class | `agent_factor` | Activation criterion | Evidence base |
|-----------|---------------|----------------------|---------------|
| `mechanical-single-domain` | **0.45** | High pattern-reuse OR mechanical port; single-domain backend/frontend | Sprint 57.40-44 + 57.47 + 57.48 + 57.49 |
| `mixed-multidomain-bundle` | **0.65** | 3+ independent tracks with context-switching | Sprint 57.46 |
| `partial` | **0.75** | 20-79% via agent (linear interpolation) | — |
| `human` | **1.0** | < 20% via agent | — |

See `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier` for full formula + rollback rule + tracking discipline. **NEW pattern-reuse acceleration scaling observation** (Sprint 57.49 retro Q4): 5× (single-domain) → 7× (single-tab) → 11× (4-endpoint) → **24× (5-tab+1-drawer; highest of 21 consecutive delegations)** — speedup scales with mechanical repetition count.

### 🆕 7 NEW carryover ADs (Sprint 57.50+ candidates; ordered by ROI / actionability)

73. 🆕 **`AD-AgentFactor-Sub-Class-Validation-Sprint-57.50`** (Sprint 57.49 NEW) — 2nd validation under `mechanical-single-domain` 0.45 needed. Current: 1st = Sprint 57.49 ratio actual/committed-with-agent-factor **~0.14 BELOW band by ~0.71** → KEEP single-data-point caution. If Sprint 57.50 also < 0.7 → escalate to tier-2 refinement (see #74). Naturally generated by any single-domain agent-delegated sprint scope.

74. 🆕 **`AD-AgentFactor-Tier-2-Refinement-Proposal`** (Sprint 57.49 NEW) — If Sprint 57.50 2nd `mechanical-single-domain` data point also < 0.7 → propose tier-2 refinement: split `mechanical-pattern-reuse-heavy` **0.30** (≥4 mechanical repetitions in 1 sprint; matches Sprint 57.48/49 mean ~0.155) vs `mechanical-greenfield` **0.50** (single new component/endpoint; matches Sprint 57.47 ratio ~0.27 closer to band). Pending Sprint 57.50 evidence.

75. 🆕 **`AD-TenantSettings-IdentityFixture-Cleanup`** (Sprint 57.49 NEW) **~1 hr** — `IDENTITY_FIXTURE` in `tenantSettingsService.ts` retained per Sprint 57.49 §_fixtures.ts cleanup; not yet migrated to real backend (5-tab migration shipped + DANGER_OPS retained too). Completes the fixture purge. Class `mechanical-single-domain` 0.45 candidate (single-file migration; natural 2nd validation data point for #73).

76. 🆕 **`AD-Lint-Detector-Code-Aware-Masking-Rule`** (Sprint 57.48 NEW) **~1-2 hr** — Codify D-DAY0-6 lesson into `.claude/rules/`: lint detectors using regex pattern matching must apply code-aware masking (HTML/JSX attribute names like `placeholder=` / TS keys / string literals) to avoid false-positives. Root cause for AP-4 detector breaking 9/9 V2 lints in Sprint 57.46 → Sprint 57.48 Track E false-positive fix. Class `audit-cycle / docs / template` 0.40 candidate.

77. 🆕 **`AD-medium-frontend-Baseline-Recalibration`** (Sprint 57.49 carryover) — 3rd data point needed for class `medium-frontend` 0.65. Current: 1st = Sprint 57.13 ratio 0.95-1.0 in band; 2nd = Sprint 57.49 ratio actual/class-committed 0.064 (confound resolved by sub-class split; under agent_factor `mechanical-single-domain` 0.45 = ratio ~0.14). Per `When to adjust` 3-sprint window rule → KEEP class baseline pending 3rd data point. Naturally generated by next medium-frontend sprint.

78. 🆕 **`AD-MockupCapture-Frontend-Visual-Diff-Pipeline`** (Sprint 57.46 carryover) DEFERRED Phase 58+ **~5-8 hr** — `mockup-sweep.mjs` (Option B Python http.server + Playwright 1440×900) already implements basic capture per Sprint 57.46 D-DAY0-5 revelation; missing: per-page parity scoring + drift alerting + CI integration.

79. 🆕 **`AD-TenantSettings-RateLimits-Persistence`** (Sprint 57.48 carryover) DEFERRED Phase 58.x — Sprint 57.48 Track D shipped Option A fixture-projection from `tenants.meta_data` JSONB; full persistence model (dedicated `tenant_rate_limits` table + admin PATCH endpoint + audit chain) deferred to Phase 58.x.

### Phase progress (post Sprint 57.49)

- V2 22/22 ✅ (unchanged)
- SaaS Stage 1 3/3 ✅ (unchanged)
- **Phase 57+ DUAL CLEAN 22/22 PARITY ✅ preserved** through Sprint 57.45-57.49 (5 consecutive sprints maintain milestone)
- **Phase 58+ Backend Schema Extension COMPLETE** for tenant-settings 6-tab + admin-tenants LIST + members (Sprint 57.46-48)
- **Phase 58+ Frontend Real-Data Migration COMPLETE** for /tenant-settings + /admin-tenants Members (Sprint 57.49)

### Top 3 next-sprint candidates (post Sprint 57.49)

1. 🥇 **`AD-TenantSettings-IdentityFixture-Cleanup`** (#75) **~1 hr** — Class `mechanical-single-domain` 0.45; naturally generates #73 (2nd validation data point). Cleanest hygiene close.
2. **`AD-Lint-Detector-Code-Aware-Masking-Rule`** (#76) **~1-2 hr** — Class `audit-cycle / docs / template` 0.40; codifies repeatable lesson into `.claude/rules/`.
3. **Pause** — Natural break point after 5 consecutive sprints (57.45-57.49) cleanly closed + 14 ADs total + DUAL CLEAN milestone preserved.

---

## 🆕 Sprint 57.42 Carryover (2026-05-25 — /memory Memory Layers Matrix Full Mockup-Fidelity Rebuild)

Sprint 57.42 (`AD-Memory-Layers-Matrix-Rebuild`) ✅ **CLOSED**: single-domain rebuild closes drift audit 2026-05-25 #2 priority `/memory` 🔴 CATASTROPHIC verdict (post Sprint 57.41 it was elevated to #2 priority; with Sprint 57.42 close it is fully RESOLVED).

- **6 NEW components** (under `frontend/src/features/memory/components/`): MemoryPageHeader (~85 lines; `.page-head` + 3 actions + cond time-travel Badge) / TimeTravelScrubber (~155; 24h interactive playback Card with slider+op markers+marks+cursor display) / MemoryMatrix (~175; 5×3 grid with cursor-aware visibility filter + hover bg + AP-2 banner) / RecentMemoryOpsCard (~105; 6-col fixture table + AP-2 banner) / GdprErasureCard (~70; subject+select+danger Button + AP-2 banner) / MemoryView (~85; container with useState cursor/playing + useEffect setInterval cleanup)
- **`_fixtures.ts` verbatim port** (~195 lines): SCOPES / TIME_SCALES / MEMORY_ENTRIES / TIME_TRAVEL_MARKS / MEMORY_OPS_TIMELINE / RECENT_MEMORY_OPS / TOTAL_ENTRIES
- **Outer 2-tab DROP per §1.4 Option B** — **1st DROP precedent** of Phase-2 epic (Recent + By-Scope BOTH subsumed by mockup unified view, unlike Sprint 57.40 `/audit-log` / Sprint 57.41 `/timeline` distinct production-only concepts preserved)
- **Backward-compat redirects**: `/memory/recent` + `/memory/by-scope` + `*` → `<Navigate to="/memory" replace />` inside `pages/memory/index.tsx`
- **11 orphan deletes per Karpathy §3** — **largest single-wave of Phase-2 epic** (3 vintage components MemoryRecentList/MemoryByScopeBrowser/MemoryScopeBadge + 3 vintage hooks useMemoryByScope/useMemoryByTime/useMemoryRecent + 4 Vitest specs (24 tests) + 1 e2e memory-page.spec.ts)
- **`mockup-ui.tsx` `ButtonVariant` 1-line widen** to add `"warning" | "danger"` (D-DAY1-1; CSS+styles-mockup.css already supported; same pattern as Sprint 57.41 Badge tones widening)
- **+12 NEW Vitest tests** (6 NEW spec files; 474 → **486**; +150-240% over +5-8 target; within Sprint 57.40 +15 / 57.41 +9 cohort range)
- **route-sweep envelope mock NO-OP decision** (D-DAY2-2) — rebuild fixture-only; `AD-RouteSweep-Envelope-Mock-Convention` stays at 2 applications
- **HEX_OKLCH_BASELINE 46 unchanged** (estimated +0-4 didn't materialize — 3rd consecutive +0 actual; verbatim-CSS protocol +0-4 envelope consistently over-cautious)
- **Drift audit report `/memory` verdict 🔴 → ✅ PARITY**; summary 18→19 PARITY / 3→2 CATASTROPHIC
- **3-way evidence pair**: BEFORE 71.4 KB / AFTER 173.9 KB / MOCKUP 189.4 KB → **AFTER = 92% of MOCKUP** (structural PARITY confirmed)
- **24-route sweep cleanest of Phase-2 epic**: 20 IDENTICAL + 4 CHANGED (1 INTENDED `/memory` +144% + 3 sub-300-byte noise auth-callback -23 / chat-v2 -19 / overview -38) + 0 unintended regressions (lowest noise + lowest regression count of class history)
- **Class `frontend-mockup-strict-rebuild` 0.60 8th data point ratio ~0.33** — BELOW band by 0.52; 8-pt mean 0.71 lower band edge; **last 3 = 3 of 3 < 0.7 → `When to adjust` lower-trigger MET ✅** → propose Sprint 57.43 baseline lift 0.60 → 0.40-0.45
- ✅ **`AD-Sprint-Plan-Agent-Delegation-Factor-Modifier`** — **CLOSED 2026-05-25** via Option A multiplicative `agent_factor = 0.55` (Sprint 57.42 closeout follow-up `chore/agent-delegation-factor-activate` branch). 5 cross-class data points (57.39 0.41 + FIX-015 outlier + 57.40 0.36 + 57.41 0.18 + 57.42 0.33) + 4 consecutive `mockup-strict-rebuild` < 0.7 = activation criteria FULLY MET. See `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier` for formula + rollback rule + tracking discipline. First validation: Sprint 57.43 retro Q2.

### Phase-2 epic progress (post Sprint 57.42)

- Pre-Sprint 57.42: 18 PARITY + 1 NEAR-PARITY + 3 🔴 CATASTROPHIC
- **Post Sprint 57.42**: **19 PARITY + 1 NEAR-PARITY + 2 🔴 CATASTROPHIC** remaining (`/admin-tenants` + `/tenant-settings`)

### 🆕 7 NEW carryover ADs (Sprint 57.43+ candidates; ordered by ROI / priority)

66. 🆕 **`AD-Memory-Matrix-Backend-Cursor-Aware-Endpoint`** — Backend `/api/v1/memory/matrix?scope=*&time_scale=*&cursor=*` endpoint for real cursor-aware time-travel data. Sprint 57.42 fixture + client-side filter simulation. Phase 58+.
67. 🆕 **`AD-Memory-Ops-Timeline-Backend-Endpoint`** — Backend `/api/v1/memory/ops/recent?limit=100` endpoint for RecentMemoryOpsCard. Sprint 57.42 fixture-only. Phase 58+.
68. 🆕 **`AD-Memory-GDPR-Erasure-Backend-Endpoint`** — Backend `/api/v1/memory/erasure` POST endpoint for GdprErasureCard form (audit chain WORM record). Sprint 57.42 form button non-functional (window.alert stub). Phase 58+.
69. 🆕 **`AD-Memory-Vintage-Hooks-Cleanup`** — `memoryService.ts` preserved Day 1 but has 0 consumers post-rebuild. Phase 58+ either wire to RecentMemoryOpsCard (when ops endpoint ships) OR fully orphan delete.
70. 🆕 **`AD-Memory-Old-URL-Redirect-Phase58-Retire`** — Sprint 57.42 keeps `/memory/recent` + `/memory/by-scope` → `/memory` redirects for backward compat. Phase 58+ analytics-based retire once bookmark traffic decays.
71. 🆕 **`AD-Memory-New-Entry-Modal-Phase58`** + **`AD-Memory-Export-Action-Phase58`** — Mockup `.page-head` "New entry" and "Export" buttons are Sprint 57.42 AP-2 stubs. Phase 58+ wires write modal + CSV/JSON export endpoint.
72. 🆕 **`AD-Sprint-Plan-frontend-mockup-strict-rebuild-baseline-lift`** — **Lower-trigger MET** (3 consecutive < 0.7: 57.40 0.36 + 57.41 0.18 + 57.42 0.33). Propose Sprint 57.43 plan lifts baseline 0.60 → 0.40-0.45. Validate next 2-3 sprints.

### Carryover from Sprint 57.41 (still open as of Sprint 57.42 closeout)

- ✅ **`AD-Sprint-Plan-Agent-Delegation-Factor-Modifier`** — **CLOSED 2026-05-25** via Option A multiplicative `agent_factor = 0.55` (Sprint 57.42 closeout follow-up; 5 cross-class data points + 4 consecutive mockup-strict-rebuild < 0.7 = activation FULLY MET). See top of file `Updated` field + `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier`.
- `AD-Verification-Out-Of-Scope-Components-Phase2-C-Mop-Up` — 2 residue sites in VerificationPanel.tsx (chat-v2) + CorrectionTraceView.tsx (/timeline) — still out-of-scope
- `AD-Verification-Filter-Form-Phase58-Migrate` / `AD-Verification-Backend-Claim-Evidence-Extension` / `AD-Verification-Failure-Kinds-+-Flaky-Checks-Aggregation-Endpoints` — Sprint 57.41 Phase 58+ carryover continues

### Top 3 next-sprint candidates (post Sprint 57.42)

1. 🥇 **`AD-AdminTenants-Tenants-Table-Rebuild`** — `/admin-tenants` ~12-15 hr (4th CATASTROPHIC; backend GET list endpoint already wired; pure frontend work)
2. **`AD-TenantSettings-6-Tab-Rebuild`** — `/tenant-settings` ~15-20 hr (5th and LAST CATASTROPHIC; largest scope; mostly form work)
3. **`AD-ChatV2-Inspector-Tab-Rename`** — Inspector tab vocabulary rename ~30 min (NEAR-PARITY quick win)

---

## 🆕 Sprint 57.41 Carryover (2026-05-25 — /verification recent view Full Mockup-Fidelity Rebuild)

Sprint 57.41 (`AD-Verification-Catastrophic-Rebuild`) ✅ **CLOSED**: single-domain rebuild closes drift audit 2026-05-25 #2 priority `/verification` 🔴 CATASTROPHIC verdict.

- **6 NEW components** (under `frontend/src/features/verification/components/`): VerificationPageHeader (rename Sprint 57.40 ApprovalsPageHeader) / VerificationStatsStrip (rename + Pass rate compute swap) / VerificationRunsTable (NEW 6-col with claim+evidence dual-line + adaptItem mapping) / FailureKindsCard (NEW 5-row bar-track AP-2) / FlakyChecksCard (NEW 3-row rate Badge AP-2) / VerificationView (NEW container)
- **VerificationList.tsx orphan-deleted 299 lines** per Karpathy §3 (filter form retired; carryover `AD-Verification-Filter-Form-Phase58-Migrate`)
- **route swap**: `pages/verification/index.tsx` `recent` Route element swapped; outer 2-tab + `/timeline` CorrectionTraceView preserved
- **+9 NEW Vitest specs** (5 files; 489→498; +112-225% over +5-8 target)
- **route-sweep `/verification/recent` envelope mock**: 2nd application of `AD-RouteSweep-Envelope-Mock-Convention`
- **HEX_OKLCH_BASELINE 46 unchanged** (estimated +2-4 bump didn't materialize — verbatim-CSS protocol correct; components use `var(--*)` refs)
- **e2e adapt**: 3 obsolete filter-form tests deleted + 2 NEW mockup-shape view tests added (D-DAY0-3 resolution)
- **drift audit report `/verification` verdict 🔴 → ✅ PARITY**; summary 17→18 PARITY / 4→3 CATASTROPHIC
- **3-way evidence pair**: BEFORE 79.9 KB / AFTER 133.0 KB / MOCKUP 207.2 KB
- **22-route sweep cleanest of Phase-2 epic**: 22 IDENTICAL + 1 expected CHANGED (`/verification` +66.4%) + 1 sub-300-byte noise (`/overview` -44 bytes) + 0 unintended regressions
- **Class `frontend-mockup-strict-rebuild` 0.60 7th data point ratio ~0.18** — deepest below-band of class history; 7-pt mean 0.76; last 3 only 2 < 0.7 → KEEP 0.60 per 3-sprint window rule (need 3+ consecutive)
- **🔴 Critical**: `AD-Sprint-Plan-Agent-Delegation-Factor-Modifier` 4th cross-class data point — **activation criteria MET** (57.39 0.41 + FIX-015 outlier + 57.40 0.36 + 57.41 0.18 all agent-delegated < 0.7); propose Sprint 57.42 retro structural evaluation

### Phase-2 epic progress (post Sprint 57.41)

- Pre-Sprint 57.41: 17 PARITY + 1 NEAR-PARITY + 4 🔴 CATASTROPHIC
- **Post Sprint 57.41**: **18 PARITY + 1 NEAR-PARITY + 3 🔴 CATASTROPHIC** remaining (`/memory` + `/admin-tenants` + `/tenant-settings`)

### 🆕 6 NEW carryover ADs (Sprint 57.42+ candidates; ordered by ROI / priority)

60. ✅ **`AD-Memory-Layers-Matrix-Rebuild`** — **CLOSED Sprint 57.42** (Day 1 agent-delegated 10th consecutive code-implementer ~40 min wall-clock + Day 2 +12 NEW Vitest specs + drift audit verdict PARITY; 6 NEW components + _fixtures.ts + outer 2-tab DROP §1.4 Option B + 11 orphan deletes Karpathy §3; actual ~3 hr human-eq vs est 10-15 hr → 8th data point for `frontend-mockup-strict-rebuild` 0.60 baseline ratio 0.33; lower-trigger MET for Sprint 57.43 baseline lift; 5th cross-class data point for agent-delegation modifier activation FULLY MET)
61. 🆕 **`AD-AdminTenants-Tenants-Table-Rebuild`** — `/admin-tenants` tenants table rebuild ~12-15 hr.
62. 🆕 **`AD-TenantSettings-6-Tab-Rebuild`** — `/tenant-settings` 6-tab rebuild ~15-20 hr. **Largest scope of remaining 3 CATASTROPHIC.**
63. 🆕 **`AD-Verification-Filter-Form-Phase58-Migrate`** — Sprint 57.41 retired filter form per Karpathy §3 (mockup has none). Phase 58+ admin filter UI on `/verification/admin` separate route OR collapsible `<details>` panel.
64. 🆕 **`AD-Verification-Backend-Claim-Evidence-Extension`** — Backend `VerificationLogItem` lacks structured `claim` / `evidence` / `kind`; mapped best-effort via Sprint 57.41 `adaptItem()`. Phase 58+ backend schema extension.
65. 🆕 **`AD-Verification-Failure-Kinds-+-Flaky-Checks-Aggregation-Endpoints`** — Sprint 57.41 sidebar Failure kinds + Flaky checks are AP-2 fixtures. Phase 58+ backend `GET /verifications/stats/{failure-kinds,flaky-checks}` endpoints.

### Carryover from Sprint 57.40 (still open as of Sprint 57.41 closeout)

- `AD-Sprint-Plan-Agent-Delegation-Factor-Modifier` — Sprint 57.41 contributes 4th cross-class data point; activation criteria now MET; **propose Sprint 57.42 retro structural evaluation** (Option A multiplicative `agent_factor` 0.55 coefficient OR Option B per-class sub-class split)
- `AD-Verification-Out-Of-Scope-Components-Phase2-C-Mop-Up` — 2 residue sites in VerificationPanel.tsx (chat-v2) + CorrectionTraceView.tsx (/timeline) out-of-scope for Sprint 57.41

---

## 🆕 Sprint 57.40 Carryover (2026-05-25 — /governance Approvals view Full Mockup-Fidelity Rebuild)

Sprint 57.40 (`AD-Governance-Full-Mockup-Fidelity-Rebuild`) closed: single-domain rebuild closes drift audit 2026-05-25 (`claudedocs/5-status/drift-audit-2026-05-25/audit-report.md`) #3 priority `/governance` 🔴 CATASTROPHIC verdict.

- **5 NEW components**: ApprovalsPageHeader / ApprovalsStatsStrip (4 KPI + AP-2 banner) / ApprovalsFilterTabs (5-tab nav + TabId union) / ApprovalDetailPane (rich right-col Detail) / ApprovalsEmptyTab (AP-2 placeholder)
- **1 NEW `KvRow` primitive** in `mockup-ui.tsx` (verbatim port of `page-governance.jsx:265-272`)
- **`ApprovalsPage.tsx`** restructure (73 → 115 lines; 5-component composition + `selected` state)
- **`ApprovalList.tsx`** upgrade (102 → 131 lines; 6-col → 7-col with SevDot; row `onClick` replaces DecisionModal flow; `RISK_COLOR_CLASS` deleted in favor of mockup-ui `<RiskBadge>`)
- **`DecisionModal.tsx`** Karpathy §3 orphan delete
- **+15 NEW Vitest specs** (478 → 493; target +4-8 → **188-375%**)
- **`route-sweep.mjs`** `/governance/approvals` envelope-shape mock (D-DAY0-1 closes audit's red-banner sweep-mock artifact)
- **`check-mockup-fidelity.mjs`** `HEX_OKLCH_BASELINE` 45 → 46 (+1 row-highlight literal mockup-token vocabulary)
- **Drift audit report**: `/governance` 🔴 → ✅ PARITY; 16 → 17 PARITY / 5 → 4 CATASTROPHIC; Recommendations #1+#3 struck; Key finding #5 RESOLVED
- **22-route sweep**: 19 IDENTICAL + 1 expected CHANGED + 4 noise + 0 unintended regressions
- **3-way evidence pair** (BEFORE 79.9 KB / AFTER 115.8 KB / MOCKUP 210.7 KB) staged

**6th data point for `frontend-mockup-strict-rebuild` 0.60 baseline**: sprint-aggregate ratio ≈0.36 BELOW band [0.85, 1.20] by 0.49 (deepest below-band of class history). 6-pt mean 0.86 at lower band edge (-0.10 vs prior 5-pt mean 0.96). Per `When to adjust` rule: only 1 of last 3 < 0.7 → lower-trigger NOT met → **KEEP 0.60 baseline**.

Root cause: code-implementer agent-delegation 7th consecutive ~40 min wall-clock for 5 NEW + 1 primitive + 2 restructures (human-equivalent ~6-8 hr); not modeled in baseline. **3rd data point for `AD-Sprint-Plan-Agent-Delegation-Factor-Modifier`** across 2 classes (57.39=0.41 + FIX-015 + 57.40=0.36).

### Phase-2 epic progress

- Pre-Sprint 57.40 (per audit): 16 PARITY + 1 NEAR-PARITY + 5 🔴 CATASTROPHIC + 12 PROP stubs + 4 DRAFT inactive
- **Post Sprint 57.40**: **17 PARITY + 1 NEAR-PARITY + 4 🔴 CATASTROPHIC** remaining
- 4 remaining CATASTROPHIC: `/memory` (Memory Layers 5×N matrix) / `/verification` (4-KPI + 2-col Recent + sidebar) / `/admin-tenants` (Tenants table 9-col) / `/tenant-settings` (6-tab architecture)
- 1 NEAR-PARITY: `/chat-v2` Inspector tab rename (~30 min quick win)

### 🆕 9 NEW carryover ADs (Sprint 57.41+ candidates; ordered by ROI per audit Recommendations 1-6)

50. ✅ ~~**`AD-Verification-Catastrophic-Rebuild`**~~ — **CLOSED Sprint 57.41** (this rebuild). `/verification` rebuild to mockup 4-KPI + 2-col Recent verification runs + Failure modes + Flaky checks sidebar. Class `frontend-mockup-strict-rebuild` 0.60. Final actual 1.5 hr / committed 8.5 hr / ratio 0.18 (deepest below band; agent-delegated 8th+9th consecutive). Pattern reuse hit: 2 of Sprint 57.40's 5 NEW (PageHeader + StatsStrip) transferred via rename + 4 NEW unique (RunsTable + FailureKindsCard + FlakyChecksCard + View container). See `memory/project_phase57_41_verification_full_rebuild.md` for detail.

51. 🆕 **`AD-ChatV2-Inspector-Tab-Rename`** — Inspector tab vocabulary rename `Turn/Trace/Memory/Tree` → mockup `Run/Tools/Memory/Verify`. Class `frontend-refactor-mechanical` 0.50. Est ~30 min (quick win).

52. 🆕 **`AD-Memory-Layers-Matrix-Rebuild`** — `/memory` rebuild to mockup `Memory Layers` 5×N matrix design (SYSTEM/TENANT/ROLE/USER/SESSION × time-scale columns + playback slider + time travel + Export + New write + Recent memory ops strip). Currently Sprint 57.12 vintage shadcn-utility. Class `frontend-mockup-strict-rebuild` 0.60. Est ~10-15 hr.

53. 🆕 **`AD-AdminTenants-Tenants-Table-Rebuild`** — `/admin-tenants` rebuild to mockup Tenants + 4 KPI + 9-col table 9 rows (TENANT/PLAN/REGION/SEATS/AGENTS/RUNS/STATUS/CREATED). Known CLAUDE.md 🟡 STRUCTURAL Phase 58+ #1 + matches Sprint 57.22 audit `6-tab architectural finding`. Backend GET endpoint already wired. Class `frontend-mockup-strict-rebuild` 0.60. Est ~12-15 hr.

54. 🆕 **`AD-TenantSettings-6-Tab-Rebuild`** — `/tenant-settings` rebuild to mockup 6-tab nav (General/Feature Flags 14/Quotas/HITL Policies/Members 8/Danger Zone) + 2-col General form + Identity & SSO sidebar. Known CLAUDE.md 🟡 STRUCTURAL Phase 58+ #2. Class `frontend-mockup-strict-rebuild` 0.60. **Largest scope** (mostly form work). Est ~15-20 hr.

55. 🆕 **`AD-Shell-Defensive-Guards-For-Malformed-AuthMe`** (D-DAY1-1 investigation byproduct) — pre-emptive hardening of Sidebar / Topbar / OverviewPage / UserMenu against hypothetical malformed `/auth/me` shape. Sprint 57.33 pattern precedent. FIX-019 candidate. Est ~30 min.

56. 🆕 **`AD-Playwright-Mock-LIFO-Fixture-Convention`** (D-DAY1-2 investigation byproduct) — codify `r.fallback()` LIFO pattern + envelope-shape mock requirement into `.claude/rules/testing.md` or `docs/rules-on-demand/testing.md`. Est ~30 min.

57. 🆕 **`AD-DecisionModal-Doc-References-Mop-Up`** (Day 1 Karpathy §3 orphan delete follow-up) — clean 3 stale doc refs after `DecisionModal.tsx` delete (dialog.tsx / useApprovalDecide.ts / guardrails README). Est ~15 min.

58. 🆕 **`AD-RouteSweep-Envelope-Mock-Convention`** (Day 2 audit-report carryover) — codify in `frontend-mockup-fidelity.md` or `testing.md`: any endpoint returning envelope shape (e.g. `{items, total, has_more}`) needs explicit sweep mock entry; default `[]` is only safe for list-shaped endpoints. Grep-pattern + example. Est ~30 min.

59. ✅ **`AD-Sprint-Plan-Agent-Delegation-Factor-Modifier`** — **CLOSED 2026-05-25** via Option A multiplicative `agent_factor = 0.55` (Sprint 57.42 closeout follow-up `chore/agent-delegation-factor-activate` branch). 5 cross-class data points (57.39 0.41 + FIX-015 outlier + 57.40 0.36 + 57.41 0.18 + 57.42 0.33) + 4 consecutive `mockup-strict-rebuild` < 0.7 = activation criteria FULLY MET at Sprint 57.42 retro Q4. See top of file `Updated` field + `.claude/rules/sprint-workflow.md §Active Agent Delegation Factor Modifier`. Actual ~1 hr (calibration class `audit-cycle / docs / template` 0.40 — within estimate).

---

## 🆕 Sprint 57.39 Carryover (2026-05-24 — Governance Category Multi-Page Phase-2 4-domain batched)

Sprint 57.39 (`AD-Governance-Category-Multipage-Phase-2`) closed: 4-domain batched.

- **Domain A `/governance`**: tab-shell verbatim CSS swap to `Tabs` mockup-ui primitive (commit `71088441`; 75 → 83 lines; backend wiring untouched)
- **Domain B `/verification`**: same tab-shell pattern (commit `019fa12f`; 77 → 80 lines; Sprint 57.33 defensive `(items ?? []).length` guard intact in `VerificationList.tsx`)
- **Domain C `/redaction`**: PROP→real port (commit `2eefffcd`; 1-line stub → 273 lines verbatim per `page-platform2.jsx:254 RedactionPage` + 6 NEW Vitest specs + AP-2 BackendGapBanner)
- **Domain D `/error-policy`**: PROP→real port (commit `3d5b442e`; 1-line stub → 272 lines verbatim per `page-platform.jsx:426 ErrorPolicyPage` + 8 NEW Vitest specs + AP-2 BackendGapBanner)
- **routes.config.ts cleanup** (commit `085dacec`): dropped `proposed: true` from `/redaction` + `/error-policy` rows
- **22-route sweep** (Day 2.5 `e97cb05b`): 13 CHANGED / 9 IDENTICAL / 0 unexpected regression — 2 intended Day 1 (governance + verification) + 11 collateral sidebar PROP-badge cascade (consistent ~-1.9 KB delta)

**1st deliberate-test data point for `-with-extras` 0.65 baseline**: sprint-aggregate ratio ≈0.41 BELOW band [0.85, 1.20] by 0.44. Root cause = code-implementer agent-delegation (6th + 7th consecutive) ~3-5× speedup vs human-rewrite estimates not modeled in baseline. KEEP 0.65 per `When to adjust` 3-sprint window rule (1-data-point insufficient).

### Phase-2 epic progress

- **11/17 → 15/17 Phase-2 routes shipped / 2 🟡 remaining**: only Phase 58+ STRUCTURAL: `/memory` + `/tenant-settings` (both need backend pair)
- /governance + /verification are NEAR-PARITY shell-level only (child component re-point deferred — see new AD #47 below)
- `/audit-log` still requires backend pair (Round 4 carryover; not part of this sprint per plan §1.3)

### 🆕 5 NEW carryover ADs (Sprint 57.40+ candidates)

47. ✅ **`AD-Governance-Verification-Child-Component-Re-Point-Phase58`** — RESOLVED 2026-05-25 via **FIX-015** (6 child component re-point with agent delegation; ~25 min wall-clock). Day 0 grep scope adjusted from AD spec: 5 listed → final 6 files (ApprovalsPage already clean / VerificationDetail renamed to VerificationPanel / +ApprovalList +DecisionModal NEW findings). Token-level swap shadcn-utility (`bg-card`/`text-foreground`/`border-border`/`bg-muted`/`text-muted-foreground`) → mockup verbatim (`.card`/`.table`/`.btn`/`.badge`/`.field`/`.input`/`.subtle`/`.mono`/`.row`). HEX_OKLCH_BASELINE tightened 51→50. Vitest 478/478 + mockup-fidelity ✓ + build ✓ + tsc 0. Phase-2 epic 15/17 → 17/17 non-STRUCTURAL routes (2 🟡 STRUCTURAL `/memory` + `/tenant-settings` remain Phase 58+). See `claudedocs/4-changes/bug-fixes/FIX-015-governance-verification-child-component-repoint.md`.

47.5. ✅ **`AD-ApprovalList-Risk-Color-Tailwind-Hex-Sentinels`** — RESOLVED 2026-05-25 via **FIX-017** (post-4-AD-sequence next item per user authorization). Day 0 scope adjusted from AD spec 1 file → 3 governance files (ApprovalList + Badge cva variants + AuditChainBadge; chat_v2 already migrated). Tailwind v4 typed arbitrary value with CSS var pattern: `text-[color:var(--risk-X)]` + `bg-[color:var(--risk-X)]/10` (preserves `/<opacity>` modifier). Vitest spec assertion updated (`tests/unit/components/ui/components.test.tsx:91` hex literal → token reference). HEX_OKLCH_BASELINE tightened 50→45. All validation green (tsc 0 / lint 0 / mockup-fidelity ✓ / Vitest 478/478 / build 3.44s). See `claudedocs/4-changes/bug-fixes/FIX-017-risk-color-normalization-approvallist-and-governance-badge-family.md`.

48. ✅ **`AD-Day0-Prong2-Child-Component-Tree-Depth-Audit`** — RESOLVED 2026-05-25 via **`chore(rules)`** (rule update commit, not FIX). `.claude/rules/sprint-workflow.md §Step 2.5` adds new sub-prong **Prong 2.5 — Child Component Tree Depth Audit** (frontend page sprints only): enumerate child component tree via `grep "import.*@/features/<area>"` then run anti-pattern greps (shadcn-utility token residue / inline style escape comments / outer wrapper artifact / fullBleed drop / tab-shell-vs-monolithic divergence) on each child file. Promoted as **AD-Plan-5** alongside existing AD-Plan-1/2/3/4. ROI evidence appended (Sprint 57.39 D-DAY1-1 escape + FIX-015 post-hoc validation = 20-60× when caught Day 0 vs Day 1+ scope expansion). MHist updated. See sprint-workflow.md §Step 2.5 §Prong 2.5.

48.5. ✅ **`AD-Pre-Push-Lint-Silent-Suppression-Anti-Pattern`** — RESOLVED 2026-05-25 via **`chore(rules)` Item #4 bundle** (Option A — documentation update). `.claude/rules/sprint-workflow.md §Before Commit Checklist §2 Lint+Format` Frontend line annotated: "**MUST run WITHOUT `--silent` flag**"; documents FIX-015 CI fail evidence + suggests `2>&1 | tail -20` for clean-but-error-preserving output. Lighter than Option B/C (package.json edits) — keeps the discipline in the rule layer where the lesson is reusable. See sprint-workflow.md §Before Commit Checklist.

49. ✅ **`AD-RouteSweep-Coverage-Extend-PROP-Promoted-Pages`** — RESOLVED 2026-05-25 via **FIX-016** (Option A — manual additions per Karpathy §2 Simplicity First). Added `/redaction` + `/error-policy` to `APPSHELL_ROUTES` (14 → 16 entries: 13 → 15 real + 1 PROP rep unchanged). Comment refreshed (13 PROP → 11 PROP). Sprint 57.40+ route-sweep runs now capture the 2 promoted routes in before/after directories. See `claudedocs/4-changes/bug-fixes/FIX-016-route-sweep-coverage-extend-prop-promoted.md`.

49.5. ✅ **`AD-RouteSweep-Auto-Derive`** — RESOLVED 2026-05-25 via **FIX-018**. Option (b) regex text-parse chosen and validated robust: split routes.config.ts ROUTES body on `},` boundaries (safe — RouteEntry blocks have no nested braces since `lazy(() => import(...))` uses parens), extract `path` + `active` + optional `proposed` per block. Derived 16 entries (15 real + 1 PROP rep `/compaction`) byte-identical to prior FIX-016 hardcoded list. Fail-fast `throw` on schema mismatch / zero-real result (per AD-Pre-Push-Lint-Silent-Suppression-Anti-Pattern lesson). `--list-only` dry-run mode added for future validation. Greppable count log on real runs (`auto-derived: 15 real + 1 of 12 PROP rep`). Future PROP→real promotions auto-sync — `AD-RouteSweep-Coverage-Extend-PROP-Promoted-Pages` class of bug eliminated. See `claudedocs/4-changes/bug-fixes/FIX-018-route-sweep-auto-derive-from-routes-config.md`.

50. ✅ **`AD-RouteSweep-Cwd-Relative-OUT_DIR-Foot-Gun-Fix`** — RESOLVED 2026-05-25 via **FIX-014**. ESM `__dirname` derivation via `fileURLToPath(import.meta.url)` + `path.resolve(__dirname, '../../claudedocs/...')` makes OUT_DIR cwd-invariant. Smoke-tested from non-project-root cwd; resolution correctly lands at `<project>/claudedocs/4-changes/<slug>/screenshots/<mode>/`. See `claudedocs/4-changes/bug-fixes/FIX-014-route-sweep-cwd-relative-outdir.md`.

51. ✅ **`AD-Sprint-Plan-Agent-Delegation-Factor-Modifier`** — **RESOLVED twice 2026-05-25** (same day, 2-step closure):
    1. **Step 1 — PROPOSAL** via `chore(rules)` Item #4 bundle (2026-05-25 morning): `.claude/rules/sprint-workflow.md §Scope-class multiplier matrix` adds **Proposed Agent Delegation Factor Modifier (PENDING VALIDATION)** subsection (Hypothesis + 2-data-point Evidence table + Option A 0.50-0.60 + Option B fallback + Activation rule 3-sprint window + Tracking discipline). 2 data points (57.39 + FIX-015) — INSUFFICIENT for activation.
    2. **Step 2 — ACTIVATED** via `chore/agent-delegation-factor-activate` branch (2026-05-25 — Sprint 57.42 closeout follow-up): 5th cross-class data point reached at Sprint 57.42 retro Q4 (57.39 0.41 + FIX-015 + 57.40 0.36 + 57.41 0.18 + 57.42 0.33; 4 consecutive `mockup-strict-rebuild` < 0.7) = **activation criteria FULLY MET**. Selected **Option A multiplicative `agent_factor = 0.55`** (mid-band conservative). §Proposed block replaced with §Active block + §Workload Calibration §Four-segment form added. First validation: Sprint 57.43 retro Q2. See sprint-workflow.md §Active Agent Delegation Factor Modifier.

### Next sprint candidates (post-57.39)

After Sprint 57.39, the Phase-2 epic non-STRUCTURAL backlog is mostly cleared. High-ROI next candidates:

- ~~**`AD-Governance-Verification-Child-Component-Re-Point-Phase58`**~~ ✅ DONE 2026-05-25 via FIX-015 (6 child component re-point + HEX_OKLCH_BASELINE 51→50; ~25 min agent wall-clock; closes Phase-2 epic NEAR-PARITY → PARITY for /governance + /verification)
- **`/audit-log` DRAFT→active** (paired with Cat 9 backend; medium-backend + medium-frontend joint sprint)
- ~~**`AD-RouteSweep-Auto-Derive`**~~ ✅ DONE 2026-05-25 via FIX-018 (regex text-parse Option (b) chosen; 16 entries byte-identical match; fail-fast on schema drift; `--list-only` dry-run; future PROP→real promotions auto-sync)
- ~~**`AD-Pre-Push-Lint-Silent-Suppression-Anti-Pattern`**~~ ✅ DONE 2026-05-25 via `chore(rules)` Item #4 bundle (sprint-workflow.md §Before Commit annotation; Option A documentation update)
- ~~**`AD-ApprovalList-Risk-Color-Tailwind-Hex-Sentinels`**~~ ✅ DONE 2026-05-25 via FIX-017 (3 governance files token swap + Vitest spec update + HEX baseline 50→45; chat_v2 already migrated pre-FIX-017)
- ~~**`AD-Sprint-Plan-Agent-Delegation-Factor-Modifier`**~~ ✅ DONE 2026-05-25 via `chore(rules)` Item #4 bundle (proposal logged in matrix; Option A `agent_factor` 0.50-0.60 PENDING 2-3 sprint validation per existing 3-sprint window rule)
- **`/admin-tenants` Phase-2** (`-simple` 0.50 3rd validation data point; ~1.5-2 hr with agent)
- ~~**`AD-Shadcn-Border-Token-Visual-Audit-Or-Align-To-Mockup`** Path A 1-line global micro-fix~~ ✅ DONE 2026-05-25 via FIX-012 (Path A applied; see §Sprint 57.38 Follow-up Carryover for resolution detail)
- ~~**`AD-Inline-Font-Baseline-Alignment`** typography audit~~ ✅ DONE 2026-05-25 via FIX-013 (documented case; B/C dispositioned Skip per Karpathy §3)
- **Phase 58+ structural epic** `/memory` or `/tenant-settings` (~25-30 hr; needs backend pair)
- ~~**`AD-RouteSweep-Cwd-Relative-OUT_DIR-Foot-Gun-Fix`**~~ ✅ DONE 2026-05-25 via FIX-014 (ESM `__dirname` via `fileURLToPath` + `path.resolve(__dirname, '../../...')`)

---

## 🆕 Sprint 57.38 Follow-up Carryover (2026-05-24 — 3 user-reported issues → FIX-011 + 3 NEW ADs + frontend-mockup-fidelity.md updated)

User-reported via screenshots after Sprint 57.38 PR #176 merge `44489aba`:

1. `/state-inspector` left/right padding visibly wider than mockup
2. `/state-inspector` detail card title `[v18 by orchestrator_loop]` — `by` baseline lower than mono tokens
3. All-page buttons render black borders vs mockup light grey

### What got fixed in PR (this hotfix)

- ✅ **Issue 1 — FIX-011**: `StateInspectorPage.tsx` drop `padding: 18` from outer wrapper (production-only Sprint 57.19 vintage; mockup has no outer wrapper)
- ✅ **3 systematic anti-patterns codified** in `docs/rules-on-demand/frontend-mockup-fidelity.md` §Phase-2 re-point systematic anti-patterns:
  - **AP-Phase2-A**: Production-only outer padding wrapper (translation-era artifact)
  - **AP-Phase2-B**: Inline mixed-font span baseline misalignment
  - **AP-Phase2-C**: Tailwind utility `border-border` → shadcn `--sc-border` token residue
- ✅ Code review checklist (3 new mandatory items per Phase-2 re-point PR)

### 🆕 NEW carryover ADs (Sprint 57.39+)

- 🆕 **`AD-State-Inspector-Outer-Padding-Wrapper-Fix`** — ✅ RESOLVED by FIX-011 (logged for trace)
- ✅ **`AD-Inline-Font-Baseline-Alignment`** — RESOLVED 2026-05-25 via **FIX-013** for the FIX-011 §Issue 2 documented case (`StateInspectorPage` card title row `CARD_TITLE_ROW_STYLE` adds `alignItems: "baseline"`). Day 0 audit dispositioned Candidate B (CostBurnChart legend — plain inline `<span>`, no flex) + Candidate C (IncidentsCard row — compound badge+text children where `center` is correct) as Skip per Karpathy §3. Closes AP-Phase2-B deferred fix from FIX-011. See `claudedocs/4-changes/bug-fixes/FIX-013-inline-font-baseline-alignment.md`.
- ✅ **`AD-Shadcn-Border-Token-Visual-Audit-Or-Align-To-Mockup`** — RESOLVED 2026-05-25 via **FIX-012** (user chose Path A as transitional fix). Both consumer sites retargeted at mockup `--border` (`index.css:85` global `* { border-color }` + `tailwind.config.ts:26` `border` utility); `--sc-border` declarations fully retired (0 residual code references). Sprint 57.28 4-layer dual-track partially relaxed (only `--sc-primary` remains as de-collided shadcn token). Path B Phase-2 epic completion still proceeds independently — Path A does NOT substitute for finishing the remaining 2 🟡 STRUCTURAL routes. See `claudedocs/4-changes/bug-fixes/FIX-012-shadcn-border-token-align-to-mockup.md`.
- 🆕 **Sister-bug observation**: FIX-010 (`/loop-debug` fullBleed prop drop) + FIX-011 (`/state-inspector` outer padding wrapper) form a recurring **layout-class production-only artifact** class. Each Phase-2 re-point sprint Day 0 Prong 1 should grep for these artifacts on the target page BEFORE Day 1 code.

### Why Sprint 57.38 Day 2.1 audit missed Issue 1

Domain C `AD-FullBleed-Pages-Audit` cross-referenced production `AppShellV2` mounts vs mockup outer wrapper classes (`chat-shell` / `loop-canvas` / `page-head`) — looking for **fullBleed prop drops**. It found 0 sites. But the audit scope was **only the `fullBleed` decision class**; it did NOT scan for *production-only outer padding wrappers ADDED inside the AppShellV2 mount*. Issue 1 falls into a different class (AP-Phase2-A) that the Sprint 57.38 audit didn't cover.

**Lesson for next audit**: extend Day 0 grep to include:
```bash
grep -n "style={{.*padding\|<div style={{[^}]*padding" frontend/src/pages/<target>/<page>.tsx
```

---

## 🆕 Sprint 57.38 Carryover (2026-05-24 — 3-domain batched: class-split decision + /subagents re-point + fullbleed audit)

Sprint 57.38 (`AD-ClassSplit-Decision-And-Subagents-Repoint-And-FullBleed-Audit`) closed:

- **Domain A — Option 2 class split applied** for `frontend-verbatim-css-repoint`:
  - `-simple` baseline **0.50** — applies when ALL hold: ≤3 files / no AP-2 banner / no dual-mount / no playback/filter widgets / HEX_OKLCH_BASELINE bump < 4. Empirical: 57.34 (/orchestrator) + 57.38B (/subagents) — 2-pt mean ~1.0 in band middle ✅
  - `-with-extras` baseline **0.65** — applies when ANY hold: multi-file > 3 / AP-2 BackendGapBanner / dual-mount / playback/filter/inspector widgets / HEX_OKLCH_BASELINE bump ≥ 4. Empirical: 57.35 + 57.36 + 57.37B historical mean 1.48 at 0.50 → equivalent ~1.14 at 0.65 in band ✅
  - Per-sprint classification rule codified in `.claude/rules/sprint-workflow.md §Scope-class multiplier matrix`
- **Domain B — `/subagents` Phase-2 verbatim CSS re-point shipped** (commit `7466d6ef`; agent-delegated 5th consecutive). Day 0 D5 cautiously reclassified `-with-extras` but Day 3 strict criteria re-eval reverted to `-simple` 2nd app (0/5 criteria met). Ratio ~0.91-1.09 estimated.
- **Domain C — `AD-FullBleed-Pages-Audit` 0 sites missing** (happy outcome) — confirms FIX-010 was isolated prop-drop, NOT systematic layout-class assignment failure. 13 production AppShellV2 mounts mapped to mockup wrapper classes: 2 fullbleed (loop-canvas + chat-shell) both correctly opt in; 11 page-head padded card-layout pages all correctly default to NO fullBleed.

### 🔚 CLOSED carryover ADs (Sprint 57.38)

- **`AD-Sprint-Plan-frontend-verbatim-css-repoint-class-split-proposal`** (Sprint 57.37 NEW) — RESOLVED via Option 2 split
- **`AD-Sprint-Plan-frontend-verbatim-css-repoint-multi-dimensional-variance-watch`** (Sprint 57.36 NEW) — RESOLVED; class split absorbs multi-D variance into 2 baselines
- **`AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift`** (Sprint 57.31 NEW) — RESOLVED; class split was alternative chosen path
- **`AD-FullBleed-Pages-Audit`** (FIX-010 Sprint 57.37+ follow-up) — RESOLVED 0 sites missing

### 🆕 NEW carryover candidates (Sprint 57.39+)

- **`AD-Day0-Prong-Test-Dir-Convention`** — extend Day 0 Prong 1 grep template to cover BOTH `frontend/src/**/__tests__/` AND `frontend/tests/unit/pages/<name>/<name>.test.*` (per Sprint 57.38 D-DB1-2 lesson — project uses separated test dir convention not always co-located `__tests__/`)
- **`AD-Day0-D5-Reclass-Strict-Criteria-Checklist`** — codify 5-item strict checklist before reclassifying `-simple` → `-with-extras` at Day 0 D5 (per Sprint 57.38 retro Q4#2: multi-file > 3 / AP-2 banner / dual-mount / playback widgets / HEX_OKLCH_BASELINE bump ≥ 4 — if 0 of 5 check, keep `-simple` even when internal structure complex)
- **Convention candidate (D-DB1-1)**: agent proactive div-wrap pattern preserves text+role+class-selector spec compat — document in `docs/rules-on-demand/frontend-react.md` as recommended-pattern when spec uses `getByText(x, { selector: "div" })`

### Phase-2 epic progress

- **11 routes shipped** since Sprint 57.29 epic open: /overview / /chat-v2 / /cost-dashboard / /sla-dashboard / /orchestrator / /loop-debug LoopVisualizer (Sprint 57.36) / /state-inspector / /subagents (Sprint 57.38) + AuthShell + LoopVisualizer dual-mount + StateInspectorPage
- **6 🟡 routes remaining**: /governance multi-page / /admin-tenants / /tenant-settings STRUCTURAL Phase 58+ / /memory STRUCTURAL Phase 58+ / /verification / /compaction (PROP stub representative)

---

## 🆕 Sprint 57.37 Carryover (2026-05-24 — 2-domain batched: /loop-debug full rebuild + /state-inspector Phase-2)

Sprint 57.37 (`AD-LoopDebug-Full-Rebuild-And-StateInspector-Repoint`) closed: 2-domain batched. **Domain A /loop-debug full mockup-fidelity rebuild** closes Sprint 57.36 §Frontend Mockup-Fidelity Hard Constraint gap — 18-event fixture (`_fixtures/demoLoopEvents.ts` NEW) + playback strip (cursor/play/pause/scrubber/speed 1×/4×/8×/16×) + filter pills (6 categories) + LoopInspector right pane (KvRow + HITL Policy + Raw payload) + corrected AP-2 DEMO DATA banner. **User-reported `/loop-debug` empty-state issue FULLY RESOLVED** (after.png shows visual parity with mockup `localhost:8080/#loop-debug`). **Domain B /state-inspector** Phase-2 verbatim CSS re-point per `page-platform.jsx:21-155` preserves Sprint 57.19 US-B3 backend wiring. 22-route sweep **18 IDENTICAL + 4 CHANGED** (loop-debug +63,405 B fixture-rich +66%; state-inspector -14,681 B verbatim simpler; chat-v2 **0 B PERFECT cascade**; auth-callback -68 B + overview +138 B noise). 4 gates green. Vitest **464/464** (+8 NEW Domain A specs; D-DAY3-1 Domain B spec class-swap-resilient — NO update needed). HEX_OKLCH_BASELINE 41→50 within Day 0 D-DAY0-6 estimate. Sprint total ratio ~1.0 IN BAND middle (2-domain HYBRID averaging). Agent-assisted Day 1-3 (4th consecutive code-implementer; ~4.5 hr wall-clock). Updates:

- ✅ **RESOLVED: Sprint 57.36 §Frontend Mockup-Fidelity Hard Constraint gap on /loop-debug** — fixture demo + 4 mockup widgets shipped per CLAUDE.md rule "後端尚未支援的 widget → 仍依 mockup 視覺實作，data 用 fixture"
- ✅ **RESOLVED: User-reported `/loop-debug` empty-state UX issue 2026-05-24** — page now visually parity with mockup

- 🆕 **NEW DECISION CANDIDATE: `AD-Sprint-Plan-frontend-verbatim-css-repoint-class-split-proposal`** — Domain B 4th non-rich data point 1.33 ABOVE band; **3-consecutive-above-band lift trigger MET** (57.35=1.7 + 57.36=1.42 + 57.37B=1.33; 4-pt non-rich mean 1.36). Per `When to adjust` rule (3+ consecutive > 1.20 → raise multiplier). **Two options for Sprint 57.38 retro decision**:
  - **Option 1**: class-wide baseline lift 0.50 → 0.60 (simpler; over-corrects truly simple 57.34 baseline)
  - **Option 2 (recommended)**: class split `-simple` (0.50): pure 1-file CSS swap no extras (Sprint 57.34 baseline 1.0 in-band) vs `-with-extras` (0.65): + any of {AP-2 banner, dual-mount, playback/filter/inspector widgets, verbatim oklch-heavy port with HEX_OKLCH_BASELINE bumps, multi-file batched > 3 files} (Sprints 57.35/57.36/57.37B mean 1.48)

- 🔄 **Updated: `AD-Sprint-Plan-frontend-verbatim-css-repoint-multi-dimensional-variance-watch`** (Sprint 57.36 NEW) — 4th non-rich data point empirically confirms multi-D hypothesis; closed either Option 1 or Option 2 in Sprint 57.38

- 🔄 **Updated: `AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift`** (Sprint 57.31 NEW) — alternative lift path; closed either Option 1 or Option 2 in Sprint 57.38

- 🆕 **Convention candidate (D-DAY3-1 positive surprise)**: Vitest spec class-swap-resilience — prefer `getByText` / `getByRole` / `data-testid` over class-name selectors. Codify in `.claude/rules/sprint-workflow.md` OR `docs/rules-on-demand/frontend-react.md`. StateInspectorPage spec needed NO update during Sprint 57.37 Day 3 verbatim port — saved ~10-15 min spec adapt time.

- 🆕 **Lesson**: Calibration ratio formula clarification — `actual / calibrated` (NOT `actual / bottom-up`); codify in sprint-workflow.md to prevent agent prediction errors like Sprint 57.37 Day 3 estimate

- 🆕 **Tracking**: `/overview` + `/auth-callback` recurring noise pattern in route-sweep PNGs (overview +138 B Sprint 57.37 / +70 B Sprint 57.36; auth-callback -68 B Sprint 57.37 first occurrence) — investigate if persists 3+ sprints; likely time-relative text or PNG AA variance

- 🎯 **Phase-2 epic progress**: 7+1 routes shipped (7 Phase-2 routes + AuthShell + LoopVisualizer dual-mount + StateInspectorPage full re-point) / **7 🟡 routes remaining** (governance / admin-tenants / tenant-settings STRUCTURAL Phase 58+ / memory STRUCTURAL Phase 58+ / compaction + 3 unblocked-by-57.33 PROP stubs)

- 🔍 **Drift findings** (Day 0-3): D-DAY0-1..7 (Day 0 verifications) / D-DAY1-1 (TS forEach→for-loop) / D-DAY2-1..3 (17 lint fixes + baseline +3 + fixture 18 events) / D-DAY3-1..3 (spec NO update positive surprise + baseline +6 + KvLine helper <10 line creep)

## 🆕 Sprint 57.36 Carryover (2026-05-24 — /loop-debug Phase-2)

Sprint 57.36 (`AD-Loop-Debug-Verbatim-Repoint`) closed: `frontend/src/features/orchestrator-loop/components/LoopVisualizer.tsx` single-file re-pointed to mockup verbatim per `reference/design-mockups/page-governance.jsx:33-212`. **7th Phase-2 epic app; 3rd shape-validation data point.** 22-route sweep **19 IDENTICAL + 3 CHANGED** (loop-debug +22,512 B expected structural; chat-v2 +18 B cascade ε; overview +70 B time-text noise). 4 gates green (TS 0 / lint 0 / Vitest 456/456 / mockup-fidelity 41/41 unchanged). Agent-assisted Day 1-2 via code-implementer agent (3rd consecutive validated; ~80 min wall-clock). AP-2 BackendGapBanner + EmptyInspectorPlaceholder explicitly defer playback/scrubber/filter/inspector pane to Phase 58+ per Sprint 57.12 AP-6. Dual-mount preserved (Sprint 57.30 chat-v2 inline ship safe). ~205 min total human-equivalent. Ratio actual/committed ~1.42 ABOVE band by 0.22. Updates:

- 🆕 **AD-Sprint-Plan-frontend-verbatim-css-repoint-multi-dimensional-variance-watch** — Sprint 57.36 is 3rd shape data point: 1-file non-rich AGAIN (like 57.34) but ratio diverged sharply (1.0 vs 1.42). Both prior 1-D hypotheses (bimodal-by-shape AND scale-overhead) insufficient. Emerging compound drivers: file count + AP-2 banner addition + dual-mount complexity + spec adapt + drift handling. If Sprint 57.37+ continues > 1.20, propose either (a) baseline lift 0.50 → 0.60, or (b) class split `frontend-verbatim-css-repoint-simple` (0.50, no AP-2 / no dual-mount) vs `frontend-verbatim-css-repoint-with-ap2-or-dual-mount` (0.65). KEEP 0.50 this iteration per `When to adjust` 3-sprint window rule (3-pt non-rich: 1.0/1.7/1.42 needs 1 more above-band for formal lift trigger).

- 🔚 **CLOSED: AD-Sprint-Plan-frontend-verbatim-css-repoint-shape-bimodal-watch** (Sprint 57.34 NEW; Sprint 57.35 weakened) — 3 non-rich data points (57.34=1.0 / 57.35=1.7 / 57.36=1.42) span the whole band; not bimodal. REJECTED.

- 🔄 **Updated → WEAKENED: AD-Sprint-Plan-frontend-verbatim-css-repoint-scale-overhead-watch** (Sprint 57.35 NEW) — 1-file (57.36) ALSO above band (1.42); file-count alone is not the variance driver. Broaden into multi-dimensional-variance-watch.

- 🔄 **Updated: AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift** (Sprint 57.31 NEW) — 4th validation data point logged. 0.50 baseline still appropriate for **simple non-rich 1-file** sprints (57.34 only in-band data point); above-band trend (57.35 + 57.36) needs 1 more above-band sprint for formal lift trigger.

- 📚 **Lessons logged**:
  - Day 0 Prong 1 glob coverage rule: extend to BOTH `frontend/src/**` AND `frontend/tests/**` for spec-existence claims (test files conventionally live outside `src/`). D-DAY1-1 cost ~5 min in agent re-discovery. Codify in `.claude/rules/sprint-workflow.md` §Step 2.5 Prong 1.
  - AP-2 BackendGapBanner addition: ~10-15% calibration surcharge candidate.
  - Dual-mount preservation (mode-branching): ~5-10% surcharge candidate.
  - Combined sprints (AP-2 + dual-mount) should baseline ~0.60-0.65 not 0.50.
  - ESLint `no-restricted-syntax` JSXAttribute style matcher is body-blind for `style={CONSTANT_REF}`; Sprint 57.24 BarTrack STYLE.md §3 escape hatch (module-scope constants + per-site `eslint-disable-next-line`) is the documented workaround.

- 🔍 **Drift findings** (Day 0-1): D-DAY0-1..7 catalogued in progress.md; D-DAY1-1 (test file location) + D-DAY1-2 (ESLint body-blind) caught by agent.

- 🎯 **Phase-2 epic progress**: 6 routes shipped (+ AuthShell + LoopVisualizer dual-mount) / 8 routes remaining (state-inspector, memory STRUCTURAL Phase 58+, governance multi-page, admin-tenants, tenant-settings STRUCTURAL, compaction, 3 unblocked-by-57.33 PROP stubs).

## Sprint 57.35 Carryover (2026-05-24 — AuthShell + 7 auth routes Phase-2)

Sprint 57.35 (`AD-Auth-Shell-And-Pages-Verbatim-Repoint`) closed: 8 files (1 AuthShell + 7 auth routes) re-pointed to mockup verbatim — **6th Phase-2 epic app**; user-reported `/auth/login` drift 2026-05-24 (SSO unstyled / Continue no fill / `dev-login` orange missing) **fully RESOLVED**; **closes Sprint 57.23 vintage HSL-translation epic gap** on auth routes (CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint warning). 22-route sweep **0 regressions** on other 14 routes. 5 gates green. Vitest **456/456 baseline preserved** (4 spec files updated `getByLabelText` → `getByText`+id selectors for mockup-ui Field DOM change; behavioral test intent preserved). Agent-assisted Day 1-3 via code-implementer agent. ~7-7.5 hr human-equivalent effort. Updates:

- ✅ **RESOLVED — Sprint 57.23 vintage HSL-translation epic gap on auth routes** (CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint warning) — fully closed by this sprint.

- 🆕 **AD-Sprint-Plan-frontend-verbatim-css-repoint-scale-overhead-watch** — Sprint 57.35 ratio ~1.65-1.75 ABOVE [0.85, 1.20] band by ~0.45-0.55 (8-file batched sprint). Combined with 57.34 (1-file ≈1.0 in band) + 57.35 (8-file ~1.7 above band), both non-rich-dashboard but vastly different ratios — **file-count + Vitest-spec-update overhead emerging as 2nd variance driver** (not pure shape-driven). If Sprint 57.36+ multi-file sprints again > 1.20 → propose **file-count surcharge** in calibration multiplier (e.g. 0.50 + 0.05/extra-file beyond ~3). KEEP 0.50 baseline this iteration per `When to adjust` 3-sprint window rule (3-pt span 0.40/1.0/1.7 inconclusive).

- 🔄 **Updated AD-Sprint-Plan-frontend-verbatim-css-repoint-shape-bimodal-watch** (Sprint 57.34 NEW) — bimodal-by-shape hypothesis **WEAKENED but not REJECTED**. 2 non-rich data points (57.34 vs 57.35) span ratio 1.0 to 1.7, suggesting shape is NOT the dominant variance driver; file-count is. Broaden to **scale-and-shape watch**; don't propose class split until 4th data point discriminates.

- 🔄 **Updated AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift** (Sprint 57.31 NEW) — 3rd validation data point logged. 0.50 baseline still appropriate for typical 1-file re-points.

- 📚 **Lessons logged**:
  - File-count + Vitest-spec-update overhead may be 2nd variance driver beyond shape; budget per-file linearly for multi-file sprints
  - Vitest spec update budget when primitive API changes (e.g. `<label>` → `<div>`); 30-60 min per primitive switch
  - Mockup-internal drift: `page-extras.jsx:13` AuthShell width 400px vs sibling `page-auth-extras.jsx:13` AuthShellX 420px — designate canonical source in `reference/design-mockups/AGENTS.md`

- 🔍 **Drift findings** (Day 1-3): D-DAY1-1 (AuthShell width 420→400 mockup truth) / D-DAY2-1 (register plan label a11y aria-label added) / D-DAY2-2 (register demo banner recast as `.hitl-card[data-severity="risk-medium"]`) / D-DAY3-1 (expired Badge tone="warning" per mockup)

## Sprint 57.34 Carryover (2026-05-24 — /orchestrator Phase-2)

Sprint 57.34 (`AD-Orchestrator-Verbatim-Repoint`) closed: `/orchestrator` re-pointed to mockup verbatim — **1st non-rich-dashboard shape** in the Phase-2 epic (prior 4 = rich operator dashboards). 22-route sweep **0 regressions** on other 21 routes. 5 gates green. Vitest 456/456 baseline preserved. Agent-assisted Day 1-3 via code-implementer agent (per CLAUDE.md Tool Optimization). 3 mockup-ui primitives promoted (Tabs / Field / Switch). OrchestratorPage 644 → 605 net –39 lines (drop ~150 lines of local primitives + Tailwind translations; add mockup-ui imports + verbatim CSS classes + data-testid hooks). ~3-4 hr human-equivalent effort. Carryover updates:

- 🆕 **AD-Sprint-Plan-frontend-verbatim-css-repoint-shape-bimodal-watch** — Sprint 57.34 ratio ≈0.95-1.05 lands in [0.85, 1.20] band middle. Combined with prior 4 rich-dashboard apps (3-pt mean ≈0.40 below band ex-57.29 anchor), **bimodal-by-shape pattern emerging** — rich-dashboard ratios consistently below band; non-rich-dashboard (1st data point) in band middle. 2-data-point span (57.32 rich + 57.34 non-rich) suggestive but insufficient per `When to adjust` 3-sprint window rule. **KEEP 0.50 baseline this iteration.** If Sprint 57.35 (another non-rich-dashboard shape — `/loop-debug` / `/state-inspector` / `/admin-tenants` / `/governance` / `/tenant-settings`) confirms in-band → propose class split `-rich-dashboard` (0.40) vs `-config-form` (0.50). If lands below band → class-wide variance after all → 0.50 → 0.40 lift.

- 🆕 **AD-Tabs-Migration-To-MockupUi** (low priority) — `frontend/src/components/ui/tabs.tsx` Sprint 57.19 vintage primitive still imported by other consumers (governance/loop-debug/state-inspector candidates); out-of-scope this sprint. Future Phase-2 re-point of those routes will naturally migrate them to mockup-ui Tabs, then `ui/tabs.tsx` can be deleted.

- 🔄 **Updated AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift** (Sprint 57.31 NEW) — 2nd validation data point logged. 0.50 baseline still appropriate but bimodal-by-shape signal emerging. If 57.35 confirms, may close this AD in favor of class split.

- 📚 **Atomic primitive promotion lesson** — when primitive promotions span multiple Days but consumer components consume them together, atomic Day 1 promotion is the right call (vs staggered across Days). Agent correctly identified this build-dep; Day 2/3 commits became cycle housekeeping. Plan structure looks "off" in retrospect but result was clean.

## Sprint 57.33 Carryover (2026-05-24 — Page Bug Fix Sweep)

Sprint 57.33 (`AD-Page-Bug-Fix-Sweep`) closed: 3 ⚪ pre-existing crash routes (`/subagents` + `/memory` + `/verification`) fixed by adding defensive `(query.data.X ?? []).length/map` across 5 files / 11 sites including 4 drift sites D1-D4 (`.map` × 3 + `_groupByTurn(items)` × 1) found by widening Day 0 grep beyond `.length`. 22-route sweep: **3 ⚪ → ✅ flip + 0 regressions** on other 19 routes. Vitest 452 → 456 (4 NEW defensive specs). NEW class `frontend-page-bug-fix` 0.45 1st application; ratio actual/committed **1.24** top edge of [0.85, 1.20] band +0.04 over. ~2.8 hr wall-clock. Closes `AD-Overview-PreExisting-Route-Crashes` carryover from Sprint 57.29-32. Updates:

- ✅ **RESOLVED — AD-Overview-PreExisting-Route-Crashes** (Sprint 57.29-32 carryover) — fully closed. 3 ⚪ routes now render proper UI (subagents = full Registry + 4 KPI cards + table; memory = Recent + By Scope tabs + empty state; verification = Recent + Correction Trace tabs + filter form + empty state).

- 🆕 **AD-Sprint-Plan-frontend-page-bug-fix-1st-data-point** — KEEP 0.45 baseline per `When to adjust` 3-sprint window rule. If next 2-3 applications show ratio > 1.20 consistently → propose **0.45 → 0.55-0.60 lift** (mechanical-class-like trend, parallel to Sprint 57.16 AD-Sprint-Plan-13 `frontend-refactor-mechanical` 0.50 → 0.80 evidence).

- 🆕 **AD-CorrectionTraceView-Defensive-Spec** (low priority) — defensive Vitest spec for `CorrectionTraceView` deliberately skipped this sprint per US-D3 "1-2 new specs" scope discipline. Crash path is indirect (via `_groupByTurn(entries)` for…of); covered by Day 4 manual smoke + 22-route sweep flip. Add in future maintenance sprint if `/verification` structural rebuild is scheduled.

- 📚 **Lesson logged in retrospective Q4** — for "undefined-field" / "missing property" crash classes, Day 0 Prong 2 grep should query **all access patterns** on the at-risk field (`\.length`, `\.map`, `\.filter`, `\.forEach`, bare references as function args), not just the access pattern surfaced in the bug repro. 4 drift sites D1-D4 in this sprint are evidence.

- 🔓 **Unblocks** — Phase-2 verbatim CSS re-point candidates for `/subagents`, `/memory`, `/verification` (sweep `after` baselines now meaningful; visual fidelity audit can proceed). `/memory` STRUCTURAL rebuild Phase 58+ remains unchanged scope (independent of crash-fix).

## Sprint 57.32 Carryover (2026-05-24 — /sla-dashboard Phase-2)

Sprint 57.32 (`AD-Sla-Dashboard-Verbatim-Repoint`) closed: `/sla-dashboard` 7 files re-pointed — fidelity verdict **PARITY**, 22-route sweep **cleanest yet** (17 🟢 PARITY shell + 1 🟢 PARITY target + 1 🟢 PROP-stub + 0 🟡/🟠/🔴 + 3 ⚪ pre-existing fails). 4th data point for `frontend-verbatim-css-repoint` 0.50 (lifted) class; **cleanest mockup mapping of any Phase-2 sprint** (0 production-only widgets — distinct from Sprint 57.31 cost-dashboard which had 3). ~3 hr total wall-clock. Carryover updates:

- **AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift** (Sprint 57.31 NEW; **1st validation data point this sprint**) — Sprint 57.32 ratio actual/committed ~0.40-0.55 (lower band edge). 4-pt mean ≈0.55 lower edge; 3-pt mean ≈0.40 excluding 57.29 anchor (below band by 0.30). Per `When to adjust` 3-sprint window rule, 1 validation data point insufficient to adjust further → **KEEP 0.50 baseline this iteration**. If Sprint 57.33 + 57.34 also < 0.7 → propose 0.50 → 0.40 in Sprint 57.34 retrospective.

- **Hybrid Tailwind+inline color bridge pattern matured across 5 files** (Sprint 57.29 carryover `AD-Inline-Style-Rule-vs-Verbatim-Method` partial exercise) — applied across SLAOverview, LatencyChart, SLOStatusCard, TopSlowOpsTable, ErrorRateByServiceCard. Day 2 SLOStatusCard caught 2 spec drift; Day 3 applied bridge preemptively → 0 spec drift. Pattern documented as standard for Sprint 57.25+ dashboards being Phase-2 re-pointed. Lesson: any color-tone Tailwind class (`text-warning`, `text-danger`, `text-fg-muted`) used in Sprint 57.25 spec contracts should be preserved alongside inline `style={{ color: var(--*) }}` for verbatim.

## Sprint 57.31 Carryover (2026-05-23 — /cost-dashboard Phase-2)

Sprint 57.31 (`AD-Cost-Dashboard-Verbatim-Repoint`) closed: `/cost-dashboard` 7 components batched Day 1 single agent delegation — fidelity verdict **PARITY**, 22-route sweep **cleanest yet** (18 🟢 PARITY + 1 🟢 PROP-stub + 0 🟡/🟠/🔴 + 3 ⚪ pre-existing fails — shell unchanged from 57.30 + cost-dashboard gain internal). 3rd data point for `frontend-verbatim-css-repoint` 0.60 class. New carryover:

- **AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift** (Day 4 calibration) — replaces CLOSED `AD-Sprint-Plan-frontend-verbatim-bimodal-watch` (Sprint 57.30 carryover). Bimodal hypothesis REJECTED — 57.29 + 57.31 same rich-dashboard shape with vastly different ratios (1.0 vs 0.35), so shape NOT the driver of variance. Driver IS estimate generosity diminishing as class iteration matures. Per `When to adjust` 3+ consecutive < 0.7 rule (57.30 + 57.31 + the 0.45+ below-band magnitude on 2 of 3 = clear signal) → LOWER baseline 0.60 → 0.50. Validate 0.50 across next 2-3 sprints; if continues < 0.5 → consider 0.40 next iteration.
- **AD-CostBreakdownTable-Backend-Tenant-Scope** (Day 1 D4 finding) — `CostBreakdownTable.tsx` shows real backend `by_type` 2-level drill-down (`cost_type/sub_type/quantity/total_cost_usd/entry_count`) for current authenticated tenant; distinct from `TenantTopTable` (cross-tenant admin fixture). Document data ownership to prevent accidental merge in future sprints; consider adding ARCHITECTURE.md section on cost-dashboard data flows.

**3 production-only widget patterns identified** (generalizable for future Phase-2 sprints):
1. **Mockup token vocabulary only** (MonthPicker D5) — `var(--*)` inline; no AP-2 banner; UI affordance.
2. **Mockup `.table` vocabulary verbatim** (CostBreakdownTable D4 decision c) — real backend; no AP-2; same vocabulary as if mockup had it.
3. **Mockup vocabulary + AP-2 BackendGapBanner** (e.g. Sprint 57.30 InputBar error) — fixture data; AP-2 honesty banner.

---

## Sprint 57.30 Carryover (2026-05-23 — chat-v2 Phase-2 + shell hotfix; AD-Sprint-Plan-frontend-verbatim-bimodal-watch CLOSED in 57.31)

Sprint 57.30 (`AD-Chatv2-Verbatim-Repoint + Shell-Hotfix-UserMenu-Avatar`) closed: `/chat-v2` 19 components re-pointed to verbatim mockup CSS + Day 1 shell hotfix (UserMenu Radix-drop + verbatim `useDismiss` port + avatar trigger 36→26 split + topbar icon audit 0 drift) — fidelity verdict **PARITY**, 22-route sweep 0 catastrophic / 0 structural; Day 5 orphan cleanup deletes `dropdown-menu.tsx` + `npm uninstall @radix-ui/react-dropdown-menu` → bundle **-116.87 KB / -38.37 KB gzipped**. Closed `AD-UserMenu-Mockup-Structural-Deltas` (Sprint 57.29 carryover). New carryover:

- ✅ **CLOSED Sprint 57.31**: **AD-Sprint-Plan-frontend-verbatim-bimodal-watch** — Sprint 57.31 3rd data point evaluation rejected bimodal hypothesis; replaced by `AD-Sprint-Plan-frontend-verbatim-css-repoint-baseline-lift` above.
- **AD-Tsconfig-Node-NoEmit** (Day 1 finding) — `tsc --strict` reports pre-existing `TS6310: referenced project tsconfig.node.json may not disable emit` since baseline `5c0ce0dd`. Not introduced by Sprint 57.30. Defer to tooling cleanup sprint or separate PR.
- **AD-Topbar-Use-Button-Primitive** (Day 0 D4 finding) — production Topbar uses raw `<button className="btn ghost" data-size="sm">` instead of mockup-ui `<Button>` primitive. Rendered DOM byte-identical; cosmetic-code-style refactor, low ROI. Defer.
- **AD-Topbar-Tweaks-Panel-Phase58+** (Day 0 D5 finding) — mockup `shell.jsx:218` has `<Button icon="sliders" onToggleTweaks>` Tweaks button; production omits it (no Tweaks panel implementation). Defer to Phase 58+ when Tweaks panel ships.
- **AD-ApprovalCard-Legacy-Phase58-Migrate** (Day 4 finding) — `ApprovalCard` confirmed legacy per `chatStore.ts:L324` dual-emit comment; HITLTurn is canonical Phase-1 chat-inline render. Re-pointed this sprint for completeness; 0 main render path. Migrate governance integration to HITLTurn-only in Phase 58+, then delete.

---

## 🆕 Sprint 57.29 Carryover (2026-05-22 — Phase-2 per-page re-point opens; partially closed in 57.30)

Sprint 57.29 (`AD-Overview-Verbatim-Repoint`) closed: `/overview` + app shell + 3 topbar overlays + 7 widgets re-pointed to verbatim mockup CSS — fidelity verdict **PARITY**, 22-route regression sweep 0 catastrophic / 0 structural. The Phase-2 per-page re-point template is validated (`frontend-verbatim-css-repoint` 0.60 class). Carryover:

- **AD-Inline-Style-Rule-vs-Verbatim-Method** — the `no-restricted-syntax` ESLint inline-`style=` ban (Sprint 57.15/57.16) conflicts with the verbatim method's required mockup inline-style literals; currently handled per-file with `eslint-disable` + rationale. Decide: scope the rule to exclude verbatim-re-pointed dirs, or retire it.
- **AD-UserMenu-Mockup-Structural-Deltas** — ✅ **CLOSED in Sprint 57.30 Day 1**: Radix `<DropdownMenu>` dropped entirely; `useDismiss` hook ported verbatim from mockup `topbar-overlays.jsx:9-27`; avatar trigger 36→26 split via `.avatar` CSS class; dropdown now flush against topbar bottom edge (`top:50; right:12` verbatim positioning honoured).
- **AD-MockupFidelity-Guard-TokenRelative-Oklch** — `frontend/scripts/check-mockup-fidelity.mjs` grep counts token-relative `oklch(from var(--token) …)` literals as "hardcoded"; refine the grep to exclude them so faithful verbatim re-points don't grow `HEX_OKLCH_BASELINE` (raised 18→21 in 57.29; 21→25 in 57.30).
- ~~**AD-Overview-PreExisting-Route-Crashes** — `/subagents`, `/memory`, `/verification` render an error boundary (`Cannot read properties of undefined (reading 'length')`) — pre-existing (Day-0 baseline == after sweep on both 57.29 and 57.30); NOT a regression. Separate FIX sprint candidate (Sprint 57.31+ "frontend-page-bug-fix" class at ~0.45 mid-band).~~ **✅ RESOLVED Sprint 57.33** — see Sprint 57.33 Carryover section above.
- **Next Phase-2 per-page re-point** — Sprint 57.30 picked `/chat-v2`. Remaining 12 🟡 AppShellV2 routes: orchestrator / loop-debug / memory / state-inspector / governance / verification / cost-dashboard / sla-dashboard / admin-tenants / tenant-settings / compaction (+ subagents / memory / verification but those need crash fix first).

---

## 🔴 Top Candidates (User-Aligned Priority)

### 1. AD-ChatV2-Full-Mockup-Fidelity Phase-2

Multi-sprint epic continuation. Sprint 57.21 Phase-1 already shipped:
- Turn Block Model
- SessionList fixture
- Inspector 4-tab frame
- Composer visual scaffolding

**Phase-2 carryover ADs** (from Sprint 57.21 retro):
- AD-ChatV2-Memory-Block-Phase2
- AD-ChatV2-HITL-FourAction-Phase2
- AD-ChatV2-Composer-Richness-Phase2
- AD-ChatV2-Composer-Wire-Phase2
- AD-ChatV2-Inspector-{Trace, Memory, SubagentTree}-Phase2
- AD-ChatV2-SessionList-Backend
- AD-Cat12-SSE-Trace-Id-Phase2

**Mode**: Pick subset for Phase-2 first sprint depending on backend dependency ordering. Likely structural-rewrite mode → `frontend-mockup-direct-port` ratio ~1.0-1.2 predicted.

### 2. 🆕 AD-Mockup-Direct-Port-Round-2

NEW Sprint 57.20 Day 4 DRIFT-REPORT-ROUND-2 (16 R2 findings).

**Scope** — Token migration sweep for **8 remaining ship pages**:
- cost-dashboard / memory / verification / governance + 4 governance sub-routes / sla-dashboard / admin-tenants / tenant-settings

Plus:
- 3 overlay backend wiring
- R2-A 5 cosmetic Card visual polish

**Class**: Same `frontend-mockup-direct-port` 0.55 class likely.

### 3. AD-Mockup-Existing-Pages-Retrofit Tier 1

Sprint 57.19 US-F1 DRIFT-REPORT; partially closed Sprint 57.20 via `/overview` + `/chat-v2` token migration; **folds INTO Round-2 above**.

**Scope**: 9-page retrofit Tier 1 ~10.5 hr bottom-up = ~5.8 hr calibrated commit at NEW class `mockup-fidelity-retrofit` 0.55 1st app (HYBRID: cosmetic mechanical 0.45 + structural design 0.65 + closeout 0.80).

**5 priority pages**:
- cost-dashboard (3 hr)
- chat-v2 (3 hr)
- memory (2 hr)
- verification (2 hr)
- governance (1.5 hr)

**Tier 2**: ~5.5 hr → Sprint 57.21+
**Tier 3**: ~1 hr + Round 3 epic

---

## 🟡 Mockup-Page-Port Continuation

### 4. AD-Mockup-Page-X-Port Round 3 — Auth 4

Sprint 57.19 carryover. Pages:
- register / invite / mfa / expired

**Pairing**: IAM Block B (WorkOS SCIM/SAML/org-level RBAC) per 用戶 2026-05-16 Q3 alignment「前後端同 sprint」.

### 5. AD-Mockup-Page-X-Port Round 4 — Governance 3

Sprint 57.19 carryover. Pages:
- redaction / error-policy / audit-log (DRAFT → active promote)

**Pairing**: Cat 9 endpoint extensions.

---

## 🟢 Backend Wire Bundle

### 6. AD-Backend-Wire Bundle

Sprint 57.19 4 NEW ADs:
- Subagent-RealList-Phase58
- Loop-Session-Enrich-Phase58
- Overview-Backend-Wire
- Orchestrator-Backend-Wire

**Scope**: Backend persistence + aggregation for Operations 4 pages (current fixture/stub). Can pair with retrofit work.

### 7. 🆕 AD-CommandPalette-Backend-Wire

NEW Sprint 57.19 US-D1. Tenants + sessions groups currently fixture; wire Cat 1 sessions list + Cat 12 tenants index.

### 8. 🆕 AD-NotificationsPanel-Backend-Feed

NEW Sprint 57.19 US-D2. 6 mockup items local state; Cat 12 SSE/poll feed spec TBD.

### 9. 🆕 AD-UserMenu-Tenant-Switch

NEW Sprint 57.19 US-D3. Wire tenant switching paired with Round 2 WorkOS SCIM.

---

## 🛠️ Tooling / Infrastructure / Style

### 10. AD-Tailwind-v4-Config-Migration

Sprint 57.17 carryover. Full v4 idiomatic `@theme inline {}` block 取代 `@config "../tailwind.config.ts"` + 刪 legacy v3 config file. ~6-8 hr standalone sprint, same class `frontend-css-engine-hotfix`.

### 11. AD-Post-Hotfix-Token-Audit

NEW Sprint 57.17 contrast-ratio portion. **Folds INTO** AD-Mockup-Existing-Pages-Retrofit Tier 1 work (same shadcn slate base sub-AA pairs).

### 12. 🆕 AD-Brand-Primary-Color-Decision

Sprint 57.18 D-PRE-1. Partially actioned by Sprint 57.19 US-A1 mockup indigo; finalization decision pending.

### 13. 🆕 AD-Theme-Variant-Mechanism

Sprint 57.18 D-PRE-2.

### 14. 🆕 AD-Density-Variant-Mechanism

Sprint 57.18 D-PRE-3.

### 15. AD-CI-7-GHA-PR-Permission

Sprint 57.17 carryover. `playwright-e2e.yml:163-188` auto-PR-create blocked by repo setting.

### 16. AD-Lighthouse-Visual-Hard-Gate

Baselines reliable post-57.17; required CI check.

### 17. AD-Bundle-Size code-split

### 18. AD-i18n-Feature-Namespaces

### 19. AD-A11y-Structural-Nits

Sprint 57.16 carryover. `/chat-v2` 的 `heading-order` + duplicate `<main>` landmarks moderate/minor；`/auth/callback?error` `page-has-heading-one`.

---

## 🏢 Enterprise / SaaS Stage 2

### 20. IAM Block B Spike

~12-18 hr — WorkOS SCIM/SAML/org-level. Pairs with #4 Auth 4.

### 21. Tier 1 IaC + DR Drill

~15-20 hr.

### 22. SOC 2 + SBOM

~12-15 hr.

---

## 🟣 Sprint 57.23 Auth Page Rebuild Carryovers (NEW 2026-05-18)

7 ADs from Sprint 57.23 AD-Auth-Page-Full-Rebuild-Round-2 closeout. Frontend rebuild shipped 8/8 USs with stub-501 demo banners; backend wiring deferred to Phase 58+ IAM Block B/C per Q2 frontend-only decision.

### 23. AD-Auth-Register-Backend-IAM-Block-B-Phase58
`POST /api/v1/tenants/register` real implementation. Currently 501 stub. Frontend `/auth/register` 4-step wizard fully shipped + i18n + Vitest 5 cases. Phase 58+ IAM Block B scope.

### 24. AD-Auth-Invite-Backend-IAM-Block-B-Phase58
`GET /api/v1/invites/:token` (metadata) + `POST /api/v1/invites/:token/accept`. Currently 501 stubs; frontend falls back to fixture metadata silently for GET, surfaces explicit error for POST. Frontend `/auth/invite/:token` shipped + Vitest 4 cases. Phase 58+ IAM Block B scope.

### 25. AD-Auth-MFA-Backend-IAM-Block-C-Phase58
`POST /api/v1/mfa/verify` + TOTP secret enrollment + WebAuthn credential registration backend. Currently 501 stub. Frontend `/auth/mfa` Roll-own UI shipped (TOTP 6-digit grid + WebAuthn conic ring + Simulate button) + Vitest 7 cases. Phase 58+ IAM Block C scope.

### 26. AD-Auth-MFA-Recovery-Page-Phase58
`/auth/mfa/recovery` page wire — currently displayed as `<span pointer-events-none>` with tooltip "Recovery flow pending Phase 58+ IAM Block C". Backend recovery-code generation + verification. Phase 58+ IAM Block C scope.

### 27. AD-Auth-Callback-Loading-UX-Phase58
Replace static 3-step `setTimeout` (800/1800/2800ms) with real backend SSE per-step events when WorkOS OIDC callback wiring exists. Frontend already has 3-step UI + parallel-bootstrap + min-2800ms-enforce mechanism. Phase 58+ IAM Block B scope.

### 28. AD-WorkOS-Multi-IdP-Phase58
Wire actual SAML / Microsoft / Google SSO via WorkOS. Currently 3 buttons disabled with "Enterprise SSO via WorkOS roadmap" tooltip per mockup. Backend WorkOS Multi-IdP integration. Phase 58+ IAM Block B scope. (Existed pre-57.23 as design intent; now actively blocks Sprint 57.23 login button enablement.)

### 29. AD-Sprint-57-23-Playwright-MCP-Visual-Verify-Followup
Re-run Playwright MCP visual pair-verify on Sprint 57.23 12 page-states. Day 4 closeout encountered stuck browser state from prior Sprint 57.22 session (`Error: Browser is already in use ... use --isolated`). Closure via code-level audit + Sprint 57.22 baseline + visual-regression CI mechanism. Re-run in future session with fresh browser instance. **Low priority** — line-by-line port discipline + DRIFT-REPORT verdicts (all PARITY or COSMETIC; 0 STRUCTURAL/FUNCTIONAL) already cover fidelity gate.

### 30. AD-I18n-Symmetric-Keys-Lint-Phase58
Implement automated symmetric-keys lint at `frontend/tests/unit/i18n/` that runs `jq paths(scalars)` diff between en/<namespace>.json and zh-TW/<namespace>.json on every PR. Sprint 57.23 verified manually for `auth.json`; this AD generalizes for `chat-v2.json` / `governance.json` / `tenant-settings.json` etc. ~2-3 hr.

---

## 🔵 Sprint 57.24 Decision Carryovers (NEW 2026-05-19)

### 31. AD-Memory-Structural-Rebuild-Phase58
`/memory` page rebuild — Sprint 57.22 Unit 10 audit identified STRUCTURAL severity drift: production has simple 2-tab UI (Recent / By Scope) + 3 backend-wired scopes (system/tenant/user); mockup `page-governance.jsx:462-598` has full 5-scope × 3-time-scale matrix grid + time-travel scrubber + memory-ops timeline + per-memory CRUD.

**Scope**: Frontend rebuild ~12-15 hr + backend Cat 3 NEW SSE event `memory_op_emitted` ~3-4 hr + Cat 12 audit log ~2 hr + role/session backend scopes (currently Phase 58+ stubs) ~6-8 hr. **Total ~25-30 hr**.

**Class candidate**: NEW `frontend-mockup-structural-rebuild` (parallel to Sprint 57.23 NEW `frontend-mockup-strict-rebuild` 0.60 1st app; or HYBRID with backend wire).

**Defer rationale (Sprint 57.24 Q2 decision 2026-05-19)**: STRUCTURAL retrofit exceeds Sprint 57.24 `mockup-fidelity-retrofit` 0.55 scope (which is cosmetic-only by class definition). Memory structural rebuild needs dedicated sprint with backend pairing per Sprint 57.22 §Sprint 57.23+ Recommendation Tier 2 priority.

**Phase**: 58+ (after Auth Block B/C IAM backend lands; role/session memory scopes are part of IAM).

---

## 🟢 Sprint 57.24 v2 Cost Dashboard Rebuild Carryovers (NEW 2026-05-19)

7 ADs from Sprint 57.24 v2 AD-Cost-Dashboard-Full-Mockup-Fidelity-Rebuild closeout. Frontend rebuild shipped 6 widget groups + 7 reusable primitives (PageHead/Spark/StatCard/AreaChart/BarTrack/CardShell/BackendGapBanner) for Sprint 57.25-57.28 epic; 3 of 6 widgets ship fixture + visible BackendGapBanner per AP-2 honesty (backend wiring deferred).

### 32. ✅ CLOSED — AD-Mockup-Fidelity-Rebuild-Sla-Dashboard (shipped Sprint 57.25 2026-05-19)
~~Rebuild `/sla-dashboard` per mockup `reference/design-mockups/page-admin.jsx:31-199` (SlaPage).~~ **Shipped Sprint 57.25**: 6 widget groups (page-head + TimeRangeTabs / 4-stat sparkline / 24h LatencyChart 3-series / 5-row SLO status / Top slow ops table / Error rate by service); reused 7 Sprint 57.24 v2 primitives without API change validating Karpathy §2 ROI; 1 NEW feature-scoped LatencyChart inline; SLAMetricsCard Karpathy §3 orphan delete. Class 3rd app ratio 0.88 in-band lower; rich-dashboard 2-pt mean 1.04 in-band middle → sub-class hypothesis NOT confirmed; sub-classification DEFER (see #41). See `memory/project_phase57_25_sla_dashboard_rebuild.md` for detail.

### 33. AD-Mockup-Fidelity-Rebuild-Admin-Tenants-Phase58
Rebuild `/admin/tenants` list per mockup `page-admin.jsx:322-410` (AdminTenants section). Existing filters/table/pagination preserved; mockup-fidelity polish + admin context widgets added (avatar rendering / row-level actions / status badges per mockup). Sprint 57.27 candidate (foundation-fidelity Sprint 57.26 was inserted ahead as a user-directed sprint, shifting this +1).

### 34. AD-Mockup-Fidelity-Rebuild-Verification-Phase58
Rebuild `/verification` per mockup `page-extras.jsx:817-927` (VerificationPage). 2-tab structure (Recent / Correction Trace) preserved; inner widget mockup-fidelity port pending. Sprint 57.28 candidate.

### 35. AD-Mockup-Fidelity-Rebuild-Tenant-Settings-Phase58
Rebuild `/admin/tenants/settings` per mockup `page-admin.jsx:411+` (TenantSettings 6-tab) + lift `/feature-flags` out per Sprint 57.22 Unit 31 architectural finding + page-extras.jsx:928 comment "/feature-flags (lifted out of /tenant-settings)". Architectural-level refactor + new standalone `/feature-flags` route. Sprint 57.29 candidate.

### 36. AD-Cost-Dashboard-Backend-Extensions-Phase58
Backend follow-on for Sprint 57.24 v2 fixture-driven widgets:
- Cross-tenant aggregation endpoint (`GET /api/v1/admin/cost-summary/by-tenant` returning top-N tenant rows; platform-admin-scoped) — drives TenantTopTable
- Cross-provider aggregation endpoint (`GET /api/v1/admin/cost-summary/by-provider`; platform-admin-scoped) — drives ProviderMixCard with LLM-neutrality redacted labels
- 30-day daily history endpoint (`GET /api/v1/admin/cost-summary/history?days=30`) — drives AreaChart
- Harmonize category taxonomy: mockup 6 flat categories (Inference input/output / Thinking tokens / Tool runs / Embeddings / Sandbox compute) ≠ current backend `by_type` 2-level dict shape (cost_type → sub_type → AggregatedSlice); decision: either backend reshape OR define explicit aggregation mapping in spec

Drives Sprint 57.24 BackendGapBanner removal for 3 of 6 widgets + flips fixture data to real. ~8-12 hr backend + ~2-3 hr frontend wire-up. Phase 58+ backend-led; could pair with Sprint 57.25 sla-dashboard rebuild if scope permits.

### 37. AD-Playwright-MCP-Recovery-Phase58
**3-consecutive-sprint blocker** (Sprint 57.22 + 57.23 + 57.24 v2): Playwright MCP browser-stuck on every visual pair-verify attempt. `browser_close` returns "Browser is already in use for ...mcp-chrome-... use --isolated to run multiple instances of the same browser". Root cause: Claude Code session-process management — prior session's chrome instance not released to next session.

**Mitigation today**: code-level audit + Vitest spec coverage + Playwright CLI (separate from MCP) cover verification; visual baselines regen via CI workflow_dispatch + cherry-pick (Sprint 57.14 + 57.23 PR #156 + 57.24 v2 PR pattern).

**Phase 58+ resolution paths**:
- Option A: pass `--isolated` flag to MCP browser per session
- Option B: explicit cleanup hook on Claude Code session end (`process.kill` on chrome PID)
- Option C: contribute fix upstream to Anthropic Playwright MCP plugin

Cost: ~2-4 hr investigation + fix. Phase 58+; meanwhile workaround acceptable.

### 38. AD-Sprint-Plan-Audit-Cross-Ref-Prong5
**Plan-draft discipline addition** (Sprint 57.24 v1 abort lesson):

Sprint 57.24 v1 plan misclassified 3 of 5 retrofit targets (cost / sla / tenant-settings) as "cosmetic-feasible Tier 1" when Sprint 57.22 AUDIT-REPORT had already marked them P0 full-rebuild. Day 0 三-prong (Prong 1 path + Prong 2 content + Prong 3 schema + Prong 4 test selector) didn't catch this because they verify code-vs-plan drift, NOT plan-vs-audit-classification mismatch.

**Proposed Prong 5: Audit Cross-Reference**:
Before drafting Tier-N retrofit/rebuild plan, grep AUDIT-REPORT(s) for each target's prior classification:
```bash
# Example for Sprint 57.24 v1
for target in cost-dashboard sla-dashboard verification admin/tenants tenant-settings; do
  grep -l "Unit.*$target" claudedocs/4-changes/sprint-57-*-audit/AUDIT-REPORT*.md
done
```
If any target is already audit-classified as P0 / structural-rebuild → lift conflicting entries into structural-rebuild scope before drafting cosmetic-retrofit batch.

**Scope**: Add to `.claude/rules/sprint-workflow.md` §Step 2.5 as new Prong 5; ~30 min doc edit. Phase 58+ when next Tier-N retrofit/rebuild batch is drafted.

---

## 🟢 Sprint 57.25 SLA Dashboard Rebuild Carryovers (NEW 2026-05-19)

3 ADs from Sprint 57.25 AD-Mockup-Fidelity-Rebuild-Sla-Dashboard closeout. Frontend rebuild shipped 6 widget groups reusing 7 Sprint 57.24 v2 primitives without API change + 1 NEW feature-scoped LatencyChart (Karpathy §2 inline); SLAMetricsCard Karpathy §3 orphan delete. Class 3rd app ratio 0.88 in-band lower; rich-dashboard 2-pt mean 1.04 in-band middle → sub-class hypothesis NOT confirmed; sub-classification DEFER pending 4th data point.

### 39. AD-SLA-Dashboard-Backend-Extensions-Phase58
Backend follow-on for Sprint 57.25 fixture-driven widgets:
- 24h time-series aggregation endpoint (`GET /api/v1/sla/latency-history?range=24h`) returning per-time-bucket {p50, p95, p99} — drives LatencyChart 24h
- Cross-operation p99 aggregation endpoint (`GET /api/v1/sla/slow-operations?range=24h&limit=N`) — drives TopSlowOpsTable
- Per-service error rate aggregation endpoint (`GET /api/v1/sla/error-rates?range=1h`) — drives ErrorRateByServiceCard
- Dedicated SLO threshold metrics (`tool_success_pct` / `hitl_response_p95_min` / `subagent_depth_max` / `cost_per_run_usd`) — drives SLOStatusCard 4 of 5 fixture rows
- Existing `useSLAReport` SLAReportResponse extension: `latency_p50_ms` + `latency_p95_ms` + `error_budget_pct` fields (currently fixture per D-PRE-2)

Drives Sprint 57.25 BackendGapBanner removal for 3 widgets (LatencyChart 24h / cross-op p99 / per-service error rate) + flips 3 stat cards (p50/p95/error_budget) + 4 of 5 SLO rows from fixture to real. ~10-14 hr backend + ~3-4 hr frontend wire-up. Phase 58+ backend-led; pairs with Sprint 57.26-57.28 backend extensions for cost-dashboard #36.

### 40. AD-LatencyChart-Extraction-Phase58
Extract `LatencyChart` from `frontend/src/features/sla-dashboard/components/` to `frontend/src/components/charts/` as generalizable 3-series multi-line primitive **IF 2nd consumer arises** per Karpathy §2 "extract on 2nd consumer" rule.

Current state (Sprint 57.25): inline feature-scoped (~110 lines); single consumer = SLA dashboard 24h LatencyChart. Sprint 57.26+ may have 2nd consumer if `/admin/tenants` rebuild needs similar multi-series visualization OR Sprint 57.27 `/verification` correction-trace shows latency distribution.

**Extraction trigger criteria**:
- 2 distinct production consumers with comparable 3-series multi-line shape (NOT just any chart need)
- API generalizable beyond hardcoded p50/p95/p99 series → e.g. `<MultiLineChart series={[{key, stroke, width, opacity}]} data />`
- Estimate: ~2 hr extraction + Vitest update

If 4th data point sprint (57.26+) doesn't surface 2nd consumer → DROP this AD entirely (Karpathy §2 rule applied correctly).

### 41. AD-Sprint-Plan-rich-dashboard-sub-class-DEFER — ✅ RESOLVED (Sprint 57.27 — DROPPED)
Sub-classification proposal logged Sprint 57.24 v2 retro Q4 (rich-dashboard ratio 1.19 vs auth-flow 0.59) deferred per Sprint 57.25 3rd data point ratio 0.88. 2-data-point rich-dashboard mean (57.24 v2 + 57.25) = ~1.04 sits in-band middle of [0.85, 1.20] — does NOT justify split.

**Resolution path** (original):
- Sprint 57.27 = 4th data point (admin-tenants list rebuild; rich-dashboard shape — foundation-fidelity Sprint 57.26 was inserted ahead, shifting it +1)
- If 57.27 ratio in band → **DROP** sub-class proposal (3-of-3 rich in band; KEEP 0.60 baseline)
- If 57.27 ratio > 1.20 → reconsider rich sub-class higher (~0.70-0.75); 2-of-3 rich above band
- If 57.27 ratio < 0.85 → drop rich-dashboard pattern entirely; KEEP 0.60 baseline accepts auth-flow + rich mixed

**✅ RESOLVED 2026-05-21 (Sprint 57.27 closeout — DROPPED)**: Sprint 57.27 became the `/overview` full rebuild (user-directed; superseded the planned admin-tenants 57.27 candidate, but `/overview` is itself a rich operator dashboard — 2 charts + 4-stat KPI + 4 cards — so it serves as the 4th rich data point). 57.27 ratio ≈0.95 — **IN BAND**. Rich-subset 57.24=1.19 / 57.25=0.88 / 57.27≈0.95 → 3-pt mean ~1.01 in-band middle → **sub-class proposal DROPPED, no split**; KEEP the single `frontend-mockup-strict-rebuild` 0.60 baseline for the whole class. Matrix row + MHist updated in `.claude/rules/sprint-workflow.md`.

---

## 🟡 Sprint 57.26 Foundation-Fidelity Carryover (NEW 2026-05-21)

1 AD from Sprint 57.26 post-closeout CI investigation. PR #159's first `Frontend E2E` run failed — `visual-regression.spec.ts` 5 `toHaveScreenshot()` baselines (auth-login / cost-dashboard / governance / verification-recent / admin-tenants) mismatched because the foundation-token correction deliberately moved the visuals. Resolved by regenerating baselines via the Sprint 57.14 `playwright-e2e.yml` workflow_dispatch mechanism (baseline commit `f0b24bd2`); CI then green, `state: CLEAN`. The gap is a planning-discipline miss, not a code defect.

### 42. AD-Day0-Prong4-Visual-Baseline-Scope
Sprint 57.26 plan §Risks listed the "22-route blast radius" of changing `html` font-size but scoped it only to the sprint's own route-sweep harness — it missed CI's pre-existing Playwright `visual-regression.spec.ts` screenshot baselines. Day 0 三-prong Prong 4 (test selector verify) checks only **Vitest** specs asserting literal foundation values; it does not cover `tests/e2e/visual/*-snapshots/` PNG baselines, which are a second class of "asserts the visuals" test. Visual-baseline regen is a known pattern (Sprint 57.14 mechanism, used in 57.23 + 57.24) but was not pre-adopted into the 57.26 plan.

**Fix proposal**: extend `.claude/rules/sprint-workflow.md` §Step 2.5 Prong 4 — when a sprint plan touches global CSS / foundation tokens / shell layout / any broad visual change, Day 0 must (a) `Glob tests/e2e/visual/**/*-snapshots/*.png` to confirm baselines exist + assess visual blast radius, and (b) if visuals will move, plan §Risks must pre-list "visual baseline regen via `playwright-e2e.yml` workflow_dispatch" as a known closeout step rather than a post-CI surprise.

**Cross-ref**: AD GHA-PR-create-blocked (line 131 — `playwright-e2e.yml` `gh pr create` step failed for the 3rd time across 57.23 / 57.24 / 57.26; the bot pushes the baseline branch fine but cannot open the PR, so the manual `fetch + ff-merge` is the working path). Effort: ~15 min rule edit; no code change.

---

## 🟢 Sprint 57.27 Overview Rebuild Carryover (NEW 2026-05-21)

2 ADs from Sprint 57.27 `AD-Mockup-Fidelity-Rebuild-Overview` closeout. `/overview` operator dashboard rebuilt 1:1 from `reference/design-mockups/page-overview.jsx` — 9 widgets, OverviewPage 728→~215-line assembly (AP-3 reversal complete), DRIFT-REPORT verdict PARITY. 8 of 9 widgets are fixture-backed (declared via `<BackendGapBanner>`); ActiveLoopsCard targets real data but its endpoint 404s.

### 43. AD-Overview-Backend-Extensions-Phase58
The 9 `/overview` widgets need real backend data. Currently 8 are fixture-backed (HITL Queue / Providers / Incidents / Error Trend / Cost Burn + the 4-stat KPI row), declared honestly via `<BackendGapBanner>`. ActiveLoopsCard targets real data via `useActiveLoops` → `fetchLoops` → `GET /api/v1/loops?status=running` — but that endpoint returns **404 (does not exist)**, so the widget always renders its error state in production (pre-existing; the hook + `loopsService` predate Sprint 57.27). Phase 58 scope: (a) build the `GET /api/v1/loops` list endpoint — closes ActiveLoopsCard live data + folds in D15 (`maxTurns` hardcoded; `Session` ORM enrich = existing `AD-Loop-Session-Enrich-Phase58`); (b) aggregation endpoints for HITL-queue / providers-health / incidents / error-trend / cost-burn / KPI stats. Pairs with cost-dashboard #36 + sla-dashboard #39 backend-extension ADs (same Phase 58+ backend-led batch).

### 44. AD-CardShell-Title-Crossverify-cost-sla
Sprint 57.27 R9 (user decision) changed the shared `CardShell` card-title `text-sm` → `text-[12.5px]` (closes D8 toward mockup `.card-title` 12.5px). `/cost-dashboard` (57.24) + `/sla-dashboard` (57.25) also consume `CardShell` → both shifted toward the mockup (they carried the same D8 drift unnoticed). Pure mockup-fidelity correction, NOT a regression — but a light Playwright pair-verify pass on those 2 pages should confirm the 12.5px title renders right. Fold into the next dashboard-touching sprint, or a small shared-primitive token-audit pass. ~15 min.

---

## 🟢 Sprint 57.28 Foundation-Switch Carryover (NEW 2026-05-22)

Sprint 57.28 `AD-Mockup-Fidelity-Foundation-Switch` switched the production frontend CSS delivery to the verbatim-CSS 4-layer sync protocol (Phase 1 — foundation only; Option B). The 22-route sweep verified 0 catastrophic / 0 structural regression. The Phase-2 per-page re-point epic (the `frontend-mockup-strict-rebuild` candidates #2 / #33-35 etc.) now re-points page markup on a **correct foundation** — CSS colour fidelity comes "for free" per re-point.

### 45. AD-RouteSweep-Object-Mock-Gap

NEW Sprint 57.28 D-DAY3-2. The `route-sweep.mjs` harness's generic `[]` API mock crashes the object-shaped data hooks of `/subagents`, `/memory`, `/verification` (AppErrorBoundary `undefined.length` — identically in before/ + after/ sweeps, so NOT a foundation-switch regression). Extend `route-sweep.mjs` with object-shaped mocks for `/api/v1/subagents` + `/api/v1/memory/recent` + the verification endpoint (mirroring the Sprint 57.26 D-DAY1-1 `cost-summary` / `sla-report` object mocks) so those 3 routes become sweep-assessable. Harness maintenance ~1 hr; fold into a Phase-2 re-point sprint touching those pages.

### 46. AD-Mockup-Fidelity-HexBaseline-Migration

NEW Sprint 57.28. `check-mockup-fidelity.mjs` grep guard baselines `HEX_OKLCH_BASELINE = 18` — 18 hardcoded `bg-[#hex]`/`text-[#hex]` lines in the governance + chat_v2 risk-colour maps (DecisionModal / AuditChainBadge / ApprovalList / ApprovalCard / HITLTurn). Each Phase-2 re-point of those pages should migrate the literals to mockup `--risk-*` tokens and lower `HEX_OKLCH_BASELINE` accordingly. Not a standalone sprint — folds into the governance + chat-v2 re-point work.

---

## Maintenance Notes

- New carryover ADs from each sprint retrospective should be **appended here**, NOT to CLAUDE.md table cells (per §Sprint Closeout policy).
- When a candidate becomes the selected next sprint, leave the entry marked `→ Sprint XX.Y` until that sprint closes; then move to "Closed" section or delete.
- Cross-references: see `memory/MEMORY.md` index + per-sprint memory subfile + retrospective.md for sprint-by-sprint detail.

---

## Modification History

- 2026-05-22: Sprint 57.28 Day 4 closeout — verbatim-CSS foundation switch SHIPPED (22-route sweep 0 catastrophic / 0 structural regression); +2 ADs (#45 `AD-RouteSweep-Object-Mock-Gap` + #46 `AD-Mockup-Fidelity-HexBaseline-Migration`); the Phase-2 per-page re-point epic now runs on a correct verbatim foundation
- 2026-05-21: Sprint 57.27 Day 3 closeout — `/overview` rebuild SHIPPED (DRIFT verdict PARITY); +2 ADs (#43 `AD-Overview-Backend-Extensions-Phase58` + #44 `AD-CardShell-Title-Crossverify-cost-sla`); RESOLVED #41 (rich-dashboard sub-class DROPPED — 57.27 `/overview` 4th `frontend-mockup-strict-rebuild` data point ratio ≈0.95 in-band; rich-subset 3-pt mean ~1.01 → no split, KEEP single 0.60 baseline)
- 2026-05-21: Sprint 57.26 post-closeout CI fix — +1 AD #42 (`AD-Day0-Prong4-Visual-Baseline-Scope`); PR #159's first CI run failed on 5 stale `visual-regression.spec.ts` baselines (foundation-token correction deliberately moved the visuals); baselines regenerated via `playwright-e2e.yml` workflow_dispatch (`f0b24bd2`), CI re-run green / `state: CLEAN`
- 2026-05-21: Sprint 57.26 Day 3 closeout — foundation-fidelity sprint (global token correction across 22 routes; user-directed insertion, NOT drawn from this candidate list) shipped with 0 regression; 0 new carryover ADs at closeout (later +1 AD #42 post-closeout CI fix — see entry above); 3 FOUNDATION-APPLIED routes folded into the existing rebuild epic per DRIFT-REPORT §5; #33/#34/#35 candidate sprint numbers shifted +1 (→ 57.27/57.28/57.29) + #41 4th-data-point sprint → 57.27 (foundation-fidelity took the 57.26 slot)
- 2026-05-19: Sprint 57.25 Day 3 closeout — close #32 (sla-dashboard rebuild SHIPPED) + +3 ADs (#39-#41) SLA Dashboard Rebuild carryovers (backend extensions + LatencyChart extraction trigger + rich-dashboard sub-class DEFER decision)
- 2026-05-19: Sprint 57.24 v2 Day 3 closeout — +7 ADs (#32-#38) Cost Dashboard Rebuild carryovers (4 page rebuilds 57.25-57.28 + 1 backend extension + 1 Playwright MCP recovery + 1 plan-draft Prong 5 discipline addition)
- 2026-05-19: Sprint 57.24 Day 0 — +1 AD #31 Memory STRUCTURAL Rebuild carryover (Q2 decision: defer from 57.24 cosmetic retrofit to dedicated Phase 58+ sprint)
- 2026-05-18: Sprint 57.23 Day 4 closeout — +8 ADs (#23-#30) Auth Page Rebuild Round 2 carryovers (Phase 58+ IAM Block B/C + Playwright MCP followup + i18n lint)
- 2026-05-18: Initial creation (REFACTOR-001 Step 3; extracted from CLAUDE.md V2 Refactor Status table 20-bullet `Next Phase 候選` row per §Sprint Closeout policy)
