/**
 * File: frontend/src/features/tenant-settings/components/tabs/HITLPoliciesTab.tsx
 * Purpose: HITL policies tab — table of 4 risk-tiered approval policies (mockup verbatim).
 * Category: Frontend / tenant-settings / components / tabs
 * Scope: Phase 57 / Sprint 57.44 Day 1 (mockup-fidelity rebuild — D-DAY0-4 Option A)
 *
 * Description:
 *   Verbatim port of mockup `page-admin.jsx` L542-568. Single Card with 5-col
 *   table (Risk tier / Default policy / SLA / Approvers / Off-platform). Risk
 *   tier renders `sev-dot sev-{level}` + capitalized label. Policy renders
 *   Badge w/ tone dispatch: auto=success, ask_once=info, default=warning.
 *
 * Created: 2026-05-26 (Sprint 57.44 Day 1)
 * Last Modified: 2026-05-26
 *
 * Modification History (newest-first):
 *   - 2026-05-26: Initial creation (Sprint 57.44 Day 1) — tenant-settings full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx L542-568
 *   - ../../_fixtures.ts (HITL_POLICIES)
 */

import { Badge, Card } from "../../../../components/mockup-ui";
import { BackendGapBanner } from "../../../../components/ui/BackendGapBanner";
import { HITL_POLICIES } from "../../_fixtures";

function policyTone(policy: "always_ask" | "ask_once" | "auto"): string {
  if (policy === "auto") return "success";
  if (policy === "ask_once") return "info";
  return "warning";
}

export function HITLPoliciesTab(): JSX.Element {
  return (
    <Card title="HITL policies" subtitle="Per-tool · risk-tiered · escalation routing">
      <BackendGapBanner reason="HITL risk-tier policy configuration: backend extension Phase 58+ — values shown are mockup defaults" />
      <table className="table">
        <thead>
          <tr>
            <th>Risk tier</th>
            <th>Default policy</th>
            <th>SLA</th>
            <th>Approvers</th>
            <th>Off-platform</th>
          </tr>
        </thead>
        <tbody>
          {HITL_POLICIES.map((p) => (
            <tr key={p.risk}>
              <td>
                {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: row gap */}
                <span className="row" style={{ gap: 6 }}>
                  <span className={`sev-dot sev-${p.risk}`} />
                  {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: fontSize + capitalize */}
                  <span style={{ fontSize: 12, textTransform: "capitalize" }}>{p.risk}</span>
                </span>
              </td>
              <td><Badge tone={policyTone(p.policy)}>{p.policy}</Badge></td>
              <td className="mono">{p.sla}</td>
              {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: mono subtle fontSize */}
              <td className="mono subtle" style={{ fontSize: 11.5 }}>{p.approvers}</td>
              <td>
                {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: row gap */}
                <div className="row" style={{ gap: 4 }}>
                  {p.off.length ? (
                    p.off.map((c) => <Badge key={c}>{c}</Badge>)
                  ) : (
                    <span className="subtle">—</span>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}
