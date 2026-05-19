# Sprint 57.25 — DRIFT-REPORT (SLA Dashboard Rebuild)

**Sprint**: 57.25 (AD-Mockup-Fidelity-Rebuild-Sla-Dashboard)
**Class**: `frontend-mockup-strict-rebuild` 0.60 (3rd application)
**Mockup ref**: `reference/design-mockups/page-admin.jsx:31-199` (SlaPage + LatencyChart helper)
**Production ref**: `frontend/src/features/sla-dashboard/components/SLAOverview.tsx` (Sprint 57.1 + 57.9 + 57.13 + 57.16 evolved baseline)
**Audit lineage**: Sprint 57.22 AUDIT-REPORT-COMPREHENSIVE.md Unit 9 (P0 full rebuild; same FUNCTIONAL pattern as Unit 8 cost-dashboard)

---

## Initial Drift Inventory (Day 0)

### 6-Widget-Group Coverage Matrix

| # | Mockup widget group | Mockup ref line | Production state | Drift severity | Sprint 57.25 work | Final verdict (Day 3 close) |
|---|---------------------|-----------------|------------------|----------------|-------------------|------------------------------|
| 1 | page-head (title + sub + route-pill + 4-button time-range tabs + Refresh + Export) | `:33-52` | ❌ Missing (only AppShellV2 chrome title + plaintext paragraph) | STRUCTURAL | US-B1 PageHead + TimeRangeTabs + Refresh + Export stubs | TBD |
| 2 | 4-stat sparkline grid (p50 / p95 / p99 latency + Error budget) | `:54-59` | ❌ Missing (production = 6-card MetricsCard layout with different field semantic) | STRUCTURAL | US-B2 4 × `<StatCard>` + `<Spark>` reuse | TBD |
| 3 | 24h LatencyChart 3-series SVG (p50 / p95 / p99 over 48 time points) | `:61-70 + :157-198` | ❌ Missing (no chart at all) | STRUCTURAL | US-B3 NEW `<LatencyChart>` feature-scoped (Karpathy §2 inline) | TBD |
| 4 | 5-row SLO status card (Loop p95 / Tool success / HITL response / Subagent depth / Cost per run) | `:72-99` | ❌ Missing (production has flat 6-card MetricsCard) | STRUCTURAL | US-C1 NEW `<SLOStatusCard>` + `<BarTrack>` reuse | TBD |
| 5 | Top slow operations table (6-row × Operation + Kind Badge + p50/p95/p99/Calls) | `:104-129` | ❌ Missing | STRUCTURAL + backend gap | US-C2 NEW `<TopSlowOpsTable>` + fixture + AP-2 banner | TBD |
| 6 | Error rate by service card (6-row × service + rate + `<BarTrack>`) | `:131-152` | ❌ Missing | STRUCTURAL + backend gap | US-C3 NEW `<ErrorRateByServiceCard>` + fixture + AP-2 banner | TBD |
| — | violations Badge + MonthPicker (production-only) | (not in mockup) | ✅ existing | reverse-drift | Preserve MonthPicker as auxiliary + sibling note (Q1 user alignment); drop violations Badge OR move to subtle location | TBD |
| — | 6 × SLAMetricsCard flat layout (production-only) | (not in mockup) | ✅ existing | reverse-drift | Karpathy §3 orphan delete (Q3 user alignment) | TBD |

---

## Field Semantic Mismatch (D-PRE-2)

`useSLAReport` backend response shape vs mockup field expectations:

| Mockup field expectation | Backend `useSLAReport` response | Mapping |
|--------------------------|----------------------------------|---------|
| `p50 latency` | ❌ NOT in response | Fixture in `__fixtures__/statSparklines.ts` + AP-2 banner |
| `p95 latency` | ❌ NOT in response | Fixture |
| `p99 latency` | ✅ `api_p99_ms` | Real backend → stat card #3 |
| `Error budget` | ❌ NOT in response | Fixture + AP-2 banner |
| `LatencyChart 24h time-series (p50 / p95 / p99 × 48 points)` | ❌ NOT in response (only month-level aggregate) | Fixture in `__fixtures__/latencyChart24h.ts` + AP-2 banner |
| `SLO Loop p95 < 2s` | ✅ `loop_simple_p95_ms` (if Sprint 57.13+ has p95 split) OR fixture | TBD Day 2.1 verify |
| `SLO Tool success` / `SLO HITL response` / `SLO Subagent depth` / `SLO Cost per run` | ❌ NOT in response | Fixture (4 of 5 SLO rows fixture) |
| `Top slow ops × p50/p95/p99/Calls` | ❌ NOT in response | Fixture + AP-2 banner |
| `Error rate by service × rate` | ❌ NOT in response | Fixture + AP-2 banner |

**3 expected BackendGapBanner instances** (LatencyChart 24h history / cross-operation p99 / per-service error rate); Plan §Risks R2 mitigation.

---

## Mockup Reference Resolution

| Mockup section | Lines | Function/component | Sprint 57.25 mapping |
|----------------|-------|--------------------|-----------------------|
| `AreaChart` helper | `:4-29` | Single-series AreaChart (NOT used this sprint; Sprint 57.24 v2 `<AreaChart>` is for SVG single-series stack — mockup's LatencyChart is multi-series) | N/A (LatencyChart inline) |
| `SlaPage` body | `:32-156` | Full SLA dashboard layout | SLAOverview.tsx rewrite |
| `LatencyChart` helper | `:157-198` | 3-series multi-line SVG | NEW `LatencyChart.tsx` feature-scoped |

---

## Tools/References Used Day 0

- Sprint 57.22 AUDIT-REPORT-COMPREHENSIVE.md Unit 9 (Prong 5 audit cross-ref)
- next-phase-candidates.md #32 (rebuild quartet 57.25-57.28 anchor)
- Sprint 57.24 v2 plan + checklist + retrospective (template + class baseline data point reference)
- Sprint 57.20 plan (Option W frontend-leads + backend-follows philosophy carryover)
- CLAUDE.md §Frontend Mockup-Fidelity Hard Constraint (Mockup ≠ retrofit; rebuild only)
- `.claude/rules/sprint-workflow.md §Step 2.5` (Day-0 verify discipline; Prong 5 audit cross-ref)
- `.claude/rules/sprint-workflow.md §Scope-class multiplier matrix` (frontend-mockup-strict-rebuild 0.60 class history)

---

## Day 1 — pending (US-B1 + US-B2 + US-B3 verdicts)

## Day 2 — pending (US-C1 + US-C2 + US-C3 verdicts)

## Day 3 — final verdict (target: PARITY code-level audit per Q4 user alignment on Playwright MCP 4th-consecutive blocker fallback)
