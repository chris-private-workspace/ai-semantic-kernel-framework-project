/**
 * File: frontend/src/features/chat_v2/components/ChatLayout.tsx
 * Purpose: 3-column body — sessions sidebar / conversation / inspector sidebar.
 * Category: Frontend / chat_v2 / components
 * Scope: Phase 50 / Sprint 50.2 (Day 3.6) → Sprint 57.8 D11 surgical fix → Sprint 57.16 Tailwind migration
 *
 * Description:
 *   Minimal version of the layout sketched in 16-frontend-design.md Chat 頁面設計.
 *   Sprint 50.2 fills only the conversation column; sidebar + inspector are
 *   placeholders until 51.x (sessions list) and 52.x (inspector with token /
 *   memory layers / verifier state).
 *
 *   Sprint 57.8 D11 surgical fix (preserved):
 *     - No internal <header> (AppShellV2 sticky header provides page title h1)
 *     - height = calc(100vh - 6.5rem) to fit inside AppShellV2 main column
 *       (subtracts AppShellV2 header 3.5rem + main p-6 vertical 3rem)
 *     - No own background colour (AppShellV2 provides bg-background)
 *     - No own fontFamily (inherits from AppShellV2 body)
 *
 *   Sprint 57.16 (AD-Inline-Style-Cleanup-Sweep-Round2): migrated to Tailwind
 *   utility classes; placeholder + h3 text use text-muted-foreground
 *   (≈ 4.6:1 on bg-muted — AA-compliant; prerequisite for re-enabling
 *   color-contrast on /chat-v2 in a11y-scan.spec.ts).
 *
 * Created: 2026-04-30 (Sprint 50.2 Day 3.6)
 * Last Modified: 2026-05-11
 *
 * Modification History (newest-first):
 *   - 2026-05-17: Sprint 57.20 Day 3 US-D1 — token migration bg-muted→bg-bg-1 for new shell mockup consistency
 *   - 2026-05-11: Sprint 57.16 — inline styles → Tailwind utility classes (AD-Inline-Style-Cleanup-Sweep-Round2)
 *   - 2026-05-09: Sprint 57.8 D11 — drop internal header + 100vh adjustment for AppShellV2 wrap
 *   - 2026-04-30: Initial creation (Sprint 50.2 Day 3.6)
 *
 * Related:
 *   - 16-frontend-design.md §Chat 頁面設計
 *   - frontend/src/components/AppShellV2.tsx (page-level shell consumer)
 *   - MessageList / InputBar (Day 4)
 *   - frontend/STYLE.md §2 (verified tokens: bg-muted / text-muted-foreground / text-foreground / border-border)
 */

import type { ReactNode } from "react";

type Props = {
  children: ReactNode;
};

export default function ChatLayout({ children }: Props): JSX.Element {
  return (
    <div className="grid h-[calc(100vh_-_6.5rem)] grid-cols-[240px_1fr_280px]">
      <aside className="overflow-y-auto border-r border-border bg-bg-1 p-4 text-sm text-foreground">
        <h3 className="mt-0 text-[13px] text-foreground/80">Sessions</h3>
        <p className="text-[13px] leading-relaxed text-foreground/80">
          Session list lands in Phase 51.x (when DB-backed session storage is wired).
          For now, each page reload starts a new in-memory session.
        </p>
      </aside>

      <main className="flex flex-col overflow-hidden">{children}</main>

      <aside className="overflow-y-auto border-l border-border bg-bg-1 p-4 text-[13px] text-foreground">
        <h3 className="mt-0 text-[13px] text-foreground/80">Inspector</h3>
        <p className="text-[13px] leading-relaxed text-foreground/80">
          Token / cost tracker (52.1+), memory layer inspector (51.2),
          verification status (54.1) — coming in later sprints.
        </p>
      </aside>
    </div>
  );
}
