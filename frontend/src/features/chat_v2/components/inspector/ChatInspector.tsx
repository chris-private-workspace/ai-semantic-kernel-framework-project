/**
 * File: frontend/src/features/chat_v2/components/inspector/ChatInspector.tsx
 * Purpose: Right-rail Inspector — verbatim mockup re-point of page-chat.jsx L371-390 4-tab frame.
 * Category: Frontend / chat_v2 / components / inspector
 * Scope: Phase 57.30 Day 4 §D3 (AD-Mockup-Direct-Port-Round-2 chatv2 shell repoint)
 *
 * Description:
 *   Mockup L371-390 — 4-tab Inspector frame (all 4 tabs now wired to real data):
 *     - Turn:    <InspectorTurn> (last AgentTurn KV + Block sequence + 2 buttons)
 *     - Trace:   <InspectorTrace> (Sprint 57.75 — A-5; span waterfall from
 *                span_started/span_ended SSE; chatStore.spans)
 *     - Memory:  <InspectorMemory> (Sprint 57.75 — A-5; memory ops list from
 *                memory_accessed SSE; chatStore.memoryOps)
 *     - Tree:    <InspectorTree> (Sprint 57.72 — A-5c; chatStore.subagents)
 *
 *   Tab state is local; resets per page mount (mockup behavior). Sprint 57.75
 *   wired the last 2 ComingSoon tabs (Trace + Memory), closing
 *   AD-ChatV2-Inspector-Trace-Phase2 + -Memory-Phase2.
 *
 *   Sprint 57.30 Day 4: re-pointed from shared shadcn-shaped Tabs primitive
 *   (frontend/src/components/ui/tabs.tsx — uses pre-57.18 tokens
 *   `border-primary`/`text-foreground`) to verbatim mockup `.chat-inspector`
 *   container + inline `.tabs` row of `.tab[data-active]` button-divs
 *   (mockup ui.jsx L123-133 Tabs shape; styles-mockup.css L590-610
 *   .tabs/.tab/.tab-count). Tab activation behavior + state + a11y
 *   (role="tab" + aria-selected) preserved verbatim.
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 3 §3.2 stub) → 2026-05-17 (Sprint 57.21 Day 4 §4.1 full)
 * Last Modified: 2026-05-23
 *
 * Modification History (newest-first):
 *   - 2026-06-24: Sprint 57.140 — add 5th "Todos" tab (research #1 task primitive; existing mockup classes, no new CSS)
 *   - 2026-06-03: Sprint 57.75 — wire Trace + Memory tabs (A-5); all 4 tabs now real (closes -Trace/-Memory-Phase2)
 *   - 2026-06-03: Sprint 57.72 — wire Tree tab to InspectorTree (A-5c); Trace/Memory stay ComingSoon
 *   - 2026-05-23: Sprint 57.30 Day 4 §D3 — verbatim re-point shared Tabs primitive → mockup .chat-inspector + inline .tabs/.tab buttons (a11y role="tab"/aria-selected preserved)
 *   - 2026-05-17: Sprint 57.21 Day 4 §4.1 — Day 3 stub → 4-tab frame + Turn tab populated + 3 coming-soon tabs
 *   - 2026-05-17: Sprint 57.21 Day 3 §3.2 — initial Day 3 stub
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L371-390 (ChatInspector 4-tab frame)
 *   - reference/design-mockups/ui.jsx L123-133 (Tabs shape)
 *   - frontend/src/styles-mockup.css L705-710 (.chat-inspector) + L590-610 (.tabs/.tab)
 *   - ./InspectorTurn.tsx (Turn tab content)
 *   - ./InspectorTrace.tsx (Trace tab content — Sprint 57.75)
 *   - ./InspectorMemory.tsx (Memory tab content — Sprint 57.75)
 *   - ./InspectorTree.tsx (Tree tab content — Sprint 57.72)
 *   - ../ChatLayout.tsx (right rail consumer)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: mockup page-chat.jsx L373
   (`<div style={{ borderBottom: "1px solid var(--border)" }}>` wrapping Tabs) uses
   inline-style; preserved verbatim per Layer-4 verbatim rule. */

import { useState } from "react";

import { InspectorMemory } from "./InspectorMemory";
import { InspectorTodos } from "./InspectorTodos";
import { InspectorTrace } from "./InspectorTrace";
import { InspectorTree } from "./InspectorTree";
import { InspectorTurn } from "./InspectorTurn";

type InspectorTabId = "turn" | "trace" | "memory" | "tree" | "todos";

interface TabItem {
  id: InspectorTabId;
  label: string;
}

// Sprint 57.140: "Todos" is a NEW tab for the explicit task primitive (research
// #1) — a feature the reference mockup doesn't cover. It reuses existing mockup
// .tab / .badge classes (no new CSS), so styles-mockup.css stays byte-identical.
const TAB_ITEMS: TabItem[] = [
  { id: "turn", label: "Turn" },
  { id: "trace", label: "Trace" },
  { id: "memory", label: "Memory" },
  { id: "tree", label: "Tree" },
  { id: "todos", label: "Todos" },
];

export function ChatInspector(): JSX.Element {
  const [tab, setTab] = useState<InspectorTabId>("turn");

  return (
    <aside data-testid="chat-inspector" className="chat-inspector">
      <div style={{ borderBottom: "1px solid var(--border)" }}>
        <div role="tablist" aria-label="Inspector tabs" className="tabs">
          {TAB_ITEMS.map((t) => {
            const active = tab === t.id;
            return (
              <button
                key={t.id}
                type="button"
                role="tab"
                aria-selected={active}
                data-active={active}
                onClick={() => setTab(t.id)}
                className="tab"
              >
                {t.label}
              </button>
            );
          })}
        </div>
      </div>

      {tab === "turn" && <InspectorTurn />}
      {tab === "trace" && <InspectorTrace />}
      {tab === "memory" && <InspectorMemory />}
      {tab === "tree" && <InspectorTree />}
      {tab === "todos" && <InspectorTodos />}
    </aside>
  );
}

export default ChatInspector;
