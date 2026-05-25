/**
 * File: frontend/src/features/tenant-settings/components/TenantSettingsView.tsx
 * Purpose: Tenant Settings page inner view — 6-tab router (General/Flags/Quotas/HITL/Members/Danger).
 * Category: Frontend / tenant-settings / components
 * Scope: Phase 57 / Sprint 57.44 Day 1 (mockup-fidelity rebuild)
 *
 * Description:
 *   Sprint 57.44 full rebuild: replaces Sprint 57.16-vintage single-card dl/dt
 *   readonly view + TenantSettingsEditForm toggle with the mockup 6-tab IA from
 *   `page-admin.jsx:411-621`. PageHeader renders title + mono display_name +
 *   route-pill + plan Badge; Tabs primitive drives 6-tab switching; each tab
 *   component renders its own Card grid.
 *
 *   Backend wire: useTenantSettings(tenantId) feeds display_name / code / plan
 *   into PageHeader + GeneralTab. GeneralTab's display_name field is the ONLY
 *   field PATCH-able via backend (TenantUpdateRequest); all other tabs render
 *   _fixtures.ts data + BackendGapBanner per AP-2 honesty (D-DAY0-4 Option A
 *   fixture-first decision).
 *
 *   Outer layout (AppShellV2 + RequireAuth) lives in pages/tenant-settings/
 *   index.tsx and is unchanged.
 *
 * Created: 2026-05-07 (Sprint 57.3 Day 3 — initial readonly view)
 * Last Modified: 2026-05-26
 *
 * Modification History (newest-first):
 *   - 2026-05-26: Sprint 57.44 — full rewrite to 6-tab mockup IA (drop EditForm + JSON dump + dl/dt view)
 *   - 2026-05-11: Sprint 57.16 — inline styles → Tailwind utility classes; stateBadgeColor/planBadgeColor → *Class fns
 *   - 2026-05-10: Sprint 57.13 US-A2 — tenant_id from authStore.tenant.id (was URL ?tenant_id=)
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — migrate to useTenantSettings TanStack hook (drop store loadData)
 *   - 2026-05-07: Initial creation (Sprint 57.3 Day 3)
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx L411-621
 *   - ../hooks/useTenantSettings.ts (display_name / code / plan source)
 *   - ./TenantSettingsPageHeader.tsx + ./tabs/*
 *   - frontend/src/components/mockup-ui.tsx (Tabs primitive)
 */

import { useState } from "react";

import { Tabs } from "../../../components/mockup-ui";
import { useAuthStore } from "../../auth/store/authStore";
import { useTenantSettings } from "../hooks/useTenantSettings";
import { TenantSettingsPageHeader } from "./TenantSettingsPageHeader";
import { DangerZoneTab } from "./tabs/DangerZoneTab";
import { FeatureFlagsTab } from "./tabs/FeatureFlagsTab";
import { GeneralTab } from "./tabs/GeneralTab";
import { HITLPoliciesTab } from "./tabs/HITLPoliciesTab";
import { MembersTab } from "./tabs/MembersTab";
import { QuotasTab } from "./tabs/QuotasTab";

type TabId = "general" | "flags" | "quotas" | "hitl" | "members" | "danger";

const TAB_ITEMS = [
  { id: "general", label: "General" },
  { id: "flags", label: "Feature Flags", count: 14 },
  { id: "quotas", label: "Quotas" },
  { id: "hitl", label: "HITL Policies" },
  { id: "members", label: "Members", count: 8 },
  { id: "danger", label: "Danger Zone" },
];

export function TenantSettingsView(): JSX.Element {
  const tenantId = useAuthStore((s) => s.tenant?.id ?? "");
  const [tab, setTab] = useState<TabId>("general");

  const { data, isLoading, error, refetch } = useTenantSettings(tenantId);

  if (!tenantId) {
    return (
      <div>
        <p className="muted">No tenant in your session.</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div>
        <p className="muted">Loading tenant settings…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        {/* eslint-disable-next-line no-restricted-syntax -- inline-style minor error banner */}
        <div style={{ padding: 14, border: "1px solid var(--danger)", borderRadius: "var(--radius)", color: "var(--danger)" }}>
          <p>Error: {error.message}</p>
          <button className="btn outline" onClick={() => void refetch()}>Retry</button>
        </div>
      </div>
    );
  }

  if (!data) return <div />;

  return (
    <div>
      <TenantSettingsPageHeader
        displayName={data.display_name}
        code={data.code}
        plan={data.plan}
      />
      <Tabs
        items={TAB_ITEMS}
        value={tab}
        onChange={(id) => setTab(id as TabId)}
        ariaLabel="Tenant settings sections"
      />
      {tab === "general" && <GeneralTab data={data} />}
      {tab === "flags" && <FeatureFlagsTab />}
      {tab === "quotas" && <QuotasTab />}
      {tab === "hitl" && <HITLPoliciesTab />}
      {tab === "members" && <MembersTab />}
      {tab === "danger" && <DangerZoneTab />}
    </div>
  );
}
