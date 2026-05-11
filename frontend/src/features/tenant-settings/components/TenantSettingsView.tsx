/* eslint-disable no-restricted-syntax -- AD-Inline-Style-Cleanup-Sweep-Round2: inline styles deferred (tenant-settings batch — migrated in a follow-up sprint). */
/**
 * File: frontend/src/features/tenant-settings/components/TenantSettingsView.tsx
 * Purpose: Read-only view of tenant settings — TanStack-driven container for /tenant-settings/{id}.
 * Category: Frontend / tenant-settings / components
 * Scope: Phase 57 / Sprint 57.3 US-4 → Sprint 57.9 US-6 Day 4 (TanStack hook)
 *
 * Description:
 *   Sprint 57.9 US-6 Day 4: replaced manual useEffect + loadData orchestration
 *   with `useTenantSettings` TanStack Query hook.
 *   Sprint 57.13 US-A2: tenant_id from the authenticated session
 *   (authStore.tenant.id) — page is wrapped in <RequireAuth>. (Tailwind-ize
 *   the inline styles in Sprint 57.13 US-B9 inline-cleanup sweep.)
 *
 *   Edit toggle button switches to TenantSettingsEditForm. Loading skeleton +
 *   error retry UX. State + Plan rendered as colored badges.
 *
 * Created: 2026-05-07 (Sprint 57.3 Day 3)
 * Last Modified: 2026-05-10
 *
 * Modification History (newest-first):
 *   - 2026-05-10: Sprint 57.13 US-A2 — tenant_id from authStore.tenant.id (was URL ?tenant_id=)
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — migrate to useTenantSettings TanStack hook (drop store loadData)
 *   - 2026-05-07: Initial creation (Sprint 57.3 Day 3)
 */

import { useState } from "react";

import { useAuthStore } from "../../auth/store/authStore";
import { useTenantSettings } from "../hooks/useTenantSettings";
import { TenantPlan, TenantState } from "../types";
import { TenantSettingsEditForm } from "./TenantSettingsEditForm";

function stateBadgeColor(state: TenantState): string {
  switch (state) {
    case TenantState.ACTIVE:
      return "#0a0";
    case TenantState.PROVISIONING:
    case TenantState.REQUESTED:
      return "#a80";
    case TenantState.SUSPENDED:
    case TenantState.ARCHIVED:
      return "#888";
    default:
      return "#666";
  }
}

function planBadgeColor(plan: TenantPlan): string {
  return plan === TenantPlan.ENTERPRISE ? "#06c" : "#888";
}

export function TenantSettingsView() {
  const tenantId = useAuthStore((s) => s.tenant?.id ?? "");
  const [editing, setEditing] = useState(false);

  const { data, isLoading, error, refetch } = useTenantSettings(tenantId);

  return (
    <div style={{ padding: "2rem", fontFamily: "system-ui, sans-serif" }}>
      <p style={{ color: "#666", fontSize: "0.9rem" }}>
        Configuration for your tenant.
      </p>

      {!tenantId && <p style={{ color: "#a00" }}>No tenant in your session.</p>}

      {isLoading && tenantId && <p style={{ fontStyle: "italic" }}>Loading tenant settings…</p>}

      {error && (
        <div style={{ marginTop: "1rem", padding: "1rem", border: "1px solid #a00", color: "#a00" }}>
          <p>Error: {error.message}</p>
          <button onClick={() => void refetch()}>Retry</button>
        </div>
      )}

      {data && !isLoading && !error && !editing && (
        <div style={{ marginTop: "1.5rem" }}>
          <dl style={{ display: "grid", gridTemplateColumns: "max-content 1fr", gap: "0.5rem 1rem" }}>
            <dt style={{ fontWeight: 600 }}>Tenant ID</dt>
            <dd style={{ margin: 0, fontFamily: "monospace" }}>{data.id}</dd>

            <dt style={{ fontWeight: 600 }}>Code</dt>
            <dd style={{ margin: 0, fontFamily: "monospace" }}>{data.code}</dd>

            <dt style={{ fontWeight: 600 }}>Display Name</dt>
            <dd style={{ margin: 0 }}>{data.display_name}</dd>

            <dt style={{ fontWeight: 600 }}>State</dt>
            <dd style={{ margin: 0 }}>
              <span
                style={{
                  padding: "0.15rem 0.5rem",
                  borderRadius: "0.25rem",
                  background: stateBadgeColor(data.state),
                  color: "white",
                  fontSize: "0.85rem",
                }}
              >
                {data.state}
              </span>
            </dd>

            <dt style={{ fontWeight: 600 }}>Plan</dt>
            <dd style={{ margin: 0 }}>
              <span
                style={{
                  padding: "0.15rem 0.5rem",
                  borderRadius: "0.25rem",
                  background: planBadgeColor(data.plan),
                  color: "white",
                  fontSize: "0.85rem",
                }}
              >
                {data.plan}
              </span>
            </dd>

            <dt style={{ fontWeight: 600 }}>Created</dt>
            <dd style={{ margin: 0 }}>{data.created_at}</dd>

            <dt style={{ fontWeight: 600 }}>Updated</dt>
            <dd style={{ margin: 0 }}>{data.updated_at}</dd>
          </dl>

          <details style={{ marginTop: "1rem" }}>
            <summary style={{ cursor: "pointer" }}>Provisioning + Onboarding progress (JSON)</summary>
            <pre style={{ background: "#f0f0f0", padding: "0.75rem", fontSize: "0.85rem" }}>
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

          <button
            style={{ marginTop: "1.5rem", padding: "0.5rem 1rem" }}
            onClick={() => setEditing(true)}
          >
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
