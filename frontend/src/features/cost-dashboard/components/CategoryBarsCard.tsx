/**
 * File: frontend/src/features/cost-dashboard/components/CategoryBarsCard.tsx
 * Purpose: 6-bar spend-by-category breakdown — verbatim re-point to mockup page-admin.jsx:230-252.
 * Category: Frontend / cost-dashboard / components
 * Scope: Phase 57 / Sprint 57.24 Day 2 US-C1 → 57.31 Day 1 (verbatim re-point)
 *
 * Description:
 *   Renders mockup "Spend by category" card: 6 rows (Inference input/output
 *   / Thinking tokens / Tool runs / Embeddings / Sandbox compute) × dot +
 *   name + $value + .bar-track.
 *
 *   Sprint 57.31 Day 1 verbatim re-point: consume mockup-ui <Card> + mockup
 *   verbatim CSS classes (.col / .spread / .row / .mono / .tnum / .bar-track)
 *   directly per page-admin.jsx:230-252; drop translated-Tailwind CardShell /
 *   BarTrack wrappers + Tailwind-bg-tone dot wrappers in favor of inline
 *   `background: var(--*)` literals copied byte-for-byte from the mockup.
 *
 *   Day 2 R3 mitigation: mockup's 6 flat categories DO NOT 1:1 map to backend
 *   CostSummaryResponse.by_type 2-level dict (cost_type → sub_type → slice).
 *   This sprint ships fully-fixture demo per CLAUDE.md §Mockup-Fidelity + AP-2
 *   honesty banner. Category taxonomy harmonization tracked Phase 58+
 *   AD-Cost-Backend-Category-Taxonomy.
 *
 * Created: 2026-05-19 (Sprint 57.24 Day 2 US-C1)
 * Last Modified: 2026-05-23
 *
 * Modification History:
 *   - 2026-05-23: Sprint 57.31 Day 1 — verbatim re-point to mockup .col/.spread/.bar-track/.mono per page-admin.jsx:230-252
 *   - 2026-05-19: Initial creation (Sprint 57.24 Day 2 US-C1)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline-style literals (dot bg + .bar-track fill width%/bg) are mockup page-admin.jsx visual-layer literals copied byte-for-byte; STYLE.md §1 escape hatch + frontend-mockup-fidelity.md */

import type { CSSProperties, FC } from "react";
import { useTranslation } from "react-i18next";

import { Card } from "../../../components/mockup-ui";
import { BackendGapBanner } from "../../../components/ui/BackendGapBanner";
import { CATEGORY_BREAKDOWN_FIXTURE } from "../__fixtures__/categoryBreakdown";

export const CategoryBarsCard: FC = () => {
  const { t } = useTranslation("common");
  return (
    <Card
      title={t("cost.category.title")}
      subtitle={t("cost.category.subtitle")}
    >
      {/* verbatim from page-admin.jsx:231-251 — .col + spread row + .bar-track */}
      <div
        className="col"
        style={{ gap: 12 } satisfies CSSProperties}
        data-testid="category-bars-card"
      >
        {CATEGORY_BREAKDOWN_FIXTURE.map((row) => (
          <div key={row.key}>
            <div className="spread" style={{ marginBottom: 4 } satisfies CSSProperties}>
              <span className="row" style={{ gap: 6 } satisfies CSSProperties}>
                <span
                  aria-hidden
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: 2,
                    background: row.toneColor,
                  } satisfies CSSProperties}
                />
                <span style={{ fontSize: 12 } satisfies CSSProperties}>
                  {t(`cost.category.${row.key}`)}
                </span>
              </span>
              <span
                className="mono tnum"
                style={{ fontSize: 11.5 } satisfies CSSProperties}
              >
                ${row.value.toLocaleString()}
              </span>
            </div>
            <div className="bar-track" data-testid="bar-track">
              <span
                data-testid="bar-track-fill"
                data-pct={row.pct}
                style={{
                  width: `${row.pct}%`,
                  background: row.toneColor,
                } satisfies CSSProperties}
              />
            </div>
          </div>
        ))}
      </div>
      <BackendGapBanner reason={t("cost.banner.categoryTaxonomy")} />
    </Card>
  );
};
