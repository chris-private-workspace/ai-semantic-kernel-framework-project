/**
 * File: frontend/src/features/chat_v2/components/blocks/SubagentForkBlock.tsx
 * Purpose: Renders subagent fork block — verbatim mockup re-point of page-chat.jsx L245-264.
 * Category: Frontend / chat_v2 / components / blocks
 * Scope: Phase 57.30 Day 4 §D2 (AD-Mockup-Direct-Port-Round-2 chatv2 shell repoint)
 *
 * Description:
 *   Inline block within AgentTurn body. Header row ("Fork · concurrent" +
 *   spawned N count) + per-agent row list (chevron + name + task + status
 *   badge + turns count). Source: mockup
 *   reference/design-mockups/page-chat.jsx L245-264; styles
 *   frontend/src/styles-mockup.css L899-916 (.subagent-tree + .subagent-row +
 *   .subagent-tree .indent).
 *
 *   Sprint 57.30 Day 4: re-pointed from translated-Tailwind utility classes
 *   (rounded-md border bg-bg-1 p-2 + flex flex-1 ... hover:bg-bg-2) to
 *   verbatim mockup `.subagent-tree` + `.subagent-row`. The border / background /
 *   padding / hover / cursor / font-mono are all CSS-owned by mockup;
 *   production no longer composes them via Tailwind.
 *
 *   Header row uses mockup `.row` class + inline-style verbatim (mockup L248
 *   `style={{ padding: "4px 8px", fontSize: 11, color: "var(--fg-muted)" }}`).
 *   Status badge uses verbatim mockup `.badge` family with tone class
 *   (`.badge.success` / `.badge.info`) per mockup L259
 *   `<Badge tone={a.status === "done" ? "success" : "info"} dot>`.
 *
 * Created: 2026-05-17 (Sprint 57.21 Day 2 §2.2)
 * Last Modified: 2026-06-11
 *
 * Modification History (newest-first):
 *   - 2026-06-11: Sprint 57.103 B2b — mode-aware label/icon (Teammate vs Fork) + real tokens vs 0t
 *   - 2026-05-23: Sprint 57.30 Day 4 §D2 — verbatim re-point Tailwind → mockup .subagent-tree/.subagent-row/.badge family
 *   - 2026-05-17: Initial extract from mockup L245-264 + Tailwind convert
 *
 * Related:
 *   - reference/design-mockups/page-chat.jsx L245-264 (source JSX)
 *   - frontend/src/styles-mockup.css L899-916 (.subagent-tree / .subagent-row / .indent)
 *   - frontend/src/styles-mockup.css L507-535 (.badge + tone variants)
 *   - ../../types.ts (SubagentForkBlock + SubagentEntry types)
 */

/* eslint-disable no-restricted-syntax -- verbatim re-point: mockup page-chat.jsx L248
   (header row inline padding/font/color), L256-260 (per-row inline color/flex/overflow)
   all use inline-style. Tokens via var(--*) — not literals. */

import { ChevronRight, GitFork, Users } from "lucide-react";

import type { SubagentForkBlock as SubagentForkBlockType } from "../../types";

const STATUS_BADGE_TONE: Record<"running" | "done", string> = {
  running: "info",
  done: "success",
};

export function SubagentForkBlock({ block }: { block: SubagentForkBlockType }): JSX.Element {
  // Sprint 57.103 (B2b): the inline block was a verbatim mockup port that hardcoded
  // "Fork · concurrent" + a per-row turn count — both wrong for a TEAMMATE spawn
  // (a teammate is not a fork; the turn count was always 0). Render a mode-aware
  // label/icon + the real token count (once the subagent completes) so the inline
  // block agrees with the authoritative Inspector Tree. The mockup `.subagent-tree` /
  // `.subagent-row` / `.badge` CSS vocabulary is unchanged — only the data-driven text.
  const allTeammate =
    block.agents.length > 0 && block.agents.every((a) => a.mode === "teammate");
  const HeaderIcon = allTeammate ? Users : GitFork;
  const headerLabel = allTeammate ? "Teammate · peer" : "Fork · concurrent";
  return (
    <div className="subagent-tree">
      <div
        className="row"
        style={{ padding: "4px 8px", fontSize: 11, color: "var(--fg-muted)" }}
      >
        <HeaderIcon size={12} />
        <span className="mono" style={{ color: "var(--primary)", fontWeight: 600 }}>
          {headerLabel}
        </span>
        <span className="mono subtle">
          spawned {block.agents.length} subagent{block.agents.length === 1 ? "" : "s"}
        </span>
      </div>
      {block.agents.map((a) => (
        <div key={a.id} className="subagent-row">
          <ChevronRight size={12} className="subtle" />
          <span style={{ color: "var(--primary)" }}>{a.name}</span>
          <span className="subtle">·</span>
          <span
            style={{
              color: "var(--fg-muted)",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
              flex: 1,
            }}
          >
            {a.task}
          </span>
          <span className={`badge ${STATUS_BADGE_TONE[a.status]} dot`}>
            {a.status}
          </span>
          <span className="subtle">
            {a.tokensUsed != null ? `${a.tokensUsed.toLocaleString()} tok` : ""}
          </span>
        </div>
      ))}
    </div>
  );
}
