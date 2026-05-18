/**
 * File: frontend/src/features/chat_v2/components/TurnList.tsx
 * Purpose: Renders chatStore.turns via role dispatcher — replaces MessageList.tsx.
 * Category: Frontend / chat_v2 / components
 * Scope: Phase 57.21 (Day 2 — Option C cp+convert; AD-ChatV2-Full-Mockup-Fidelity Phase-1)
 *
 * Description:
 *   Subscribes to chatStore.turns + dispatches each Turn to the matching
 *   role component (user / agent / hitl). Auto-scrolls to bottom on new
 *   turn or block append. Empty state matches Sprint 57.20 baseline copy
 *   for behavioral continuity (echo_demo hint preserved).
 *
 *   Sprint 57.21 Day 2 ships TurnList; Day 3 ChatLayout 3-col rewrite
 *   replaces MessageList consumer with TurnList; MessageList.tsx becomes
 *   thin compat re-export Day 3 EOD.
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 2 §2.1)
 *
 * Modification History:
 *   - 2026-05-17: Initial creation (Sprint 57.21 Day 2 §2.1)
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L159-163 (TurnRender dispatcher source)
 *   - ./turns/{UserTurn,AgentTurn,HITLTurn}.tsx (role components)
 *   - ../store/chatStore.ts (subscribes to turns + block-sequence reducer)
 */

import { useEffect, useRef } from "react";

import { useChatStore } from "../store/chatStore";
import { AgentTurn } from "./turns/AgentTurn";
import { HITLTurn } from "./turns/HITLTurn";
import { UserTurn } from "./turns/UserTurn";

export function TurnList(): JSX.Element {
  const turns = useChatStore((s) => s.turns);
  const scrollRef = useRef<HTMLDivElement>(null);
  const lastTurn = turns[turns.length - 1];
  const turnCount = turns.length;

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [turnCount, lastTurn]);

  if (turns.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center overflow-y-auto p-8 text-center text-sm text-fg-muted">
        <p>
          Type a message below to start. Try <code className="rounded bg-bg-2 px-1.5 py-0.5 font-mono text-xs">echo hello</code>{" "}
          in echo_demo mode.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col overflow-y-auto" ref={scrollRef}>
      {turns.map((turn) => {
        if (turn.role === "user") return <UserTurn key={turn.id} turn={turn} />;
        if (turn.role === "agent") return <AgentTurn key={turn.id} turn={turn} />;
        if (turn.role === "hitl") return <HITLTurn key={turn.id} turn={turn} />;
        return null;
      })}
    </div>
  );
}

export default TurnList;
