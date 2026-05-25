/**
 * File: frontend/src/features/admin-tenants/components/TenantsTable.tsx
 * Purpose: Verbatim port of admin tenants 9-col table card (cmdk filter + Plan/Sort + tenant rows).
 * Category: Frontend / admin-tenants / components
 * Scope: Phase 57 / Sprint 57.43 Day 1 (mockup-fidelity rebuild)
 *
 * Description:
 *   Verbatim port of mockup `page-admin.jsx` L357-407 — Card wrapping a 9-col
 *   table (Tenant avatar+name+id / Plan badge / Region / Seats / Agents /
 *   Runs · 24h / Status badge+dot / Created / dots). Toolbar = cmdk filter
 *   visual stub + 2 ghost buttons (Plan: all + Sort: runs(24h)). AP-2
 *   BackendGapBanner declares backend wire deferred Phase 58+ per D-DAY0-6.
 *
 * Key Components:
 *   - TenantsTable: stateless visual table component
 *
 * Created: 2026-05-25 (Sprint 57.43 Day 1)
 * Last Modified: 2026-05-25
 *
 * Modification History (newest-first):
 *   - 2026-05-25: Initial creation (Sprint 57.43 Day 1) — admin-tenants full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx L357-407
 *   - frontend/src/features/admin-tenants/_fixtures.ts (TENANTS_FIXTURE, TABLE_SUBTITLE)
 *   - frontend/src/components/mockup-ui.tsx (Card, Button, Badge, Icon primitives)
 *   - frontend/src/components/ui/BackendGapBanner.tsx (AP-2 honesty banner)
 */

/* eslint-disable no-restricted-syntax -- mockup verbatim inline styles ported byte-for-byte from page-admin.jsx L359, L385-401 (avatar cell + mono fontSize / textAlign / width); STYLE.md §3 escape hatch + frontend-mockup-fidelity.md verbatim-CSS method */

import { Badge, Button, Card, Icon } from "../../../components/mockup-ui";
import { BackendGapBanner } from "../../../components/ui/BackendGapBanner";
import { TABLE_SUBTITLE, TENANTS_FIXTURE, type TenantFixture } from "../_fixtures";

function planTone(plan: TenantFixture["plan"]): string {
  if (plan === "Enterprise") return "primary";
  if (plan === "Pro") return "info";
  return "";
}

function statusTone(status: TenantFixture["status"]): string {
  if (status === "active") return "success";
  if (status === "anomaly") return "danger";
  return "warning";
}

export function TenantsTable(): JSX.Element {
  return (
    <Card
      title="All tenants"
      subtitle={TABLE_SUBTITLE}
      bodyClass="flush"
      actions={
        <div className="row">
          <div className="cmdk" style={{ minWidth: 220 }}>
            <Icon name="search" size={13} />
            <span className="grow">Filter by name, id, region…</span>
          </div>
          <Button variant="ghost" size="sm" icon="filter">
            Plan: all
          </Button>
          <Button variant="ghost" size="sm" icon="sliders">
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
          {TENANTS_FIXTURE.map((t) => (
            <tr key={t.id}>
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
                    {t.name[0].toUpperCase()}
                  </span>
                  <div>
                    <div className="mono" style={{ fontSize: 12.5, fontWeight: 500 }}>
                      {t.name}
                    </div>
                    <div className="mono subtle" style={{ fontSize: 10.5 }}>
                      {t.id}
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
                {t.agents}
              </td>
              <td className="mono tnum" style={{ textAlign: "right" }}>
                {t.runs24.toLocaleString()}
              </td>
              <td>
                <Badge tone={statusTone(t.status)} dot>
                  {t.status}
                </Badge>
              </td>
              <td className="subtle" style={{ fontSize: 11.5 }}>
                {t.created}
              </td>
              <td>
                <Icon name="dots" size={14} className="subtle" />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <BackendGapBanner reason="Admin tenants list backend wire deferred (Phase 58+) — TenantListItem schema lacks seats/region/agents/runs24/status (5 of 9 mockup columns); see AD-AdminTenants-Backend-Schema-Extension" />
    </Card>
  );
}
