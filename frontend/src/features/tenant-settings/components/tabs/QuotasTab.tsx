/**
 * File: frontend/src/features/tenant-settings/components/tabs/QuotasTab.tsx
 * Purpose: Quotas tab — 2-col grid w/ Usage quotas (5 bar-track rows) + Rate limits (3 .spread rows + AP-2 stub).
 * Category: Frontend / tenant-settings / components / tabs
 * Scope: Phase 57 / Sprint 57.44 Day 1 (mockup-fidelity rebuild — D-DAY0-4 Option A)
 *
 * Description:
 *   Verbatim port of mockup `page-admin.jsx` L507-540. Two Cards in `.grid-main`:
 *   - Usage quotas: 5 rows (Tokens/month / Runs/day / Subagents concurrent /
 *     Memory entries / Audit storage) each w/ used/max + bar-track width: pct%.
 *   - Rate limits: 3 .spread rows (API requests / Tool calls / SSE connections)
 *     + Request increase Button (AP-2 stub).
 *
 *   All values fixture pending Phase 58+ backend quota endpoint.
 *
 * Created: 2026-05-26 (Sprint 57.44 Day 1)
 * Last Modified: 2026-05-26
 *
 * Modification History (newest-first):
 *   - 2026-05-26: Initial creation (Sprint 57.44 Day 1) — tenant-settings full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx L507-540
 *   - ../../_fixtures.ts (QUOTAS + RATE_LIMITS)
 */

import { Button, Card } from "../../../../components/mockup-ui";
import { BackendGapBanner } from "../../../../components/ui/BackendGapBanner";
import { QUOTAS, RATE_LIMITS } from "../../_fixtures";

export function QuotasTab(): JSX.Element {
  const handleRequestIncrease = (): void => {
    window.alert("Request increase: backend gap (Phase 58+) — rate limit increase request endpoint pending");
  };

  return (
    <div className="grid-main">
      <Card title="Usage quotas">
        <BackendGapBanner reason="Usage quotas: backend extension Phase 58+ — values shown are mockup defaults" />
        {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: col gap */}
        <div className="col" style={{ gap: 14, marginTop: 8 }}>
          {QUOTAS.map((q) => (
            <div key={q.k}>
              {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: spread marginBottom */}
              <div className="spread" style={{ marginBottom: 4 }}>
                {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: fontSize */}
                <span style={{ fontSize: 12.5 }}>{q.k}</span>
                {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: mono fontSize */}
                <span className="mono tnum" style={{ fontSize: 11.5 }}>
                  {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: fg color */}
                  <span style={{ color: "var(--fg)" }}>{q.used.toLocaleString()}</span>{q.unit}
                  <span className="subtle"> / {q.max.toLocaleString()}{q.unit}</span>
                </span>
              </div>
              <div className="bar-track">
                {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: width pct */}
                <span style={{ width: q.pct + "%" }} />
              </div>
            </div>
          ))}
        </div>
      </Card>
      <Card title="Rate limits">
        {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: col gap + fontSize */}
        <div className="col" style={{ gap: 10, fontSize: 12 }}>
          {RATE_LIMITS.map((r) => (
            <div key={r.label} className="spread">
              <span className="muted">{r.label}</span>
              <span className="mono">{r.value}</span>
            </div>
          ))}
          <Button variant="outline" size="sm" onClick={handleRequestIncrease}>
            Request increase
          </Button>
        </div>
      </Card>
    </div>
  );
}
