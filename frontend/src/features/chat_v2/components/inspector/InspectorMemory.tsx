/**
 * File: frontend/src/features/chat_v2/components/inspector/InspectorMemory.tsx
 * Purpose: Inspector "Memory" tab — verbatim mockup re-point of page-chat.jsx L468-487 (memory ops list).
 * Category: Frontend / chat_v2 / components / inspector
 * Scope: Phase 57.75 (A-5 Inspector UI — Memory tab; consumes MemoryAccessed SSE)
 *
 * Description:
 *   Mockup L468-487 (InspectorMemory): a section header ("Memory ops · this
 *   session") then one bordered row per memory access — a `.row` of
 *   `<Badge tone="memory">{op}</Badge>` + scope (`var(--fg-muted)`) + a right
 *   `.subtle` timestamp, then a `{key} = {summary}` detail line.
 *
 *   Reads the chatStore.memoryOps slice (Sprint 57.75; populated by the
 *   memory_accessed SSE branch on the real_llm path). The `op` badge follows the
 *   InspectorTree precedent of consuming the verbatim mockup `.badge` CSS class
 *   (`<span className="badge memory">`) rather than the shadcn Badge primitive.
 *
 *   The timestamp is formatted from the client-side `at` epoch (the backend
 *   MemoryAccessed event carries no server timestamp — see chatStore.MemoryOp).
 *   The time_scale (memory 雙軸) is surfaced next to the scope so the operator
 *   sees whether the hit was permanent / quarterly / daily.
 *
 *   Honest empty state: an echo_demo session injects no prompt_builder so no
 *   MemoryAccessed events fire (Sprint 57.75 D-DAY0-5) — the tab shows "no memory
 *   accesses this session", NOT a fabricated row (AP-4).
 *
 *   Pure read; no side effects.
 *
 * Key Components:
 *   - InspectorMemory: tab component reading useChatStore((s) => s.memoryOps)
 *   - formatTime(): client epoch (ms) → HH:MM:SS label (matches mockup)
 *
 * Created: 2026-06-03 (Sprint 57.75)
 * Last Modified: 2026-06-03
 *
 * Modification History (newest-first):
 *   - 2026-06-03: Initial creation (Sprint 57.75) — A-5 Memory tab verbatim re-point
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L468-487 (InspectorMemory)
 *   - frontend/src/styles-mockup.css L507-530 (.badge / .badge.memory) + L617 (.subtle)
 *   - ../../store/chatStore.ts (memoryOps slice + MemoryOp — Sprint 57.75)
 *   - ./InspectorTree.tsx (sibling wired tab — empty-state + verbatim-class pattern)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: mockup page-chat.jsx L470
   (section header inline font-size/color/text-transform/letter-spacing/font-family),
   L477-484 (op row inline padding/borderBottom/font + scope color + .subtle
   marginLeft:auto + detail line marginTop/color). Colors via var(--*) — not literals. */

import { useChatStore } from "../../store/chatStore";
import type { MemoryOp } from "../../store/chatStore";

/** Format a client-receive epoch (ms) as HH:MM:SS to match the mockup timestamp. */
function formatTime(at: number): string {
  const d = new Date(at);
  const pad = (n: number): string => String(n).padStart(2, "0");
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

function MemoryRow({ op, index }: { op: MemoryOp; index: number }): JSX.Element {
  // scope label: mockup shows "user.jamie" / "session.sess_4tk2p". The backend
  // layer is the scope (e.g. "user" / "tenant" / "session"); append time_scale
  // (memory 雙軸) when present so the operator sees the time dimension.
  const scopeLabel = op.timeScale ? `${op.scope} · ${op.timeScale}` : op.scope;
  return (
    <div
      data-testid={`inspector-memory-op-${index}`}
      style={{
        padding: "7px 0",
        borderBottom: "1px solid var(--border)",
        fontSize: 11,
        fontFamily: "var(--font-mono)",
      }}
    >
      <div className="row" style={{ gap: 6 }}>
        <span className="badge memory">{op.op}</span>
        <span style={{ color: "var(--fg-muted)" }}>{scopeLabel}</span>
        <span className="subtle" style={{ marginLeft: "auto" }}>
          {formatTime(op.at)}
        </span>
      </div>
      <div style={{ marginTop: 4, color: "var(--fg)" }}>
        {op.key} <span className="subtle">=</span> {op.summary}
      </div>
    </div>
  );
}

export function InspectorMemory(): JSX.Element {
  const memoryOps = useChatStore((s) => s.memoryOps);

  if (memoryOps.length === 0) {
    return (
      <div
        data-testid="inspector-memory-empty"
        style={{ padding: "12px 16px", fontSize: 12, color: "var(--fg-muted)" }}
      >
        <div
          style={{
            fontSize: 11.5,
            color: "var(--fg-subtle)",
            textTransform: "uppercase",
            letterSpacing: "0.06em",
            fontFamily: "var(--font-mono)",
          }}
        >
          Memory ops · this session
        </div>
        <p style={{ marginTop: 8, lineHeight: 1.55 }}>no memory accesses this session</p>
      </div>
    );
  }

  return (
    <div data-testid="inspector-memory" style={{ padding: "12px 16px" }}>
      <div
        style={{
          fontSize: 11.5,
          color: "var(--fg-subtle)",
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          marginBottom: 8,
          fontFamily: "var(--font-mono)",
        }}
      >
        Memory ops · this session
      </div>
      {memoryOps.map((op, i) => (
        <MemoryRow key={i} op={op} index={i} />
      ))}
    </div>
  );
}

export default InspectorMemory;
