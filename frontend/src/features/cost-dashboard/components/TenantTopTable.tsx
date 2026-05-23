/**
 * File: frontend/src/features/cost-dashboard/components/TenantTopTable.tsx
 * Purpose: Admin-scope top-8 spend-by-tenant table — verbatim re-point to mockup page-admin.jsx:258-293.
 * Category: Frontend / cost-dashboard / components
 * Scope: Phase 57 / Sprint 57.24 Day 2 US-C2 → 57.31 Day 1 (verbatim re-point)
 *
 * Description:
 *   Renders the mockup "Spend by tenant" admin-scope card: top-8 rows with
 *   tenant avatar + slug + optional anomaly Badge + Plan Badge + Tokens +
 *   Cost + Quota used % (color-coded) + quota .bar-track (color-coded).
 *
 *   Sprint 57.31 Day 1 verbatim re-point: consume mockup-ui <Card> + <Badge> +
 *   verbatim CSS classes (.table / .row / .mono / .tnum / .subtle / .bar-track)
 *   per page-admin.jsx:258-293; drop translated-Tailwind CardShell / BarTrack /
 *   shadcn Badge wrappers in favor of mockup primitives + inline verbatim
 *   visual-layer literals (avatar 18×18 rounded square, color-coded quota %).
 *
 *   Quota color: production keeps the text-danger / text-warning / text-fg-muted
 *   class names on the quota % span (Vitest spec contract — class membership
 *   check, NOT visual styling — class is wired to the same oklch token tree
 *   via Tailwind config; same final color).
 *
 *   Admin scope gate: this component itself is ADMIN-AGNOSTIC — the parent
 *   (CostOverview) checks isPlatformAdmin and conditionally mounts. This
 *   keeps the component pure and reusable in tests.
 *
 *   Data source: fully-fixture (TENANT_TOP_8_FIXTURE). Backend cross-tenant
 *   aggregation API pending Phase 58+ AD-Cost-Dashboard-Backend-Extensions.
 *   BackendGapBanner marks fixture state per AP-2 honesty.
 *
 *   Quota color logic mirrors mockup page-admin.jsx:282-287:
 *   - pct > 100 → danger (over-quota)
 *   - pct > 80  → warning (near-limit)
 *   - else      → muted text + success bar tone
 *
 * Created: 2026-05-19 (Sprint 57.24 Day 2 US-C2)
 * Last Modified: 2026-05-23
 *
 * Modification History:
 *   - 2026-05-23: Sprint 57.31 Day 1 — verbatim re-point to mockup .table/.bar-track/.row/Badge per page-admin.jsx:258-293
 *   - 2026-05-19: Initial creation (Sprint 57.24 Day 2 US-C2)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: inline-style literals (avatar geom + col widths + .bar-track fill width%/bg + colored % via var(--*)) are mockup page-admin.jsx visual-layer literals copied byte-for-byte; STYLE.md §1 escape hatch + frontend-mockup-fidelity.md */

import type { CSSProperties, FC } from "react";
import { useTranslation } from "react-i18next";

import { Badge } from "../../../components/mockup-ui";
import { BackendGapBanner } from "../../../components/ui/BackendGapBanner";
import { Card } from "../../../components/mockup-ui";
import {
  TENANT_TOP_8_FIXTURE,
  type TenantTopRow,
} from "../__fixtures__/tenantTop8";

const quotaBarTone = (pct: number): string => {
  if (pct > 100) return "var(--danger)";
  if (pct > 80) return "var(--warning)";
  return "var(--success)";
};

// Production class membership preserved for Vitest spec contract
// (TenantTopTable.test.tsx asserts className contains text-danger / text-warning).
// Tailwind config wires text-danger → var(--danger) — same token as inline below.
const quotaTextClass = (pct: number): string => {
  if (pct > 100) return "text-danger";
  if (pct > 80) return "text-warning";
  return "text-fg-muted";
};

