/**
 * File: frontend/src/features/cost-dashboard/components/TenantTopTable.tsx
 * Purpose: Admin-scope top-8 spend-by-tenant table per mockup page-admin.jsx:258-293.
 * Category: Frontend / cost-dashboard / components
 * Scope: Phase 57 / Sprint 57.24 Day 2 US-C2
 *
 * Description:
 *   Renders the mockup "Spend by tenant" admin-scope card: top-8 rows with
 *   tenant avatar + slug + optional anomaly Badge + Plan Badge + Tokens +
 *   Cost + Quota used % (color-coded) + quota BarTrack (color-coded).
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
 *
 * Modification History:
 *   - 2026-05-19: Initial creation (Sprint 57.24 Day 2 US-C2)
 */

import type { FC } from "react";
import { useTranslation } from "react-i18next";

import { BarTrack } from "../../../components/charts/BarTrack";
import { Badge } from "../../../components/ui/badge";
import { BackendGapBanner } from "../../../components/ui/BackendGapBanner";
import { CardShell } from "../../../components/ui/CardShell";
import {
  TENANT_TOP_8_FIXTURE,
  type TenantTopRow,
} from "../__fixtures__/tenantTop8";

const quotaBarTone = (pct: number): string => {
  if (pct > 100) return "var(--danger)";
  if (pct > 80) return "var(--warning)";
  return "var(--success)";
};

const quotaTextClass = (pct: number): string => {
  if (pct > 100) return "text-danger";
  if (pct > 80) return "text-warning";
  return "text-fg-muted";
};

const TenantRow: FC<{ row: TenantTopRow; anomalyLabel: string }> = ({
  row,
  anomalyLabel,
}) => (
  <tr className="border-t border-border" data-testid="tenant-row">
    <td className="px-3 py-2">
      <span className="inline-flex items-center gap-1.5">
        <span
          aria-hidden
          className="inline-flex h-[18px] w-[18px] items-center justify-center rounded bg-primary/15 text-[10px] font-semibold uppercase text-primary"
        >
          {row.slug[0]}
        </span>
        <span className="font-mono text-xs">{row.slug}</span>
        {row.alert && (
          <span
            data-testid="tenant-anomaly-badge"
            className="inline-flex items-center gap-1 rounded-full bg-danger/15 px-2 py-0.5 text-[10.5px] font-medium text-danger"
          >
            <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-current" />
            {anomalyLabel}
          </span>
        )}
      </span>
    </td>
    <td className="px-3 py-2">
      <Badge variant="outline">{row.plan}</Badge>
    </td>
    <td className="px-3 py-2 text-right font-mono text-xs tabular-nums text-fg-muted">
      {row.tokens}
    </td>
    <td className="px-3 py-2 text-right font-mono text-xs tabular-nums">
      ${row.cost}
    </td>
    <td className="px-3 py-2 text-right">
      <span
        data-testid="tenant-quota-pct"
        className={`font-mono text-[11px] tabular-nums ${quotaTextClass(row.pct)}`}
      >
        {row.pct}%
      </span>
    </td>
    <td className="w-[100px] px-3 py-2">
      <BarTrack pct={row.pct} tone={quotaBarTone(row.pct)} />
    </td>
  </tr>
);

export const TenantTopTable: FC = () => {
  const { t } = useTranslation("common");
  return (
    <CardShell
      title={t("cost.tenant.title")}
      subtitle={t("cost.tenant.subtitle")}
      bodyClass=""
    >
      <table
        className="w-full text-left text-xs"
        data-testid="tenant-top-table"
      >
        <thead>
          <tr className="text-[11px] uppercase tracking-wide text-fg-muted">
            <th className="px-3 py-2 font-medium">{t("cost.tenant.col.tenant")}</th>
            <th className="px-3 py-2 font-medium">{t("cost.tenant.col.plan")}</th>
            <th className="px-3 py-2 text-right font-medium">
              {t("cost.tenant.col.tokens")}
            </th>
            <th className="px-3 py-2 text-right font-medium">
              {t("cost.tenant.col.cost")}
            </th>
            <th className="px-3 py-2 text-right font-medium">
              {t("cost.tenant.col.quotaUsed")}
            </th>
            <th className="px-3 py-2" aria-hidden />
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
      <div className="px-3 pb-3 pt-1">
        <BackendGapBanner reason={t("cost.banner.crossTenant")} />
      </div>
    </CardShell>
  );
};
