/**
 * File: frontend/src/features/tenant-settings/components/tabs/FeatureFlagsTab.tsx
 * Purpose: Feature flags tab — table of tenant-scoped flag overrides + edit mode (real backend persistence).
 * Category: Frontend / tenant-settings / components / tabs
 * Scope: Phase 57 / Sprint 57.55 Track B (edit mode + useFeatureFlagsSave wiring)
 *
 * Description:
 *   Read side: useFeatureFlags(tenantId) → projected items list (Sprint 57.49).
 *   Write side (Sprint 57.55): Edit button toggles edit mode; per-row Switch +
 *   "Clear override" button mutate the draft Record<string, boolean>. Save
 *   invokes useFeatureFlagsSave mutation → PUT /admin/tenants/{id}/feature-flags
 *   (composite-replace: flags omitted from payload but with prior tenant
 *   override → auto-cleared) → query invalidation refreshes the table.
 *
 *   Reverse-projection on Edit: draft seeded from items.filter(overridden).
 *   Flags NOT in draft → composite-replace clears any prior override on save.
 *
 *   AP-2 BackendGapBanner copy updated: numeric overrides + per-flag audit log
 *   filtering + registry CRUD remain Phase 58+; booleans now editable.
 *
 * Created: 2026-05-26 (Sprint 57.44 Day 1) — original fixture port
 * Last Modified: 2026-05-27
 *
 * Modification History (newest-first):
 *   - 2026-05-27: Sprint 57.55 Track B — add edit mode (Save/Cancel/per-row Switch + clear override)
 *   - 2026-05-26: Sprint 57.49 — fixture → useFeatureFlags real backend (Sprint 57.48 Track B)
 *   - 2026-05-26: Initial creation (Sprint 57.44 Day 1)
 *
 * Related:
 *   - backend/src/api/v1/admin/tenants.py (FeatureFlagOverridesUpsertRequest / put_tenant_feature_flag_overrides)
 *   - ../../hooks/useFeatureFlags.ts (read TanStack consumer)
 *   - ../../hooks/useFeatureFlagsSave.ts (write TanStack consumer)
 */

import { useEffect, useState } from "react";

import { Badge, Card, Switch } from "../../../../components/mockup-ui";
import { BackendGapBanner } from "../../../../components/ui/BackendGapBanner";
import { useFeatureFlags } from "../../hooks/useFeatureFlags";
import { useFeatureFlagsSave } from "../../hooks/useFeatureFlagsSave";
import type { FeatureFlagItem } from "../../types";

export interface FeatureFlagsTabProps {
  tenantId: string;
}

/**
 * Reverse-project: seed draft from explicitly-overridden items only.
 *
 * Flags NOT in draft on Save → composite-replace semantics auto-clear them.
 * Flags present in draft → tenant override value persisted.
 */
function draftFromItems(items: ReadonlyArray<FeatureFlagItem>): Record<string, boolean> {
  const draft: Record<string, boolean> = {};
  for (const item of items) {
    if (item.overridden) {
      draft[item.name] = item.value;
    }
  }
  return draft;
}

