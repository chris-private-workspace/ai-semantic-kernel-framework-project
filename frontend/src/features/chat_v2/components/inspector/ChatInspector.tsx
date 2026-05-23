/**
 * File: frontend/src/features/chat_v2/components/inspector/ChatInspector.tsx
 * Purpose: Right-rail Inspector — verbatim mockup re-point of page-chat.jsx L371-390 4-tab frame.
 * Category: Frontend / chat_v2 / components / inspector
 * Scope: Phase 57.30 Day 4 §D3 (AD-Mockup-Direct-Port-Round-2 chatv2 shell repoint)
 *
 * Description:
 *   Mockup L371-390 — 4-tab Inspector frame:
 *     - Turn:    populated via <InspectorTurn> (last AgentTurn KV + Block
 *                sequence + 2 action buttons)
 *     - Trace:   <ComingSoonInspectorTab name="Trace" ad="AD-ChatV2-Inspector-Trace-Phase2">
 *     - Memory:  <ComingSoonInspectorTab name="Memory" ad="AD-ChatV2-Inspector-Memory-Phase2">
 *     - Tree:    <ComingSoonInspectorTab name="Tree" ad="AD-ChatV2-Inspector-SubagentTree-Phase2">
 *
 *   Tab state is local; resets per page mount (mockup behavior). Backend feeds
 *   for Trace / Memory / Tree land Sprint 57.22+ per their respective carryover
 *   ADs in checklist §Carryover.
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
 *   - 2026-05-23: Sprint 57.30 Day 4 §D3 — verbatim re-point shared Tabs primitive → mockup .chat-inspector + inline .tabs/.tab buttons (a11y role="tab"/aria-selected preserved)
 *   - 2026-05-17: Sprint 57.21 Day 4 §4.1 — Day 3 stub → 4-tab frame + Turn tab populated + 3 coming-soon tabs
 *   - 2026-05-17: Sprint 57.21 Day 3 §3.2 — initial Day 3 stub
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L371-390 (ChatInspector 4-tab frame)
 *   - reference/design-mockups/ui.jsx L123-133 (Tabs shape)
 *   - frontend/src/styles-mockup.css L705-710 (.chat-inspector) + L590-610 (.tabs/.tab)
 *   - ./InspectorTurn.tsx (Turn tab content)
 *   - ./ComingSoonInspectorTab.tsx (Trace / Memory / Tree placeholders)
 *   - ../ChatLayout.tsx (right rail consumer)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: mockup page-chat.jsx L373
   (`<div style={{ borderBottom: "1px solid var(--border)" }}>` wrapping Tabs) uses
   inline-style; preserved verbatim per Layer-4 verbatim rule. */

import { useState } from "react";

import { ComingSoonInspectorTab } from "./ComingSoonInspectorTab";
import { InspectorTurn } from "./InspectorTurn";

type InspectorTabId = "turn" | "trace" | "memory" | "tree";

interface TabItem {
  id: InspectorTabId;
  label: string;
}

const TAB_ITEMS: TabItem[] = [
  { id: "turn", label: "Turn" },
  { id: "trace", label: "Trace" },
  { id: "memory", label: "Memory" },
  { id: "tree", label: "Tree" },
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
      {tab === "trace" && (
        <ComingSoonInspectorTab
          name="Trace"
          mockupSection="L434-466"
          carryoverAd="AD-ChatV2-Inspector-Trace-Phase2"
          hint="Cat 12 OTel spans waterfall — loop iteration timing, tool durations, subagent spans, HITL pauses."
        />
      )}
      {tab === "memory" && (
        <ComingSoonInspectorTab
          name="Memory"
          mockupSection="L468-487"
          carryoverAd="AD-ChatV2-Inspector-Memory-Phase2"
          hint="Cat 3 memory ops — READ / WRITE per scope (user / tenant / session) with key, value, timestamp."
        />
      )}
      {tab === "tree" && (
        <ComingSoonInspectorTab
          name="Tree"
          mockupSection="L489-531"
          carryoverAd="AD-ChatV2-Inspector-SubagentTree-Phase2"
          hint="Cat 11 subagent tree — live feed with mode / depth / concurrency / subtree tokens."
        />
      )}
    </aside>
  );
}

export default ChatInspector;
