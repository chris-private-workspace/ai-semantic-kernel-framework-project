/**
 * File: frontend/src/features/cost-dashboard/components/CategoryBarsCard.tsx
 * Purpose: 6-bar spend-by-category breakdown widget per mockup page-admin.jsx:230-252.
 * Category: Frontend / cost-dashboard / components
 * Scope: Phase 57 / Sprint 57.24 Day 2 US-C1
 *
 * Description:
 *   Renders mockup "Spend by category" card: 6 rows (Inference input/output
 *   / Thinking tokens / Tool runs / Embeddings / Sandbox compute) × dot +
 *   name + $value + BarTrack.
 *
 *   Day 2 R3 mitigation: mockup's 6 flat categories DO NOT 1:1 map to backend
 *   CostSummaryResponse.by_type 2-level dict (cost_type → sub_type → slice).
 *   This sprint ships fully-fixture demo per CLAUDE.md §Mockup-Fidelity + AP-2
 *   honesty banner. Category taxonomy harmonization tracked Phase 58+
 *   AD-Cost-Backend-Category-Taxonomy.
 *
 *   The raw 2-level backend breakdown lives on the existing CostBreakdownTable
 *   component below this card (CostOverview integration) — kept as detail row
 *   so reviewers can verify backend data alongside the mockup-fidelity summary.
 *
 * Created: 2026-05-19 (Sprint 57.24 Day 2 US-C1)
 *
 * Modification History:
 *   - 2026-05-19: Initial creation (Sprint 57.24 Day 2 US-C1)
 */

import type { FC } from "react";
import { useTranslation } from "react-i18next";

import { BarTrack } from "../../../components/charts/BarTrack";
import { BackendGapBanner } from "../../../components/ui/BackendGapBanner";
import { CardShell } from "../../../components/ui/CardShell";
import { CATEGORY_BREAKDOWN_FIXTURE } from "../__fixtures__/categoryBreakdown";

export const CategoryBarsCard: FC = () => {
  const { t } = useTranslation("common");
  return (
    <CardShell
      title={t("cost.category.title")}
      subtitle={t("cost.category.subtitle")}
    >
      <div className="flex flex-col gap-3" data-testid="category-bars-card">
        {CATEGORY_BREAKDOWN_FIXTURE.map((row) => (
          <div key={row.key}>
            <div className="mb-1 flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <span
                  aria-hidden
                  className={`inline-block h-2 w-2 rounded-sm ${row.toneClass}`}
                />
                <span className="text-xs">{t(`cost.category.${row.key}`)}</span>
              </span>
              <span className="font-mono text-[11.5px] tabular-nums">
                ${row.value.toLocaleString()}
              </span>
            </div>
            <BarTrack pct={row.pct} tone={row.toneColor} />
          </div>
        ))}
      </div>
      <BackendGapBanner reason={t("cost.banner.categoryTaxonomy")} />
    </CardShell>
  );
};