const TenantRow: FC<{ row: TenantTopRow; anomalyLabel: string }> = ({
  row,
  anomalyLabel,
}) => (
  <tr data-testid="tenant-row">
    {/* verbatim from page-admin.jsx:273-277 — .row + 18×18 avatar */}
    <td className="row" style={{ gap: 6 } satisfies CSSProperties}>
      <span
        aria-hidden
        style={{
          width: 18,
          height: 18,
          borderRadius: 4,
          background: "var(--primary-soft-2)",
          color: "var(--primary)",
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 10,
          fontWeight: 600,
        } satisfies CSSProperties}
      >
        {row.slug[0].toUpperCase()}
      </span>
      <span className="mono" style={{ fontSize: 12 } satisfies CSSProperties}>
        {row.slug}
      </span>
      {row.alert && (
        <span data-testid="tenant-anomaly-badge" style={{ display: "inline-flex" } satisfies CSSProperties}>
          <Badge tone="danger" dot>
            {anomalyLabel}
          </Badge>
        </span>
      )}
    </td>
    <td>
      <Badge>{row.plan}</Badge>
    </td>
    {/* verbatim from page-admin.jsx:279-280 — .mono .tnum .subtle / .mono .tnum right-aligned */}
    <td className="mono tnum subtle" style={{ textAlign: "right" } satisfies CSSProperties}>
      {row.tokens}
    </td>
    <td className="mono tnum" style={{ textAlign: "right" } satisfies CSSProperties}>
      ${row.cost}
    </td>
    {/* verbatim from page-admin.jsx:281-283 — text color via inline var(--*) tone */}
    <td style={{ textAlign: "right" } satisfies CSSProperties}>
      <span
        data-testid="tenant-quota-pct"
        className={`mono tnum ${quotaTextClass(row.pct)}`}
        style={{
          fontSize: 11,
          color:
            row.pct > 100
              ? "var(--danger)"
              : row.pct > 80
                ? "var(--warning)"
                : "var(--fg-muted)",
        } satisfies CSSProperties}
      >
        {row.pct}%
      </span>
    </td>
    {/* verbatim from page-admin.jsx:284-288 — 100px-wide .bar-track */}
    <td style={{ width: 100 } satisfies CSSProperties}>
      <div className="bar-track" data-testid="bar-track">
        <span
          data-testid="bar-track-fill"
          data-pct={Math.min(100, row.pct)}
          style={{
            width: `${Math.min(100, row.pct)}%`,
            background: quotaBarTone(row.pct),
          } satisfies CSSProperties}
        />
      </div>
    </td>
  </tr>
);

export const TenantTopTable: FC = () => {
  const { t } = useTranslation("common");
  return (
    <Card
      title={t("cost.tenant.title")}
      subtitle={t("cost.tenant.subtitle")}
      bodyClass="flush"
    >
      {/* verbatim from page-admin.jsx:259-292 — .table */}
      <table className="table" data-testid="tenant-top-table">
        <thead>
          <tr>
            <th>{t("cost.tenant.col.tenant")}</th>
            <th>{t("cost.tenant.col.plan")}</th>
            <th style={{ textAlign: "right" } satisfies CSSProperties}>
              {t("cost.tenant.col.tokens")}
            </th>
            <th style={{ textAlign: "right" } satisfies CSSProperties}>
              {t("cost.tenant.col.cost")}
            </th>
            <th style={{ textAlign: "right" } satisfies CSSProperties}>
              {t("cost.tenant.col.quotaUsed")}
            </th>
            <th aria-hidden />
          </tr>
        </thead>
        <tbody>
          {TENANT_TOP_8_FIXTURE.map((row) => (
            <TenantRow
              key={row.slug}
              row={row}
              anomalyLabel={t("cost.tenant.anomaly")}
            />
          ))}
        </tbody>
      </table>
      <div style={{ padding: "8px 16px 16px" } satisfies CSSProperties}>
        <BackendGapBanner reason={t("cost.banner.crossTenant")} />
      </div>
    </Card>
  );
};
