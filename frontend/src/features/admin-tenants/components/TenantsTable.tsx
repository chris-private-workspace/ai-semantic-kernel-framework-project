/**
 * File: frontend/src/features/admin-tenants/components/TenantsTable.tsx
 * Purpose: Verbatim port of admin tenants 9-col table card (cmdk filter + Plan/Sort + tenant rows).
 * Category: Frontend / admin-tenants / components
 * Scope: Phase 57 / Sprint 57.43 Day 1 (mockup-fidelity rebuild) → Sprint 57.73 (real-data wiring)
 *
 * Description:
 *   Verbatim port of mockup `page-admin.jsx` L357-407 — Card wrapping a 9-col
 *   table (Tenant avatar+name+id / Plan badge / Region / Seats / Agents /
 *   Runs · 24h / Status badge+dot / Created / dots). Toolbar = cmdk filter
 *   visual stub + 2 ghost buttons (Plan: all + Sort: runs(24h)).
 *
 *   Sprint 57.73 (A-6a) re-wired the rows to REAL GET /api/v1/admin/tenants
 *   data via props (TenantListItem[]). Sprint 57.74 fills the two formerly
 *   unbacked columns Agents + Runs · 24h from a `statsByTenant` map (real
 *   per-tenant counts from GET /api/v1/admin/tenants/stats); a subtle "—"
 *   renders only when a tenant is absent from the map OR its count is 0 (the
 *   mockup's empty-cell convention). With agents/runs24 now backed, the table
 *   no longer carries a gap banner — the stats strip owns the remaining
 *   Anomalies/deltas gap (single honest banner per gap; no double banner).
 *   Loading / error / empty states stay MOCKUP-NATIVE table rows (the table's
 *   own markup + mockup classes + var(--*) tokens) — NOT the shadcn-token
 *   shared TableSkeleton/ErrorRetry (those would inject residue into this
 *   verbatim-mockup page).
 *
 * Key Components:
 *   - TenantsTable: prop-driven visual table component (real data + states)
 *
 * Created: 2026-05-25 (Sprint 57.43 Day 1)
 * Last Modified: 2026-06-07
 *
 * Modification History (newest-first):
 *   - 2026-06-07: FIX-031 — disclose toolbar filter/Plan/Sort gap via window.alert (AP-4)
 *   - 2026-06-07: FIX-030 — subtitle from real tenants.length (drop fixture TABLE_SUBTITLE "48 active · 3 anomalies")
 *   - 2026-06-03: Sprint 57.74 — fill agents/runs24 columns from statsByTenant map + drop gap banner (strip owns Anomalies/deltas gap) (A-6a)
 *   - 2026-06-03: Sprint 57.73 — accept real TenantListItem[] via props + loading/error/empty mockup-native rows + "—" for unbacked agents/runs24 (A-6a)
 *   - 2026-05-26: Sprint 57.49 — add optional onRowClick prop for Members drawer drill-down (Track B)
 *   - 2026-05-25: Initial creation (Sprint 57.43 Day 1) — admin-tenants full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx L357-407
 *   - frontend/src/features/admin-tenants/types.ts (TenantListItem + PerTenantStat)
 *   - frontend/src/components/mockup-ui.tsx (Card, Button, Badge, Icon primitives)
 */

/* eslint-disable no-restricted-syntax -- mockup verbatim inline styles ported byte-for-byte from page-admin.jsx L359, L385-401 (avatar cell + mono fontSize / textAlign / width) + Sprint 57.73 mockup-native state rows reuse the same token literals; STYLE.md §3 escape hatch + frontend-mockup-fidelity.md verbatim-CSS method */

import { Badge, Button, Card, Icon } from "../../../components/mockup-ui";
import { TenantPlan, TenantState, type TenantListItem } from "../types";

