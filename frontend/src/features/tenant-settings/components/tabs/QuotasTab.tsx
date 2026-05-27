/**
 * File: frontend/src/features/tenant-settings/components/tabs/QuotasTab.tsx
 * Purpose: Quotas tab — Usage quotas (edit mode) + Rate limits (edit mode Sprint 57.57).
 * Category: Frontend / tenant-settings / components / tabs
 * Scope: Phase 57 / Sprint 57.57 Track B (Rate limits edit mode + useRateLimitsSave wiring)
 *
 * Description:
 *   Read side: useQuotas(tenantId) + useRateLimits(tenantId) (Sprint 57.49).
 *
 *   Write side — Usage quotas (Sprint 57.56): Edit button toggles edit mode;
 *   per-row numeric input + "Clear override" mutate draft Record<string,number>.
 *   Save invokes useQuotasSave → PUT /admin/tenants/{id}/quotas.
 *
 *   Write side — Rate limits (Sprint 57.57): Edit button toggles edit mode;
 *   per-row two text inputs (label + value) + add-row + remove-row mutate
 *   draft RateLimitItem[] (variable-length list). Empty list save allowed
 *   (composite-clear → backend falls back to DEFAULT_RATE_LIMITS). Save
 *   invokes useRateLimitsSave → PUT /admin/tenants/{id}/rate-limits.
 *
 *   SCOPE GUARD: Sprint 57.56 Usage quotas Card edit mode preserved bit-for-bit
 *   intact; Sprint 57.57 only ADDS Rate limits Card edit mode (no Usage Card
 *   modifications). Verified via scope-guard assertion test.
 *
 * Created: 2026-05-26 (Sprint 57.44 Day 1) — original fixture port
 * Last Modified: 2026-05-27
 *
 * Modification History (newest-first):
 *   - 2026-05-27: Sprint 57.57 Track B — +Rate limits Card edit mode (Usage Card unchanged)
 *   - 2026-05-27: Sprint 57.56 Track B — +Usage quotas Card edit mode (Rate limits Card unchanged)
 *   - 2026-05-26: Sprint 57.49 — fixture → useQuotas + useRateLimits real backend (Sprint 57.48 Track C+D)
 *   - 2026-05-26: Initial creation (Sprint 57.44 Day 1)
 *
 * Related:
 *   - backend/src/api/v1/admin/tenants.py (RateLimitsUpsertRequest / upsert_tenant_rate_limits)
 *   - ../../hooks/useQuotas.ts + useQuotasSave.ts (Usage quotas read/write)
 *   - ../../hooks/useRateLimits.ts + useRateLimitsSave.ts (Rate limits read/write)
 */

import { useEffect, useState } from "react";

