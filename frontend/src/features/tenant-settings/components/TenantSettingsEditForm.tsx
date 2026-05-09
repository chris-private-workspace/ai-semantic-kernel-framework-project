/**
 * File: frontend/src/features/tenant-settings/components/TenantSettingsEditForm.tsx
 * Purpose: Edit form for tenant settings — TanStack-driven mutation.
 * Category: Frontend / tenant-settings / components
 * Scope: Phase 57 / Sprint 57.3 US-4 → Sprint 57.9 US-6 Day 4 (TanStack mutation)
 *
 * Description:
 *   Two editable fields per US-2 backend PATCH scope:
 *   - display_name: text input (1-256 chars validation)
 *   - meta_data: JSON textarea (parse + validate on blur)
 *
 *   Plan + state + code are read-only (per backend 57.3 D8).
 *
 *   Sprint 57.9 US-6 Day 4: replaced store.save / saving / saveError with
 *   `useTenantSettingsSave` mutation hook. On success, the hook invalidates
 *   `TENANT_SETTINGS_QUERY_KEY_BASE` and the parent View re-renders with the
 *   fresh server state via TanStack auto-refetch; this component then calls
 *   `onDone()` to switch back to View mode.
 *
 *   API change: NEW required `tenantId` prop (parent passes the URL-resolved
 *   tenant id; mutation hook signature uses `{ tenantId, payload }`).
 *
 * Created: 2026-05-07 (Sprint 57.3 Day 3)
 * Last Modified: 2026-05-09
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Sprint 57.9 US-6 Day 4 — drop store.save → useTenantSettingsSave mutation; NEW tenantId prop
 *   - 2026-05-07: Initial creation (Sprint 57.3 Day 3)
 */

import { useState } from "react";

import { useTenantSettingsSave } from "../hooks/useTenantSettingsSave";
import type { TenantSettingsResponse, TenantUpdateRequest } from "../types";

interface Props {
  tenantId: string;
  initialData: TenantSettingsResponse;
  onDone: () => void;
}

export function TenantSettingsEditForm({ tenantId, initialData, onDone }: Props) {
  const saveM = useTenantSettingsSave();
  const [displayName, setDisplayName] = useState(initialData.display_name);
  const [metaDataText, setMetaDataText] = useState(JSON.stringify(initialData.meta_data, null, 2));
  const [jsonError, setJsonError] = useState<string | null>(null);

  function validateJson(text: string) {
    try {
      const parsed = JSON.parse(text);
      if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
        setJsonError("meta_data must be a JSON object");
        return null;
      }
      setJsonError(null);
      return parsed as Record<string, unknown>;
    } catch (err) {
      setJsonError(`Invalid JSON: ${(err as Error).message}`);
      return null;
    }
  }

  const displayNameInvalid = displayName.length === 0 || displayName.length > 256;
  const saving = saveM.isPending;
  const canSave = !saving && !jsonError && !displayNameInvalid;

  function handleSubmit() {
    const parsed = validateJson(metaDataText);
    if (parsed === null || displayNameInvalid) return;

    const payload: TenantUpdateRequest = {};
    if (displayName !== initialData.display_name) payload.display_name = displayName;
    if (JSON.stringify(parsed) !== JSON.stringify(initialData.meta_data)) {
      payload.meta_data = parsed;
    }
    saveM.mutate({ tenantId, payload }, { onSuccess: onDone });
  }

  return (
    <div style={{ marginTop: "1.5rem", padding: "1.5rem", border: "1px solid #ccc" }}>
      <h2>Edit Tenant Settings</h2>

      <div style={{ marginTop: "1rem" }}>
        <label style={{ display: "block", fontWeight: 600 }}>
          Display Name (1-256 chars)
        </label>
        <input
          type="text"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          maxLength={256}
          style={{ width: "100%", padding: "0.4rem", marginTop: "0.25rem" }}
        />
        {displayNameInvalid && (
          <p style={{ color: "#a00", fontSize: "0.85rem", marginTop: "0.25rem" }}>
            {displayName.length === 0 ? "Display name cannot be empty" : "Display name too long"}
          </p>
        )}
      </div>

      <div style={{ marginTop: "1rem" }}>
        <label style={{ display: "block", fontWeight: 600 }}>
          Meta Data (JSON object)
        </label>
        <textarea
          value={metaDataText}
          onChange={(e) => setMetaDataText(e.target.value)}
          onBlur={(e) => validateJson(e.target.value)}
          rows={8}
          style={{
            width: "100%",
            padding: "0.4rem",
            marginTop: "0.25rem",
            fontFamily: "monospace",
            fontSize: "0.85rem",
          }}
        />
        {jsonError && (
          <p style={{ color: "#a00", fontSize: "0.85rem", marginTop: "0.25rem" }}>{jsonError}</p>
        )}
      </div>

      {saveM.error && (
        <p style={{ color: "#a00", marginTop: "1rem" }}>Save failed: {saveM.error.message}</p>
      )}

      <div style={{ marginTop: "1.5rem", display: "flex", gap: "0.75rem" }}>
        <button onClick={handleSubmit} disabled={!canSave} style={{ padding: "0.5rem 1rem" }}>
          {saving ? "Saving…" : "Save"}
        </button>
        <button onClick={onDone} disabled={saving} style={{ padding: "0.5rem 1rem" }}>
          Cancel
        </button>
      </div>
    </div>
  );
}
