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
 *   Sprint 57.30 Day 3 re-points scroll container + empty-state pad/text
 *   to verbatim mockup vocabulary (mockup page-chat.jsx L83 inline
 *   `{ flex: 1, overflowY: "auto" }` wrapper around the TURNS.map). No
 *   dedicated mockup class for the scroller — preserve inline-style
 *   `{ flex: 1, overflowY: "auto" }` to match L83 verbatim. Empty state
 *   uses mockup `.subtle` color + mockup `.mono` for the echo code chip.
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 2 §2.1)
 *
 * Modification History:
 *   - 2026-07-07: Sprint 57.159 — dispatch role==="compaction" to CompactionMarker (Cat 4 L2→L3 timeline surface)
 *   - 2026-06-06: chat-v2 honest surface — empty-state copy explains real_llm (live) vs echo_demo (mock) instead of only teaching echo_demo (CHANGE-054)
 *   - 2026-05-23: Sprint 57.30 Day 3 §D1 — re-point scroll wrapper to mockup L83 verbatim inline-style + empty-state to mockup .subtle/.mono
 *   - 2026-05-17: Initial creation (Sprint 57.21 Day 2 §2.1)
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L83-85 (scrolling wrapper around TURNS.map)
 *   - reference/design-mockups/page-chat.jsx L159-163 (TurnRender dispatcher source)
 *   - ./turns/{UserTurn,AgentTurn,HITLTurn,CompactionMarker}.tsx (role components)
 *   - ../store/chatStore.ts (subscribes to turns + block-sequence reducer)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: mockup page-chat.jsx L83
   wraps the turns list in `{ flex: 1, overflowY: "auto" }`; preserve inline-style. */

import { useEffect, useRef } from "react";

import { useChatStore } from "../store/chatStore";
import { AgentTurn } from "./turns/AgentTurn";
import { CompactionMarker } from "./turns/CompactionMarker";
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
      <div
        ref={scrollRef}
        style={{ flex: 1, overflowY: "auto" }}
        className="subtle"
      >
        <div style={{ padding: "32px 24px", textAlign: "center", fontSize: 13 }}>
          Type a message below to start. The mode toggle switches between{" "}
          <code className="mono" style={{ fontSize: 11 }}>real_llm</code>{" "}
          (live agent) and{" "}
          <code className="mono" style={{ fontSize: 11 }}>echo_demo</code>{" "}
          (offline mock that just echoes your input).
        </div>
      </div>
    );
  }

  return (
    <div ref={scrollRef} style={{ flex: 1, overflowY: "auto" }}>
      {turns.map((turn) => {
        if (turn.role === "user") return <UserTurn key={turn.id} turn={turn} />;
        if (turn.role === "agent") return <AgentTurn key={turn.id} turn={turn} />;
        if (turn.role === "hitl") return <HITLTurn key={turn.id} turn={turn} />;
        if (turn.role === "compaction") return <CompactionMarker key={turn.id} turn={turn} />;
        return null;
      })}
    </div>
  );
}

export default TurnList;