import { Button, Card } from "../../../../components/mockup-ui";
import { BackendGapBanner } from "../../../../components/ui/BackendGapBanner";
import { useQuotas } from "../../hooks/useQuotas";
import { useQuotasSave } from "../../hooks/useQuotasSave";
import { useRateLimits } from "../../hooks/useRateLimits";
import { useRateLimitsSave } from "../../hooks/useRateLimitsSave";
import type { QuotaItem, RateLimitItem } from "../../types";

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
  const rlSaveMutation = useRateLimitsSave(tenantId);

  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<Record<string, number>>({});

  // Sprint 57.57 — Rate limits Card edit mode state
  const [rlEditing, setRlEditing] = useState(false);
  const [rlDraft, setRlDraft] = useState<RateLimitItem[]>([]);

  // Reset on tenant switch
  useEffect(() => {
    setEditing(false);
    setDraft({});
    setRlEditing(false);
    setRlDraft([]);
    saveMutation.reset();
    rlSaveMutation.reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps -- mutation reset on tenant switch only
  }, [tenantId]);

  // Auto-exit edit mode after successful save (Usage Card)
  useEffect(() => {
    if (saveMutation.isSuccess && editing) {
      setEditing(false);
      setDraft({});
    }
  }, [saveMutation.isSuccess, editing]);

  // Auto-exit edit mode after successful save (Rate limits Card)
  useEffect(() => {
    if (rlSaveMutation.isSuccess && rlEditing) {
      setRlEditing(false);
      setRlDraft([]);
    }
  }, [rlSaveMutation.isSuccess, rlEditing]);

  const items = quotas.data?.items ?? [];
  const rlItems = rateLimits.data?.items ?? [];

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

  // Sprint 57.57 — Rate limits Card handlers
  const handleRlEdit = (): void => {
    setRlDraft(rlItems.map((r) => ({ label: r.label, value: r.value })));
    setRlEditing(true);
    rlSaveMutation.reset();
  };

  const handleRlCancel = (): void => {
    setRlDraft([]);
    setRlEditing(false);
    rlSaveMutation.reset();
  };

  const handleRlSave = (): void => {
    rlSaveMutation.mutate({ items: rlDraft });
  };

  const updateRlRow = (index: number, field: "label" | "value", value: string): void => {
    setRlDraft((d) => d.map((row, i) => (i === index ? { ...row, [field]: value } : row)));
  };

  const removeRlRow = (index: number): void => {
    setRlDraft((d) => d.filter((_, i) => i !== index));
  };

  const addRlRow = (): void => {
    setRlDraft((d) => [...d, { label: "", value: "" }]);
  };

  // Sprint 57.57 — handleRequestIncrease removed (replaced by Edit button on Rate limits Card)

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
        <BackendGapBanner reason="Rate limit syntax validation + per-rule live usage tracking: backend extension Phase 58+ — items are now editable via Edit button" />

        {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: row flex gap */}
        <div className="row" style={{ gap: 8, marginBottom: 12, justifyContent: "flex-end" }}>
          {!rlEditing ? (
            <button
              type="button"
              className="btn-secondary"
              onClick={handleRlEdit}
              disabled={rateLimits.isLoading}
              data-testid="ratelimits-edit-btn"
            >
              Edit
            </button>
          ) : (
            <>
              <button
                type="button"
                className="btn-secondary"
                onClick={handleRlCancel}
                disabled={rlSaveMutation.isPending}
                data-testid="ratelimits-cancel-btn"
              >
                Cancel
              </button>
              <button
                type="button"
                className="btn-primary"
                onClick={handleRlSave}
                disabled={rlSaveMutation.isPending}
                data-testid="ratelimits-save-btn"
              >
                {rlSaveMutation.isPending ? "Saving…" : "Save"}
              </button>
            </>
          )}
        </div>

        {rlSaveMutation.error ? (
          // eslint-disable-next-line no-restricted-syntax -- inline-style error hint
          <p style={{ color: "var(--danger)", fontSize: 12, marginBottom: 8 }} data-testid="ratelimits-save-error">
            Save failed: {rlSaveMutation.error.message}
          </p>
        ) : null}

        {rateLimits.isLoading ? (
          <p className="muted">Loading rate limits…</p>
        ) : rateLimits.error ? (
          // eslint-disable-next-line no-restricted-syntax -- inline-style error hint
          <p style={{ color: "var(--danger)", fontSize: 12 }}>
            Error loading rate limits: {rateLimits.error.message}
          </p>
        ) : rlEditing ? (
          // eslint-disable-next-line no-restricted-syntax -- verbatim port: col gap edit mode
          <div className="col" style={{ gap: 10, fontSize: 12 }}>
            {rlDraft.length === 0 ? (
              <p className="muted" data-testid="ratelimits-empty-draft">
                No rate limit rows. Save with empty list to clear all overrides.
              </p>
            ) : (
              rlDraft.map((row, index) => (
                // eslint-disable-next-line no-restricted-syntax -- verbatim port: row gap
                <div key={index} className="row" style={{ gap: 6, alignItems: "center" }}>
                  <input
                    type="text"
                    value={row.label}
                    placeholder="Label"
                    onChange={(e) => updateRlRow(index, "label", e.target.value)}
                    // eslint-disable-next-line no-restricted-syntax -- verbatim port: input sizing
                    style={{ width: 180, fontSize: 12, padding: "2px 6px" }}
                    data-testid={`ratelimits-label-input-${index}`}
                    aria-label={`Rate limit row ${index + 1} label`}
                  />
                  <input
                    type="text"
                    value={row.value}
                    placeholder="Value"
                    onChange={(e) => updateRlRow(index, "value", e.target.value)}
                    // eslint-disable-next-line no-restricted-syntax -- verbatim port: input sizing
                    style={{ width: 160, fontSize: 12, padding: "2px 6px" }}
                    data-testid={`ratelimits-value-input-${index}`}
                    aria-label={`Rate limit row ${index + 1} value`}
                  />
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => removeRlRow(index)}
                    // eslint-disable-next-line no-restricted-syntax -- verbatim port: remove-btn sizing
                    style={{ fontSize: 11, padding: "2px 8px" }}
                    data-testid={`ratelimits-remove-${index}`}
                    aria-label={`Remove rate limit row ${index + 1}`}
                  >
                    ×
                  </button>
                </div>
              ))
            )}
            <Button variant="outline" size="sm" onClick={addRlRow} data-testid="ratelimits-add-row-btn">
              + Add row
            </Button>
          </div>
        ) : (
          // eslint-disable-next-line no-restricted-syntax -- verbatim port: col gap + fontSize
          <div className="col" style={{ gap: 10, fontSize: 12 }}>
            {rlItems.map((r) => (
              <div key={r.label} className="spread">
                <span className="muted">{r.label}</span>
                <span className="mono">{r.value}</span>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
