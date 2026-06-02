/**
 * File: frontend/src/features/chat_v2/components/ChatLayout.tsx
 * Purpose: 3-column chat shell — sessions sidebar / conversation center / inspector sidebar.
 * Category: Frontend / chat_v2 / components
 * Scope: Phase 50 / Sprint 50.2 (Day 3.6) → 57.8 D11 surgical → 57.16 Tailwind → 57.20 token migration → 57.21 Day 3 §3.2 3-col rewrite → 57.30 Day 2 verbatim re-point
 *
 * Description:
 *   Mockup `page-chat.jsx` L79-91 `chat-shell` — verbatim three-column grid wrapper.
 *   The grid template + responsive @media + data-list/data-insp toggle semantics
 *   are entirely in `styles-mockup.css` L669-708 via `.chat-shell` class +
 *   `[data-list]` / `[data-insp]` attribute selectors. This component contributes
 *   ONLY the outer `<div className="chat-shell">` wrapper + the rail open/close
 *   state + the column children — NEVER inlines the grid template.
 *
 *   Both rails ALWAYS render. CSS handles the 0-width collapse so keyboard tab
 *   order is preserved (vs. Sprint 57.21 D11 which unmounted conditionally).
 *
 *   Sprint 57.30 Day 2 — verbatim re-point: Tailwind `grid grid-cols-[…]`
 *   translation replaced with `.chat-shell` mockup class; rail wrapping
 *   `<aside>` / `<div>` elements dropped (the mockup ships `SessionList` and
 *   `ChatInspector` as the grid children directly).
 *
 * Created: 2026-04-30 (Sprint 50.2 Day 3.6)
 * Last Modified: 2026-05-23
 *
 * Modification History (newest-first):
 *   - 2026-06-02: Sprint 57.69 — mount <HandoffBanner /> above the conversation (HANDOFF pivot notice)
 *   - 2026-05-23: Sprint 57.30 Day 2 US-C1 — verbatim re-point to .chat-shell mockup class + data-list/data-insp attrs
 *   - 2026-05-18: Sprint 57.21 Day 4 D-DAY4-7 — column widths align to mockup `chat-shell` (240/minmax(480,1fr)/320 vs Day 3 280/1fr/360); h-full (fullBleed parent fills viewport) instead of calc(100vh - 6.5rem)
 *   - 2026-05-17: Sprint 57.21 Day 3 §3.2 — 2-col placeholder → 3-col with collapsible rails + ChatHeader + SessionList + ChatInspector
 *   - 2026-05-17: Sprint 57.20 Day 3 US-D1 — token migration bg-muted→bg-bg-1
 *   - 2026-05-11: Sprint 57.16 — inline styles → Tailwind utility classes
 *   - 2026-05-09: Sprint 57.8 D11 — drop internal header + 100vh adjustment for AppShellV2 wrap
 *   - 2026-04-30: Initial creation (Sprint 50.2 Day 3.6)
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L79-91 (ChatV2 shell)
 *   - frontend/src/styles-mockup.css L669-708 (.chat-shell grid + responsive + data-list/data-insp toggles)
 *   - ./SessionList.tsx (left rail; first grid child)
 *   - ./ChatHeader.tsx (top of center column)
 *   - ./inspector/ChatInspector.tsx (right rail; third grid child)
 *   - frontend/src/components/AppShellV2.tsx (page-level shell consumer)
 *   - docs/rules-on-demand/frontend-mockup-fidelity.md (verbatim re-point method)
 */

import { useState, type ReactNode } from "react";

import { ChatHeader } from "./ChatHeader";
import { HandoffBanner } from "./HandoffBanner";
import { ChatInspector } from "./inspector/ChatInspector";
import { SessionList } from "./SessionList";

type Props = {
  children: ReactNode;
};

export default function ChatLayout({ children }: Props): JSX.Element {
  const [listOpen, setListOpen] = useState(true);
  const [inspOpen, setInspOpen] = useState(true);

  return (
    <div
      data-testid="chat-shell"
      className="chat-shell"
      data-list={listOpen ? "open" : "hidden"}
      data-insp={inspOpen ? "open" : "hidden"}
    >
      <SessionList />
      <div className="chat-stream">
        <ChatHeader
          listOpen={listOpen}
          inspOpen={inspOpen}
          onToggleList={() => setListOpen((o) => !o)}
          onToggleInsp={() => setInspOpen((o) => !o)}
        />
        {/* Sprint 57.69: HANDOFF transition banner above the conversation. */}
        <HandoffBanner />
        {children}
      </div>
      <ChatInspector />
    </div>
  );
}
