/**
 * File: frontend/src/features/tenant-settings/components/tabs/MembersTab.tsx
 * Purpose: Members tab — table of 8 active members w/ avatar gradient + role badge (mockup verbatim).
 * Category: Frontend / tenant-settings / components / tabs
 * Scope: Phase 57 / Sprint 57.44 Day 1 (mockup-fidelity rebuild — D-DAY0-4 Option A)
 *
 * Description:
 *   Verbatim port of mockup `page-admin.jsx` L570-601. Single Card "Members"
 *   subtitle "8 active · 0 invitations" + Invite Button action (AP-2 stub) +
 *   5-col table (Member / Email / Role / Last active / actions). Member cell
 *   renders 24×24 circular avatar w/ verbatim oklch linear-gradient seeded by
 *   `m.c` (hue index) + initials. Role Badge tone: admin=primary,
 *   compliance=memory, default=empty.
 *
 * Created: 2026-05-26 (Sprint 57.44 Day 1)
 * Last Modified: 2026-05-26
 *
 * Modification History (newest-first):
 *   - 2026-05-26: Initial creation (Sprint 57.44 Day 1) — tenant-settings full mockup-fidelity rebuild
 *
 * Related:
 *   - reference/design-mockups/page-admin.jsx L570-601
 *   - ../../_fixtures.ts (MEMBERS)
 */

import { Badge, Button, Card, Icon } from "../../../../components/mockup-ui";
import { BackendGapBanner } from "../../../../components/ui/BackendGapBanner";
import { MEMBERS } from "../../_fixtures";

function roleTone(role: "admin" | "operator" | "compliance"): string {
  if (role === "admin") return "primary";
  if (role === "compliance") return "memory";
  return "";
}

function initials(name: string): string {
  return name
    .split(" ")
    .map((x) => x[0])
    .join("");
}

export function MembersTab(): JSX.Element {
  const handleInvite = (): void => {
    window.alert("Invite member: backend gap (Phase 58+) — member invitation endpoint pending");
  };

  return (
    <Card
      title="Members"
      subtitle="8 active · 0 invitations"
      actions={
        <Button variant="primary" size="sm" icon="plus" onClick={handleInvite}>
          Invite
        </Button>
      }
      bodyClass="flush"
    >
      <BackendGapBanner reason="Member roster + role assignment: backend extension Phase 58+ — values shown are mockup defaults" />
      <table className="table">
        <thead>
          <tr>
            <th>Member</th>
            <th>Email</th>
            <th>Role</th>
            <th>Last active</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {MEMBERS.map((m) => (
            <tr key={m.e}>
              <td>
                {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: row gap */}
                <div className="row" style={{ gap: 8 }}>
                  <span
                    // eslint-disable-next-line no-restricted-syntax -- verbatim port: oklch avatar gradient + dimensions
                    style={{
                      width: 24,
                      height: 24,
                      borderRadius: "50%",
                      background: `linear-gradient(135deg, oklch(0.65 0.15 ${m.c}), oklch(0.5 0.16 ${(m.c + 60) % 360}))`,
                      color: "white",
                      display: "inline-flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: 10,
                      fontWeight: 600,
                    }}
                  >
                    {initials(m.n)}
                  </span>
                  {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: fontSize */}
                  <span style={{ fontSize: 12.5 }}>{m.n}</span>
                </div>
              </td>
              {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: mono subtle fontSize */}
              <td className="mono subtle" style={{ fontSize: 11.5 }}>{m.e}</td>
              <td><Badge tone={roleTone(m.r)}>{m.r}</Badge></td>
              {/* eslint-disable-next-line no-restricted-syntax -- verbatim port: subtle fontSize */}
              <td className="subtle" style={{ fontSize: 11.5 }}>{m.a}</td>
              <td><Icon name="dots" size={14} className="subtle" /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </Card>
  );
}
