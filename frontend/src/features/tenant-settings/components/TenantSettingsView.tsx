/**
 * File: frontend/src/features/tenant-settings/components/TenantSettingsView.tsx
 * Purpose: Read-only view of tenant settings — top-level container for /tenant-settings/{id}.
 * Category: Frontend / tenant-settings / components
 * Scope: Phase 57 / Sprint 57.3 US-4
 *
 * Description:
 *   Reads tenant_id from URL query string `?tenant_id=...` for now (admin-driven
 *   per 57.1 v2 D8 — backend enforces require_admin_platform_role). Auto-loads
 *   on mount. Edit toggle button switches to TenantSettingsEditForm. Loading
 *   skeleton + error retry UX. State + Plan rendered as colored badges.
 *
 * Created: 2026-05-07 (Sprint 57.3 Day 3)
 * Last Modified: 2026-05-07
 *
 * Modification History:
 *   - 2026-05-07: Initial creation (Sprint 57.3 Day 3 / US-4 — Tenant Settings View)
 */

import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { useTenantSettingsStore } from "../store/tenantSettingsStore";
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
  const [searchParams] = useSearchParams();
  const urlTenantId = searchParams.get("tenant_id") ?? "";

  const { tenantId, data, loading, error, setTenantId, loadData } = useTenantSettingsStore();
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    if (urlTenantId && urlTenantId !== tenantId) {
      setTenantId(urlTenantId);
    }
  }, [urlTenantId, tenantId, setTenantId]);

  useEffect(() => {
    if (tenantId) {
      void loadData();
    }
  }, [tenantId, loadData]);

  return (
    <div style={{ padding: "2rem", fontFamily: "system-ui, sans-serif" }}>
      <h1>Tenant Settings</h1>
      <p style={{ color: "#666", fontSize: "0.9rem" }}>
        Per-tenant configuration. Backend enforces admin-platform role
        (Sprint 57.3 endpoints). 401/403 surfaces as error below.
      </p>

      {!urlTenantId && (
        <p style={{ color: "#a00" }}>
          Missing <code>?tenant_id=...</code> query parameter.
        </p>
      )}

      {loading && <p style={{ fontStyle: "italic" }}>Loading tenant settings…</p>}

      {error && (
        <div style={{ marginTop: "1rem", padding: "1rem", border: "1px solid #a00", color: "#a00" }}>
          <p>Error: {error}</p>
          <button onClick={() => void loadData()}>Retry</button>
        </div>
      )}

      {data && !loading && !error && !editing && (
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
        <TenantSettingsEditForm initialData={data} onDone={() => setEditing(false)} />
      )}
    </div>
  );
}
