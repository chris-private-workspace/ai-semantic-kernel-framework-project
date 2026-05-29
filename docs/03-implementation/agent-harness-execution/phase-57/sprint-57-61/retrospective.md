# Sprint 57.61 — Retrospective

**Sprint**: 57.61 — RateLimits SyntaxValidation (close `AD-RateLimits-SyntaxValidation-Phase58`)
**Closed**: 2026-05-29
**Class**: `medium-backend` 0.80 / agent-delegated yes (single agent `rl-syntax-validation`, 27th consecutive code-implementer) / agent-factor `mechanical-greenfield-design-decisions` 0.65 (1st backend-only application)
**Commits**: Day 0 `6bf23e63` · Day 1 `093a161d` · Day 2 (closeout) pending

---

## Q1 — What went well

- **The `"50 concurrent"` critical edge case was caught at Day 0, not Day 1**: Prong 2 content grep on `DEFAULT_RATE_LIMITS` (`tenants.py:1355-1359`) confirmed the SSE row carries the display-only `"50 concurrent"` value the runtime parsers intentionally can't enforce. A naive "reject everything `parse_config_item` returns None for" validator would have rejected the verbatim load-defaults→edit→save round-trip. Day 0 D-DAY0-F surfaced this BEFORE code → the predicate was designed with a separate `_CONCURRENCY_RE` accept branch + an explicit defaults-round-trip acceptance test (the negative-of-the-negative case). No mid-Day-1 surprise.
- **Shared-model placement constraint confirmed GREEN before any code (D-DAY0-E)**: `RateLimitItem` (`tenants.py:1341`) is shared by GET (`RateLimitListResponse`) AND PUT (`RateLimitsUpsertRequest`) AND a 3rd model at L1391. Day 0 Prong 2 proved the sharing → the `field_validator("items")` went on the **request model only** (not the shared `RateLimitItem`, which would also reject the GET-side `DEFAULT_RATE_LIMITS` projection). The single most important placement decision, verified at Day 0.
- **No 4th rate-regex copy**: the predicate reuses the store's existing `_VALUE_RE` (L86) + `_WINDOW_ALIASES` (L75); the only NEW pattern is `_CONCURRENCY_RE`. The 3-parser-copy smell (R3) was held flat — the US-2 consistency guard now locks store⟺counter validity so a future window-alias divergence fails a test, not a tenant's enforcement silently.
- **Surgical, 0 regressions**: 2 source edits (predicate + validator) + 39 NEW tests by a single agent; pytest 1848 → 1887 (+39), mypy `src/` 0/317, 9/9 V2 lints, black/isort/flake8 clean. All edge cases behaved as planned (`-5 / min` + `abc / min` → shape-reject 422; `0 / min` → positive-number reason; `50 / week` → unsupported-window reason). 0 existing tests needed conversion (validation is purely additive on the write path).
- **D-DAY0-J micro-simplification**: `field_validator` was already imported at `tenants.py:85` (Sprint 57.54/57.56 added it for other models) → only the predicate import was new. Day 0 grep caught it; plan §4.2 import line dropped to one.

## Q2 — What didn't go well

- **Agent environment Docker Postgres was down** → the 16 US-1 integration tests couldn't run in-agent (the 23 US-2 unit tests ran green, since they're pure-function over the parsers). The agent correctly reported the blocker rather than faking a pass. The parent resolved it by starting `docker-compose.dev.yml` (the `dev.py start docker` shortcut reported "no configuration file" — the compose file is `docker-compose.dev.yml`, not the default name) → Postgres Healthy → full 1887 suite ran. **Lesson**: an agent-delegated backend sprint with integration tests should state the Postgres/Redis prerequisite in the agent prompt, OR the parent should confirm the dev stack is up before delegating (so the agent runs the full suite itself).
- **Calibration: the 1st backend-only `-design-decisions` application landed BELOW band** (R6 materialized — see Q4). Not a process failure, but the tier-4 `-design-decisions` 0.65 was calibrated on backend+frontend component-pairs (57.56/57.57); a backend-only validator sprint runs faster. Single data point → KEEP + flag (see Q4).

## Q3 — What we learned (generalizable)

