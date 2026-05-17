/**
 * File: frontend/src/features/chat_v2/components/ChatLayout.tsx
 * Purpose: 3-column chat shell — sessions sidebar / conversation center / inspector sidebar.
 * Category: Frontend / chat_v2 / components
 * Scope: Phase 50 / Sprint 50.2 (Day 3.6) → 57.8 D11 surgical → 57.16 Tailwind → 57.20 token migration → 57.21 Day 3 §3.2 3-col rewrite
 *
 * Description:
 *   Mockup L73-91 `chat-shell` — three-column grid with collapsible side rails:
 *     [SessionList 280px | ChatHeader + body + Composer 1fr | ChatInspector 360px]
 *
 *   `listOpen` + `inspOpen` local state controls rail visibility. When a rail
 *   collapses, the grid column width drops to 0 and the rail unmounts (zero
 *   layout cost; preserves keyboard tab order). Mobile (<768px) hides both
 *   rails permanently per Sprint 57.13 a11y standards (rails only meaningful
 *   on operator desktops).
 *
 *   Center column composition:
 *     - <ChatHeader> at top (sticky-feel via flex; no `position: sticky` —
 *       avoids interaction with AppShellV2's own sticky header)
 *     - children (TurnList + side panels + InputBar from chat-v2/index.tsx)
 *
 *   Sprint 57.21 Day 3 §3.2 preserves:
 *     - height = calc(100vh - 6.5rem) to fit inside AppShellV2 main column
 *     - No internal page-title <h1> (AppShellV2 sticky header provides h1)
 *     - No own background (AppShellV2 provides bg-background)
 *
 * Created: 2026-04-30 (Sprint 50.2 Day 3.6)
 * Last Modified: 2026-05-17
 *
 * Modification History (newest-first):
 *   - 2026-05-18: Sprint 57.21 Day 4 D-DAY4-7 — column widths align to mockup `chat-shell` (240/minmax(480,1fr)/320 vs Day 3 280/1fr/360); h-full (fullBleed parent fills viewport) instead of calc(100vh - 6.5rem)
 *   - 2026-05-17: Sprint 57.21 Day 3 §3.2 — 2-col placeholder → 3-col with collapsible rails + ChatHeader + SessionList + ChatInspector
 *   - 2026-05-17: Sprint 57.20 Day 3 US-D1 — token migration bg-muted→bg-bg-1
 *   - 2026-05-11: Sprint 57.16 — inline styles → Tailwind utility classes
 *   - 2026-05-09: Sprint 57.8 D11 — drop internal header + 100vh adjustment for AppShellV2 wrap
 *   - 2026-04-30: Initial creation (Sprint 50.2 Day 3.6)
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L73-91 (ChatV2 shell) + L93-121 (ChatHeader)
 *   - ./SessionList.tsx (left rail mount)
 *   - ./ChatHeader.tsx (top of center)
 *   - ./inspector/ChatInspector.tsx (right rail mount — Day 3 stub, Day 4 full)
 *   - frontend/src/components/AppShellV2.tsx (page-level shell consumer)
 *   - frontend/STYLE.md §2 (verified tokens: bg-bg-1 / text-fg / border-border)
 */

import { useState, type ReactNode } from "react";

import { cn } from "@/lib/utils";

import { ChatHeader } from "./ChatHeader";
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
      data-list={listOpen ? "open" : "hidden"}
      data-insp={inspOpen ? "open" : "hidden"}
      className={cn(
        "grid h-full w-full",
        // Mobile: hide both rails.
        "grid-cols-[1fr]",
        // ≥768px: render rails based on open state (md-and-up).
        // Column widths mirror mockup `chat-shell` exactly (styles.css §669-678).
        listOpen && inspOpen && "md:grid-cols-[240px_minmax(480px,1fr)_320px]",
        listOpen && !inspOpen && "md:grid-cols-[240px_minmax(480px,1fr)]",
        !listOpen && inspOpen && "md:grid-cols-[minmax(480px,1fr)_320px]",
        !listOpen && !inspOpen && "md:grid-cols-[minmax(0,1fr)]",
      )}
    >
      {listOpen && (
        <aside className="hidden border-r border-border md:block">
          <SessionList />
        </aside>
      )}

      <main className="flex min-w-0 flex-col overflow-hidden">
        <ChatHeader
          listOpen={listOpen}
          inspOpen={inspOpen}
          onToggleList={() => setListOpen((o) => !o)}
          onToggleInsp={() => setInspOpen((o) => !o)}
        />
        <div className="flex flex-1 flex-col overflow-hidden">{children}</div>
      </main>

      {inspOpen && (
        <div className="hidden md:block">
          <ChatInspector />
        </div>
      )}
    </div>
  );
}
