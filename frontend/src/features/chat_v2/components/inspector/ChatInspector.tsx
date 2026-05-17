/**
 * File: frontend/src/features/chat_v2/components/inspector/ChatInspector.tsx
 * Purpose: Right-rail Inspector — 4-tab frame (Turn populated; Trace/Memory/Tree coming soon).
 * Category: Frontend / chat_v2 / components / inspector
 * Scope: Phase 57.21 Day 4 §4.1 (AD-ChatV2-Full-Mockup-Fidelity Phase-1)
 *
 * Description:
 *   Mockup L371-390 — 4-tab Inspector frame:
 *     - Turn:    populated this sprint via <InspectorTurn> (last AgentTurn KV
 *                + Block sequence + 2 actions)
 *     - Trace:   <ComingSoonInspectorTab name="Trace" ad="AD-ChatV2-Inspector-Trace-Phase2">
 *     - Memory:  <ComingSoonInspectorTab name="Memory" ad="AD-ChatV2-Inspector-Memory-Phase2">
 *     - Tree:    <ComingSoonInspectorTab name="Tree" ad="AD-ChatV2-Inspector-SubagentTree-Phase2">
 *
 *   Tab state is local; resets per page mount (mockup behavior). Backend feeds
 *   for Trace / Memory / Tree land Sprint 57.22+ per their respective carryover
 *   ADs in checklist §Carryover.
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 3 §3.2 stub) → 2026-05-17 (Sprint 57.21 Day 4 §4.1 full)
 *
 * Modification History (newest-first):
 *   - 2026-05-17: Sprint 57.21 Day 4 §4.1 — Day 3 stub → 4-tab frame + Turn tab populated + 3 coming-soon tabs
 *   - 2026-05-17: Sprint 57.21 Day 3 §3.2 — initial Day 3 stub
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L371-390 (ChatInspector 4-tab frame)
 *   - ./InspectorTurn.tsx (Turn tab content)
 *   - ./ComingSoonInspectorTab.tsx (Trace / Memory / Tree placeholders)
 *   - ../ChatLayout.tsx (right rail consumer)
 *   - frontend/src/components/ui/tabs.tsx (Sprint 57.19 NEW Tabs primitive)
 */

import { useState } from "react";

import { Tabs, type TabItem } from "@/components/ui/tabs";

import { ComingSoonInspectorTab } from "./ComingSoonInspectorTab";
import { InspectorTurn } from "./InspectorTurn";

type InspectorTabId = "turn" | "trace" | "memory" | "tree";

const TAB_ITEMS: TabItem[] = [
  { id: "turn", label: "Turn" },
  { id: "trace", label: "Trace" },
  { id: "memory", label: "Memory" },
  { id: "tree", label: "Tree" },
];

export function ChatInspector(): JSX.Element {
  const [tab, setTab] = useState<InspectorTabId>("turn");

  return (
    <aside
      data-testid="chat-inspector"
      className="flex h-full flex-col overflow-y-auto border-l border-border bg-bg-1 text-fg"
    >
      <Tabs
        items={TAB_ITEMS}
        value={tab}
        onChange={(id) => setTab(id as InspectorTabId)}
        ariaLabel="Inspector tabs"
      />

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
