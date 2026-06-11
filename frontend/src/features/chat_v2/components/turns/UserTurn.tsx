/**
 * File: frontend/src/features/chat_v2/components/turns/UserTurn.tsx
 * Purpose: Renders user-role Turn — verbatim mockup re-point of L165-176.
 * Category: Frontend / chat_v2 / components / turns
 * Scope: Phase 57.21 (Day 2 — Option C cp+convert; AD-ChatV2-Full-Mockup-Fidelity Phase-1)
 *
 * Description:
 *   Per-turn shell with timeline rail + marker dot + head row (role label
 *   + route pill + timestamp) + body text. Source: mockup
 *   reference/design-mockups/page-chat.jsx L165-176; styles
 *   styles-mockup.css L742-771 + L1101 .route-pill. Display name resolves
 *   from authStore.user (display_name ?? email ?? "You"); primary role
 *   from authStore.roles[0] ?? "operator".
 *
 *   Sprint 57.30 Day 3: re-pointed from translated-Tailwind utility classes
 *   to verbatim mockup `.turn` / `.turn-rail` / `.turn-marker` / `.turn-head`
 *   / `.role` / `.route-pill` / `.mono.subtle` / `.turn-body` classes from
 *   styles-mockup.css. No inline-style literals needed — mockup CSS owns
 *   geometry + color.
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 2 §2.1)
 *
 * Modification History:
 *   - 2026-06-11: Sprint 57.101 B1 — tag injected mid-run user turns (.route-pill reuse, no new token)
 *   - 2026-05-23: Sprint 57.30 Day 3 §D1 — verbatim re-point Tailwind → mockup .turn/.turn-rail/.turn-marker/.turn-head/.role/.route-pill
 *   - 2026-05-17: Initial extract from mockup L165-176 + Tailwind convert
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L165-176 (source JSX)
 *   - frontend/src/styles-mockup.css L742-771 (.turn / .turn-rail / .turn-marker / .turn-head / .turn-body)
 *   - frontend/src/styles-mockup.css L1101 (.route-pill)
 *   - ../../types.ts (UserTurn type)
 *   - ../../../auth/store/authStore.ts (display_name + roles)
 */

import { useAuthStore } from "../../../auth/store/authStore";
import type { UserTurn as UserTurnType } from "../../types";

export function UserTurn({ turn }: { turn: UserTurnType }): JSX.Element {
  const user = useAuthStore((s) => s.user);
  const roles = useAuthStore((s) => s.roles);
  const displayName = user?.display_name ?? user?.email ?? "You";
  const primaryRole = roles[0] ?? "operator";
  return (
    <div className="turn" data-role="user" data-injected={turn.injected ? "true" : undefined}>
      <div className="turn-rail" />
      <div className="turn-marker" />
      <div className="turn-head">
        <span className="role">{displayName}</span>
        <span className="route-pill">{primaryRole}</span>
        {/* Sprint 57.101 B1: tag a mid-run injected instruction. No mockup source
            for this tag → reuse the existing .route-pill class (no new HEX/oklch). */}
        {turn.injected && (
          <span className="route-pill" data-testid="injected-tag">
            injected mid-run
          </span>
        )}
        <span className="mono subtle">{turn.at}</span>
      </div>
      <div className="turn-body">{turn.text}</div>
    </div>
  );
}
