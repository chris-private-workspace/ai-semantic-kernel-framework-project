/**
 * File: frontend/src/features/tenant-settings/components/TenantSettingsView.tsx
 * Purpose: Read-only view of tenant settings — TanStack-driven container for /tenant-settings/{id}.
 * Category: Frontend / tenant-settings / components
 * Scope: Phase 57 / Sprint 57.3 US-4 → Sprint 57.9 US-6 Day 4 (TanStack hook) → Sprint 57.16 Tailwind migration
 *
 * Description:
 *   Sprint 57.9 US-6 Day 4: replaced manual useEffect + loadData orchestration
 *   with `useTenantSettings` TanStack Query hook.
 *   Sprint 57.13 US-A2: tenant_id from the authenticated session
 *   (authStore.tenant.id) — page is wrapped in <RequireAuth>.
 *   Sprint 57.16 (AD-Inline-Style-Cleanup-Sweep-Round2): inline styles →
 *   Tailwind utility classes; state/plan badge helpers now return Tailwind
 *   class strings (57.15 vocab `bg-success` / `bg-warning` /
 *   `bg-muted-foreground` / `bg-primary` — visual continuity with
 *   admin-tenants TenantListTable).
 *
 *   Edit toggle button switches to TenantSettingsEditForm. Loading skeleton +
 *   error retry UX. State + Plan rendered as colored badges.
 *
 * Created: 2026-05-07 (Sprint 57.3 Day 3)
 * Last Modified: 2026-05-11
 *
 * Modification History (newest-first):
 *   - 2026-05-11: Sprint 57.16 — inline styles → Tailwind utility classes; stateBadgeColor/planBadgeColor → *Class fns (AD-Inline-Style-Cleanup-Sweep-Round2)
 *   - 2026-05-10: Sprint 57.13 US-A2 — tenant_id from authStore.tenant.id (was URL ?tenant_id=)
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — migrate to useTenantSettings TanStack hook (drop store loadData)
 *   - 2026-05-07: Initial creation (Sprint 57.3 Day 3)
 */

import { useState } from "react";

import { cn } from "../../../lib/utils";
import { useAuthStore } from "../../auth/store/authStore";
import { useTenantSettings } from "../hooks/useTenantSettings";
import { TenantPlan, TenantState } from "../types";
import { TenantSettingsEditForm } from "./TenantSettingsEditForm";

function stateBadgeClass(state: TenantState): string {
  switch (state) {
    case TenantState.ACTIVE:
      return "bg-success";
    case TenantState.PROVISIONING:
    case TenantState.REQUESTED:
      return "bg-warning";
    case TenantState.SUSPENDED:
    case TenantState.ARCHIVED:
    default:
      return "bg-muted-foreground";
  }
}

function planBadgeClass(plan: TenantPlan): string {
  return plan === TenantPlan.ENTERPRISE ? "bg-primary" : "bg-muted-foreground";
}

const BADGE_CLASS = "rounded-sm px-2 py-0.5 text-[0.85rem] text-white";

export function TenantSettingsView() {
  const tenantId = useAuthStore((s) => s.tenant?.id ?? "");
  const [editing, setEditing] = useState(false);

  const { data, isLoading, error, refetch } = useTenantSettings(tenantId);

  return (
    <div className="p-8 font-sans">
      <p className="text-sm text-muted-foreground">Configuration for your tenant.</p>

      {!tenantId && <p className="text-danger">No tenant in your session.</p>}

      {isLoading && tenantId && <p className="italic">Loading tenant settings…</p>}

      {error && (
        <div className="mt-4 border border-danger p-4 text-danger">
          <p>Error: {error.message}</p>
          <button onClick={() => void refetch()}>Retry</button>
        </div>
      )}

      {data && !isLoading && !error && !editing && (
        <div className="mt-6">
          <dl className="grid grid-cols-[max-content_1fr] gap-x-4 gap-y-2">
            <dt className="font-semibold">Tenant ID</dt>
            <dd className="m-0 font-mono">{data.id}</dd>

            <dt className="font-semibold">Code</dt>
            <dd className="m-0 font-mono">{data.code}</dd>

            <dt className="font-semibold">Display Name</dt>
            <dd className="m-0">{data.display_name}</dd>

            <dt className="font-semibold">State</dt>
            <dd className="m-0">
              <span className={cn(BADGE_CLASS, stateBadgeClass(data.state))}>{data.state}</span>
            </dd>

            <dt className="font-semibold">Plan</dt>
            <dd className="m-0">
              <span className={cn(BADGE_CLASS, planBadgeClass(data.plan))}>{data.plan}</span>
            </dd>

            <dt className="font-semibold">Created</dt>
            <dd className="m-0">{data.created_at}</dd>

            <dt className="font-semibold">Updated</dt>
            <dd className="m-0">{data.updated_at}</dd>
          </dl>

          <details className="mt-4">
            <summary className="cursor-pointer">Provisioning + Onboarding progress (JSON)</summary>
            <pre className="bg-muted p-3 text-[0.85rem]">
              {JSON.stringify(
                {
                  provisioning_progress: data.provisioning_progress,
                  onboarding_progress: data.onboarding_progress,
                  meta_data: data.meta_data,
                },
                null,
                2,
              )}
            </pre>
          </details>

          <button className="mt-6 px-4 py-2" onClick={() => setEditing(true)}>
            Edit
          </button>
        </div>
      )}

      {data && editing && (
        <TenantSettingsEditForm
          tenantId={tenantId}
          initialData={data}
          onDone={() => setEditing(false)}
        />
      )}
    </div>
  );
}
