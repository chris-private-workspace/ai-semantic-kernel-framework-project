/**
 * File: frontend/src/pages/loop-debug/index.tsx
 * Purpose: Loop Debug page (real ship) — auth gate + AppShellV2 wrap + standalone LoopVisualizer.
 * Category: Frontend / pages / loop-debug
 * Scope: Phase 57 / Sprint 57.12 Day 2 / US-4 (was Phase 49.1 placeholder concept)
 *
 * Description:
 *   Standalone full-screen view of the TAO/ReAct state machine for the
 *   current chat-v2 session. Mirrors verification/index.tsx (Sprint 57.11)
 *   auth-gate + AppShellV2 pattern:
 *
 *     1. Auth gate — if !isAuthenticated → setPostLoginRedirect("/loop-debug")
 *        + <Navigate to="/auth/login" replace />
 *     2. AppShellV2 wrap — pageTitle "Loop Debug"
 *     3. <LoopVisualizer mode="standalone" /> body — reads useChatStore.rawEvents
 *        (the in-memory live session; per AP-6 YAGNI, no historical persistence
 *        — if rawEvents is empty the visualizer shows an explanatory empty state)
 *
 *   Note: chat-v2 keeps a single in-memory session (DB-backed session storage
 *   is Phase 51.x deferred per ChatLayout placeholder). So loop-debug shows
 *   whatever session chat-v2 last ran in this browser tab. Cross-session /
 *   historical inspection would need a persisted loop_event table — out of
 *   scope this sprint per AP-6.
 *
 * Created: 2026-05-10 (Sprint 57.12 Day 2 / US-4)
 * Last Modified: 2026-05-10
 *
 * Modification History (newest-first):
 *   - 2026-05-10: Sprint 57.13 US-A1 — gate via <RequireAuth> (was inline isAuthenticated() check)
 *   - 2026-05-10: Initial creation (Sprint 57.12 US-4 Day 2 — real ship)
 *
 * Related:
 *   - frontend/src/features/auth/components/RequireAuth.tsx (route gate)
 *   - frontend/src/components/AppShellV2.tsx (page-level shell)
 *   - frontend/src/features/orchestrator-loop/components/LoopVisualizer.tsx (Day 2 §2.6)
 */

import { AppShellV2 } from "@/components/AppShellV2";
import { RequireAuth } from "@/features/auth/components/RequireAuth";
import { LoopVisualizer } from "@/features/orchestrator-loop/components/LoopVisualizer";

export default function LoopDebugPage(): JSX.Element {
  return (
    <RequireAuth>
      <AppShellV2 pageTitle="Loop Debug">
        <LoopVisualizer mode="standalone" />
      </AppShellV2>
    </RequireAuth>
  );
}
