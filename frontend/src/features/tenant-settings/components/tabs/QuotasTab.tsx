/**
 * File: frontend/src/features/tenant-settings/components/tabs/QuotasTab.tsx
 * Purpose: Quotas tab — Usage quotas (edit mode) + Rate limits (read-only Sprint 57.57 candidate).
 * Category: Frontend / tenant-settings / components / tabs
 * Scope: Phase 57 / Sprint 57.56 Track B (edit mode + useQuotasSave wiring)
 *
 * Description:
 *   Read side: useQuotas(tenantId) + useRateLimits(tenantId) (Sprint 57.49).
 *   Write side (Sprint 57.56): Edit button on Usage quotas Card toggles edit
 *   mode; per-row numeric input + "Clear override" button mutate the draft
 *   Record<string, number>. Save invokes useQuotasSave mutation → PUT
 *   /admin/tenants/{id}/quotas (composite-replace) → query invalidation
 *   refreshes the table.
 *
 *   Reverse-projection on Edit: draft seeded from current items[].limit. User
 *   can then modify values or Clear override (delete key from draft).
 *
 *   SCOPE GUARD: Rate limits Card UNCHANGED this sprint (Sprint 57.57 candidate
 *   for write-side). Only Usage quotas Card gets edit mode.
 *
 *   AP-2 BackendGapBanner copy updated: current_usage Redis counter exposure
 *   still Phase 58+; limits are now editable via Edit button.
 *
 * Created: 2026-05-26 (Sprint 57.44 Day 1) — original fixture port
 * Last Modified: 2026-05-27
 *
 * Modification History (newest-first):
 *   - 2026-05-27: Sprint 57.56 Track B — +Usage quotas Card edit mode (Rate limits Card unchanged)
 *   - 2026-05-26: Sprint 57.49 — fixture → useQuotas + useRateLimits real backend (Sprint 57.48 Track C+D)
 *   - 2026-05-26: Initial creation (Sprint 57.44 Day 1)
 *
 * Related:
 *   - backend/src/api/v1/admin/tenants.py (QuotaOverridesUpsertRequest / put_tenant_quota_overrides)
 *   - ../../hooks/useQuotas.ts (read TanStack consumer)
 *   - ../../hooks/useQuotasSave.ts (write TanStack consumer)
 */

import { useEffect, useState } from "react";

import { Button, Card } from "../../../../components/mockup-ui";
import { BackendGapBanner } from "../../../../components/ui/BackendGapBanner";
import { useQuotas } from "../../hooks/useQuotas";
import { useQuotasSave } from "../../hooks/useQuotasSave";
import { useRateLimits } from "../../hooks/useRateLimits";
import type { QuotaItem } from "../../types";

export interface QuotasTabProps {
  tenantId: string;
}

function formatLimit(limit: number, unit: string): string {
  // Tokens are usually large numbers; format M / k for readability
  if (unit === "tokens" && limit >= 1_000_000) {
    return `${(limit / 1_000_000).toFixed(1)}M`;
  }
  if (limit >= 1_000) {
    return limit.toLocaleString();
  }
  return String(limit);
}

/**
 * Reverse-project: seed draft from items[].limit (all rows enter draft on Edit).
 *
 * User can then modify values or Clear override to remove key from draft.
 * Resources NOT in draft on Save → composite-replace clears any prior override.
 */
function draftFromItems(items: ReadonlyArray<QuotaItem>): Record<string, number> {
  const draft: Record<string, number> = {};
  for (const item of items) {
    draft[item.resource] = item.limit;
  }
  return draft;
}