1. **Validator placement on a request-only model when the item type is shared**: when a Pydantic item model is reused across GET response + PUT request, a strict write-time validator must go on the **request envelope** (`field_validator("items")` / `model_validator`), never on the shared item — else it also validates (and can reject) the read-side projection of server-defined defaults. Reusable for any future "validate-on-write, lenient-on-read" admin endpoint over a shared item shape.
2. **A "recognized shape" predicate is broader than the enforcement parser**: the admin write path legitimately carries non-enforceable display values (`"50 concurrent"`). The PUT validator's job is "is this a recognized value the admin meant to set", not "can the runtime enforce it" — those are two different questions. Conflating them rejects valid display rows. The accept/reject asymmetry (validator accepts concurrency; runtime parsers skip it) is intentional and must be encoded as a test (US-2), not left implicit.
3. **`mechanical-greenfield-design-decisions` 0.65 is backend+frontend-pair-shaped**; a backend-only application of the same sub-class runs faster (see Q4 counterfactual) — the frontend-UX-design portion the 0.65 bakes in isn't present, and a backend value-shape predicate + 422 envelope behaves closer to `-port-style` 0.45.

## Q4 — Calibration

**Bottom-up ~5.25 hr → class-calibrated ~4.2 hr (`medium-backend` 0.80) → agent-adjusted ~2.7 hr (`agent_factor` 0.65 `mechanical-greenfield-design-decisions`).**

Actual ≈ **2.0 hr** (Day 0 plan+checklist+三-Prong 10 checks+drift catalog+branch+commit ~45 min + Day 1 agent wall-clock ~20 min for predicate+validator+39 tests + parent Day 1 Docker-start + full validation sweep + review ~25 min + Day 2 closeout ~30 min).

- **ratio actual/agent-adjusted ≈ 2.0 / 2.7 ≈ 0.74 — BELOW band [0.85, 1.20] by 0.11**
- ratio actual/class-committed ≈ 2.0 / 4.2 ≈ **0.48** (BELOW band — confound: agent speedup; resolved at the agent_factor sub-class layer per discipline → **KEEP `medium-backend` 0.80**)
- ratio actual/bottom-up ≈ 2.0 / 5.25 ≈ 0.38 (bottom-up ~2.6× generous — consistent with agent-delegated work)

**`medium-backend` 0.80 — 12th data point**: actual/class-committed ~0.48; last-3 (57.57≈0.72 + 57.60≈0.33 + 57.61≈0.48) — 2/3 < 0.7 but NOT 3-consecutive (57.57 ≥ 0.7 breaks the run) → lower-trigger NOT met; confound resolved at sub-class layer → **KEEP 0.80** per `When to adjust` 3-sprint window rule. `AD-MediumBackend-AICadence-Recalibration` continues Phase 58+.

**`mechanical-greenfield-design-decisions` 0.65 — 3rd validation, 1st BACKEND-ONLY application**: ratio actual/agent-adjusted ≈ **0.74 BELOW band by 0.11**. The 2 prior validations were IN band (57.56=1.02 + 57.57=1.15) — both backend+frontend pairs. This is the 1st single-domain backend-only application and it lands BELOW. Per the rollback rule (need **2 consecutive same-direction OOB** to fire structural action), this is a single BELOW-band point against 2 IN-band points → **KEEP 0.65, single-data-point caution**.

