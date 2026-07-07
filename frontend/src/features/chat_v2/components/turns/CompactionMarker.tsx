/**
 * File: frontend/src/features/chat_v2/components/turns/CompactionMarker.tsx
 * Purpose: Renders a Cat 4 context-compaction marker in the chat-v2 timeline.
 * Category: Frontend / chat_v2 / components / turns
 * Scope: Sprint 57.159 (compaction L2→L3 drive-through + fills the 57.66 A-5c surface)
 *
 * Description:
 *   A slim, centered system marker (NOT a speaker `.turn` shell) surfacing a
 *   context_compacted event: "⚡ Context compacted · 9,824 → 2,679 tokens
 *   (hybrid · 12 msgs)". The event was store-recognized as rawEvents-only
 *   (57.66 A-5c deferral) so the token reduction rendered nowhere; this makes it
 *   observable in the main conversation flow, persistent in scrollback. Reuses
 *   the mockup `.badge.warning` chip (compaction == warning, matching the
 *   InspectorTrace COMPACTION span color var(--warning)) — no new CSS / HEX /
 *   oklch (all color owned by the class). Layout-only inline styles via the
 *   established turns/ escape pattern (AgentTurn.tsx:47).
 *
 * Created: 2026-07-07 (Sprint 57.159)
 *
 * Modification History:
 *   - 2026-07-07: Initial creation (Sprint 57.159) — context_compacted timeline marker
 *
 * Related:
 *   - ../../types.ts (CompactionMarkerTurn)
 *   - ../../store/chatStore.ts (context_compacted case pushes the marker)
 *   - frontend/src/styles-mockup.css L507-535 (.badge + .badge.warning)
 *   - ../inspector/InspectorTrace.tsx (COMPACTION span == var(--warning))
 */

import type { CompactionMarkerTurn } from "../../types";

/* eslint-disable no-restricted-syntax -- Sprint 57.159: no mockup source for a
   compaction system-marker; a centered row composed from an existing token
   (reuse .badge.warning for the chip). Layout-only inline styles (flex/gap/
   padding) — no color / HEX / oklch literal; all color owned by .badge.warning. */
export function CompactionMarker({ turn }: { turn: CompactionMarkerTurn }): JSX.Element {
  const before = turn.tokensBefore.toLocaleString();
  const after = turn.tokensAfter.toLocaleString();
  return (
    <div
      data-testid="compaction-marker"
      style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: "8px 24px" }}
    >
      <span className="badge warning">
        ⚡ Context compacted · {before} → {after} tokens ({turn.strategy} · {turn.messagesCompacted} msgs)
      </span>
    </div>
  );
}

export default CompactionMarker;