export function FeatureFlagsTab({ tenantId }: FeatureFlagsTabProps): JSX.Element {
  const { data, isLoading, error } = useFeatureFlags(tenantId);
  const saveMutation = useFeatureFlagsSave(tenantId);

  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<Record<string, boolean>>({});

  // Reset on tenant switch
  useEffect(() => {
    setEditing(false);
    setDraft({});
    saveMutation.reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mutation reset on tenant switch only
  }, [tenantId]);

  // Auto-exit edit mode after successful save
  useEffect(() => {
    if (saveMutation.isSuccess && editing) {
      setEditing(false);
      setDraft({});
    }
  }, [saveMutation.isSuccess, editing]);

  if (isLoading) {
    return (
      <Card title="Feature flags" subtitle="Tenant-scoped overrides">
        <p className="muted">Loading feature flags…</p>
      </Card>
    );
  }

  if (error) {
    return (
      <Card title="Feature flags" subtitle="Tenant-scoped overrides">
        {/* eslint-disable-next-line no-restricted-syntax -- inline-style error hint */}
        <p style={{ color: "var(--danger)", fontSize: 12 }}>
          Error loading feature flags: {error.message}
        </p>
      </Card>
    );
  }

  const items = data?.items ?? [];

  const handleEdit = (): void => {
    setDraft(draftFromItems(items));
    setEditing(true);
    saveMutation.reset();
  };

  const handleCancel = (): void => {
    setDraft({});
    setEditing(false);
    saveMutation.reset();
  };

  const handleSave = (): void => {
    saveMutation.mutate({ overrides: draft });
  };

  const toggleDraft = (name: string, currentValue: boolean): void => {
    setDraft((d) => ({ ...d, [name]: !currentValue }));
  };

  const clearOverride = (name: string): void => {
    setDraft((d) => {
      const next = { ...d };
      delete next[name];
      return next;
    });
  };

  return (
    <Card title="Feature flags" subtitle="Tenant-scoped overrides">
      <BackendGapBanner reason="Numeric flag overrides + per-flag audit log filtering + registry CRUD: backend extension Phase 58+ — booleans shown are tenant-effective + editable via Edit button" />

      {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: row flex gap */}
      <div className="row" style={{ gap: 8, marginBottom: 12, justifyContent: "flex-end" }}>
        {!editing ? (
          <button
            type="button"
            className="btn-secondary"
            onClick={handleEdit}
            disabled={items.length === 0}
            data-testid="ff-edit-btn"
          >
            Edit
          </button>
        ) : (
          <>
            <button
              type="button"
              className="btn-secondary"
              onClick={handleCancel}
              disabled={saveMutation.isPending}
              data-testid="ff-cancel-btn"
            >
              Cancel
            </button>
            <button
              type="button"
              className="btn-primary"
              onClick={handleSave}
              disabled={saveMutation.isPending}
              data-testid="ff-save-btn"
            >
              {saveMutation.isPending ? "Saving…" : "Save"}
            </button>
          </>
        )}
      </div>

      {saveMutation.error ? (
        // eslint-disable-next-line no-restricted-syntax -- inline-style error hint
        <p style={{ color: "var(--danger)", fontSize: 12, marginBottom: 8 }} data-testid="ff-save-error">
          Save failed: {saveMutation.error.message}
        </p>
      ) : null}

      {items.length === 0 ? (
        <p className="muted">No feature flags registered for this tenant.</p>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>Flag</th>
              <th>Description</th>
              <th>Default</th>
              <th>Tenant override</th>
            </tr>
          </thead>
          <tbody>
            {items.map((f) => {
              const inDraft = f.name in draft;
              const effectiveValue = editing && inDraft ? draft[f.name] : f.value;
              return (
                <tr key={f.name}>
                  {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: mono fontSize */}
                  <td className="mono" style={{ fontSize: 12 }}>{f.name}</td>
                  {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: subtle fontSize */}
                  <td className="subtle" style={{ fontSize: 12 }}>{f.description ?? "—"}</td>
                  <td><Badge>{f.default_enabled ? "on" : "off"}</Badge></td>
                  <td>
                    {editing ? (
                      // eslint-disable-next-line no-restricted-syntax -- verbatim port: row gap
                      <span className="row" style={{ gap: 6, alignItems: "center" }}>
                        <button
                          type="button"
                          onClick={() => toggleDraft(f.name, effectiveValue)}
                          // eslint-disable-next-line no-restricted-syntax -- verbatim port: switch button no-styling
                          style={{ background: "none", border: "none", padding: 0, cursor: "pointer" }}
                          data-testid={`ff-toggle-${f.name}`}
                          aria-label={`Toggle ${f.name}`}
                        >
                          <Switch on={effectiveValue} />
                        </button>
                        {inDraft ? (
                          <button
                            type="button"
                            className="btn-secondary"
                            onClick={() => clearOverride(f.name)}
                            // eslint-disable-next-line no-restricted-syntax -- verbatim port: clear-btn sizing
                            style={{ fontSize: 11, padding: "2px 6px" }}
                            data-testid={`ff-clear-${f.name}`}
                          >
                            Clear override
                          </button>
                        ) : null}
                      </span>
                    ) : (
                      <Switch on={f.value} />
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </Card>
  );
}
