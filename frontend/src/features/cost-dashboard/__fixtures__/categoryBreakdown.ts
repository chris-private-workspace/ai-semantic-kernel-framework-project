/**
 * File: frontend/src/features/cost-dashboard/__fixtures__/categoryBreakdown.ts
 * Purpose: 6-category Spend breakdown fixture for /cost-dashboard CategoryBarsCard (Sprint 57.24 US-C1).
 * Category: Frontend / cost-dashboard / fixtures
 * Scope: Phase 57 / Sprint 57.24 Day 2 US-C1
 *
 * Description:
 *   Mirrors mockup reference/design-mockups/page-admin.jsx:232-238 inline
 *   array. Mockup uses 6 flat categories (Inference input/output / Thinking
 *   tokens / Tool runs / Embeddings / Sandbox compute) that DO NOT 1:1 map
 *   to backend CostSummaryResponse.by_type 2-level dict shape (cost_type
 *   → sub_type → AggregatedSlice). Category taxonomy harmonization tracked
 *   in Phase 58+ AD-Cost-Backend-Category-Taxonomy (logged by Sprint 57.24
 *   Day 2 D-Day2-1 drift finding).
 *
 *   `key` is the i18n translation key suffix under cost.category.*; `tone`
 *   is the Tailwind text-color class name (token wired Sprint 57.18).
 *
 * Created: 2026-05-19 (Sprint 57.24 Day 2 US-C1)
 *
 * Modification History:
 *   - 2026-05-19: Initial creation (Sprint 57.24 Day 2 US-C1)
 */

export interface CategoryBreakdownRow {
  key: string; // i18n suffix under cost.category.*
  value: number; // dollars
  pct: number; // 0-100
  toneColor: string; // raw CSS for Spark / BarTrack tone
  toneClass: string; // Tailwind class for label dot
}

export const CATEGORY_BREAKDOWN_FIXTURE: CategoryBreakdownRow[] = [
  { key: "inferenceInput", value: 1240, pct: 44, toneColor: "hsl(var(--thinking))", toneClass: "bg-thinking" },
  { key: "inferenceOutput", value: 780, pct: 27, toneColor: "hsl(var(--primary))", toneClass: "bg-primary" },
  { key: "thinkingTokens", value: 412, pct: 14, toneColor: "hsl(var(--info))", toneClass: "bg-info" },
  { key: "toolRuns", value: 280, pct: 10, toneColor: "hsl(var(--tool))", toneClass: "bg-tool" },
  { key: "embeddings", value: 90, pct: 3, toneColor: "hsl(var(--memory))", toneClass: "bg-memory" },
  { key: "sandboxCompute", value: 45, pct: 2, toneColor: "hsl(var(--warning))", toneClass: "bg-warning" },
];
