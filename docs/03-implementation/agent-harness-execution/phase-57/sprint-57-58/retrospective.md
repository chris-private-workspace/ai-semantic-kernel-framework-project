# Sprint 57.58 — Retrospective

**Sprint**: 57.58 — RateLimits RuntimeEnforcement D3 Full (Phase 58.x portfolio 1/5 deeper extensions)
**Closed**: 2026-05-28
**Branch**: `feature/sprint-57-58-rate-limits-runtime-enforcement`
**Commits**: `f20ef896` (Day 0) + `5e6fc72f` (Day 1) + Day 2 closeout (pending)
**Class**: `mixed-multidomain-bundle` 0.65 (4th data point) / agent_factor `mixed-multidomain-bundle-mechanical` 0.65 (tier-3 **1st validation**)
**Agent-delegated**: yes (2 sequential code-implementer agents; 22nd + 23rd consecutive chain)

---

## Q1 — What went well

1. **Day 0 三-Prong caught a CRITICAL Potemkin Feature before any code**: `RateLimit` ORM (`api_keys.py:141`, table `rate_limits`) has existed since Phase 49 V2 baseline (per `09-db-schema-design.md L902-919`) but is NEVER queried/written in production. Grep confirmed 0 usage. This is exactly the AP-4 anti-pattern V1 was full of. Surfacing it at Day 0 (not Day 1) let the user make a clean architectural decision (Path B) instead of discovering mid-implementation.
2. **4 RED path drifts all caught Day 0** (mechanical s/old/new/): `agent_harness/middleware/` → `platform_layer/middleware/`; `core/cache/` → `platform_layer/tenant/rate_limit_counter.py`; `agent_harness/tool/` → `tools/` (with s); `backend/src/main.py` → `api/main.py`. Zero mid-Day-1 path surprises.
3. **2 sequential agents shipped cleanly**: backend (`rl-backend` ~18 min, 3 tracks) + frontend (`rl-frontend` ~7 min) — pytest +13 exact target + Vitest +12, 0 regressions across both, mypy 0 + tsc 0 + 9/9 V2 lints.
4. **Agents self-corrected 2 design constraints honestly** rather than faking: D-DAY1-1 (stored shape `{label,value}` not `{resource,window,limit}` → `parse_rate_limit_item()` normalizer) + D-DAY1-2 (Lua EVAL unsupported by fakeredis → MULTI/EXEC pipeline reserve-then-rollback matching `QuotaEnforcer` precedent). Both deviations preserve the spec's atomicity + sliding-window guarantees.
5. **LLM-neutrality preserved at the Cat 2 seam**: `RateLimitGate` Protocol (in `agent_harness/tools/`) keeps Cat 2 free of platform/Redis imports; `RedisToolRateLimitGate` (in `platform_layer/`) is the concrete adapter. 9/9 V2 lints green incl. SDK-leak check.
6. **mockup-fidelity DUAL CLEAN 22/22 PARITY preserved 14 consecutive sprints 57.45-57.58** (frontend reused existing `.bar-track` primitive + `var(--success/--warning/--danger)` tokens; 0 new oklch).

## Q2 — What didn't go well + calibration

1. **Day 0 ran ~2× the §6 estimate** (~1.6 hr actual vs ~0.8 hr planned) due to the CRITICAL Potemkin discovery + plan v1→v2 revision cycle. This was worthwhile time (prevented a wrong-architecture Day 1) but it means Day-0 estimates should budget more for first-of-kind feature sprints touching dormant schema.
2. **Plan §4.1 assumed the wrong stored shape** (`{resource,window,limit}` vs real `{label,value}`). Prong 2 content-verify (D-DAY0-H) grep'd for `rate_limits` text and matched, but a regex match confirms *presence*, not *nested dict shape* — a known Prong-2 limitation. The agent caught it Day 1; ideally Day 0 Prong 2 would read the actual `RateLimitItem` Pydantic model body, not just grep the key.
3. **Plan said HEX_OKLCH baseline 47; real baseline is 48** (bumped Sprint 57.50 hotfix). Stale figure in plan + my memory pointer. Corrected (D-DAY1-4). No functional impact (0 new oklch added either way).

### Calibration

- **Bottom-up** ~15 hr → **class-calibrated** ~9.75 hr (mult 0.65 `mixed-multidomain-bundle`) → **agent-adjusted** ~6.3 hr (agent_factor 0.65 `mixed-multidomain-bundle-mechanical`)
- **Actual** ≈ **3.1 hr** (Day 0 ~1.6 + Day 1 ~0.83 + Day 2 ~0.67)
- **ratio actual/bottom-up** = 0.21 (bottom-up ~4.9× generous)
- **ratio actual/class-committed** = 0.32 (confound: agent speedup; resolved at sub-class layer per discipline → KEEP `mixed-multidomain-bundle` 0.65)
- **ratio actual/agent-adjusted** = **~0.49 BELOW [0.85, 1.20] band by 0.36** = `mixed-multidomain-bundle-mechanical` 0.65 tier-3 **1st validation**
- **Decision**: per single-data-point caution rule → **KEEP `mixed-multidomain-bundle-mechanical` 0.65**; flag Sprint 57.59+ for 2nd validation. If 2nd also < 0.7 → tighten to 0.45; if > 1.20 → rollback to 1.0 (drop modifier).
- Root cause for below-band: high mechanical pattern reuse (quota.py counter DI + Sprint 57.57 GET/frontend-hook patterns + TenantContextMiddleware template) → agents internalized ~5× speedup vs the 0.65 sub-class's ~1.5× assumption. Same pattern as the entire Sprint 57.40-57.57 agent-delegated wave.

