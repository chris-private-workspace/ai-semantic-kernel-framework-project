/**
 * File: frontend/src/pages/chat-v2/index.tsx
 * Purpose: V2 Chat page (real ship) — auth gate + AppShellV2 wrap + ChatLayout body.
 * Category: Frontend / pages / chat-v2
 * Scope: Phase 57 / Sprint 57.8 US-5 Day 3
 *
 * Description:
 *   Sprint 57.8 Day 3 promotes the Sprint 50.2 skeleton to a real ship:
 *
 *     1. Auth gate — if !isAuthenticated → setPostLoginRedirect("/chat-v2")
 *        + <Navigate to="/auth/login" replace />. First page in V2 to gate
 *        on Sprint 57.7 IAM JWT (other pages remain admin-driven via URL
 *        ?tenant_id=... per AD-Frontend-AuthUX Phase 58.x).
 *     2. AppShellV2 wrap with pageTitle="Chat (V2)" (per A1 architecture —
 *        page-level shell wrap; ChatLayout is now pure body).
 *     3. ChatLayout + MessageList + InputBar reused unchanged from 50.2
 *        (D11 surgical: ChatLayout internal header dropped + 100vh adjusted
 *        to fit inside AppShellV2 main column).
 *
 * Created: 2026-04-30 (Sprint 50.2 Day 3.7 — placeholder)
 * Last Modified: 2026-05-09
 *
 * Modification History (newest-first):
 *   - 2026-05-10: Sprint 57.13 US-A1 — gate via <RequireAuth> (was inline isAuthenticated() check)
 *   - 2026-05-10: Sprint 57.12 US-6 §3.8 — mount inline LoopVisualizer + SubagentTree panels
 *   - 2026-05-09: Sprint 57.8 US-5 Day 3 — auth gate + AppShellV2 wrap (real ship)
 *   - 2026-04-30: Wire MessageList + InputBar (Sprint 50.2 Day 4.4)
 *   - 2026-04-30: Replace 49.1 placeholder with ChatLayout shell (Sprint 50.2 Day 3.7)
 *
 * Related:
 *   - frontend/src/features/auth/components/RequireAuth.tsx (route gate)
 *   - frontend/src/components/AppShellV2.tsx (page-level shell)
 *   - frontend/src/features/chat_v2/components/ChatLayout.tsx (D11 surgical fix)
 *   - frontend/src/features/orchestrator-loop/components/LoopVisualizer.tsx (Sprint 57.12 US-4)
 *   - frontend/src/features/subagent/components/SubagentTree.tsx (Sprint 57.12 US-6)
 */

import { AppShellV2 } from "@/components/AppShellV2";
import { RequireAuth } from "@/features/auth/components/RequireAuth";
import ChatLayout from "@/features/chat_v2/components/ChatLayout";
import InputBar from "@/features/chat_v2/components/InputBar";
import MessageList from "@/features/chat_v2/components/MessageList";
import { LoopVisualizer } from "@/features/orchestrator-loop/components/LoopVisualizer";
import { SubagentTree } from "@/features/subagent/components/SubagentTree";
import { VerificationPanel } from "@/features/verification/components/VerificationPanel";

export default function ChatV2Page(): JSX.Element {
  return (
    <RequireAuth>
      <AppShellV2 pageTitle="Chat (V2)">
        <ChatLayout>
          <MessageList />
          {/* Inline panels — each renders null when no events; mounted between
              the message stream and input. Sprint 57.11 US-5 (verification) +
              Sprint 57.12 US-4 (loop) + US-6 (subagent). */}
          <VerificationPanel />
          <SubagentTree />
          <LoopVisualizer mode="inline" />
          <InputBar />
        </ChatLayout>
      </AppShellV2>
    </RequireAuth>
  );
}
