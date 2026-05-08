/**
 * File: frontend/src/features/chat_v2/components/ChatLayout.tsx
 * Purpose: 3-column body — sessions sidebar / conversation / inspector sidebar.
 * Category: Frontend / chat_v2 / components
 * Scope: Phase 50 / Sprint 50.2 (Day 3.6) → Sprint 57.8 D11 surgical fix
 *
 * Description:
 *   Minimal version of the layout sketched in 16-frontend-design.md Chat 頁面設計.
 *   Sprint 50.2 fills only the conversation column; sidebar + inspector are
 *   placeholders until 51.x (sessions list) and 52.x (inspector with token /
 *   memory layers / verifier state).
 *
 *   Sprint 57.8 D11 surgical fix:
 *     - Dropped internal <header> (now redundant with AppShellV2 sticky header
 *       at page level — pageTitle="Chat (V2)" provides the page title h1)
 *     - height: 100vh → calc(100vh - 6.5rem) to fit inside AppShellV2 main
 *       column (subtracts AppShellV2 header 3.5rem + main p-6 vertical 3rem)
 *     - Dropped own background color (AppShellV2 provides bg-background)
 *     - Dropped own fontFamily (inherits from AppShellV2 body)
 *
 *   Inline styles only kept (Sprint 50.2 baseline; Phase 58+ Tailwind migration
 *   when sessions sidebar + inspector get real content from 51.x / 52.x).
 *
 * Created: 2026-04-30 (Sprint 50.2 Day 3.6)
 * Last Modified: 2026-05-09
 *
 * Modification History (newest-first):
 *   - 2026-05-09: Sprint 57.8 D11 — drop internal header + 100vh adjustment for AppShellV2 wrap
 *   - 2026-04-30: Initial creation (Sprint 50.2 Day 3.6)
 *
 * Related:
 *   - 16-frontend-design.md §Chat 頁面設計
 *   - frontend/src/components/AppShellV2.tsx (page-level shell consumer)
 *   - MessageList / InputBar (Day 4)
 */

import type { CSSProperties, ReactNode } from "react";

type Props = {
  children: ReactNode;
};

const styles: Record<string, CSSProperties> = {
  page: {
    display: "grid",
    gridTemplateColumns: "240px 1fr 280px",
    gridTemplateRows: "1fr",
    gridTemplateAreas: '"sidebar main inspector"',
    // Sprint 57.8 D11: subtract AppShellV2 header (3.5rem) + main p-6 vertical (3rem)
    height: "calc(100vh - 6.5rem)",
  },
  sidebar: {
    gridArea: "sidebar",
    borderRight: "1px solid #e2e6ee",
    background: "#fbfbfd",
    padding: "1rem",
    fontSize: 14,
    color: "#3b4252",
    overflowY: "auto",
  },
  main: {
    gridArea: "main",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
  },
  inspector: {
    gridArea: "inspector",
    borderLeft: "1px solid #e2e6ee",
    background: "#fbfbfd",
    padding: "1rem",
    fontSize: 13,
    color: "#3b4252",
    overflowY: "auto",
  },
  placeholder: {
    color: "#7c8696",
    fontSize: 13,
    lineHeight: 1.5,
  },
};

export default function ChatLayout({ children }: Props): JSX.Element {
  return (
    <div style={styles.page}>
      <aside style={styles.sidebar}>
        <h3 style={{ marginTop: 0, fontSize: 13, color: "#5a6377" }}>Sessions</h3>
        <p style={styles.placeholder}>
          Session list lands in Phase 51.x (when DB-backed session storage is wired).
          For now, each page reload starts a new in-memory session.
        </p>
      </aside>

      <main style={styles.main}>{children}</main>

      <aside style={styles.inspector}>
        <h3 style={{ marginTop: 0, fontSize: 13, color: "#5a6377" }}>Inspector</h3>
        <p style={styles.placeholder}>
          Token / cost tracker (52.1+), memory layer inspector (51.2),
          verification status (54.1) — coming in later sprints.
        </p>
      </aside>
    </div>
  );
}