// Map backend TenantPlan enum → mockup Badge tone. Only standard|enterprise
// exist server-side (the mockup's Pro/Starter labels were fixture-only).
function planTone(plan: TenantPlan): string {
  if (plan === TenantPlan.ENTERPRISE) return "primary";
  return "info";
}

// Map backend TenantState enum → mockup Badge tone (success = healthy active;
// suspended/archived = danger; transitional requested/provisioning = warning).
function statusTone(state: TenantState): string {
  if (state === TenantState.ACTIVE) return "success";
  if (state === TenantState.SUSPENDED || state === TenantState.ARCHIVED) return "danger";
  return "warning";
}

// ISO 8601 datetime → YYYY-MM-DD (mockup `created` column is date-only).
function formatCreated(createdAt: string): string {
  return createdAt.slice(0, 10);
}

// Subtle "—" rendered in the Agents / Runs·24h cells when a tenant is absent
// from the stats map OR its count is 0 (the mockup's empty-cell convention) —
// never a fabricated number (AP-2 honesty).
const GAP_PLACEHOLDER = (
  <span style={{ color: "var(--fg-subtle)" }}>—</span>
);

// Render a per-tenant count: real (number-formatted, mockup convention) when
// present and > 0; subtle "—" for a genuine 0 / absent tenant.
function renderCount(count: number | undefined): JSX.Element | string {
  if (count === undefined || count === 0) return GAP_PLACEHOLDER;
  return count.toLocaleString();
}

export interface TenantsTableProps {
  /** Real tenant rows from GET /api/v1/admin/tenants (Sprint 57.73 A-6a). */
  tenants: TenantListItem[];
  /**
   * Per-tenant agents/runs24 counts keyed by tenant id, from
   * GET /api/v1/admin/tenants/stats (Sprint 57.74). Absent tenants / 0 counts
   * render the subtle "—" placeholder.
   */
  statsByTenant?: Record<string, { agents: number; runs24: number }>;
  /** TanStack query loading flag (shows skeleton rows). */
  isLoading?: boolean;
  /** TanStack query error flag (shows inline error row + retry). */
  isError?: boolean;
  /** Retry handler wired to query.refetch(). */
  onRetry?: () => void;
  /**
   * Optional row click handler — when provided, table rows become clickable
   * and surface tenant_id for parent (Sprint 57.49 Track B uses this to open
   * Members drawer; AdminTenantsView wires it).
   */
  onRowClick?: (tenantId: string) => void;
}

