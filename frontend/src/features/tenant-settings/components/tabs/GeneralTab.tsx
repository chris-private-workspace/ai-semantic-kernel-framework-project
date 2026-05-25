/**
 * File: frontend/src/features/tenant-settings/components/tabs/GeneralTab.tsx
 * Purpose: General tab — 2-col grid w/ General Card (display_name live + 4 fixture fields) + Identity & SSO Card.
 * Category: Frontend / tenant-settings / components / tabs
 * Scope: Phase 57 / Sprint 57.44 Day 1 (mockup-fidelity rebuild — D-DAY0-4 Option A)
 *
 * Description:
 *   Verbatim port of mockup `page-admin.jsx` L440-465. Two Cards in `.grid-main`:
 *   - General: 5 fields. ONLY `display_name` is live-wired to backend via
 *     useTenantSettingsSave (PATCH). Other 4 fields (Tenant id readonly, Default
 *     region, Default locale, Data retention) display GENERAL_FIXTURE values
 *     with disabled controls + BackendGapBanner above.
 *   - Identity & SSO: 4 .spread rows from IDENTITY_FIXTURE + Configure button
 *     (AP-2 stub) + BackendGapBanner above.
 *
 *   The Save button only saves display_name (the only backend-supported PATCH
 *   field). Save state managed locally — input controlled state diverges from
 *   data.display_name only after user edits; resets on successful save via
 *   useTenantSettings query invalidation.
 *
 * Created: 2026-05-26 (Sprint 57.44 Day 1)
 * Last Modified: 2026-05-26
 *
 * Modification History (newest-first):
 *   - 2026-05-26: Initial creation (Sprint 57.44 Day 1) — tenant-settings full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx L440-465
 *   - ../../hooks/useTenantSettingsSave.ts (display_name PATCH)
 *   - ../../_fixtures.ts (GENERAL_FIXTURE + IDENTITY_FIXTURE)
 *   - frontend/src/components/ui/BackendGapBanner.tsx
 */

import { useEffect, useState } from "react";

import { Badge, Button, Card, Field } from "../../../../components/mockup-ui";
import { BackendGapBanner } from "../../../../components/ui/BackendGapBanner";
import { GENERAL_FIXTURE, IDENTITY_FIXTURE } from "../../_fixtures";
import { useTenantSettingsSave } from "../../hooks/useTenantSettingsSave";
import type { TenantSettingsResponse } from "../../types";

export interface GeneralTabProps {
  data: TenantSettingsResponse;
}

export function GeneralTab({ data }: GeneralTabProps): JSX.Element {
  const [displayName, setDisplayName] = useState<string>(data.display_name);
  const { mutate: save, isPending, error } = useTenantSettingsSave();

  // Reset local edit state when backend data refreshes (post-save invalidation).
  useEffect(() => {
    setDisplayName(data.display_name);
  }, [data.display_name]);

  const dirty = displayName !== data.display_name;

  const handleSave = (): void => {
    if (!dirty) return;
    save({ tenantId: data.id, payload: { display_name: displayName } });
  };

  const handleConfigureSso = (): void => {
    window.alert("Configure SSO: backend gap (Phase 58+) — SSO admin endpoint pending");
  };

  return (
    <div className="grid-main">
      <Card title="General">
        {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: mockup uses inline style for col gap + maxWidth */}
        <div className="col" style={{ gap: 14, maxWidth: 480 }}>
          <Field label="Display name">
            <input
              className="input"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              disabled={isPending}
            />
            {dirty && (
              // eslint-disable-next-line no-restricted-syntax -- inline-style row gap mirrors mockup .row pattern
              <div className="row" style={{ gap: 8, marginTop: 8 }}>
                <Button variant="primary" size="sm" onClick={handleSave} disabled={isPending}>
                  {isPending ? "Saving…" : "Save"}
                </Button>
                <Button variant="outline" size="sm" onClick={() => setDisplayName(data.display_name)} disabled={isPending}>
                  Cancel
                </Button>
              </div>
            )}
            {error && (
              // eslint-disable-next-line no-restricted-syntax -- inline-style minor error hint
              <div style={{ color: "var(--danger)", fontSize: 11.5, marginTop: 6 }}>
                Save failed: {error.message}
              </div>
            )}
          </Field>
          <Field label="Tenant id">
            <input className="input mono" readOnly value={data.code} />
          </Field>
          <BackendGapBanner reason="Region / locale / retention configuration: backend extension Phase 58+ — values shown are mockup defaults" />
          <Field label="Default region">
            <select className="select" value={GENERAL_FIXTURE.region} disabled>
              <option>ap-east-1</option>
              <option>us-east-1</option>
              <option>eu-west-1</option>
            </select>
          </Field>
          <Field label="Default locale">
            <select className="select" value={GENERAL_FIXTURE.locale} disabled>
              <option>zh-TW</option>
              <option>en-US</option>
              <option>ja-JP</option>
            </select>
          </Field>
          <Field label="Data retention" help="Memory + audit retention. WORM audit is append-only.">
            {/* eslint-disable-next-line no-restricted-syntax -- verbatim port row gap */}
            <div className="row" style={{ gap: 8 }}>
              <input
                className="input"
                value={GENERAL_FIXTURE.retentionDays}
                disabled
                // eslint-disable-next-line no-restricted-syntax -- verbatim port input maxWidth
                style={{ maxWidth: 100 }}
              />
              <span className="muted">days</span>
            </div>
          </Field>
        </div>
      </Card>
      <Card title="Identity & SSO">
        <BackendGapBanner reason="Identity / SSO / SCIM configuration: backend extension Phase 58+ — values shown are mockup defaults" />
        {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: mockup uses inline style for col gap + fontSize */}
        <div className="col" style={{ gap: 10, fontSize: 12, marginTop: 8 }}>
          <div className="spread">
            <span className="muted">Provider</span>
            <Badge>{IDENTITY_FIXTURE.provider}</Badge>
          </div>
          <div className="spread">
            <span className="muted">SCIM</span>
            <Badge tone="success" dot>{IDENTITY_FIXTURE.scim}</Badge>
          </div>
          <div className="spread">
            <span className="muted">Allowed domains</span>
            <span className="mono">{IDENTITY_FIXTURE.allowedDomains}</span>
          </div>
          <div className="spread">
            <span className="muted">MFA</span>
            <Badge tone="success" dot>{IDENTITY_FIXTURE.mfa}</Badge>
          </div>
          <Button variant="outline" size="sm" icon="settings" onClick={handleConfigureSso}>
            Configure
          </Button>
        </div>
      </Card>
    </div>
  );
}
