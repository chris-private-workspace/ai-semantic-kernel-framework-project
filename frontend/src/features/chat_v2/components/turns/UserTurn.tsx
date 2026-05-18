/**
 * File: frontend/src/features/chat_v2/components/turns/UserTurn.tsx
 * Purpose: Renders user-role Turn — Tailwind translation of mockup L165-176.
 * Category: Frontend / chat_v2 / components / turns
 * Scope: Phase 57.21 (Day 2 — Option C cp+convert; AD-ChatV2-Full-Mockup-Fidelity Phase-1)
 *
 * Description:
 *   Per-turn shell with timeline rail + marker dot + head row (role label
 *   + route pill + timestamp) + body text. Source: mockup
 *   reference/design-mockups/page-chat.jsx L165-176; styles
 *   reference/design-mockups/styles.css L742-771. Display name resolves
 *   from authStore.user (display_name ?? email ?? "You"); primary role
 *   from authStore.roles[0] ?? "operator".
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 2 §2.1)
 *
 * Modification History:
 *   - 2026-05-17: Initial extract from mockup L165-176 + Tailwind convert
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L165-176 (source JSX)
 *   - reference/design-mockups/styles.css L742-771 (turn-rail / turn-marker / turn-head / route-pill)
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
    <div className="relative border-b border-border bg-bg px-6 py-3.5" data-role="user">
      <div className="absolute bottom-0 left-[10px] top-0 w-px bg-border" />
      <div className="absolute left-[6px] top-[18px] h-[9px] w-[9px] rounded-full border-2 border-fg bg-fg" />
      <div className="mb-2 flex items-center gap-2 pl-[22px] text-[11px] text-fg-muted">
        <span className="text-xs font-semibold text-fg">{displayName}</span>
        <span className="rounded border border-border bg-bg-2 px-1.5 py-px font-mono text-[10.5px] text-fg-muted">
          {primaryRole}
        </span>
        <span className="font-mono text-fg-subtle">{turn.at}</span>
      </div>
      <div className="pl-[22px] text-[13px] leading-[1.55]">{turn.text}</div>
    </div>
  );
}