**R6 hypothesis materialized (the plan flagged it)**: backend-only validator work — value-shape predicate + 422 error envelope + accept/reject asymmetry — runs faster than the backend+frontend component-pair the 0.65 was calibrated on (57.56/57.57). The "design decisions" here genuinely exist (the predicate's three-class taxonomy + the concurrency-accept asymmetry is NOT a port of `parse_config_item`), but absent the frontend-UX-design portion, the wall-clock behaves closer to `-port-style`.

**Counterfactual check**: had this been classified `mechanical-greenfield-port-style` 0.45 → agent-adjusted = 5.25 × 0.80 × 0.45 ≈ 1.89 hr → ratio 2.0/1.89 ≈ **1.06 IN BAND middle**. So `-port-style` 0.45 would have fit this backend-only sprint better. This is the inverse of the 57.60 counterfactual (where `-port-style` 0.45 → 0.73 below band, so `-pattern-reuse-heavy` 0.30 fit better). The sub-class boundary is shape-sensitive.

**NEW carryover** `AD-AgentFactor-DesignDecisions-BackendOnly-Variant-Watch`: if the NEXT backend-only `-design-decisions` sprint ALSO lands BELOW band (2nd consecutive backend-only OOB-below) → propose either (a) a `-design-decisions-backend-only` ~0.45 variant, or (b) reclassify backend-only validator/schema work as `-port-style` 0.45. Defer until a 2nd backend-only data point (single point insufficient per discipline; the band rule needs 2 consecutive).

## Q5 — Next steps (rolling — carryover candidates only, no specific future-sprint tasks)

- `AD-RateLimits-Alerting-Phase58` — SSE 80%-threshold usage alerts; pairs with the activated `rate_limits` usage table; SSE infra ~80% from prior sprints; ~3-4 hr
- `AD-RateLimits-DuplicateResource-Validation` (NEW — R7 deferred) — PUT-time 422 on two payload items resolving to the same (resource_type, window_type); currently silent last-wins dedup; ~1 hr
- `AD-RateLimits-SyntaxValidation-ClientSide-Polish` (NEW — R5 deferred) — mirror the value-shape predicate in TS for inline client-side validation + per-item field highlighting; risks a 5th parser copy (weigh carefully); ~2 hr
- `AD-RateLimits-Parser-Extract-Shared-Predicate` (NEW — R3 follow-on) — extract the window-alias table to ONE source the counter + store reference (migration stays dep-light inline); removes the 2-live-copy smell the US-2 guard currently watches; ~2-3 hr
- `AD-AgentFactor-DesignDecisions-BackendOnly-Variant-Watch` (NEW — Q4) — 2nd backend-only `-design-decisions` data point needed before any sub-class refinement
- `AD-AgentFactor-Tier-3-MixedBundle-Mechanical-Tighten-0.45-Validation-Sprint-57.62` (DEFERS — 57.61 was single-domain, not a multi-track bundle) — awaits the next genuine `mixed-multidomain-bundle` sprint
- `AD-AgentPrompt-CrossPlatform-Mypy-Warning` (CONTINUES — 57.59 lesson; this sprint did NOT touch Redis/asyncpg stubs so it didn't recur) · `AD-Mypy-WholeDir-Conftest-Collision` (CONTINUES — pre-existing since 57.53; CI runs `mypy src/` unaffected)
- **NEW process lesson** `AD-AgentDelegate-DevStack-Precheck` — agent-delegated backend sprints with integration tests should confirm the Postgres/Redis dev stack is up (or state the prerequisite in the agent prompt) so the agent runs the full suite itself rather than the parent absorbing the Docker-start step

## Q6 — Phase 58.x RateLimits arc completeness (sprint-specific topic)

The RateLimits write path is now **fail-loud at the boundary**: a malformed rate-limit value returns 422 with a per-item reason instead of a silent drop on the next GET. Combined with the Phase 58.x arc:

- **57.57** WRITE-side ship — PUT endpoint + composite-replace (silent-drop gap present)
- **57.58** RuntimeEnforcement — middleware + Cat 2 gate + Redis counter
- **57.59** Potemkin Migration — two-table split (config + usage; AP-4 closed)
- **57.60** MetaData Cleanup — config single-source, 0 transitional fallback
- **57.61** SyntaxValidation (this) — PUT-time 422 closes the silent-drop gap

The remaining RateLimits deeper extensions (Alerting / DuplicateResource / ClientSide-Polish / Parser-Extract) are feature additions and code-hygiene, not architectural debt — the storage layer (57.59-60) + write validation (57.61) are clean. The 3-live-parser-copy smell is the one open hygiene item, now watched by the US-2 consistency guard (a test, not a silent risk).

## Q7 — Design Note Extract (spike sprint only) — **N/A SKIP**

Sprint 57.61 is a feature-ship sprint (PUT-time validation + parser-consistency guard) on an established subsystem, NOT a spike into a new domain. No design note required (10th consecutive Q7 N/A SKIP across the RateLimits + Tenant-settings ship/refactor sprints).