export function QuotasTab({ tenantId }: QuotasTabProps): JSX.Element {
  const quotas = useQuotas(tenantId);
  const rateLimits = useRateLimits(tenantId);
  const saveMutation = useQuotasSave(tenantId);

  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<Record<string, number>>({});

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

  const items = quotas.data?.items ?? [];

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

  const updateDraft = (resource: string, value: number): void => {
    setDraft((d) => ({ ...d, [resource]: value }));
  };

  const clearOverride = (resource: string): void => {
    setDraft((d) => {
      const next = { ...d };
      delete next[resource];
      return next;
    });
  };

  const handleRequestIncrease = (): void => {
    window.alert("Request increase: backend gap (Phase 58+) — rate limit increase request endpoint pending");
  };

  return (
    <div className="grid-main">
      <Card title="Usage quotas">
        <BackendGapBanner reason="Live usage tracking (current_usage Redis counter exposure): backend extension Phase 58+ — limits shown are tenant-effective + editable via Edit button" />

        {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: row flex gap */}
        <div className="row" style={{ gap: 8, marginBottom: 12, justifyContent: "flex-end" }}>
          {!editing ? (
            <button
              type="button"
              className="btn-secondary"
              onClick={handleEdit}
              disabled={items.length === 0 || quotas.isLoading}
              data-testid="quotas-edit-btn"
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
                data-testid="quotas-cancel-btn"
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn-primary"
                onClick={handleSave}
                disabled={saveMutation.isPending}
                data-testid="quotas-save-btn"
              >
                {saveMutation.isPending ? "Saving…" : "Save"}
              </button>
            </>
          )}
        </div>

        {saveMutation.error ? (
          // eslint-disable-next-line no-restricted-syntax -- inline-style error hint
          <p style={{ color: "var(--danger)", fontSize: 12, marginBottom: 8 }} data-testid="quotas-save-error">
            Save failed: {saveMutation.error.message}
          </p>
        ) : null}

        {quotas.isLoading ? (
          <p className="muted">Loading quotas…</p>
        ) : quotas.error ? (
          // eslint-disable-next-line no-restricted-syntax -- inline-style error hint
          <p style={{ color: "var(--danger)", fontSize: 12 }}>
            Error loading quotas: {quotas.error.message}
          </p>
        ) : items.length === 0 ? (
          <p className="muted">No quotas configured for this tenant plan.</p>
        ) : (
          // eslint-disable-next-line no-restricted-syntax -- verbatim port: col gap
          <div className="col" style={{ gap: 14, marginTop: 8 }}>
            {items.map((q) => {
              const used = q.current_usage ?? 0;
              const inDraft = q.resource in draft;
              const effectiveLimit = editing && inDraft ? draft[q.resource] : q.limit;
              const pct = effectiveLimit > 0 ? Math.round((used / effectiveLimit) * 100) : 0;
              return (
                <div key={q.resource}>
                  {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: spread marginBottom */}
                  <div className="spread" style={{ marginBottom: 4 }}>
                    {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: fontSize */}
                    <span style={{ fontSize: 12.5 }}>{q.resource}</span>
                    {editing ? (
                      // eslint-disable-next-line no-restricted-syntax -- verbatim port: row gap
                      <span className="row" style={{ gap: 6, alignItems: "center" }}>
                        <input
                          type="number"
                          value={inDraft ? draft[q.resource] : ""}
                          placeholder={String(q.limit)}
                          onChange={(e) => updateDraft(q.resource, Number(e.target.value))}
                          // eslint-disable-next-line no-restricted-syntax -- verbatim port: input sizing
                          style={{ width: 120, fontSize: 12, padding: "2px 6px" }}
                          data-testid={`quotas-input-${q.resource}`}
                          aria-label={`Override limit for ${q.resource}`}
                        />
                        {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: unit label fontSize */}
                        <span className="subtle" style={{ fontSize: 11.5 }}>{q.unit}</span>
                        {inDraft ? (
                          <button
                            type="button"
                            className="btn-secondary"
                            onClick={() => clearOverride(q.resource)}
                            // eslint-disable-next-line no-restricted-syntax -- verbatim port: clear-btn sizing
                            style={{ fontSize: 11, padding: "2px 6px" }}
                            data-testid={`quotas-clear-${q.resource}`}
                          >
                            Clear override
                          </button>
                        ) : null}
                      </span>
                    ) : (
                      // eslint-disable-next-line no-restricted-syntax -- verbatim port: mono fontSize
                      <span className="mono tnum" style={{ fontSize: 11.5 }}>
                        {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: fg color */}
                        <span style={{ color: "var(--fg)" }}>{formatLimit(used, q.unit)}</span>{q.unit ? ` ${q.unit}` : ""}
                        <span className="subtle"> / {formatLimit(q.limit, q.unit)}{q.unit ? ` ${q.unit}` : ""}</span>
                      </span>
                    )}
                  </div>
                  {!editing ? (
                    <div className="bar-track">
                      {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: width pct */}
                      <span style={{ width: pct + "%" }} />
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        )}
      </Card>
      <Card title="Rate limits">
        {rateLimits.isLoading ? (
          <p className="muted">Loading rate limits…</p>
        ) : rateLimits.error ? (
          // eslint-disable-next-line no-restricted-syntax -- inline-style error hint
          <p style={{ color: "var(--danger)", fontSize: 12 }}>
            Error loading rate limits: {rateLimits.error.message}
          </p>
        ) : (
          // eslint-disable-next-line no-restricted-syntax -- verbatim port: col gap + fontSize
          <div className="col" style={{ gap: 10, fontSize: 12 }}>
            {(rateLimits.data?.items ?? []).map((r) => (
              <div key={r.label} className="spread">
                <span className="muted">{r.label}</span>
                <span className="mono">{r.value}</span>
              </div>
            ))}
            <Button variant="outline" size="sm" onClick={handleRequestIncrease}>
              Request increase
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
}