export function TenantsTable({
  tenants,
  statsByTenant,
  isLoading = false,
  isError = false,
  onRetry,
  onRowClick,
}: TenantsTableProps): JSX.Element {
  // FIX-031: the cmdk filter + Plan/Sort buttons are mockup visual stubs with no
  // backend yet — disclose the gap on interaction (codebase gold pattern:
  // window.alert) instead of silently doing nothing (AP-4). Client-side wiring
  // tracked Phase 58+ (AD-AdminTenants-Toolbar-Filter-Sort-Wire-Or-Disable).
  const discloseToolbarGap = (label: string): void => {
    window.alert(
      `${label}: backend gap (Phase 58+) — admin tenant filter/sort endpoint pending`,
    );
  };
  return (
    <Card
      title="All tenants"
      subtitle={`${tenants.length} ${tenants.length === 1 ? "tenant" : "tenants"}`}
      bodyClass="flush"
      actions={
        <div className="row">
          <div
            className="cmdk"
            style={{ minWidth: 220, cursor: "pointer" }}
            role="button"
            tabIndex={0}
            onClick={() => discloseToolbarGap("Filter")}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                discloseToolbarGap("Filter");
              }
            }}
          >
            <Icon name="search" size={13} />
            <span className="grow">Filter by name, id, region…</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            icon="filter"
            onClick={() => discloseToolbarGap("Plan filter")}
          >
            Plan: all
          </Button>
          <Button
            variant="ghost"
            size="sm"
            icon="sliders"
            onClick={() => discloseToolbarGap("Sort")}
          >
            Sort: runs (24h)
          </Button>
        </div>
      }
    >
      <table className="table">
        <thead>
          <tr>
            <th>Tenant</th>
            <th>Plan</th>
            <th>Region</th>
            <th style={{ textAlign: "right" }}>Seats</th>
            <th style={{ textAlign: "right" }}>Agents</th>
            <th style={{ textAlign: "right" }}>Runs · 24h</th>
            <th>Status</th>
            <th>Created</th>
            <th style={{ width: 28 }}></th>
          </tr>
        </thead>
        <tbody>
          {isLoading ? (
            // Mockup-native skeleton: 3 placeholder rows of `.subtle` cells
            // (no shadcn TableSkeleton — keeps this page residue-free).
            <>
              {[0, 1, 2].map((i) => (
                <tr key={`skeleton-${i}`} data-testid="tenant-row-skeleton">
                  {[0, 1, 2, 3, 4, 5, 6, 7, 8].map((c) => (
                    <td key={c} className="subtle" style={{ color: "var(--fg-subtle)" }}>
                      ···
                    </td>
                  ))}
                </tr>
              ))}
            </>
          ) : isError ? (
            <tr data-testid="tenant-row-error">
              <td colSpan={9} style={{ textAlign: "center", padding: 24 }}>
                <div className="subtle" style={{ marginBottom: 8, color: "var(--danger)" }}>
                  Failed to load tenants.
                </div>
                {onRetry && (
                  <Button variant="outline" size="sm" icon="refresh" onClick={onRetry}>
                    Retry
                  </Button>
                )}
              </td>
            </tr>
          ) : tenants.length === 0 ? (
            <tr data-testid="tenant-row-empty">
              <td
                colSpan={9}
                className="subtle"
                style={{ textAlign: "center", padding: 24, color: "var(--fg-subtle)" }}
              >
                No tenants found.
              </td>
            </tr>
          ) : (
            tenants.map((t) => (
              <tr
                key={t.id}
                onClick={onRowClick ? () => onRowClick(t.id) : undefined}
                style={onRowClick ? { cursor: "pointer" } : undefined}
                data-testid={`tenant-row-${t.code}`}
              >
                <td>
                  <div className="row" style={{ gap: 8 }}>
                    <span
                      style={{
                        width: 24,
                        height: 24,
                        borderRadius: 5,
                        background: "var(--primary-soft-2)",
                        color: "var(--primary)",
                        display: "inline-flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: 11,
                        fontWeight: 600,
                      }}
                    >
                      {t.display_name[0]?.toUpperCase() ?? "?"}
                    </span>
                    <div>
                      <div className="mono" style={{ fontSize: 12.5, fontWeight: 500 }}>
                        {t.display_name}
                      </div>
                      <div className="mono subtle" style={{ fontSize: 10.5 }}>
                        {t.code}
                      </div>
                    </div>
                  </div>
                </td>
                <td>
                  <Badge tone={planTone(t.plan)}>{t.plan}</Badge>
                </td>
                <td className="mono subtle" style={{ fontSize: 11.5 }}>
                  {t.region}
                </td>
                <td className="mono tnum" style={{ textAlign: "right" }}>
                  {t.seats}
                </td>
                <td className="mono tnum" style={{ textAlign: "right" }}>
                  {renderCount(statsByTenant?.[t.id]?.agents)}
                </td>
                <td className="mono tnum" style={{ textAlign: "right" }}>
                  {renderCount(statsByTenant?.[t.id]?.runs24)}
                </td>
                <td>
                  <Badge tone={statusTone(t.state)} dot>
                    {t.state}
                  </Badge>
                </td>
                <td className="subtle" style={{ fontSize: 11.5 }}>
                  {formatCreated(t.created_at)}
                </td>
                <td>
                  <Icon name="dots" size={14} className="subtle" />
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </Card>
  );
}