## Q3 — What we learned (generalizable)

1. **Prong 2 content-verify should read Pydantic/dataclass bodies, not just grep keys** when the plan asserts a specific nested field shape. Grep confirms a symbol exists; it does NOT confirm the dict shape. Candidate codification: extend `sprint-workflow.md §Step 2.5 Prong 2` Drift Class table with a "Claimed-but-wrong-nested-shape" row — when plan asserts `X["key"] = {a, b, c}`, Day 0 must read the model/serializer body, not grep the key string. (NEW carryover `AD-Day0-Prong2-Nested-Shape-Read`.)
2. **Dormant ORM tables are latent Potemkin Features**. The repo carries a fully-defined `rate_limits` table never wired since Phase 49. When a sprint's domain overlaps a dormant table, Day 0 must grep the ORM class for usage (instantiation/query/write) to decide activate-vs-bypass upfront. (Already partially covered by Prong 2; this is a concrete instance.)
3. **The LLM-neutral Protocol + platform adapter split is the reusable seam** for any future Cat-2-touches-platform integration (rate limits, quotas live consume, cost metering). Codify as a pattern: define a `*Gate`/`*Hook` Protocol in `agent_harness/`, inject optionally, supply concrete `Redis*` adapter from `platform_layer/`.

## Q4 — Audit Debt deferred

| ID | Status | Target |
|----|--------|--------|
| `AD-RateLimits-Potemkin-Migration-Phase58` | NEW (Day 0 D-DAY0-CRITICAL) | Sprint 57.59+ — activate dormant `RateLimit` ORM OR formally delete it; close AP-4. ~5-8 hr |
| `AD-RateLimits-SyntaxValidation-Phase58` | CARRYOVER | Sprint 57.59+ — PUT-time validation of `{label,value}` → structured (~2 hr) |
| `AD-RateLimits-LiveUsageTracking-Phase58` | PARTIAL-CLOSE | Live usage exposure DONE this sprint; alerting threshold remains |
| `AD-RateLimits-Alerting-Phase58` | CARRYOVER | SSE emit when 80% threshold crossed (~2-3 hr) |
| `AD-RateLimits-DedicatedTable-Phase58` | CONDITIONAL | Folds into `AD-RateLimits-Potemkin-Migration-Phase58` (same table) |
| `AD-AgentFactor-Tier-3-MixedBundle-Mechanical-Validation-Sprint-57.59` | NEW | 2nd validation of `mixed-multidomain-bundle-mechanical` 0.65 |
| `AD-Day0-Prong2-Nested-Shape-Read` | NEW (Q3 Lesson 1) | Codify into `sprint-workflow.md §Step 2.5 Prong 2` when 2-3 data points accumulate |
| `AD-medium-frontend-Baseline-Recalibration` | CONTINUES | 8th data point pending |
| `AD-MediumBackend-AICadence-Recalibration` | CONTINUES | Phase 58+ |
| `AD-Test-Cleanup-Pattern-Shared-Helper` | CONTINUES | Phase 58.x |

## Q5 — Next steps (carryover candidates only; rolling planning §6 — no specific Sprint 57.59 tasks pre-written)

Candidate directions for Sprint 57.59 (user picks):
- **`AD-RateLimits-Potemkin-Migration-Phase58`** (close the AP-4 surfaced this sprint — natural follow-on)
- RateLimits Alerting (SSE 80% threshold) — pairs with the Live usage Card shipped this sprint
- RateLimits SyntaxValidation (PUT-time `{label,value}` structured parse)
- Quotas LiveUsageTracking (parallel to this sprint's RateLimits live tracking; shared counter pattern)
- Other Phase 58+ portfolio items (FeatureFlags per-flag audit / Identity persistence / Test-Cleanup shared helper)

## Q6 — Solo-dev policy validation

- `required_approving_review_count = 0` honored; PR opened for audit trail + CI gate
- `enforce_admins = true` active (no direct main push)
- 5 required CI checks must pass before merge
- No `--admin` bypass, no `--no-verify`, no force push

## Q7 — N/A SKIP

Feature ship, NOT a spike sprint → no design note extract required (8th consecutive feature ship 57.51-57.58 where Q7 is N/A; spike-extract design notes apply only to new-domain exploration sprints per `sprint-workflow.md §Step 5.5`).

---

## Summary metrics

| Metric | Value |
|--------|-------|
| Files | 24 changed (9 NEW + 15 EDIT incl. docs) — code: 14 backend + 8 frontend |
| pytest | 1806 → 1819 (+13 exact target) |
| Vitest | 663 → 675 (+12) |
| mypy --strict / tsc | 0 / 0 |
| 9 V2 lints | 9/9 green |
| new oklch / SDK leak | 0 / 0 |
| mockup-fidelity | DUAL CLEAN 22/22 PARITY 14 consec 57.45-57.58 |
| Calibration | `mixed-multidomain-bundle-mechanical` 0.65 tier-3 1st validation ratio ~0.49 BELOW band → KEEP |
| Day 0 drift | 9 findings (4 RED + 4 NOTABLE + 1 CRITICAL Potemkin) |
| Day 1 drift | 4 findings (D-DAY1-1 shape / D-DAY1-2 Lua→pipeline / D-DAY1-3 contracts site / D-DAY1-4 baseline 48) |
| Phase 58.x portfolio | 1/5 RateLimits deeper extensions shipped (RuntimeEnforcement) |
